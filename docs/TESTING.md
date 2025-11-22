# Testing Guide

This document describes the testing setup and how to run tests for the AI Notes application.

## Test Structure

Tests are organized in the `notes/tests/` directory:

- `test_models.py` - Unit tests for Note model
- `test_utils.py` - Unit tests for utility functions (embeddings, similarity)
- `test_admin.py` - Unit tests for admin functionality
- `test_integration.py` - Integration tests for semantic search
- `test_load.py` - Load/performance tests

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test File

```bash
pytest notes/tests/test_models.py
```

### Run Specific Test

```bash
pytest notes/tests/test_models.py::TestNoteModel::test_create_note
```

### Run Tests by Marker

```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Load tests (slow)
pytest -m slow

# Skip slow tests
pytest -m "not slow"
```

### Run with Coverage

```bash
pytest --cov=notes --cov-report=html --cov-report=term
```

This generates:
- Terminal output with coverage summary
- HTML report in `htmlcov/index.html`

### Run with Verbose Output

```bash
pytest -v
```

### Run Tests in Parallel

```bash
pip install pytest-xdist
pytest -n auto
```

## Test Markers

Tests are marked with the following markers:

- `@pytest.mark.unit` - Unit tests (fast)
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow running tests
- `@pytest.mark.embedding` - Tests that require embedding generation

## Writing Tests

### Example Unit Test

```python
@pytest.mark.unit
@pytest.mark.django_db
def test_create_note():
    """Test creating a basic note."""
    note = Note.objects.create(
        title="Test Title",
        content="Test content"
    )
    assert note.id is not None
    assert note.title == "Test Title"
```

### Example Integration Test

```python
@pytest.mark.integration
@pytest.mark.django_db
def test_semantic_search():
    """Test semantic search functionality."""
    # Create test data
    note = Note.objects.create(...)
    
    # Perform search
    results = perform_search("query")
    
    # Assertions
    assert len(results) > 0
```

## Test Fixtures

Common fixtures are defined in `conftest.py`:

- `admin_user` - Admin user for testing
- `regular_user` - Regular user for testing
- `sample_note` - Single note with embedding
- `multiple_notes` - Multiple notes with embeddings
- `mock_request` - Mock request object

### Using Fixtures

```python
def test_with_fixture(sample_note):
    assert sample_note.title == "Test Note"
```

## Continuous Integration

Tests run automatically on:
- Push to `main` or `develop` branches
- Pull requests

See `.github/workflows/test.yml` for CI configuration.

## Test Database

Tests use a separate test database (SQLite in memory by default). The database is created fresh for each test run.

## Performance Testing

Load tests are marked with `@pytest.mark.slow` and `@pytest.mark.load`. These tests:
- Create larger datasets
- Measure performance metrics
- Verify system behavior under load

Run load tests separately:
```bash
pytest -m slow
```

## Best Practices

1. **Write tests first** (TDD) when possible
2. **Keep tests fast** - Unit tests should run quickly
3. **Use descriptive names** - Test names should describe what they test
4. **One assertion per concept** - Don't test multiple things in one test
5. **Use fixtures** - Reuse common test data
6. **Clean up** - Tests should be independent and not leave side effects
7. **Test edge cases** - Test both happy path and error conditions

## Debugging Tests

### Run with PDB

```bash
pytest --pdb
```

### Print statements

```python
def test_something():
    result = some_function()
    print(f"Result: {result}")  # Will show in pytest output with -s
    assert result == expected
```

Run with `-s` flag:
```bash
pytest -s
```

### Verbose output

```bash
pytest -vv  # Very verbose
```

## Coverage Goals

Aim for:
- **Unit tests**: 80%+ coverage
- **Integration tests**: Cover all major workflows
- **Critical paths**: 100% coverage

Check current coverage:
```bash
pytest --cov=notes --cov-report=term-missing
```

