# Monitoring Guide

This document describes the monitoring and health check capabilities of the AI Notes application.

## Health Check Endpoint

### `/health/`

Returns the health status of the system. Returns HTTP 200 if healthy, 503 if unhealthy.

**Response Format:**
```json
{
  "status": "healthy",
  "checks": {
    "database": "ok",
    "embedding_model": "ok",
    "notes": {
      "total": 100,
      "with_embeddings": 95,
      "without_embeddings": 5
    }
  }
}
```

**Usage:**
```bash
curl http://localhost:8000/health/
```

## Metrics Endpoint

### `/metrics/`

Returns basic metrics about the system.

**Response Format:**
```json
{
  "notes": {
    "total": 100,
    "with_embeddings": 95
  },
  "database": {
    "size_bytes": 1048576,
    "size_mb": 1.0
  }
}
```

**Usage:**
```bash
curl http://localhost:8000/metrics/
```

## Management Commands

### Health Check Command

Run a comprehensive health check:

```bash
python manage.py health_check
```

With verbose output:

```bash
python manage.py health_check --verbose
```

### Database Backup

Backup the database:

```bash
python manage.py backup_database
```

Options:
- `--output-dir`: Directory to store backups (default: `backups`)
- `--keep`: Number of backups to keep (default: 10)

Example:
```bash
python manage.py backup_database --output-dir /backups --keep 30
```

### Regenerate Embeddings

Regenerate embeddings for notes:

```bash
# Only regenerate missing embeddings (default)
python manage.py regenerate_embeddings --missing-only

# Regenerate all embeddings
python manage.py regenerate_embeddings --all

# Dry run to see what would be done
python manage.py regenerate_embeddings --dry-run

# Process in batches
python manage.py regenerate_embeddings --batch-size 50
```

## Logging

Logs are written to:
- `logs/django.log` - General application logs
- `logs/django_errors.log` - Error logs only

Log levels:
- **INFO**: General information
- **ERROR**: Error conditions

## Monitoring Best Practices

1. **Set up health check monitoring**: Configure your monitoring system (e.g., Prometheus, Datadog) to poll `/health/` every 30-60 seconds.

2. **Set up alerts**: Alert on:
   - Health check returns 503
   - Database connection failures
   - Embedding model failures
   - High number of notes without embeddings

3. **Regular backups**: Schedule regular database backups using cron or a task scheduler:
   ```bash
   # Add to crontab (daily at 2 AM)
   0 2 * * * cd /path/to/project && python manage.py backup_database
   ```

4. **Monitor metrics**: Track:
   - Total number of notes
   - Number of notes without embeddings
   - Database size
   - Search response times

5. **Log analysis**: Regularly review error logs for patterns or recurring issues.

## Integration with Monitoring Tools

### Prometheus

You can use a simple exporter or scrape the `/metrics/` endpoint. For more advanced metrics, consider using `django-prometheus`.

### Docker Health Check

Add to your `docker-compose.yml`:

```yaml
services:
  web:
    # ... other config ...
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### Kubernetes Liveness/Readiness Probes

```yaml
livenessProbe:
  httpGet:
    path: /health/
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health/
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

