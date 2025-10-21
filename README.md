# AI Assistant Skills Collection

Collection of custom skills for AI coding assistants like [Claude Code](https://claude.com/code).

## Available Skills

### Odoo

- **[odoo_model_inspector](odoo/odoo_model_inspector/)** - Analyze Odoo model inheritance chains and fields across modules. Shows complete "who stands on whom" picture with all fields, methods, and dependencies.

## Installation

### Install specific skill to your project

```bash
# Clone this repository
git clone https://github.com/YOUR_USERNAME/ai-assistant-skills

# Copy skill to your Claude Code project
cp -r ai-assistant-skills/odoo/odoo_model_inspector /path/to/your/project/.claude/skills/
```

### Direct use from repository

```bash
# Clone into your project's .claude directory
cd /path/to/your/project
git clone https://github.com/straga/ai-assistant-skills .claude/skills_library

# Symlink skills you want to use
ln -s ../.claude/skills_library/odoo/odoo_model_inspector .claude/skills/odoo_model_inspector
```

## Usage

Each skill contains:
- `Skill.md` - Instructions for AI assistant on when and how to use the skill
- `README.md` - Technical documentation for developers
- Implementation files (Python scripts, parsers, formatters, etc.)

Skills are automatically discovered by Claude Code when placed in `.claude/skills/` directory.

## Skill Categories

- **odoo/** - Odoo ERP framework skills
- **python/** - Python development skills (coming soon)
- **web/** - Web development skills (coming soon)

## Contributing

Feel free to submit your own skills via pull requests.

Each skill should follow the structure:
```
skill_name/
├── Skill.md          # AI assistant instructions
├── README.md         # Developer documentation
├── main_script.py    # Entry point
├── config.py         # Configuration (if needed)
└── ...               # Supporting modules
```

## License

MIT License - see individual skills for specific licensing information.

## Requirements

- Claude Code (or compatible AI coding assistant)
- Python 3.8+ (for Python-based skills)
- Skill-specific dependencies listed in each skill's README.md
