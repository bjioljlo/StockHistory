# Documentation Directory Structure

This directory contains all project documentation organized by type and purpose.

## Directory Structure

```
docs/
├── plans/      # Project plans and specifications
└── guides/     # User and developer guides
```

## Plans (`plans/`)

Project planning and specification documents:

- `reports_sql_optimization_plan.md` - SQL storage optimization plan for reports
- `StockHistoryImprovementSsuggestions.md` - General improvement suggestions

## Guides (`guides/`)

User manuals and developer documentation:

- `AGENTS.md` - Agent architecture and design documentation
- `backup_strategy.md` - Backup strategy and procedures
- `DEVELOPMENT_GUIDE.md` - Development guidelines and best practices
- `GEMINI.md` - Gemini integration documentation
- `MONGODB_CACHE_IMPLEMENTATION.md` - MongoDB cache implementation details
- `PERFORMANCE_OPTIMIZATION_GUIDE.md` - Performance optimization techniques
- `phase4_optimization_final_report.md` - Phase 4 optimization final report
- `PROJECT_CONTEXT.md` - Project overview and architecture

## Documentation Standards

### File Naming
- Use lowercase with underscores for file names
- End with `.md` extension
- Use descriptive names that clearly indicate content

### Content Structure
Each document should include:

1. **Title** - Clear, descriptive title
2. **Overview** - Brief description of the document's purpose
3. **Table of Contents** - For longer documents
4. **Main Content** - Well-organized sections
5. **References** - Links to related documents

### Markdown Formatting
- Use headers (# ## ###) for section hierarchy
- Use code blocks for code examples
- Use tables for structured data
- Use links for cross-references
- Use lists for steps and enumerations

## Contributing to Documentation

### Adding New Documents

1. **Choose appropriate subdirectory**:
   - `plans/` for specifications, plans, and designs
   - `guides/` for tutorials, manuals, and references

2. **Follow naming conventions**:
   - Use descriptive, lowercase names with underscores
   - Include relevant keywords for searchability

3. **Document structure**:
   - Start with a clear title and overview
   - Include table of contents for documents >5 sections
   - End with version information and last updated date

4. **Content quality**:
   - Write in clear, concise language
   - Include examples where helpful
   - Keep information up-to-date

### Updating Existing Documents

1. Update version information and dates
2. Maintain backward compatibility in links
3. Review and update cross-references
4. Ensure consistency with other documents

### Review Process

All documentation changes should:

1. Be reviewed by at least one other team member
2. Follow the established style guidelines
3. Be tested for clarity and accuracy
4. Be committed with descriptive commit messages

## Documentation Tools

### Local Development
- Use any Markdown editor or IDE with Markdown support
- Preview with VS Code Markdown Preview or similar tools
- Validate links and formatting before committing

### Building Documentation
```bash
# Generate table of contents (if using automated tools)
# Convert to other formats if needed
```

## Related Resources

- [Project README](../README.md)
- [Scripts Documentation](../scripts/README.md)
- [Tests Documentation](../tests/README.md)

## Version History

- **v1.0** - Initial documentation structure
  - Created organized directory structure
  - Moved existing documents to appropriate locations
  - Added documentation standards and guidelines
