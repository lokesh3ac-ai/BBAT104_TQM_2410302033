# Inventory Management System [Q09: Reduce Bugs]
### Total Quality Management (BBAT104) Course Project

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![GUI Framework](https://img.shields.io/badge/GUI-CustomTkinter%20%2B%20NextGen%20Desktop-darkblue.svg)](https://customtkinter.tomschimansky.com/)
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

## 🌟 Dual-Mode Desktop Suite Architecture
The system provides **two modern desktop interfaces**, sharing the unified SQLite engine and Poka-Yoke logic tier:

### Mode 1: Next-Gen Web-Powered Desktop Suite (`Launch_NextGen_App.bat`)
- Standalone borderless desktop window powered by Chromium app mode (`--app`).
- Modern glassmorphic dark theme (`#070a13`), animated Chart.js Pareto & Category charts, live Lucide icons.
- Instant search with keystroke filtering, real-time Poka-Yoke visual regex feedback, stock adjustment steppers (`-5`, `-1`, `+1`, `+5`).
- Defect Tracker with 1-click lifecycle transitions (`Open` ➔ `In-Progress` ➔ `Resolved`).
- Interactive FMEA Risk Scorecard (93.1% RPN reduction), Ishikawa Root-Cause Diagram, and PDCA cycles.
- Live system audit console and one-click CSV export.

### Mode 2: Native CustomTkinter Desktop Application (`Launch_CustomTkinter_App.bat`)
- Pure Python desktop GUI utilizing CustomTkinter dark theme.
- Persistent 260px navigation sidebar, 5 modular workspaces, and real-time treeview tables.
- Satisfies formal university BBAT104 curriculum requirements.

---

## 🎯 Target Features Implemented (Q09 Matrix)
1. **Crash-Proof Exception Handling:** Robust `try-except-finally` blocks and SQLite connection timeouts (20s) preventing unhandled write locks and application crashes.
2. **Poka-Yoke Strict Validation:** Regex pattern matching for SKU formats (`^SKU-[A-Z0-9]{3,8}$`), strictly positive unit prices (`price > 0`), and non-negative stock counts (`quantity >= 0`).
3. **Automated Unit Tests:** Standalone `unittest` suite verifying boundary constraints, lower limits, and duplicate entry prevention.
4. **In-App Bug Tracker:** Comprehensive defect dashboard tracking defect type, severity (1–5), origin module, and 1-click status transitions (`Open` ➔ `In-Progress` ➔ `Resolved`).
5. **Real-Time Audit Console:** Live in-app file stream capturing formatted timestamps, module traces, and error levels from `logs/system_errors.log`.
6. **Embedded TQM SQC Suite:** In-app Pareto 80/20 analysis chart, Ishikawa (Fishbone) root cause diagram, interactive FMEA risk reduction matrix (93.1% RPN reduction), and PDCA Deming cycles.

---

## 🏛️ System Architecture Flow
```
+-------------------------------------------------------------------+
|               AERO-FLOW DUAL-MODE DESKTOP SUITE                   |
|   [ Mode 1: Next-Gen Desktop App ]  |  [ Mode 2: CustomTkinter ]  |
+-------------------------------------+-----------------------------+
                                      | User Inputs & Actions
                                      v
+-------------------------------------------------------------------+
|                   Poka-Yoke Validation Layer                      |
|       (Regex SKU Pattern, Bounds Checking, Numeric Cast)          |
+-------------------------------------+-----------------------------+
| Valid Data Payload                  | Invalid Entry Trapped
v                                     v
+-------------------------------------+  +--------------------------+
|           SQLite3 Engine            |  |   Bug Tracker & Audit    |
|     (items, bug_reports tables)     |  |   - system_errors.log    |
+-------------------------------------+  |   - bug_reports table    |
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

## 🚀 One-Click Launch Instructions

### Method A: One-Click Desktop Launchers (Recommended)
- **Launch Next-Gen Modern Desktop App:** Double-click `Launch_NextGen_App.bat`
- **Launch CustomTkinter Native App:** Double-click `Launch_CustomTkinter_App.bat`
- **Launch Silent (Windowless Background Server):** Double-click `Launch_Silent_NextGen_App.vbs`

### Method B: Command Line Launch
1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Launch Next-Gen Desktop Application:**
   ```bash
   python -m app.launcher
   ```
3. **Launch CustomTkinter Desktop Application:**
   ```bash
   python -m app.gui
   ```
4. **Run Automated Test Suite:**
   ```bash
   python -m unittest discover -s tests -p "test_*.py" -v
   ```
5. **Regenerate SQC Charts:**
   ```bash
   python -m tqm_tools.generate_pareto
   python -m tqm_tools.generate_fishbone
   ```

---

## 📁 Repository Directory Structure
```
BBAT104_TQM_2410302033/
├── Launch_NextGen_App.bat        # One-click Next-Gen desktop launcher
├── Launch_CustomTkinter_App.bat  # One-click CustomTkinter launcher
├── Launch_Silent_NextGen_App.vbs # Silent background desktop launcher
├── app/
│   ├── __init__.py               # Package definition
│   ├── database.py               # SQLite connection & schema initialization
│   ├── inventory_logic.py        # CRUD operations, Poka-Yoke validations & stats
│   ├── bug_tracker.py            # Defect logging, status workflow & DB reporting
│   ├── gui.py                    # CustomTkinter aesthetic & modern UI dashboard
│   ├── launcher.py               # Standalone desktop window launcher
│   └── desktop_web/              # Next-Gen modern application tier
│       ├── server.py             # REST API & application server
│       ├── templates/
│       │   └── index.html        # Responsive glassmorphic SPA (Tailwind + Chart.js)
│       └── static/
├── tests/
│   ├── __init__.py
│   └── test_inventory.py         # Automated unit test suite (6 passing tests)
├── tqm_tools/
│   ├── generate_pareto.py        # 80/20 Pareto analysis chart generator
│   └── generate_fishbone.py      # Ishikawa root-cause diagram generator
├── docs/
│   ├── SRS_Document.md           # Software Requirements Specification (CO1)
│   ├── FMEA_Matrix.md            # Risk audit, RPN scores & SIPOC map (CO2)
│   ├── PDCA_Log.md               # Continuous improvement cycles (CO3)
│   ├── pareto_analysis.png       # Generated SQC Pareto chart
│   └── fishbone_diagram.png      # Generated Ishikawa diagram
├── logs/
│   ├── .gitkeep
│   └── system_errors.log         # Runtime system error logs
├── requirements.txt              # Python project dependencies
└── README.md                     # Project documentation & user guide
```
