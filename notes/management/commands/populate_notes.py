from typing import Dict, List, Optional, Sequence, Tuple
from urllib.parse import quote

import requests
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from notes.models import Note
from notes.utils import generate_embedding

WIKI_SUMMARY_URL = "https://{lang}.wikipedia.org/api/rest_v1/page/summary/{title}"
WIKI_RANDOM_URL = "https://{lang}.wikipedia.org/api/rest_v1/page/random/summary"
WIKI_EXTRACT_URL = "https://{lang}.wikipedia.org/w/api.php"

DEFAULT_TOPICS: Sequence[str] = (
    "Artificial intelligence",
    "Quantum computing",
    "Pythagorean theorem",
    "Neural network",
    "Climate change mitigation",
    "Mars exploration",
    "CRISPR gene editing",
    "Blockchain",
    "Renewable energy storage",
    "History of the internet",
    "Human immune system",
    "Black holes",
    "Photosynthesis",
    "Renaissance art",
    "Data privacy",
)

HTTP_HEADERS = {
    "User-Agent": "AI Notes Seeder/1.0 (https://github.com/)",
    "Accept": "application/json",
}


class Command(BaseCommand):
    help = "Populate the Notes table with high-quality Wikipedia content."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=12,
            help="Number of notes to create/update (default: 12)",
        )
        parser.add_argument(
            "--topics",
            nargs="+",
            help="Specific Wikipedia topics to pull. Defaults to curated list.",
        )
        parser.add_argument(
            "--random",
            action="store_true",
            help="Use random Wikipedia pages instead of curated topics.",
        )
        parser.add_argument(
            "--language",
            default="en",
            help="Wikipedia language edition (default: en).",
        )
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete existing notes before seeding new ones.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Fetch and display the notes without writing to the database.",
        )

    def handle(self, *args, **options):
        topics = options["topics"]
        use_random = options["random"]
        limit = max(1, options["limit"])
        language = options["language"]
        dry_run = options["dry_run"]
        flush = options["flush"]

        if topics and use_random:
            raise CommandError("Cannot supply --topics and --random simultaneously.")

        topic_source = topics or list(DEFAULT_TOPICS)

        records = self._collect_wikipedia_notes(
            topic_source=topic_source,
            use_random=use_random,
            limit=limit,
            language=language,
        )

        if not records:
            raise CommandError("Unable to fetch any Wikipedia content.")

        if dry_run:
            self.stdout.write(self.style.MIGRATE_HEADING("Dry run: notes to be created"))
            for title, content in records:
                preview = content[:160].replace("\n", " ") + ("..." if len(content) > 160 else "")
                self.stdout.write(f"- {title}: {preview}")
            return

        if flush:
            deleted, _ = Note.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Deleted {deleted} existing notes."))

        created, updated = self._persist_notes(records)
        self.stdout.write(
            self.style.SUCCESS(
                f"Finished seeding notes. Created {created}, updated {updated} (Total requested: {limit})."
            )
        )

    # ------------------------------------------------------------------
    def _collect_wikipedia_notes(
        self,
        topic_source: Sequence[str],
        use_random: bool,
        limit: int,
        language: str,
    ) -> List[Tuple[str, str]]:
        """Fetch and build (title, content) tuples ready for persistence."""
        results: List[Tuple[str, str]] = []
        seen_titles = set()
        topic_index = 0
        max_attempts = limit * 5  # give ourselves room for network/errors
        attempts = 0

        while len(results) < limit and attempts < max_attempts:
            attempts += 1
            topic = None
            if use_random:
                summary = self._fetch_random_summary(language)
            else:
                topic = topic_source[topic_index % len(topic_source)]
                topic_index += 1
                summary = self._fetch_summary(topic, language)

            if not summary:
                continue

            title = summary.get("title") or topic
            if not title or title in seen_titles:
                continue

            content = self._build_content_block(summary, language)
            if not content or len(content.split()) < 40:
                continue

            source_url = summary.get("content_urls", {}).get("desktop", {}).get("page")
            if source_url:
                content = f"{content}\n\nSource: {source_url}"

            seen_titles.add(title)
            results.append((title, content))

        if len(results) < limit:
            self.stdout.write(
                self.style.WARNING(
                    f"Requested {limit} notes but only collected {len(results)} unique Wikipedia extracts."
                )
            )

        return results

    def _fetch_summary(self, topic: str, language: str) -> Optional[Dict]:
        return self._request_json(
            WIKI_SUMMARY_URL.format(lang=language, title=quote(topic)),
            params={"redirect": "true"},
        )

    def _fetch_random_summary(self, language: str) -> Optional[Dict]:
        return self._request_json(WIKI_RANDOM_URL.format(lang=language))

    def _request_json(self, url: str, params: Optional[Dict] = None) -> Optional[Dict]:
        try:
            response = requests.get(url, headers=HTTP_HEADERS, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            self.stdout.write(self.style.WARNING(f"Request failed for {url}: {exc}"))
            return None

    def _fetch_long_extract(self, title: str, language: str) -> Optional[str]:
        params = {
            "action": "query",
            "format": "json",
            "prop": "extracts",
            "titles": title,
            "explaintext": 1,
            "exchars": 1400,
            "redirects": 1,
        }
        data = self._request_json(WIKI_EXTRACT_URL.format(lang=language), params=params)
        if not data:
            return None

        pages = data.get("query", {}).get("pages", {})
        if not pages:
            return None

        page = next(iter(pages.values()))
        extract = page.get("extract")
        return extract.strip() if extract else None

    def _build_content_block(self, summary: Dict, language: str) -> Optional[str]:
        pieces: List[str] = []
        description = summary.get("description")
        summary_extract = summary.get("extract")
        title = summary.get("title")

        if description and description not in summary_extract:
            pieces.append(description.strip().rstrip(".") + ".")
        if summary_extract:
            pieces.append(summary_extract.strip())

        if title:
            long_extract = self._fetch_long_extract(title, language)
            if long_extract and long_extract not in pieces:
                pieces.append(long_extract)

        combined = "\n\n".join(piece for piece in pieces if piece)
        return combined.strip() or None

    @transaction.atomic
    def _persist_notes(self, records: List[Tuple[str, str]]) -> Tuple[int, int]:
        created = 0
        updated = 0

        for title, content in records:
            note, was_created = Note.objects.get_or_create(title=title, defaults={"content": content})
            if not was_created:
                note.content = content
                updated += 1
            else:
                created += 1

            embedding = generate_embedding(content)
            note.set_embedding_list(embedding)
            note.save()

        return created, updated

