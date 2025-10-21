"""
Configuration for Odoo Model Inspector

Customize these paths for your project structure.
"""

from pathlib import Path

# Project root (4 levels up from this file: skills/odoo_model_inspector/config.py)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent

# Odoo addon directories (relative to PROJECT_ROOT)
# Add or remove directories as needed for your project
ADDON_DIRECTORIES = [
    'server/addons',
    'server/odoo/addons',
    'addons_oca',
]

# Output directory for Markdown analysis files
# Relative to PROJECT_ROOT or absolute path
OUTPUT_DIRECTORY = '.odoo_inspect'

# Alternative: use absolute path
# OUTPUT_DIRECTORY = Path.home() / 'Documents' / 'odoo_analysis'