# Odoo Skills

Collection of skills for working with Odoo ERP framework.

## Available Skills

### odoo_model_inspector

Analyzes Odoo model inheritance chains and fields across modules.

**Use cases:**
- Understanding complete model structure before making changes
- Finding which module defines a specific field
- Checking if a field already exists before adding it
- Understanding module dependencies through models
- Debugging "field not found" errors

**Features:**
- Zero code execution (AST parsing only)
- Complete inheritance chain visualization
- Field types and required status
- Method detection with super() calls
- Circular dependency handling
- Configurable addon paths

**Quick start:**
```bash
# Copy to your project
cp -r odoo_model_inspector /path/to/your/project/.claude/skills/

# Customize addon paths in config.py
# Then use from Claude Code
```

See [odoo_model_inspector/README.md](odoo_model_inspector/README.md) for detailed documentation.

## Requirements

- Python 3.8+
- Odoo project structure (for model analysis)
- No external dependencies (uses Python stdlib only)
