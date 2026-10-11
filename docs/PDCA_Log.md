# Continuous Improvement (PDCA) Cycle Log
## System: Inventory Management System [Q09: Reduce Bugs]

- **Student Name:** LOKESH MAURYA | **Roll No:** 2410302033
- **Standard Applied:** Deming PDCA Cycle (Plan-Do-Check-Act) for Software Defect Elimination

---

### Cycle 1: Eliminating Data Entry Errors via Poka-Yoke Validation

#### 1. Plan
- **Problem Statement:** During baseline testing, 48 out of 100 test runs failed due to invalid formats (e.g., letters entered into price/quantity, negative quantities entered).
- **Target:** Reduce input validation errors to 0% through strict defensive programming.
- **Root Cause Identified:** Missing client-side validation logic allowing malformed data to directly hit SQL queries.
- **Action Plan:** Design regex pattern constraints for SKU codes and enforce strictly positive bounds on price and quantity.

#### 2. Do
- Implemented `validate_item_data()` in `app/inventory_logic.py`.
- Configured regex `^SKU-[A-Z0-9]{3,8}$` for item SKU format standardization.
- Added explicit type conversion guards with informative `ValueError` messaging.

#### 3. Check
- Executed unit tests in `tests/test_inventory.py` covering boundary values:
  - Input `quantity = -5` $\rightarrow$ Correctly trapped with `ValueError` ("Quantity cannot be negative").
  - Input `unit_price = -100` $\rightarrow$ Correctly trapped with `ValueError` ("Unit price must be strictly greater than 0").
  - Input `sku = "INVALID_CODE"` $\rightarrow$ Rejected by regex guard.
- Measured defect count drop: 48 validation failures reduced to 0 in automated test suites.

#### 4. Act
- Standardized the validation routine across all form submissions in `app/gui.py`.
- Formulated Standard Operating Procedure (SOP): Any future database write module must inherit validation rules from `inventory_logic.py`.

---

### Cycle 2: Implementing Crash-Proof Exception Handling & Traceability

#### 1. Plan
- **Problem Statement:** Uncaught SQLite constraint exceptions triggered console crashes and caused confusion for end-users.
- **Target:** 0 system crashes on database conflicts; 100% error traceability.

#### 2. Do
- Wrapped all database interactions inside `try-except` blocks.
- Integrated automated error routing to `logs/system_errors.log` via Python's `logging` module.
- Built the in-app defect database table `bug_reports` to store defect history with severity ratings.

#### 3. Check
- Simulated duplicate SKU entries and locked database states.
- Verified that the UI displays a clean error dialog while writing the full traceback to `system_errors.log`.
- Verified that the defect is listed in real-time under the "In-App Bug Tracker" tab.

#### 4. Act
- Standardized the logging pattern across the entire project repository.
- Transitioned closed bugs to `Resolved` status directly through the GUI table interface.
