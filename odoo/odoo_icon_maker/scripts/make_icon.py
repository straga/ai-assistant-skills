#!/usr/bin/env python3
"""
Odoo Icon Maker - Generate icons for Odoo modules
Automatically creates icon PNG and updates manifest/menu files
"""

import argparse
import json
import math
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("Error: PIL/Pillow not installed. Run: pip install Pillow")
    sys.exit(1)

# Import configuration
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import ADDON_DIRECTORIES, ICON_SIZE


class OdooIconMaker:
    """Generate icons for Odoo modules"""

    # Use values from config.py
    ICON_SIZE = ICON_SIZE
    ADDON_DIRS = ADDON_DIRECTORIES

    def __init__(self, module_name: str, description: str,
                 colors: Optional[List[str]] = None, dry_run: bool = False):
        self.module_name = module_name
        self.description = description
        self.colors = colors or []
        self.dry_run = dry_run
        self.result = {
            'status': 'pending',
            'icon_created': False,
            'icon_path': None,
            'manifest_updated': False,
            'menu_files_updated': [],
            'backups_created': [],
            'warnings': []
        }

    def run(self) -> Dict:
        """Main execution flow"""
        try:
            # Find module directory
            module_path = self._find_module()
            if not module_path:
                self.result['status'] = 'error'
                self.result['error'] = f"Module directory not found: {self.module_name}"
                return self.result

            # Create icon
            icon_path = self._create_icon(module_path)
            if icon_path:
                self.result['icon_created'] = True
                self.result['icon_path'] = str(icon_path.relative_to(Path.cwd()))

            # Update manifest
            if self._update_manifest(module_path):
                self.result['manifest_updated'] = True

            # Update menu files
            updated_menus = self._update_menu_files(module_path)
            self.result['menu_files_updated'] = updated_menus

            self.result['status'] = 'success'
            return self.result

        except Exception as e:
            self.result['status'] = 'error'
            self.result['error'] = str(e)
            return self.result

    def _find_module(self) -> Optional[Path]:
        """Find module directory in addon paths"""
        cwd = Path.cwd()

        # Check each addon directory
        for addon_dir in self.ADDON_DIRS:
            module_path = cwd / addon_dir / self.module_name
            if module_path.exists() and module_path.is_dir():
                return module_path

        # Check root directory
        root_module = cwd / self.module_name
        if root_module.exists() and root_module.is_dir():
            return root_module

        return None

    def _create_icon(self, module_path: Path) -> Optional[Path]:
        """Generate icon PNG file"""
        # Create static/description directory
        icon_dir = module_path / 'static' / 'description'
        icon_path = icon_dir / 'icon.png'

        if not self.dry_run:
            icon_dir.mkdir(parents=True, exist_ok=True)

        # Generate icon based on description
        img = self._create_smart_icon()

        # Save icon
        if not self.dry_run:
            img.save(icon_path, 'PNG', optimize=True)

            # Verify file
            if not icon_path.exists():
                raise Exception(f"Failed to create icon at {icon_path}")

        return icon_path

    def _create_smart_icon(self) -> Image.Image:
        """Create intelligent icon based on description keywords using primitives composition"""
        size = self.ICON_SIZE
        desc_lower = self.description.lower()

        # Detect primitives to draw based on keywords
        primitives = []

        # Manufacturing/Production
        if any(kw in desc_lower for kw in ['workcenter', 'manufacturing', 'machine', 'production', 'gear']):
            primitives.append('gear')

        # Calendar/Planning
        if any(kw in desc_lower for kw in ['calendar', 'schedule', 'planning', 'event', 'date']):
            primitives.append('calendar')

        # Tasks/Checklist
        if any(kw in desc_lower for kw in ['task', 'checklist', 'todo', 'check']):
            primitives.append('checkbox')

        # Documents/Files
        if any(kw in desc_lower for kw in ['document', 'file', 'paper', 'form']):
            primitives.append('document')

        # Folder/Directory
        if any(kw in desc_lower for kw in ['folder', 'directory']):
            primitives.append('folder')

        # Users/People
        if any(kw in desc_lower for kw in ['user', 'people', 'person', 'team', 'employee']):
            primitives.append('user')

        # Charts/Analytics
        if any(kw in desc_lower for kw in ['chart', 'analytics', 'graph', 'report', 'statistics']):
            primitives.append('chart')

        # Warehouse/Boxes
        if any(kw in desc_lower for kw in ['warehouse', 'inventory', 'stock', 'box', 'package']):
            primitives.append('box')

        # Messages/Communication
        if any(kw in desc_lower for kw in ['message', 'chat', 'telegram', 'communication', 'notification']):
            primitives.append('message')

        # Settings/Configuration
        if any(kw in desc_lower for kw in ['settings', 'config', 'setup', 'preferences']):
            primitives.append('settings')

        # Arrow/Flow
        if any(kw in desc_lower for kw in ['arrow', 'flow', 'process', 'workflow']):
            primitives.append('arrow')

        # Lock/Security
        if any(kw in desc_lower for kw in ['lock', 'security', 'secure', 'protection']):
            primitives.append('lock')

        # Choose background color based on module type
        bg_colors = self._get_background_colors(desc_lower)

        # Create composed icon
        return self._compose_icon(size, primitives, bg_colors)

    def _get_background_colors(self, desc_lower: str) -> Tuple[Tuple[int, int, int], Tuple[int, int, int]]:
        """Choose background colors based on module category"""
        if self.colors and len(self.colors) >= 2:
            return (self._hex_to_rgb(self.colors[0]), self._hex_to_rgb(self.colors[1]))

        # Manufacturing/Production - industrial blue
        if any(kw in desc_lower for kw in ['manufacturing', 'production', 'workcenter']):
            return ((52, 73, 94), (41, 128, 185))

        # Calendar/Planning - red/orange
        if any(kw in desc_lower for kw in ['calendar', 'schedule', 'planning']):
            return ((231, 76, 60), (192, 57, 43))

        # Tasks - green
        if any(kw in desc_lower for kw in ['task', 'checklist', 'todo']):
            return ((46, 204, 113), (39, 174, 96))

        # Messages - blue (Telegram)
        if any(kw in desc_lower for kw in ['message', 'chat', 'telegram']):
            return ((0, 136, 204), (0, 108, 163))

        # Documents - purple
        if any(kw in desc_lower for kw in ['document', 'file', 'folder']):
            return ((155, 89, 182), (142, 68, 173))

        # Warehouse - orange
        if any(kw in desc_lower for kw in ['warehouse', 'inventory', 'stock']):
            return ((243, 156, 18), (230, 126, 34))

        # Analytics - teal
        if any(kw in desc_lower for kw in ['analytics', 'chart', 'report']):
            return ((26, 188, 156), (22, 160, 133))

        # Default - blue
        return ((52, 152, 219), (41, 128, 185))

    def _compose_icon(self, size: int, primitives: list, bg_colors: Tuple[Tuple[int, int, int], Tuple[int, int, int]]) -> Image.Image:
        """Compose icon from primitives on white background with colored circle"""
        # Create white background with rounded corners
        img = Image.new('RGBA', (size, size), (255, 255, 255, 255))

        # Apply rounded corners to white background
        margin = 4
        radius = size // 8
        mask = Image.new('L', (size, size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([margin, margin, size - margin, size - margin],
                                   radius=radius, fill=255)
        img.putalpha(mask)

        draw = ImageDraw.Draw(img)

        # Draw colored circle in center
        circle_radius = size * 0.42
        circle_center = size / 2
        circle_color = bg_colors[0]  # Use first color for circle
        draw.ellipse([circle_center - circle_radius, circle_center - circle_radius,
                     circle_center + circle_radius, circle_center + circle_radius],
                    fill=circle_color)

        if not primitives:
            # No primitives detected - use module initials
            initials = self._get_initials(self.module_name)
            text_bbox = draw.textbbox((0, 0), initials)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            text_x = (size - text_width) // 2
            text_y = (size - text_height) // 2 - size * 0.05
            draw.text((text_x + 2, text_y + 2), initials, fill=(0, 0, 0, 50))
            draw.text((text_x, text_y), initials, fill=(255, 255, 255))
            return img

        # Position primitives based on count
        if len(primitives) == 1:
            # Single primitive - center
            self._draw_primitive(img, primitives[0], size * 0.5, size * 0.5, size * 0.5)
        elif len(primitives) == 2:
            # Two primitives - left and right
            self._draw_primitive(img, primitives[0], size * 0.38, size * 0.5, size * 0.38)
            self._draw_primitive(img, primitives[1], size * 0.62, size * 0.5, size * 0.38)
        else:
            # Three or more - main center, others as accents
            self._draw_primitive(img, primitives[0], size * 0.5, size * 0.5, size * 0.42)
            self._draw_primitive(img, primitives[1], size * 0.72, size * 0.35, size * 0.25)
            if len(primitives) > 2:
                self._draw_primitive(img, primitives[2], size * 0.28, size * 0.65, size * 0.2)

        return img

    def _draw_primitive(self, img: Image.Image, primitive: str, x: float, y: float, prim_size: float):
        """Draw a single primitive at specified position"""
        draw = ImageDraw.Draw(img)

        if primitive == 'gear':
            self._primitive_gear(draw, x, y, prim_size)
        elif primitive == 'calendar':
            self._primitive_calendar(draw, x, y, prim_size)
        elif primitive == 'checkbox':
            self._primitive_checkbox(draw, x, y, prim_size)
        elif primitive == 'document':
            self._primitive_document(draw, x, y, prim_size)
        elif primitive == 'folder':
            self._primitive_folder(draw, x, y, prim_size)
        elif primitive == 'user':
            self._primitive_user(draw, x, y, prim_size)
        elif primitive == 'chart':
            self._primitive_chart(draw, x, y, prim_size)
        elif primitive == 'box':
            self._primitive_box(draw, x, y, prim_size)
        elif primitive == 'message':
            self._primitive_message(draw, x, y, prim_size)
        elif primitive == 'settings':
            self._primitive_settings(draw, x, y, prim_size)
        elif primitive == 'arrow':
            self._primitive_arrow(draw, x, y, prim_size)
        elif primitive == 'lock':
            self._primitive_lock(draw, x, y, prim_size)

    # ========== PRIMITIVES ==========

    def _primitive_gear(self, draw: ImageDraw.Draw, cx: float, cy: float, size: float):
        """Draw gear primitive - gray metallic"""
        radius = size * 0.35
        teeth_count = 8
        teeth_size = size * 0.08

        # Colors
        gear_body = (149, 165, 166)  # Gray
        gear_outline = (127, 140, 141)
        center_hole = (52, 73, 94)  # Dark blue-gray

        # Draw gear teeth
        for i in range(teeth_count):
            angle = (360 / teeth_count) * i
            rad = math.radians(angle)
            x1 = cx + (radius + teeth_size) * math.cos(rad)
            y1 = cy + (radius + teeth_size) * math.sin(rad)
            draw.line([(cx, cy), (x1, y1)], fill=gear_outline, width=2)

        # Gear body
        draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
                    fill=gear_body, outline=gear_outline, width=2)

        # Center hole
        hole_radius = radius * 0.3
        draw.ellipse([cx - hole_radius, cy - hole_radius, cx + hole_radius, cy + hole_radius],
                    fill=center_hole, outline=gear_outline, width=1)

    def _primitive_calendar(self, draw: ImageDraw.Draw, cx: float, cy: float, size: float):
        """Draw calendar primitive - red header"""
        w = size * 0.8
        h = size * 0.8
        x = cx - w / 2
        y = cy - h / 2

        # Colors
        header_color = (231, 76, 60)  # Red
        body_color = (255, 255, 255)  # White
        binding_color = (189, 195, 199)  # Light gray
        date_color = (52, 73, 94)  # Dark gray
        highlight_color = (231, 76, 60)  # Red for highlighted date

        # Calendar body
        draw.rounded_rectangle([int(x), int(y + h * 0.15), int(x + w), int(y + h)],
                              radius=3, fill=body_color, outline=(200, 200, 200), width=1)

        # Header
        draw.rounded_rectangle([int(x), int(y + h * 0.15), int(x + w), int(y + h * 0.35)],
                              radius=3, fill=header_color)

        # Spiral bindings
        for i in range(2):
            bx = x + w * 0.3 + i * w * 0.4
            bw = w * 0.1
            by1 = y
            by2 = y + h * 0.2
            if bw > 1:
                draw.rounded_rectangle([int(bx), int(by1), int(bx + bw), int(by2)],
                                      radius=max(1, int(bw//2)), fill=binding_color)

        # Grid squares
        for row in range(2):
            for col in range(2):
                gx = x + col * w * 0.4 + w * 0.15
                gy = y + row * w * 0.25 + h * 0.45
                gs = w * 0.12
                color = highlight_color if (row == 1 and col == 0) else date_color
                draw.rectangle([int(gx), int(gy), int(gx + gs), int(gy + gs)], fill=color)

    def _primitive_checkbox(self, draw: ImageDraw.Draw, cx: float, cy: float, size: float):
        """Draw checkbox with checkmark primitive - green checkmark"""
        box_size = size * 0.6
        x = cx - box_size / 2
        y = cy - box_size / 2

        # Colors
        box_color = (255, 255, 255)  # White
        box_outline = (189, 195, 199)  # Gray
        check_color = (46, 204, 113)  # Green

        # Checkbox
        draw.rounded_rectangle([x, y, x + box_size, y + box_size],
                              radius=4, fill=box_color, outline=box_outline, width=2)

        # Checkmark
        draw.line([(x + box_size * 0.2, y + box_size * 0.5),
                  (x + box_size * 0.4, y + box_size * 0.75),
                  (x + box_size * 0.8, y + box_size * 0.25)],
                 fill=check_color, width=3)

    def _primitive_document(self, draw: ImageDraw.Draw, cx: float, cy: float, size: float):
        """Draw document primitive - blue"""
        w = size * 0.6
        h = size * 0.75
        x = cx - w / 2
        y = cy - h / 2
        fold = w * 0.25

        # Colors
        doc_color = (52, 152, 219)  # Blue
        doc_outline = (41, 128, 185)  # Darker blue
        fold_color = (41, 128, 185)  # Darker blue for fold
        line_color = (255, 255, 255, 200)  # White transparent

        # Document body
        points = [
            (x, y), (x + w - fold, y), (x + w, y + fold),
            (x + w, y + h), (x, y + h)
        ]
        draw.polygon(points, fill=doc_color, outline=doc_outline, width=2)

        # Folded corner
        fold_points = [(x + w - fold, y), (x + w, y + fold), (x + w - fold, y + fold)]
        draw.polygon(fold_points, fill=fold_color, outline=doc_outline, width=1)

        # Text lines
        for i in range(3):
            ly = y + h * 0.35 + i * h * 0.15
            draw.line([(x + w * 0.15, ly), (x + w * 0.85, ly)], fill=(255, 255, 255), width=1)

    def _primitive_folder(self, draw: ImageDraw.Draw, cx: float, cy: float, size: float):
        """Draw folder primitive - yellow"""
        w = size * 0.8
        h = size * 0.6
        x = cx - w / 2
        y = cy - h / 2

        # Colors
        folder_color = (241, 196, 15)  # Yellow
        folder_outline = (243, 156, 18)  # Darker yellow

        # Folder tab
        tab_w = w * 0.4
        draw.rectangle([x, y, x + tab_w, y + h * 0.3], fill=folder_color, outline=folder_outline, width=1)

        # Folder body
        draw.rounded_rectangle([x, y + h * 0.25, x + w, y + h],
                              radius=3, fill=folder_color, outline=folder_outline, width=2)

    def _primitive_user(self, draw: ImageDraw.Draw, cx: float, cy: float, size: float):
        """Draw user icon primitive - dark gray"""
        # Colors
        user_color = (52, 73, 94)  # Dark blue-gray
        user_outline = (44, 62, 80)  # Darker

        # Head
        head_radius = size * 0.2
        draw.ellipse([cx - head_radius, cy - size * 0.3 - head_radius,
                     cx + head_radius, cy - size * 0.3 + head_radius],
                    fill=user_color, outline=user_outline, width=2)

        # Body (shoulders)
        body_points = [
            (cx - size * 0.35, cy + size * 0.35),
            (cx - size * 0.25, cy - size * 0.1),
            (cx + size * 0.25, cy - size * 0.1),
            (cx + size * 0.35, cy + size * 0.35)
        ]
        draw.polygon(body_points, fill=user_color, outline=user_outline, width=2)

    def _primitive_chart(self, draw: ImageDraw.Draw, cx: float, cy: float, size: float):
        """Draw bar chart primitive - teal"""
        w = size * 0.7
        h = size * 0.6
        x = cx - w / 2
        y = cy - h / 2

        # Colors
        bar_colors = [(26, 188, 156), (22, 160, 133), (26, 188, 156), (22, 160, 133)]  # Teal variants
        bar_outline = (22, 160, 133)

        # Bars
        bar_heights = [0.4, 0.7, 0.5, 0.9]
        bar_width = w * 0.18
        for i, height in enumerate(bar_heights):
            bx = x + i * w * 0.25
            by = y + h * (1 - height)
            bh = h * height
            draw.rectangle([bx, by, bx + bar_width, y + h],
                          fill=bar_colors[i], outline=bar_outline, width=1)

    def _primitive_box(self, draw: ImageDraw.Draw, cx: float, cy: float, size: float):
        """Draw box/package primitive - orange"""
        box_size = size * 0.65
        x = cx - box_size / 2
        y = cy - box_size / 2

        # Colors
        box_color = (230, 126, 34)  # Orange
        box_outline = (211, 84, 0)  # Darker orange
        tape_color = (241, 196, 15)  # Yellow

        # Box
        draw.rectangle([x, y, x + box_size, y + box_size],
                      fill=box_color, outline=box_outline, width=2)

        # Tape cross
        draw.line([(x + box_size * 0.5, y), (x + box_size * 0.5, y + box_size)],
                 fill=tape_color, width=3)
        draw.line([(x, y + box_size * 0.5), (x + box_size, y + box_size * 0.5)],
                 fill=tape_color, width=3)

    def _primitive_message(self, draw: ImageDraw.Draw, cx: float, cy: float, size: float):
        """Draw message bubble primitive - white with blue dots"""
        w = size * 0.7
        h = size * 0.55
        x = cx - w / 2
        y = cy - h / 2

        # Colors
        bubble_color = (255, 255, 255)  # White
        bubble_outline = (189, 195, 199)  # Light gray
        dot_color = (52, 152, 219)  # Blue

        # Message bubble
        draw.rounded_rectangle([x, y, x + w, y + h],
                              radius=6, fill=bubble_color, outline=bubble_outline, width=2)

        # Tail
        tail_points = [
            (x + w * 0.2, y + h),
            (x + w * 0.15, y + h + size * 0.15),
            (x + w * 0.35, y + h)
        ]
        draw.polygon(tail_points, fill=bubble_color, outline=bubble_outline, width=2)

        # Dots
        for i in range(3):
            dot_x = x + w * 0.3 + i * w * 0.2
            dot_y = y + h * 0.5
            dot_r = size * 0.05
            draw.ellipse([dot_x - dot_r, dot_y - dot_r, dot_x + dot_r, dot_y + dot_r],
                        fill=dot_color)

    def _primitive_settings(self, draw: ImageDraw.Draw, cx: float, cy: float, size: float):
        """Draw settings/sliders primitive - gray"""
        w = size * 0.6
        h = size * 0.7
        x = cx - w / 2
        y = cy - h / 2

        # Colors
        track_color = (189, 195, 199)  # Light gray
        knob_color = (127, 140, 141)  # Medium gray
        knob_outline = (52, 73, 94)  # Dark gray

        # Three sliders
        for i in range(3):
            slider_y = y + h * 0.25 + i * h * 0.25

            # Track
            draw.line([(x, slider_y), (x + w, slider_y)],
                     fill=track_color, width=2)

            # Knob
            knob_x = x + w * (0.3 + i * 0.2)
            knob_r = size * 0.08
            draw.ellipse([knob_x - knob_r, slider_y - knob_r,
                         knob_x + knob_r, slider_y + knob_r],
                        fill=knob_color, outline=knob_outline, width=2)

    def _primitive_arrow(self, draw: ImageDraw.Draw, cx: float, cy: float, size: float):
        """Draw arrow primitive - white"""
        arrow_size = size * 0.6

        # Colors
        arrow_color = (255, 255, 255)  # White

        # Arrow shaft
        draw.line([(cx - arrow_size * 0.4, cy), (cx + arrow_size * 0.4, cy)],
                 fill=arrow_color, width=4)

        # Arrow head
        head_points = [
            (cx + arrow_size * 0.4, cy),
            (cx + arrow_size * 0.2, cy - arrow_size * 0.25),
            (cx + arrow_size * 0.2, cy + arrow_size * 0.25)
        ]
        draw.polygon(head_points, fill=arrow_color)

    def _primitive_lock(self, draw: ImageDraw.Draw, cx: float, cy: float, size: float):
        """Draw lock primitive - golden yellow"""
        lock_w = size * 0.5
        lock_h = size * 0.55
        x = cx - lock_w / 2
        y = cy - lock_h / 2 + size * 0.1

        # Colors
        lock_color = (241, 196, 15)  # Golden yellow
        lock_outline = (243, 156, 18)  # Darker yellow
        shackle_color = (189, 195, 199)  # Gray
        keyhole_color = (52, 73, 94)  # Dark gray

        # Shackle
        shackle_w = lock_w * 0.7
        shackle_h = size * 0.25
        draw.arc([cx - shackle_w / 2, y - shackle_h, cx + shackle_w / 2, y],
                start=180, end=0, fill=shackle_color, width=3)

        # Body
        draw.rounded_rectangle([x, y, x + lock_w, y + lock_h],
                              radius=4, fill=lock_color, outline=lock_outline, width=2)

        # Keyhole
        kh_y = y + lock_h * 0.4
        kh_r = lock_w * 0.12
        draw.ellipse([cx - kh_r, kh_y - kh_r, cx + kh_r, kh_y + kh_r],
                    fill=keyhole_color)
        draw.rectangle([cx - kh_r * 0.4, kh_y, cx + kh_r * 0.4, y + lock_h * 0.75],
                      fill=keyhole_color)

    def _create_gradient_background(self, size: int, color1: Tuple[int, int, int],
                                   color2: Tuple[int, int, int]) -> Image.Image:
        """Create base image with gradient background and rounded corners"""
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Create vertical gradient
        margin = 4
        for i in range(size - margin * 2):
            ratio = i / (size - margin * 2)
            r = int(color1[0] + (color2[0] - color1[0]) * ratio)
            g = int(color1[1] + (color2[1] - color1[1]) * ratio)
            b = int(color1[2] + (color2[2] - color1[2]) * ratio)
            color = (r, g, b, 255)
            y = margin + i
            draw.line([(margin, y), (size - margin, y)], fill=color, width=1)

        # Apply rounded corners
        radius = size // 8
        mask = Image.new('L', (size, size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([margin, margin, size - margin, size - margin],
                                   radius=radius, fill=255)
        img.putalpha(mask)

        return img


    def _get_initials(self, module_name: str) -> str:
        """Extract initials from module name"""
        # Split by underscore and take first letter of each word (max 2)
        parts = module_name.split('_')
        initials = ''.join([p[0].upper() for p in parts if p][:2])
        return initials or 'OD'

    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def _update_manifest(self, module_path: Path) -> bool:
        """Update __manifest__.py with icon path"""
        manifest_path = module_path / '__manifest__.py'

        if not manifest_path.exists():
            self.result['warnings'].append(f"__manifest__.py not found in {module_path}")
            return False

        # Read manifest
        with open(manifest_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if icon already exists
        icon_pattern = r"['\"]icon['\"]:\s*['\"][^'\"]*['\"]"
        icon_value = f"'icon': '/{self.module_name}/static/description/icon.png'"

        if re.search(icon_pattern, content):
            # Update existing icon entry
            new_content = re.sub(icon_pattern, icon_value, content)
        else:
            # Add icon entry after 'name'
            # Find the closing of 'name' entry and add icon after it
            name_pattern = r"(['\"]name['\"]:\s*['\"][^'\"]*['\"],?)"
            if re.search(name_pattern, content):
                new_content = re.sub(name_pattern, r"\1\n    " + icon_value + ",", content)
            else:
                # Add at the beginning of dict
                dict_start = content.find('{')
                if dict_start != -1:
                    new_content = content[:dict_start+1] + f"\n    {icon_value}," + content[dict_start+1:]
                else:
                    self.result['warnings'].append("Could not find where to insert icon in __manifest__.py")
                    return False

        # Save backup and write new content
        if not self.dry_run:
            backup_path = manifest_path.with_suffix('.py.backup')
            shutil.copy2(manifest_path, backup_path)
            self.result['backups_created'].append(str(backup_path.relative_to(Path.cwd())))

            with open(manifest_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

        return True

    def _update_menu_files(self, module_path: Path) -> List[str]:
        """Find and update menu XML files with web_icon"""
        updated_files = []

        # Search for menu files in views directory
        views_dir = module_path / 'views'
        if not views_dir.exists():
            return updated_files

        # Find XML files that might contain menus
        xml_files = list(views_dir.glob('*menu*.xml')) + list(views_dir.glob('*views.xml'))

        for xml_file in xml_files:
            if self._update_menu_file(xml_file):
                updated_files.append(str(xml_file.relative_to(module_path)))

        return updated_files

    def _update_menu_file(self, xml_path: Path) -> bool:
        """Update web_icon in a single menu XML file"""
        with open(xml_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if file contains menuitem
        if '<menuitem' not in content:
            return False

        # Find root menuitem entries (without parent attribute)
        # Pattern: <menuitem ... /> or <menuitem ...>...</menuitem>
        # without parent="" attribute
        menuitem_pattern = r'(<menuitem\s+[^>]*?)(/?>)'
        web_icon_value = f'web_icon="{self.module_name},static/description/icon.png"'

        modified = False
        new_content = content

        # Process each menuitem
        for match in re.finditer(menuitem_pattern, content):
            menuitem_tag = match.group(1)
            closing = match.group(2)

            # Check if this is a root menuitem (no parent attribute)
            if 'parent=' not in menuitem_tag:
                # Check if web_icon already exists
                if 'web_icon=' in menuitem_tag:
                    # Update existing web_icon
                    updated_tag = re.sub(r'web_icon="[^"]*"', web_icon_value, menuitem_tag)
                else:
                    # Add web_icon before closing
                    updated_tag = menuitem_tag + f'\n          {web_icon_value}'

                new_content = new_content.replace(menuitem_tag + closing, updated_tag + closing)
                modified = True

        if modified and not self.dry_run:
            # Backup original
            backup_path = xml_path.with_suffix('.xml.backup')
            shutil.copy2(xml_path, backup_path)
            self.result['backups_created'].append(str(backup_path.relative_to(Path.cwd())))

            # Write updated content
            with open(xml_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

        return modified


def main():
    parser = argparse.ArgumentParser(description='Generate icons for Odoo modules')
    parser.add_argument('--module', required=True, help='Module name')
    parser.add_argument('--description', required=True, help='Icon description (keywords: manufacturing, calendar, task, telegram, document, warehouse)')
    parser.add_argument('--colors', help='Comma-separated hex colors (e.g., #714B67,#4CAF50)')
    parser.add_argument('--dry-run', action='store_true', help='Preview without writing files')
    parser.add_argument('--force', action='store_true', help='Overwrite without confirmation')

    args = parser.parse_args()

    # Parse colors
    colors = []
    if args.colors:
        colors = [c.strip() for c in args.colors.split(',')]

    # Create icon maker
    maker = OdooIconMaker(
        module_name=args.module,
        description=args.description,
        colors=colors,
        dry_run=args.dry_run
    )

    # Run
    result = maker.run()

    # Output JSON result
    print(json.dumps(result, indent=2))

    # Exit with appropriate code
    sys.exit(0 if result['status'] == 'success' else 1)


if __name__ == '__main__':
    main()
