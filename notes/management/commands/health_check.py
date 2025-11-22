"""
Management command to check system health.
"""
from django.core.management.base import BaseCommand
from django.db import connection
from notes.models import Note
from notes.utils import get_model
import sys


class Command(BaseCommand):
    help = 'Check system health and report any issues'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed information',
        )

    def handle(self, *args, **options):
        verbose = options['verbose']
        issues = []
        warnings = []
        
        self.stdout.write(self.style.SUCCESS('Running health checks...\n'))
        
        # 1. Database connectivity
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            self.stdout.write(self.style.SUCCESS('✓ Database connection: OK'))
        except Exception as e:
            issues.append(f"Database connection failed: {e}")
            self.stdout.write(self.style.ERROR('✗ Database connection: FAILED'))
        
        # 2. Model loading
        try:
            model = get_model()
            test_embedding = model.encode("test")
            self.stdout.write(self.style.SUCCESS('✓ Embedding model: OK'))
        except Exception as e:
            issues.append(f"Embedding model failed: {e}")
            self.stdout.write(self.style.ERROR('✗ Embedding model: FAILED'))
        
        # 3. Note statistics
        try:
            total_notes = Note.objects.count()
            notes_with_embeddings = Note.objects.exclude(embedding='').exclude(embedding__isnull=True).count()
            notes_without_embeddings = total_notes - notes_with_embeddings
            
            self.stdout.write(self.style.SUCCESS(f'✓ Notes: {total_notes} total'))
            
            if notes_without_embeddings > 0:
                warnings.append(f"{notes_without_embeddings} notes without embeddings")
                self.stdout.write(self.style.WARNING(f'⚠ Notes without embeddings: {notes_without_embeddings}'))
            
            if verbose:
                self.stdout.write(f'  - With embeddings: {notes_with_embeddings}')
                self.stdout.write(f'  - Without embeddings: {notes_without_embeddings}')
        except Exception as e:
            issues.append(f"Note statistics failed: {e}")
            self.stdout.write(self.style.ERROR('✗ Note statistics: FAILED'))
        
        # 4. Database size check
        try:
            from django.conf import settings
            import os
            db_path = settings.DATABASES['default']['NAME']
            if os.path.exists(db_path):
                db_size = os.path.getsize(db_path) / (1024 * 1024)  # MB
                self.stdout.write(self.style.SUCCESS(f'✓ Database size: {db_size:.2f} MB'))
                
                if db_size > 100:  # Warn if > 100MB
                    warnings.append(f"Database size is {db_size:.2f} MB (consider optimization)")
            else:
                warnings.append("Database file not found")
        except Exception as e:
            if verbose:
                warnings.append(f"Could not check database size: {e}")
        
        # Summary
        self.stdout.write('\n' + '='*50)
        if issues:
            self.stdout.write(self.style.ERROR(f'\n✗ Found {len(issues)} critical issue(s):'))
            for issue in issues:
                self.stdout.write(self.style.ERROR(f'  - {issue}'))
            sys.exit(1)
        elif warnings:
            self.stdout.write(self.style.WARNING(f'\n⚠ Found {len(warnings)} warning(s):'))
            for warning in warnings:
                self.stdout.write(self.style.WARNING(f'  - {warning}'))
            self.stdout.write(self.style.SUCCESS('\n✓ System is operational'))
            sys.exit(0)
        else:
            self.stdout.write(self.style.SUCCESS('\n✓ All checks passed! System is healthy.'))
            sys.exit(0)

