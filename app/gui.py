import customtkinter as ctk
from tkinter import ttk, messagebox
from app.database import init_db
from app.inventory_logic import add_item, get_all_items, delete_item, update_stock
from app.bug_tracker import get_all_bugs, update_bug_status

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class InventoryQualityApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Inventory Management System [Q09: Reduce Bugs] - BBAT104")
        self.geometry("1050x650")

        init_db()

        # Tabs Layout
        self.tabview = ctk.CTkTabview(self, width=1000, height=600)
        self.tabview.pack(padx=20, pady=20, fill="both", expand=True)

        self.tab_inventory = self.tabview.add("📦 Inventory Master")
        self.tab_bugs = self.tabview.add("🐛 In-App Bug Tracker (Q09)")

        self.setup_inventory_tab()
        self.setup_bug_tracker_tab()

    # ================= INVENTORY TAB =================
    def setup_inventory_tab(self):
        # Left Panel (Input Form)
        form_frame = ctk.CTkFrame(self.tab_inventory, width=320)
        form_frame.pack(side="left", fill="y", padx=10, pady=10)

        ctk.CTkLabel(form_frame, text="Add / Modify Item", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)

        self.sku_entry = ctk.CTkEntry(form_frame, placeholder_text="SKU (e.g. SKU-101)")
        self.sku_entry.pack(fill="x", padx=10, pady=5)

        self.name_entry = ctk.CTkEntry(form_frame, placeholder_text="Item Name")
        self.name_entry.pack(fill="x", padx=10, pady=5)

        self.cat_entry = ctk.CTkEntry(form_frame, placeholder_text="Category (e.g. Electronics)")
        self.cat_entry.pack(fill="x", padx=10, pady=5)

        self.qty_entry = ctk.CTkEntry(form_frame, placeholder_text="Initial Quantity")
        self.qty_entry.pack(fill="x", padx=10, pady=5)

        self.price_entry = ctk.CTkEntry(form_frame, placeholder_text="Unit Price (₹)")
        self.price_entry.pack(fill="x", padx=10, pady=5)

        btn_add = ctk.CTkButton(form_frame, text="Add Item (Poka-Yoke)", command=self.handle_add_item)
        btn_add.pack(fill="x", padx=10, pady=12)

        ctk.CTkLabel(form_frame, text="Quick Stock Adjustment", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(15, 5))
        self.stock_delta_entry = ctk.CTkEntry(form_frame, placeholder_text="Quantity (+/-)")
        self.stock_delta_entry.pack(fill="x", padx=10, pady=5)

        btn_adjust = ctk.CTkButton(form_frame, text="Update Stock", fg_color="green", command=self.handle_adjust_stock)
        btn_adjust.pack(fill="x", padx=10, pady=5)

        btn_delete = ctk.CTkButton(form_frame, text="Delete Selected", fg_color="crimson", command=self.handle_delete_item)
        btn_delete.pack(fill="x", padx=10, pady=10)

        # Right Panel (Table View)
        table_frame = ctk.CTkFrame(self.tab_inventory)
        table_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        cols = ("ID", "SKU", "Name", "Category", "Qty", "Price", "Reorder")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=18)
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=90, anchor="center")

        self.tree.pack(fill="both", expand=True, padx=5, pady=5)
        self.refresh_inventory_table()

    def handle_add_item(self):
        success, msg = add_item(
            self.sku_entry.get(),
            self.name_entry.get(),
            self.cat_entry.get(),
            self.qty_entry.get(),
            self.price_entry.get()
        )
        if success:
            messagebox.showinfo("Success", msg)
            self.sku_entry.delete(0, 'end')
            self.name_entry.delete(0, 'end')
            self.cat_entry.delete(0, 'end')
            self.qty_entry.delete(0, 'end')
            self.price_entry.delete(0, 'end')
            self.refresh_inventory_table()
        else:
            messagebox.showerror("Validation / DB Error", msg)
            self.refresh_bugs_table()

    def handle_adjust_stock(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select an item from the table first.")
            return
        item_values = self.tree.item(selected[0], "values")
        sku = item_values[1]

        try:
            delta = int(self.stock_delta_entry.get())
            success, msg = update_stock(sku, delta)
            if success:
                messagebox.showinfo("Success", msg)
                self.stock_delta_entry.delete(0, 'end')
                self.refresh_inventory_table()
            else:
                messagebox.showerror("Error", msg)
                self.refresh_bugs_table()
        except ValueError:
            messagebox.showerror("Error", "Delta must be an integer (e.g. +10 or -5).")

    def handle_delete_item(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select an item to delete.")
            return
        item_id = self.tree.item(selected[0], "values")[0]
        success, msg = delete_item(item_id)
        if success:
            messagebox.showinfo("Deleted", msg)
            self.refresh_inventory_table()
        else:
            messagebox.showerror("Error", msg)

    def refresh_inventory_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for item in get_all_items():
            self.tree.insert("", "end", values=item)

    # ================= BUG TRACKER TAB (Q09) =================
    def setup_bug_tracker_tab(self):
        top_frame = ctk.CTkFrame(self.tab_bugs)
        top_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(top_frame, text="Logged System Defects & Exceptions", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=10)
        btn_refresh = ctk.CTkButton(top_frame, text="Refresh Logs", width=100, command=self.refresh_bugs_table)
        btn_refresh.pack(side="right", padx=5)

        btn_resolve = ctk.CTkButton(top_frame, text="Mark Selected as Resolved", fg_color="green", command=self.handle_resolve_bug)
        btn_resolve.pack(side="right", padx=5)

        bug_cols = ("Bug ID", "Module", "Type", "Severity", "Description", "Status", "Timestamp")
        self.bug_tree = ttk.Treeview(self.tab_bugs, columns=bug_cols, show="headings", height=18)
        for col in bug_cols:
            self.bug_tree.heading(col, text=col)
            self.bug_tree.column(col, width=120, anchor="center")
        self.bug_tree.column("Description", width=260, anchor="w")

        self.bug_tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.refresh_bugs_table()

    def handle_resolve_bug(self):
        selected = self.bug_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select a defect log to resolve.")
            return
        bug_id = self.bug_tree.item(selected[0], "values")[0]
        update_bug_status(bug_id, "Resolved")
        self.refresh_bugs_table()

    def refresh_bugs_table(self):
        for row in self.bug_tree.get_children():
            self.bug_tree.delete(row)
        for bug in get_all_bugs():
            self.bug_tree.insert("", "end", values=bug)

if __name__ == "__main__":
    app = InventoryQualityApp()
    app.mainloop()