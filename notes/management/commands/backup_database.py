"""
Management command to backup the database.
"""
from django.core.management.base import BaseCommand
from django.conf import settings
import os
import shutil
from datetime import datetime


class Command(BaseCommand):
    help = 'Backup the SQLite database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            type=str,
            default='backups',
            help='Directory to store backups (default: backups)',
        )
        parser.add_argument(
            '--keep',
            type=int,
            default=10,
            help='Number of backups to keep (default: 10)',
        )

    def handle(self, *args, **options):
        output_dir = options['output_dir']
        keep_count = options['keep']
        
        # Get database path
        db_path = settings.DATABASES['default']['NAME']
        
        if not os.path.exists(db_path):
            self.stdout.write(self.style.ERROR(f'Database file not found: {db_path}'))
            return
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'db_backup_{timestamp}.sqlite3'
        backup_path = os.path.join(output_dir, backup_filename)
        
        try:
            # Copy database file
            shutil.copy2(db_path, backup_path)
            
            # Get file size
            file_size = os.path.getsize(backup_path) / (1024 * 1024)  # MB
            
            self.stdout.write(self.style.SUCCESS(
                f'✓ Database backed up successfully: {backup_path} ({file_size:.2f} MB)'
            ))
            
            # Clean up old backups
            self._cleanup_old_backups(output_dir, keep_count)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Backup failed: {e}'))
    
    def _cleanup_old_backups(self, backup_dir, keep_count):
        """Remove old backup files, keeping only the most recent ones."""
        try:
            # Get all backup files
            backup_files = [
                os.path.join(backup_dir, f)
                for f in os.listdir(backup_dir)
                if f.startswith('db_backup_') and f.endswith('.sqlite3')
            ]
            
            # Sort by modification time (newest first)
            backup_files.sort(key=os.path.getmtime, reverse=True)
            
            # Remove old backups
            if len(backup_files) > keep_count:
                for old_backup in backup_files[keep_count:]:
                    os.remove(old_backup)
                    self.stdout.write(f'  Removed old backup: {os.path.basename(old_backup)}')
        
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Warning: Could not clean up old backups: {e}'))

