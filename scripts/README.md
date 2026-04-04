# Scripts Directory Structure

This directory contains all project scripts organized by their purpose and usage context.

## Directory Structure

```
scripts/
├── development/     # Development and debugging tools
├── migration/       # Database migration and optimization scripts
├── production/      # Production environment scripts
└── utilities/       # General utility scripts
```

## Development Scripts (`development/`)

Scripts for development, testing, and debugging:

- `analyze_db_structure.py` - Database structure analysis
- `check_db.py` - Database health checks
- `data_cleanup.py` - Data cleanup utilities
- `delete_problematic_records.py` - Remove problematic data records

## Migration Scripts (`migration/`)

Database migration and optimization tools:

- `database_optimization_plan.py` - Database optimization planning
- `migration_risk_assessment.py` - Migration risk evaluation
- `migration_script.py` - Database migration execution
- `validation_script.py` - Migration validation tools

## Production Scripts (`production/`)

Production environment management:

- `backup_scheduler.bat` - Automated backup scheduling
- `production_backup_script.py` - Production backup utilities
- `production_migration_script.py` - Production migration tools
- `production_monitoring_script.py` - Production monitoring scripts

## Utility Scripts (`utilities/`)

General purpose utilities:

- `partition_management.py` - Database partition management
- `simple_cache_test.py` - Cache testing utilities

## Usage Guidelines

1. **Development scripts** should be used during development and testing phases
2. **Migration scripts** require careful review and testing before production use
3. **Production scripts** should only be executed in production environments
4. **Utility scripts** can be used across all environments

## Contributing

When adding new scripts:

1. Place them in the appropriate subdirectory based on their purpose
2. Update this README with the new script description
3. Ensure proper documentation and error handling
4. Test thoroughly before committing

## Related Documentation

- [Project README](../README.md)
- [Development Guide](../docs/guides/DEVELOPMENT_GUIDE.md)
- [Performance Optimization Guide](../docs/guides/PERFORMANCE_OPTIMIZATION_GUIDE.md)
