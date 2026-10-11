# Failure Mode and Effects Analysis (FMEA) & Risk Audit
## System: Inventory Management System [Q09: Reduce Bugs]

- **Student Name:** LOKESH MAURYA | **Roll No:** 2410302033
- **RPN Formula:** $\text{RPN} = \text{Severity (S)} \times \text{Occurrence (O)} \times \text{Detection (D)}$ (Scale: 1–10)

---

### 1. SIPOC Process Map

| Supplier | Input | Process | Output | Customer |
| :--- | :--- | :--- | :--- | :--- |
| Inventory Clerk | SKU, Item Name, Category, Initial Stock, Unit Price | 1. Input data captured in GUI form | Sanitized item record | Inventory Manager |
| System Logic | Validated parameters | 2. Poka-Yoke boundary & regex check | Clean transaction payload | SQLite Database |
| Database Engine | Transaction query | 3. Execute SQLite insertion & commit | Updated inventory table | Audit System |
| Exception Handler | Runtime errors / Violations | 4. Trap exceptions & write to log file | Error log & bug record | QA Engineer |
| Store Manager | Stock-out / Deduct request | 5. Update stock level with lower bound check | Adjusted inventory balance | Store Staff |

---

### 2. FMEA Risk Assessment Matrix

| Process Function | Potential Failure Mode | Potential Effect of Failure | Severity (S) | Potential Cause | Occurrence (O) | Current Design Controls | Detection (D) | Initial RPN | Recommended Q09 Mitigation Action | Revised S | Revised O | Revised D | Revised RPN |
| :--- | :--- | :--- | :---: | :--- | :---: | :--- | :---: | :---: | :--- | :---: | :---: | :---: | :---: |
| Data Entry (Add Item) | Non-numeric or negative stock quantity entered | Corrupted stock totals; incorrect inventory valuation | 7 | User typing mistake; lack of format guidelines | 8 | None (raw text entry) | 7 | **392** | Poka-Yoke validation rules rejecting non-integers and negative numbers | 7 | 2 | 2 | **28** |
| Stock Checkout | Stock deduction exceeds available inventory count | Phantom negative stock; incorrect reorder triggers | 8 | User overselling; absence of lower bound checks | 6 | Manual physical check | 6 | **288** | Automated validation blocking deductions where delta > current stock | 8 | 1 | 2 | **16** |
| Database Insertion | Duplicate SKU insertion attempt | Integrity error; unhandled crash on duplicate key | 7 | Accidental double-click or reusing existing SKU | 6 | Generic SQLite crash trace | 7 | **294** | Pre-check validation + `try-except IntegrityError` showing polite UI alert | 7 | 2 | 2 | **28** |
| SKU Generation | SKU entered in unstructured, arbitrary formats | Inconsistent indexing; search failure | 5 | Inconsistent staff entry habits | 8 | None | 5 | **200** | Strict Regex pattern checking (`^SKU-[A-Z0-9]{3,8}$`) | 5 | 2 | 1 | **10** |
| Runtime Execution | Unhandled unexpected runtime exception | Application crashes abruptly; loss of active session | 9 | File access lock or database connection failure | 4 | Application exits immediately | 8 | **288** | Global exception handler routing stack trace to `system_errors.log` | 9 | 1 | 2 | **18** |

---

### 3. Critical Failure Mode Reduction Summary
- **Highest Initial Risk:** Data entry invalid quantity formatting ($\text{RPN} = 392$).
- **Action Taken:** Enforced strict Poka-Yoke boundaries in `validate_item_data()` prior to database commit.
- **Result:** Resulting post-mitigation RPN reduced by over **92%**, bringing all operational risks below the critical threshold of 100.