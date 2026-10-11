# Software Requirements Specification (SRS)
## Inventory Management System [Quality Goal Q09: Reduce Bugs]

- **Course Code:** BBAT104 - Fundamentals of Total Quality Management
- **Student Name:** LOKESH MAURYA
- **Registration / Roll No:** 2410302033
- **Branch / Section:** CSE - B
- **Target Quality Goal:** Q09 (Reduce Bugs via Exception Handling, Strict Validation, Module Tests, Bug Tracker, Error Logs)

---

### 1. Introduction & Project Scope
The objective of this project is to develop a desktop Inventory Management System that embeds Total Quality Management (TQM) principles directly into the software development lifecycle. By treating data corruption, invalid formats, and unhandled runtime exceptions as software quality defects, the application applies Poka-Yoke (mistake-proofing) and automated defect tracking to minimize the Cost of Poor Quality (COPQ).

### 2. Core TQM Principles Applied
- **Customer Focus:** Provides end-users with consistent inventory stock levels without data corruption or crash interruptions.
- **Process-Centric Approach:** Standardizes inventory data flow from point of entry to persistence through structured validation barriers.
- **Error Prevention (Poka-Yoke):** Enforces strict boundary constraints and formatting masks prior to database commit.
- **Fact-Based Decision Making:** Logs all runtime defects systematically to prioritize fixes based on empirical frequency.
- **Continuous Improvement (Kaizen):** Iteratively refines software robustness through unit tests and automated error metrics.

### 3. Critical to Quality (CTQ) Flowdown
- **Customer Need:** Reliable stock tracking with zero system downtime.
- **Quality Driver:** Application resilience and data fidelity.
- **CTQ Parameters:**
  1. *Zero Unhandled Crash States:* All system exceptions must be caught and routed to friendly alerts and log files.
  2. *Data Integrity (Poka-Yoke):* Rejection of 100% of negative stock levels, negative unit prices, and malformed SKU codes.
  3. *Traceability:* 100% of runtime errors logged to `system_errors.log` and the in-app defect database.

### 4. Functional Requirements
- **FR1 (Inventory Master CRUD):** Create, Read, Update (Stock In/Out), and Delete inventory records.
- **FR2 (Poka-Yoke Input Validation):** Validate SKU alphanumeric syntax (`SKU-XXXX`), positive price values, and non-negative counts before database queries execute.
- **FR3 (Exception Handling Engine):** Intercept all SQLite, formatting, and boundary errors without killing the application process.
- **FR4 (In-App Bug Tracker):** Dedicated visual dashboard allowing store managers to inspect caught exceptions, view severity levels (1 to 5), and mark resolved defects.
- **FR5 (Error Logging):** Automatic file output to `logs/system_errors.log` capturing module name, timestamp, and error stack trace.
- **FR6 (Automated Testing):** Standalone unit test suite verifying boundary conditions and duplicate entry prevention.

### 5. Non-Functional Requirements
- **Reliability:** Mean Time Between Failures (MTBF) maximized by catching 100% of database write locks and duplicate key violations.
- **Maintainability:** Modular architecture separating database layer (`database.py`), business logic (`inventory_logic.py`), defect tracking (`bug_tracker.py`), and presentation (`gui.py`).
- **Portability:** Standalone SQLite database with cross-platform Python execution.