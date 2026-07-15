# backend/app/services/labpro_templates.py
"""
ATLAS AI 4.0 - v12 Live Lab Pro: starter notebook templates (pure data).

Zero AI, zero DB - these are cloned into a new NotebookSession at create
time, so no per-user content seeding is ever needed. Two environments:

  python -> Pyodide kernel (pandas / numpy / sklearn / matplotlib wheels)
  sql    -> in-browser SQLite engine speaking the MySQL practice subset
            (honest boundary: DDL/DML/joins/grouping/window functions run
             locally; server-only MySQL features are taught in SkillPath)

Underscore-prefixed cell keys per platform JSON-state convention.
"""

from typing import Dict, List


def _cell(cid: str, ctype: str, source: str) -> dict:
    return {"_id": cid, "_type": ctype, "_source": source, "_output": None}


PYTHON_STARTER_CELLS: List[dict] = [
    _cell("md-1", "markdown",
          "# Live Lab Pro - Python scratch notebook\n"
          "Runs entirely on **your device** (Pyodide). Your uploaded files "
          "never leave this browser tab.\n\n"
          "- `Shift+Enter` runs a cell\n"
          "- Drag a CSV into the **Files** panel, then read it below\n"
          "- `micropip` installs pure-Python packages on the fly"),
    _cell("code-1", "code",
          "import sys\nimport pandas as pd\nimport numpy as np\n"
          "print(f'Python {sys.version.split()[0]} | '\n"
          "      f'pandas {pd.__version__} | numpy {np.__version__}')"),
    _cell("md-2", "markdown",
          "## Load a dataset\nUpload `data.csv` in the Files panel, "
          "then run the next cell."),
    _cell("code-2", "code",
          "# df = pd.read_csv('data.csv')\n"
          "# df.head()\n"
          "# df.info()\n"
          "# df.describe()"),
    _cell("md-3", "markdown",
          "## Quick chart\nmatplotlib renders inline under the cell."),
    _cell("code-3", "code",
          "import matplotlib.pyplot as plt\n"
          "xs = np.linspace(0, 10, 100)\n"
          "plt.plot(xs, np.sin(xs))\n"
          "plt.title('It works - your CPU, zero cloud cost')\n"
          "plt.show()"),
]


SQL_STARTER_CELLS: List[dict] = [
    _cell("md-1", "markdown",
          "# Live Lab Pro - SQL scratch notebook\n"
          "An in-browser SQL engine covering the MySQL practice subset: "
          "DDL, DML, aggregation, grouping, joins and window functions - "
          "all on your device."),
    _cell("code-1", "code",
          "CREATE TABLE students (\n"
          "  id INTEGER PRIMARY KEY,\n"
          "  name TEXT NOT NULL,\n"
          "  branch TEXT,\n"
          "  cgpa REAL\n"
          ");"),
    _cell("code-2", "code",
          "INSERT INTO students (id, name, branch, cgpa) VALUES\n"
          "  (1, 'Asha',  'CSE', 8.9),\n"
          "  (2, 'Rahul', 'ECE', 7.4),\n"
          "  (3, 'Meera', 'CSE', 9.2),\n"
          "  (4, 'Vikram','ME',  6.8);"),
    _cell("md-2", "markdown", "## Aggregation + grouping"),
    _cell("code-3", "code",
          "SELECT branch,\n"
          "       COUNT(*)        AS students,\n"
          "       ROUND(AVG(cgpa), 2) AS avg_cgpa\n"
          "FROM students\n"
          "GROUP BY branch\n"
          "ORDER BY avg_cgpa DESC;"),
    _cell("md-3", "markdown", "## Window functions"),
    _cell("code-4", "code",
          "SELECT name, branch, cgpa,\n"
          "       RANK() OVER (PARTITION BY branch ORDER BY cgpa DESC)\n"
          "         AS branch_rank\n"
          "FROM students;"),
]


TEMPLATES: Dict[str, dict] = {
    "python": {
        "title": "Python scratch notebook",
        "description": "Pandas / NumPy / matplotlib on your device - "
                       "upload a CSV and explore, zero cloud cost.",
        "cells": PYTHON_STARTER_CELLS,
    },
    "sql": {
        "title": "SQL scratch notebook",
        "description": "The MySQL practice subset in your browser: "
                       "DDL, DML, joins, grouping, window functions.",
        "cells": SQL_STARTER_CELLS,
    },
}


# Curated starter dataset catalog (METADATA ONLY -> lab_datasets table;
# files ship as static assets, never through the backend).
STARTER_DATASETS: List[dict] = [
    {"name": "placements.csv", "domain_tag": "data_analysis",
     "file_url": "/static/datasets/placements.csv",
     "rows_est": 500, "size_kb": 38,
     "description": "B.Tech placement records: branch, CGPA, CTC, company."},
    {"name": "sales_orders.csv", "domain_tag": "data_analysis",
     "file_url": "/static/datasets/sales_orders.csv",
     "rows_est": 1200, "size_kb": 96,
     "description": "E-commerce orders for grouping/joins practice."},
    {"name": "iris.csv", "domain_tag": "data_science",
     "file_url": "/static/datasets/iris.csv",
     "rows_est": 150, "size_kb": 5,
     "description": "The classic classification starter dataset."},
    {"name": "housing.csv", "domain_tag": "data_science",
     "file_url": "/static/datasets/housing.csv",
     "rows_est": 506, "size_kb": 49,
     "description": "Regression practice: predict prices from features."},
]