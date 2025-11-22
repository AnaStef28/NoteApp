# AI Notes - Semantic Search App

A Django application with AI-powered semantic search for notes using SentenceTransformers.

## Features

- ✅ Add notes via Django admin interface
- ✅ Automatic embedding generation using `all-MiniLM-L6-v2` model
- ✅ Semantic search through notes (finds similar meaning, not just keywords)
- ✅ Beautiful web interface at root URL (`/`)
- ✅ Admin interface for managing notes

## Installation

1. **Create a virtual environment** (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Run migrations**:
```bash
python manage.py migrate
```

4. **Create a superuser** (to access admin):
```bash
python manage.py createsuperuser
```

5. **Run the development server**:
```bash
python manage.py runserver
```

## Usage

1. **Access the app**: Open http://127.0.0.1:8000/ in your browser
2. **Add notes**: Click "Add/Manage Notes (Admin)" or go to http://127.0.0.1:8000/admin/
3. **Search**: Use the search box on the main page to find notes semantically

## How It Works

- When you create or update a note, the system automatically generates an embedding vector using SentenceTransformers
- The embedding is stored in the database as a JSON string
- When you search, the query is converted to an embedding and compared with all note embeddings using cosine similarity
- The top 5 most similar notes are returned

## Model Details

- **Model**: `all-MiniLM-L6-v2` (384 dimensions)
- **No GPU required**: Works on CPU
- **First run**: The model will be downloaded automatically (~90MB)

## Project Structure

```
project/
├── project/          # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── notes/            # Notes app
│   ├── models.py     # Note model
│   ├── admin.py      # Admin interface
│   ├── views.py      # Views and search logic
│   ├── utils.py      # Embedding utilities
│   └── templates/    # HTML templates
├── manage.py
├── requirements.txt
└── README.md
```

## Testing

See [TESTING.md](TESTING.md) for detailed testing documentation.

### Quick Start

```bash
# Install testing dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=notes --cov-report=html
```

## Monitoring

See [MONITORING.md](MONITORING.md) for detailed monitoring documentation.

### Health Check

```bash
# Command line
python manage.py health_check

# HTTP endpoint
curl http://localhost:8000/health/
```

### Metrics

```bash
curl http://localhost:8000/metrics/
```

## Maintenance

See [MAINTENANCE.md](MAINTENANCE.md) for detailed maintenance documentation.

### Common Tasks

```bash
# Backup database
python manage.py backup_database

# Regenerate missing embeddings
python manage.py regenerate_embeddings --missing-only

# Health check
python manage.py health_check --verbose
```

## Notes

- The first time you run the app, SentenceTransformers will download the model (~90MB)
- Embeddings are generated automatically when you save a note
- Search is performed in-memory (for small datasets, this is fine)
- For production, consider using a vector database like PostgreSQL with pgvector or a dedicated vector DB

## Documentation

- [TESTING.md](TESTING.md) - Testing guide and best practices
- [MONITORING.md](MONITORING.md) - Monitoring and health checks
- [MAINTENANCE.md](MAINTENANCE.md) - Maintenance procedures and troubleshooting

