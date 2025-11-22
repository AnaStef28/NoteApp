"""
Management command to regenerate embeddings for notes.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from notes.models import Note
from notes.utils import generate_embedding
from django.contrib import messages
import sys


class Command(BaseCommand):
    help = 'Regenerate embeddings for notes (useful when upgrading embedding models)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Regenerate embeddings for all notes (including those with existing embeddings)',
        )
        parser.add_argument(
            '--missing-only',
            action='store_true',
            help='Only regenerate embeddings for notes without embeddings (default)',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of notes to process in each batch (default: 100)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually doing it',
        )

    def handle(self, *args, **options):
        all_notes = options['all']
        missing_only = options['missing_only']
        batch_size = options['batch_size']
        dry_run = options['dry_run']
        
        # Default to missing-only if neither flag is set
        if not all_notes and not missing_only:
            missing_only = True
        
        # Get notes to process
        if all_notes:
            notes = Note.objects.all()
            self.stdout.write(self.style.WARNING('Regenerating embeddings for ALL notes...'))
        else:
            notes = Note.objects.filter(
                Q(embedding='') | Q(embedding__isnull=True)
            )
            self.stdout.write('Regenerating embeddings for notes without embeddings...')
        
        total_count = notes.count()
        
        if total_count == 0:
            self.stdout.write(self.style.SUCCESS('No notes to process.'))
            return
        
        if dry_run:
            self.stdout.write(self.style.WARNING(f'DRY RUN: Would process {total_count} notes'))
            return
        
        self.stdout.write(f'Processing {total_count} notes in batches of {batch_size}...\n')
        
        processed = 0
        errors = 0
        
        # Process in batches
        for i in range(0, total_count, batch_size):
            batch = notes[i:i+batch_size]
            
            with transaction.atomic():
                for note in batch:
                    try:
                        if not note.content:
                            self.stdout.write(
                                self.style.WARNING(f'  Skipping note {note.id}: empty content')
                            )
                            continue
                        
                        embedding = generate_embedding(note.content)
                        note.set_embedding_list(embedding)
                        note.save(update_fields=['embedding'])
                        
                        processed += 1
                        
                        if processed % 10 == 0:
                            self.stdout.write(f'  Processed {processed}/{total_count}...')
                    
                    except Exception as e:
                        errors += 1
                        self.stdout.write(
                            self.style.ERROR(f'  Error processing note {note.id}: {e}')
                        )
        
        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS(f'✓ Processed: {processed} notes'))
        if errors > 0:
            self.stdout.write(self.style.ERROR(f'✗ Errors: {errors}'))
        else:
            self.stdout.write(self.style.SUCCESS('✓ No errors'))

