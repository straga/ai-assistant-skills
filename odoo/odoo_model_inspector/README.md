# Odoo Model Inspector - Developer Documentation

Technical documentation for developers who want to understand or extend this skill.

## Architecture

### Core Components

```
odoo_model_inspector/
├── inspect.py                   # Entry point
├── config.py                    # Configuration (addon paths, output dir)
├── parsers/                     # Code and manifest parsing
│   ├── manifest_parser.py       # Parse __manifest__.py files
│   ├── model_parser.py          # AST parsing of Python models
│   └── dependency_resolver.py   # Build inheritance chain
└── formatters/                  # Output formatting
    ├── json_formatter.py        # JSON output for AI assistants
    └── markdown_formatter.py    # Markdown for human reading
```

### Design Principles

1. **Zero code execution** - AST parsing only, never import/run code
2. **Recursive dependencies** - Follow complete dependency graph
3. **Circular dependency handling** - Correct handling of module cycles
4. **Fast & token efficient** - Direct file parsing, no database queries

---

## Circular Dependency Handling

### The Problem

Odoo modules often have circular dependencies:

```
purchase → purchase_stock → stock_dropshipping → purchase  (CYCLE!)
   ↓                              ↑
   └──────────────────────────────┘
```

This is **normal** in Odoo, but complicates dependency analysis.

### Solution: Topological Sort + Recovery

#### Step 1: Topological Sort (Kahn's Algorithm)

```
Algorithm:
1. Count in-degree (incoming edges) for each module
2. Take modules with in-degree == 0 (no dependencies)
3. Add to result
4. Remove from graph → decrease in-degree for dependents
5. Repeat while modules with in-degree == 0 exist
```

**Result:**
- Modules WITHOUT cycles: correctly sorted (base → extensions)
- Modules IN cycle: NOT in result (in-degree never reaches 0)

#### Step 2: Cycle Detection

```python
if len(result) != len(graph):
    # Not all modules processed = cycle exists!
    modules_in_cycle = set(graph.keys()) - set(result)
    print(f"Warning: Circular dependency detected in modules: {modules_in_cycle}")
```

#### Step 3: Recovery - Add "Lost" Modules

```python
for module_name in modules_with_model:
    if module_name not in sorted_modules:
        sorted_modules.append(module_name)  # Add to END
```

**Result:**
- ALL modules present in final chain
- Modules without cycles: in correct order
- Modules in cycle: at end of list (order within cycle may be approximate)

#### Step 4: Base Module First Guarantee

```python
if base_module:
    sorted_modules.remove(base_module)  # Remove from wherever
    sorted_modules.insert(0, base_module)  # Put first
```

**Guarantee:** Base model (_name = '...') ALWAYS first in chain.

### Example: purchase.order

**Input:**
- 17 modules extend purchase.order
- 8 modules in circular dependencies

**Dependency Graph:**
```
purchase (BASE)
├─> purchase_repair (no cycle)
└─> [8 modules in cycle]:
    purchase_stock ↔ stock_dropshipping
    sale_purchase ↔ purchase_mrp
    ...
```

**Result:**
```
purchase (BASE) - 40 fields
  └─> purchase_requisition_stock - +1 fields
    └─> purchase_repair - +1 fields
      └─> ...modules without cycles...
        └─> purchase_stock - +11 fields  ← modules from cycle
          └─> stock_dropshipping - +1 fields
            └─> sale_purchase - +1 fields
```

✅ All 17 modules present
✅ Base model first
✅ Modules without cycles correctly sorted
✅ Complete dependency picture

---

## Field and Method Parsing

### Field Extraction via AST

**What is extracted:**

1. **Field type:**
   ```python
   name = fields.Char(...)  → type: "Char"
   partner_id = fields.Many2one(...)  → type: "Many2one"
   ```

2. **Required flag:**
   ```python
   name = fields.Char(required=True)  → required: true
   email = fields.Char()  → required: false
   ```

**Output format:**
```markdown
- `name`: Char [required]
- `email`: Char
- `partner_id`: Many2one [required]
```

### Method Extraction via AST

**What is extracted:**

1. **Method name:**
   ```python
   def action_confirm(self):  → method: "action_confirm"
   ```

2. **super() call detection:**
   ```python
   def write(self, vals):
       super().write(vals)  → has_super: true
   ```

3. **Parent module identification:**
   - Analyze inheritance chain
   - Find method with same name in parent modules
   - Show which module is being overridden

**Output format:**
```markdown
Methods Added (12):
- `_compute_total`
- `action_confirm`
- `write` [super from purchase]  ← overrides method from purchase
- `create` [super from mail.thread]
```

---

## Building Inheritance Chain

### Process

1. **Find all modules with model:**
   - Parse all `models/*.py` files
   - Look for classes with `_name = 'model.name'` or `_inherit = 'model.name'`

2. **Build dependency graph:**
   - From `__manifest__.py` → `depends: [...]`
   - Only modules that extend our model

3. **Topological sort + recovery:**
   - Sort by dependencies
   - Handle cycles (see above)

4. **Find base model:**
   - Look for module with `_name = 'model.name'` (not `_inherit`)
   - Put FIRST in chain

5. **Collect information:**
   - For each module: fields, methods, dependencies
   - Determine super methods (analyze parent modules)

