# Maintenance Guide

This guide covers routine maintenance tasks for the AI Notes application.

## Regular Maintenance Tasks

### Daily

- **Monitor health checks**: Check `/health/` endpoint status
- **Review error logs**: Check `logs/django_errors.log` for errors

### Weekly

- **Database backup**: Run backup command
- **Check for notes without embeddings**: Review metrics
- **Review system performance**: Check response times

### Monthly

- **Database optimization**: Run VACUUM on SQLite (if needed)
- **Review and clean old backups**: Ensure backup rotation is working
- **Update dependencies**: Review and update packages (carefully)

## Database Maintenance

### Backup Database

```bash
python manage.py backup_database
```

Backups are stored in `backups/` directory by default. The command automatically:
- Creates timestamped backup files
- Keeps only the most recent N backups (default: 10)

### Restore Database

To restore from a backup:

```bash
# Stop the application
# Copy backup file
cp backups/db_backup_YYYYMMDD_HHMMSS.sqlite3 db.sqlite3
# Restart the application
```

### Database Optimization (SQLite)

For SQLite, you can optimize the database:

```bash
python manage.py dbshell
```

Then in SQLite shell:
```sql
VACUUM;
ANALYZE;
```

Or use a management command wrapper (create if needed).

## Embedding Maintenance

### Regenerate Missing Embeddings

If notes are missing embeddings:

```bash
python manage.py regenerate_embeddings --missing-only
```

### Regenerate All Embeddings

When upgrading the embedding model:

```bash
python manage.py regenerate_embeddings --all
```

**Note**: This can take a long time for large datasets. Consider running in batches or during maintenance windows.

### Check Embedding Status

```bash
python manage.py health_check --verbose
```

## Log Management

### Log Rotation

Logs are written to:
- `logs/django.log` - General logs
- `logs/django_errors.log` - Error logs

Set up log rotation using `logrotate` (Linux) or similar:

```bash
# /etc/logrotate.d/aib-notes
/path/to/project/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0640 www-data www-data
}
```

### Manual Log Cleanup

```bash
# Keep last 7 days
find logs/ -name "*.log" -mtime +7 -delete
```

## Performance Monitoring

### Check System Health

```bash
python manage.py health_check
```

### Monitor Metrics

```bash
curl http://localhost:8000/metrics/
```

### Check Database Size

```bash
ls -lh db.sqlite3
```

## Upgrading Dependencies

### Review Updates

```bash
pip list --outdated
```

### Update Requirements

1. Update `requirements.txt` or `requirements-dev.txt`
2. Test in development environment
3. Run full test suite
4. Deploy to staging
5. Monitor for issues
6. Deploy to production

### Update Embedding Model

If upgrading the embedding model:

1. **Backup database** first
2. Regenerate all embeddings:
   ```bash
   python manage.py regenerate_embeddings --all
   ```
3. Test semantic search accuracy
4. Monitor performance

## Troubleshooting

### Notes Not Appearing in Search

1. Check if note has embedding:
   ```python
   python manage.py shell
   >>> from notes.models import Note
   >>> note = Note.objects.get(id=X)
   >>> note.get_embedding_list()
   ```

2. Regenerate embedding if missing:
   ```bash
   python manage.py regenerate_embeddings --missing-only
   ```

### Slow Search Performance

1. Check number of notes
2. Verify embeddings are present
3. Consider:
   - Adding database indexes
   - Using a vector database (pgvector, Qdrant)
   - Implementing caching

### Database Errors

1. Check database file permissions
2. Verify disk space
3. Check database integrity:
   ```bash
   python manage.py dbshell
   ```
   ```sql
   PRAGMA integrity_check;
   ```

### Embedding Model Issues

1. Check model cache:
   ```bash
   ls -lh ~/.cache/huggingface/
   ```

2. Clear cache if needed:
   ```bash
   rm -rf ~/.cache/huggingface/transformers/
   ```

3. Model will re-download on next use

## Automated Maintenance

### Cron Jobs

Set up cron jobs for automated maintenance:

```bash
# Edit crontab
crontab -e

# Daily backup at 2 AM
0 2 * * * cd /path/to/project && python manage.py backup_database

# Weekly health check report (send to email)
0 9 * * 1 cd /path/to/project && python manage.py health_check --verbose | mail -s "Weekly Health Check" admin@example.com

# Daily regenerate missing embeddings
0 3 * * * cd /path/to/project && python manage.py regenerate_embeddings --missing-only
```

### Systemd Timer (Alternative)

Create a systemd service and timer for backups:

```ini
# /etc/systemd/system/aib-backup.service
[Unit]
Description=AI Notes Database Backup

[Service]
Type=oneshot
WorkingDirectory=/path/to/project
ExecStart=/usr/bin/python3 manage.py backup_database
User=www-data
```

```ini
# /etc/systemd/system/aib-backup.timer
[Unit]
Description=Daily AI Notes Backup

[Timer]
OnCalendar=daily
OnCalendar=02:00

[Install]
WantedBy=timers.target
```

Enable:
```bash
sudo systemctl enable aib-backup.timer
sudo systemctl start aib-backup.timer
```

## Disaster Recovery

### Backup Strategy

1. **Daily backups**: Automated via cron
2. **Weekly off-site backup**: Copy backups to remote location
3. **Test restore**: Periodically test restoring from backups

### Recovery Procedure

1. Stop the application
2. Restore database from backup
3. Verify data integrity
4. Regenerate any missing embeddings
5. Run health checks
6. Restart application
7. Monitor for issues

## Security Maintenance

- **Update Django**: Keep Django and dependencies updated
- **Review logs**: Check for suspicious activity
- **Rotate secrets**: Change SECRET_KEY periodically (requires re-encryption if using encrypted fields)
- **Review permissions**: Ensure file permissions are correct

## Performance Tuning

### Database

- Add indexes for frequently queried fields
- Consider migrating to PostgreSQL with pgvector for better performance
- Regular VACUUM and ANALYZE

### Embeddings

- Cache frequently used embeddings
- Consider batch processing for large updates
- Monitor memory usage

### Application

- Enable caching (Redis/Memcached)
- Use CDN for static files
- Optimize queries (use select_related/prefetch_related)

## Support and Resources

- Django Documentation: https://docs.djangoproject.com/
- Sentence Transformers: https://www.sbert.net/
- Project Issues: Check GitHub issues or project documentation

