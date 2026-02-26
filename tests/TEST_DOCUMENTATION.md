"""
Test Suite Documentation

This document provides an overview of the test suite for the Clips AI Server project.

## Test Structure

The test suite is organized into the following modules:

### 1. conftest.py - Pytest Configuration and Fixtures
Contains shared fixtures used across all tests:
- test_db: In-memory SQLite database session for each test
- test_client: FastAPI test client with dependency overrides
- sample_clip_request: Sample ClipGenerationRequest instance
- sample_clip_job: Sample ClipJob database record
- cleanup_temp_files: Fixture for cleaning up temporary test files
- temp_test_dir: Session-level temporary directory

### 2. test_api_routes.py - API Endpoint Tests
Tests for the FastAPI routes:

TestHealthCheck:
- test_ping_endpoint: Verifies /ping endpoint returns 200 with pong=true

TestGenerateClip:
- test_generate_clip_success: Valid request creates job and returns 202
- test_generate_clip_minimal_request: Only required fields work
- test_generate_clip_missing_required_field: Missing video_path returns 422
- test_generate_clip_invalid_times: Negative times are rejected
- test_generate_clip_title_too_long: Title > 256 chars rejected
- test_generate_clip_description_too_long: Description > 1024 chars rejected

TestGetJobStatus:
- test_get_job_status_pending: Returns correct data for pending jobs
- test_get_job_status_completed: Shows output_file for completed jobs
- test_get_job_status_failed: Shows error_message for failed jobs
- test_get_job_status_processing: Shows correct status for processing
- test_get_job_status_invalid_job_id: Returns 404 for non-existent job
- test_get_job_status_empty_job_id: Handles empty job ID gracefully

### 3. test_models.py - Database Model Tests
Tests for the SQLAlchemy ORM models:

TestJobStatusEnum:
- test_job_status_values: Enum has all 4 expected values
- test_job_status_count: Exactly 4 statuses defined
- test_job_status_from_string: Can create from string values
- test_job_status_invalid_value: Invalid status raises ValueError

TestClipJobModel:
- test_clip_job_creation: Basic model creation works
- test_clip_job_with_all_fields: All fields can be populated
- test_clip_job_with_error_message: Error messages are stored
- test_clip_job_unique_job_id: job_id uniqueness constraint works
- test_clip_job_status_update: Status can be updated
- test_clip_job_default_values: Default values are applied
- test_clip_job_timestamps: Timestamps are auto-set
- test_clip_job_query_by_job_id: Can query by job_id
- test_clip_job_query_by_status: Can query by status
- test_clip_job_table_name: Correct table name is used

### 4. test_schemas.py - Pydantic Schema Tests
Tests for request and response validation schemas:

TestClipGenerationRequest:
- test_valid_request_with_all_fields: Full request validates
- test_valid_request_minimal_fields: Minimal request validates
- test_missing_required_field: video_path is required
- test_negative_start_time_validation: Negative times rejected
- test_negative_end_time_validation: Negative times rejected
- test_zero_times_are_valid: Zero times are allowed
- test_title_max_length: Title > 256 chars rejected
- test_title_at_max_length: Title = 256 chars allowed
- test_description_max_length: Description > 1024 chars rejected
- test_description_at_max_length: Description = 1024 chars allowed
- test_empty_tags_list: Empty tags list allowed
- test_tags_with_multiple_items: Multiple tags work
- test_request_serialization: Can serialize to dict

TestClipGenerationResponse:
- test_response_creation: Can create response
- test_response_serialization: Can serialize to dict
- test_response_missing_required_field: All fields required

TestJobStatusResponse:
- test_response_creation_pending: Pending status response works
- test_response_creation_completed: Completed response with output_file
- test_response_creation_failed: Failed response with error_message
- test_response_serialization: Datetime serialization works
- test_response_missing_required_field: job_id is required
- test_response_with_all_timestamps: All timestamps can be set

### 5. test_services.py - Service Layer Tests
Tests for StorageService and ClipGenerator:

TestStorageService:
- test_storage_service_initialization: Service initializes correctly
- test_directories_created_on_init: Directories are created
- test_get_output_path: Output paths generated correctly
- test_get_output_path_creates_job_directory: Job dirs auto-created
- test_cleanup_temp_file_existing: Existing files are deleted
- test_cleanup_temp_file_nonexistent: Missing files handled gracefully
- test_cleanup_job_directory: Job directories are removed
- test_cleanup_job_directory_nonexistent: Missing dirs handled gracefully
- test_file_exists_true: Identifies existing files
- test_file_exists_false: Identifies missing files
- test_file_exists_directory: Identifies directories

TestClipGenerator:
- test_clip_generator_initialization: Can initialize with db session
- test_clip_generator_clipsai_initialization: Handles clipsai availability
- test_clip_generator_has_storage: StorageService is initialized
- test_clip_generator_multiple_instances: Can create multiple instances

## Running the Tests

### Install Test Dependencies
pip install -r requirements.txt

### Run All Tests
pytest

### Run Tests with Verbose Output
pytest -v

### Run Tests with Coverage Report
pytest --cov=app --cov-report=html

### Run Specific Test File
pytest tests/test_api_routes.py

### Run Specific Test Class
pytest tests/test_models.py::TestJobStatusEnum

### Run Specific Test
pytest tests/test_api_routes.py::TestHealthCheck::test_ping_endpoint

### Run Tests Matching Pattern
pytest -k "pending"  # Runs all tests with "pending" in the name

### Run Tests with Output
pytest -s  # Shows print statements
pytest --tb=short  # Shorter traceback format
pytest --tb=long   # Full traceback format

### Run Tests in Parallel (requires pytest-xdist)
pytest -n auto

## Test Coverage

To generate a coverage report:

pytest --cov=app --cov-report=html --cov-report=term-missing

This generates:
- Terminal output showing coverage percentage
- HTML report in htmlcov/index.html with line-by-line coverage

## Continuous Integration

The test suite is designed to be CI/CD friendly:
- All tests are isolated with fixtures
- Database is in-memory (no external dependencies)
- No temporary files persist after tests
- Tests run quickly (no real video processing)

Example GitHub Actions workflow:
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.10
      - run: pip install -r requirements.txt
      - run: pytest --cov=app
```

## Test Guidelines

When adding new tests:

1. **Use descriptive names**: test_<feature>_<scenario>
2. **One assertion focus**: Each test should test one thing
3. **Use fixtures**: Reuse fixtures from conftest.py
4. **Document with docstrings**: Explain what's being tested and why
5. **Test both success and failure cases**
6. **Keep tests independent**: No test should depend on another
7. **Mock external dependencies**: Don't make real API calls or file operations

## Troubleshooting

### "ModuleNotFoundError: No module named 'app'"
Make sure you're running pytest from the project root directory:
cd /home/lcezario/code/ClipsAiServer && pytest

### "sqlalchemy.exc.OperationalError: database is locked"
This usually means multiple tests are trying to use the same database.
Tests are isolated with the test_db fixture, but if you see this error,
ensure you're not running tests in parallel without proper isolation.

### "No such file or directory: './clips_output'"
The test fixtures create these directories. If you see this error after tests,
it means the cleanup isn't running. Check that conftest.py is in the tests/ directory.

## Performance

Average test execution time:
- test_api_routes.py: ~2-3 seconds
- test_models.py: ~1 second
- test_schemas.py: ~1 second
- test_services.py: ~1 second
- Total: ~5-6 seconds for full suite

To identify slow tests:
pytest --durations=10
"""