### Context Analysis

**With context-module:**
```bash
--context-module product
```
- Analyze only dependencies of this module
- Recursively: dependencies of dependencies
- Result: modules available from product module

**Without context-module:**
```bash
# NO --context-module
```
- Analyze ALL installed modules
- Complete picture of all model extensions
- Result: all modules in system that touch the model

---

## Output Formatting

### JSON Format

**For AI assistants** - compact and parseable:

```json
{
  "model": "sale.order",
  "total_fields": 160,
  "inheritance_chain": [
    {
      "module": "sale",
      "is_base": true,
      "fields": {
        "name": {"type": "Char", "required": true}
      },
      "methods": {
        "action_confirm": false,
        "write": true
      }
    }
  ]
}
```

### Markdown Format

**For humans** - readable with dependency tree:

```markdown
# Model: sale.order
**Total Fields:** 160

## Inheritance Chain

```
sale (BASE) - 60 fields
└─> sale_stock - +12 fields
    └─> sale_management - +6 fields
```

## Module Details

### 1. sale (base definition)

**Fields Defined (60):**
- `name`: Char [required]
- `partner_id`: Many2one [required]

**Methods Defined (45):**
- `action_confirm`
- `write`
```

---

## Token Efficiency

### Problem Without Skill

**Manual analysis of sale.order:**
1. Read `sale/models/sale_order.py` (~2000 lines)
2. Search for all `_inherit = 'sale.order'` in all modules
3. Open each file (~20 files)
4. Extract fields manually

**Cost:** ~10,000 tokens, 10-15 minutes

### With Skill

```bash
python .claude/skills/odoo_model_inspector/inspect.py \
  --model sale.order \
  --context-module sale
```

**Cost:** ~300 tokens, 30 seconds ✅

**Savings:** 97% tokens, 95% time

---

## Usage Examples

### 1. Quick Model Overview

```bash
# What's in sale.order?
python .claude/skills/odoo_model_inspector/inspect.py \
  --model sale.order \
  --context-module sale
```

**Result:** JSON with fields + methods

### 2. Full Analysis with Documentation

```bash
# Complete picture of purchase.order
python .claude/skills/odoo_model_inspector/inspect.py \
  --model purchase.order \
  --output-markdown .odoo_inspect/purchase_order_FULL.md
```

**Result:**
- JSON to stdout
- Markdown file in `.odoo_inspect/`

### 3. Check Before Adding Field

```bash
# Does delivery_date already exist?
python .claude/skills/odoo_model_inspector/inspect.py \
  --model sale.order | grep delivery_date
```

**Result:** See where field is defined (if exists)

### 4. Understanding super Methods

```bash
# Which methods are overridden?
python .claude/skills/odoo_model_inspector/inspect.py \
  --model sale.order \
  --output-markdown .odoo_inspect/sale.md
```

**Result:** See `[super from MODULE]` for overridden methods

---

## Limitations and Features

### What is Parsed

✅ Fields: name + type + required
✅ Methods: name + has super()
✅ Inheritance chains
✅ Circular dependencies

### What is NOT Parsed

❌ Compute methods (which method)
❌ Domains and constraints
❌ Method content
❌ Decorators (@api.depends, etc.)

**Reason:** Focus on structure, not logic. For logic use other tools (code reading, Serena, etc.).

### AST vs Code Execution

**Why AST:**
- Safe (don't run code)
- Fast (only parsing)
- Works without Odoo server
- No dependencies needed

**Downsides:**
- Don't see dynamic fields
- Don't see computed attributes
- Approximate super method analysis

**Conclusion:** For structural analysis, AST is ideal.

---

## Configuration

Edit `config.py` to customize for your project:

```python
from pathlib import Path

# Project root (4 levels up from this file)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent

# Odoo addon directories (relative to PROJECT_ROOT)
ADDON_DIRECTORIES = [
    'server/addons',           # Core Odoo
    'server/odoo/addons',      # Base addons
    'addons_custom',           # Your custom addons
    'addons_external',         # External modules
]

# Output directory for Markdown files
OUTPUT_DIRECTORY = '.odoo_inspect'
```

---
---

## FAQ

### Q: Why warning about circular dependencies?

**A:** Informational message. Cycles are normal in Odoo (purchase ↔ stock). Skill handles them correctly via recovery mechanism.

### Q: Why can module order in cycle differ?

**A:** Inside cycle there's no "correct" order (A depends on B, B on A). Important that all modules are present.

### Q: How to add new field type?

**A:** Add to `model_parser.py` → `FIELD_TYPES`:
```python
FIELD_TYPES = {
    'Char', 'Text', ..., 'NewFieldType'
}
```

### Q: Why don't I see dynamic fields?

**A:** AST parsing doesn't execute code. Dynamic fields are created at runtime, so not visible in static analysis.

### Q: Can I use this for Odoo versions before 18?

**A:** Yes! AST parsing works for any Python-based Odoo version (8.0+). Only model structure matters, not version.

---

## Contributing

To extend this skill:

1. **Add new parser:** Create in `parsers/` directory
2. **Add new formatter:** Create in `formatters/` directory
3. **Update config:** Add new options to `config.py`
4. **Test:** Run on various models to ensure correctness
5. **Document:** Update this README with your changes

---

## License

MIT License - see repository root for details.
