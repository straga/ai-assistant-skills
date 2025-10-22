"""
Configuration for Odoo Icon Maker

Customize these paths and settings for your project structure.
"""

from pathlib import Path

# Project root (3 levels up from this file: odoo/odoo_icon_maker/config.py)
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Odoo addon directories (relative to PROJECT_ROOT)
# Add or remove directories as needed for your project
ADDON_DIRECTORIES = [
    'addons_dev_ext',
    'addons_ext',
]

# Icon size in pixels (Odoo standard is 128x128)
ICON_SIZE = 128
