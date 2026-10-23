# Inventory Management System [Q09: Reduce Bugs]
### Total Quality Management (BBAT104) Course Project

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![GUI Framework](https://img.shields.io/badge/GUI-CustomTkinter-darkblue.svg)](https://customtkinter.tomschimansky.com/)
[![Database](https://img.shields.io/badge/Database-SQLite3-brightgreen.svg)](https://www.sqlite.org/)
[![Quality Goal](https://img.shields.io/badge/TQM%20Goal-Q09%3A%20Reduce%20Bugs-red.svg)](#)

---

## 📌 Student & Project Credentials
- **Student Name:** LOKESH MAURYA
- **University Roll No / Reg ID:** 2410302033
- **Branch & Section:** CSE - B
- **Course Title:** Fundamentals of Total Quality Management (BBAT104)
- **Academic Session:** 2026–2027
- **Assigned System:** Inventory Management System (Roll No Digit: 3)
- **Assigned Quality Goal:** Q09: Reduce Bugs

---

## 🎯 Target Features Implemented (Q09 Matrix)
1. **Crash-Proof Exception Handling:** Robust `try-except-finally` blocks and SQLite connection timeouts (20s) preventing unhandled write locks and application crashes.
2. **Poka-Yoke Strict Validation:** Regex pattern matching for SKU formats (`^SKU-[A-Z0-9]{3,8}$`), strictly positive unit prices (`price > 0`), and non-negative stock counts (`quantity >= 0`).
3. **Automated Unit Tests:** Standalone `unittest` suite verifying boundary constraints, lower limits, and duplicate entry prevention.
4. **In-App Bug Tracker:** Comprehensive defect dashboard tracking defect type, severity (1–5), origin module, and 1-click status transitions (`Open` ➔ `In-Progress` ➔ `Resolved`).
5. **Real-Time Audit Console:** Live in-app file stream capturing formatted timestamps, module traces, and error levels from `logs/system_errors.log`.
6. **Embedded TQM SQC Suite:** In-app Pareto 80/20 analysis chart, Ishikawa (Fishbone) root cause diagram, interactive FMEA risk reduction matrix (93.1% RPN reduction), and PDCA Deming cycles.

---

## 🖥️ Modern & Aesthetic UI Features
The desktop interface is built using CustomTkinter with a dark cyber slate aesthetic:
- **Left Navigation Rail (Sidebar):** Quick switching between 5 dedicated workspaces:
  - 📦 **Inventory Master:** Full stock visibility, real-time keystroke search, category filter, stock status pills (`✅ Healthy`, `⚠️ Low Stock`, `❌ Out of Stock`), column header sorting, and quick stock adjustment (`-5`, `-1`, `+1`, `+5`, custom delta).
  - 🛡️ **Defect Tracker (Q09):** Defect interception logs, severity tags (`⚡ Sev 2`, `⚠️ Sev 3`, `🔥 Sev 4`), status filter, and 1-click lifecycle transitions.
  - 📊 **TQM SQC Analytics:** Embedded high-resolution Pareto Chart, Ishikawa Fishbone Diagram, FMEA Risk Scorecard, and PDCA cycles.
  - 🖥️ **Live System Logs:** Monospace terminal console rendering `logs/system_errors.log` with refresh, clear, and clipboard capabilities.
  - ℹ️ **Knowledge Base & SOP:** Embedded documentation of Poka-Yoke rules, CTQ flowdown, and student credentials.
- **Live KPI Ribbon:** Real-time metrics for Total SKUs, Warehouse Units, Asset Valuation (₹), Low Stock Alerts, and Trapped Defects.
- **Interactive Modals:** Add Item modal featuring **Live Poka-Yoke Visual Feedback** (validating regex syntax and numeric bounds as the user types), and full Edit Item dialog.
- **Export Engine:** One-click CSV inventory audit report generation.
- **Examiner Demo Sandbox:** "⚡ Trigger Poka-Yoke Trap" button allowing instant demonstration of defect interception without crashes.

---

## 🏛️ System Architecture Flow
```
+-----------------------------------------------------------+
|               CustomTkinter Modern Dashboard              |
|   (Sidebar Rail • Live KPIs • 5 Specialized Workspaces)    |
+-----------------------------+-----------------------------+
                              | User Inputs & Actions
                              v
+-----------------------------------------------------------+
|               Poka-Yoke Validation Layer                  |
|     (Regex SKU Pattern, Bounds Checking, Numeric Cast)    |
+-----------------------------+-----------------------------+
| Valid Data                  | Invalid Entry Trapped
v                             v
+-----------------------------+  +--------------------------+
|       SQLite3 Engine        |  |   Bug Tracker & Audit    |
| (items, bug_reports tables) |  |   - system_errors.log    |
+-----------------------------+  |   - bug_reports table    |
                                 +--------------------------+
```

---

## 📊 TQM Statistical Quality Control (SQC) Tools

### 1. Pareto Analysis (80/20 Defect Rule)
Automated analysis shows that over 80% of system errors were driven by data entry formatting and negative inventory attempts. These vital few causes were eliminated using defensive Poka-Yoke checks.

![Pareto Analysis](docs/pareto_analysis.png)

### 2. Ishikawa (Fishbone) Root Cause Diagram
Identifies potential causes behind system defects across People, Process, Methods, and Technology.

![Fishbone Diagram](docs/fishbone_diagram.png)

---

## 🚀 Installation & Setup Instructions

### 1. Clone Repository
```bash
git clone https://github.com/lokesh3ac-ai/BBAT104_TQM_2410302033.git
cd BBAT104_TQM_2410302033
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Initialize SQLite Database
```bash
python -m app.database
```

### 4. Launch Desktop Application
```bash
python -m app.gui
```

### 5. Run Automated Test Suite
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

### 6. Regenerate SQC Charts
```bash
python -m tqm_tools.generate_pareto
python -m tqm_tools.generate_fishbone
```

---

## 📁 Repository Directory Structure
```
BBAT104_TQM_2410302033/
├── app/
│   ├── __init__.py           # Package definition
│   ├── database.py           # SQLite connection & schema initialization
│   ├── inventory_logic.py    # CRUD operations, Poka-Yoke validations & stats
│   ├── bug_tracker.py        # Defect logging, status workflow & DB reporting
│   └── gui.py                # CustomTkinter aesthetic & modern UI dashboard
├── tests/
│   ├── __init__.py
│   └── test_inventory.py     # Automated unit test suite (6 passing tests)
├── tqm_tools/
│   ├── generate_pareto.py    # 80/20 Pareto analysis chart generator
│   └── generate_fishbone.py  # Ishikawa root-cause diagram generator
├── docs/
│   ├── SRS_Document.md       # Software Requirements Specification (CO1)
│   ├── FMEA_Matrix.md        # Risk audit, RPN scores & SIPOC map (CO2)
│   ├── PDCA_Log.md           # Continuous improvement cycles (CO3)
│   ├── pareto_analysis.png   # Generated SQC Pareto chart
│   └── fishbone_diagram.png  # Generated Ishikawa diagram
├── logs/
│   ├── .gitkeep
│   └── system_errors.log     # Runtime system error logs
├── requirements.txt          # Python project dependencies
└── README.md                 # Project documentation & user guide
```
