# Tests Directory Structure

This directory contains all test files organized by test type and scope.

## Directory Structure

```
tests/
├── unit/           # Unit tests for individual components
└── integration/    # Integration tests for system interactions
```

## Unit Tests (`unit/`)

Individual component testing:

### BackTest Components
- `BackTestFilterData_test.py` - BackTest filter data testing
- `BackTestInfoData_test.py` - BackTest info data testing
- `StockInfoDataInHand_test.py` - Stock info data in hand testing
- `StockInfos_test.py` - Stock infos testing

### Service Components
- `test_cache_service.py` - Cache service testing
- `test_data_compression.py` - Data compression testing
- `test_performance_monitor.py` - Performance monitoring testing
- `test_query_optimizer.py` - Query optimization testing
- `test_read_write_split.py` - Read/write split testing
- `test_threadpool.py` - Thread pool testing

### Utility Components
- `test_tools_report_date.py` - Report date tools testing
- `tools_test.py` - General tools testing

## Integration Tests (`integration/`)

System-level testing:

- `test_backup_services.py` - Backup service integration testing
- `test_integration.py` - General integration testing
- `test_mongodb_cache.py` - MongoDB cache integration testing

## Running Tests

### Run All Tests
```bash
pytest
```

### Run Unit Tests Only
```bash
pytest tests/unit/
```

### Run Integration Tests Only
```bash
pytest tests/integration/
```

### Run Specific Test File
```bash
pytest tests/unit/test_cache_service.py
```

### Run with Coverage
```bash
pytest --cov=src --cov-report=html
```

## Test Categories

### Unit Tests
- Test individual functions and methods
- Mock external dependencies
- Fast execution
- Isolated testing

### Integration Tests
- Test component interactions
- May require database connections
- Test end-to-end workflows
- Slower execution

## Test Naming Convention

- Unit test files: `test_<component_name>.py`
- Test methods: `test_<functionality>_<scenario>()`
- Use descriptive names that explain what is being tested

## Test Data

- Use fixtures for test data setup
- Avoid hardcoded test data in test methods
- Use factory patterns for complex object creation

## Continuous Integration

Tests are automatically run on:
- Pull request creation
- Code pushes to main branch
- Scheduled nightly runs

## Contributing

When adding new tests:

1. Place unit tests in `tests/unit/`
2. Place integration tests in `tests/integration/`
3. Follow naming conventions
4. Include docstrings explaining test purpose
5. Ensure tests are independent and repeatable
6. Add appropriate fixtures for test data

## Test Coverage Goals

- Unit tests: >90% coverage
- Integration tests: Cover critical user journeys
- Performance tests: Meet response time requirements

## Related Documentation

- [Development Guide](../docs/guides/DEVELOPMENT_GUIDE.md)
- [Project README](../README.md)
- [Performance Optimization Guide](../docs/guides/PERFORMANCE_OPTIMIZATION_GUIDE.md)
