import customtkinter as ctk
from tkinter import ttk, messagebox
import sqlite3
import re
from app.inventory_logic import add_item, update_stock, delete_item
from app.bug_tracker import get_all_bugs, log_bug_to_db
from app.database import get_connection

# Set Theme & Palette
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

PALETTE = {
    "bg": "#0d1117",
    "card": "#161b22",
    "card_border": "#30363d",
    "accent_cyan": "#00d2ff",
    "accent_purple": "#8a2be2",
    "success": "#2ea043",
    "danger": "#da3633",
    "text_main": "#f0f6fc",
    "text_muted": "#8b949e"
}

class InventoryApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AERO-FLOW // TQM Q09 Defect-Proof Inventory")
        self.geometry("1180x760")
        self.minsize(1050, 680)
        self.configure(fg_color=PALETTE["bg"])

        self.setup_layout()
        self.refresh_all_data()

    def setup_layout(self):
        # 1. Header Banner
        header = ctk.CTkFrame(self, fg_color=PALETTE["card"], corner_radius=12, border_width=1, border_color=PALETTE["card_border"])
        header.pack(fill="x", padx=20, pady=(15, 10))

        title_label = ctk.CTkLabel(
            header,
            text="✦ AERO // INVENTORY & QUALITY CONTROLLER",
            font=ctk.CTkFont(family="Inter", size=18, weight="bold"),
            text_color=PALETTE["accent_cyan"]
        )
        title_label.pack(side="left", padx=20, pady=12)

        meta_badge = ctk.CTkLabel(
            header,
            text="TQM GOAL: Q09 (ZERO-DEFECT RUNTIME)",
            font=ctk.CTkFont(family="Inter", size=11, weight="bold"),
            fg_color="#1f242c",
            text_color="#58a6ff",
            corner_radius=8,
            padx=12,
            pady=4
        )
        meta_badge.pack(side="right", padx=20, pady=12)

        # 2. KPI / Live Metrics Cards
        kpi_frame = ctk.CTkFrame(self, fg_color="transparent")
        kpi_frame.pack(fill="x", padx=20, pady=(0, 10))

        self.card_total = self.create_kpi_card(kpi_frame, "TOTAL ITEMS", "0", PALETTE["accent_cyan"])
        self.card_stock = self.create_kpi_card(kpi_frame, "ACTIVE STOCK", "0", PALETTE["accent_purple"])
        self.card_low = self.create_kpi_card(kpi_frame, "LOW STOCK ALERTS", "0", "#e3b341")
        self.card_defects = self.create_kpi_card(kpi_frame, "TRAPPED BUGS", "0", PALETTE["danger"])

        # 3. Main Body Tabview
        self.tabs = ctk.CTkTabview(
            self,
            fg_color=PALETTE["card"],
            segmented_button_fg_color="#0d1117",
            segmented_button_selected_color=PALETTE["accent_cyan"],
            segmented_button_selected_hover_color="#00a8cc",
            corner_radius=14,
            border_width=1,
            border_color=PALETTE["card_border"]
        )
        self.tabs.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        self.tab_inventory = self.tabs.add("  📦 Inventory Dashboard  ")
        self.tab_tracker = self.tabs.add("  🛡️ Quality Bug Tracker (Q09)  ")

        self.build_inventory_tab()
        self.build_tracker_tab()

    def create_kpi_card(self, parent, title, value, highlight_color):
        card = ctk.CTkFrame(parent, fg_color=PALETTE["card"], corner_radius=12, border_width=1, border_color=PALETTE["card_border"])
        card.pack(side="left", fill="both", expand=True, padx=5)

        lbl_title = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(family="Inter", size=10, weight="bold"), text_color=PALETTE["text_muted"])
        lbl_title.pack(anchor="w", padx=14, pady=(10, 0))

        lbl_value = ctk.CTkLabel(card, text=value, font=ctk.CTkFont(family="Inter", size=22, weight="bold"), text_color=highlight_color)
        lbl_value.pack(anchor="w", padx=14, pady=(0, 10))
        return lbl_value

    def build_inventory_tab(self):
        grid = ctk.CTkFrame(self.tab_inventory, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=10, pady=10)

        # Left Panel (Poka-Yoke Inputs)
        left = ctk.CTkFrame(grid, fg_color="#12161f", width=280, corner_radius=12, border_width=1, border_color=PALETTE["card_border"])
        left.pack(side="left", fill="y", padx=(0, 10), pady=0)
        left.pack_propagate(False)

        ctk.CTkLabel(left, text="Quick Entry (Poka-Yoke)", font=ctk.CTkFont(family="Inter", size=13, weight="bold"), text_color=PALETTE["text_main"]).pack(pady=(12, 10), padx=12, anchor="w")

        self.ent_sku = self.create_styled_entry(left, "SKU (e.g. SKU-101)")
        self.ent_name = self.create_styled_entry(left, "Item Name")
        self.ent_category = self.create_styled_entry(left, "Category")
        self.ent_qty = self.create_styled_entry(left, "Initial Quantity")
        self.ent_price = self.create_styled_entry(left, "Unit Price (₹)")

        btn_add = ctk.CTkButton(
            left,
            text="+ Add Verified Item",
            fg_color="#1f6feb",
            hover_color="#388bfd",
            font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            height=34,
            corner_radius=8,
            command=self.handle_add_item
        )
        btn_add.pack(fill="x", padx=12, pady=(10, 15))

        # Divider
        ctk.CTkFrame(left, fg_color=PALETTE["card_border"], height=1).pack(fill="x", padx=12, pady=5)

        ctk.CTkLabel(left, text="Stock Adjustment", font=ctk.CTkFont(family="Inter", size=13, weight="bold"), text_color=PALETTE["text_main"]).pack(pady=(10, 6), padx=12, anchor="w")
        self.ent_delta = self.create_styled_entry(left, "Delta Qty (+/-)")

        btn_update = ctk.CTkButton(
            left,
            text="Update Level",
            fg_color=PALETTE["success"],
            hover_color="#3fb950",
            font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            height=32,
            corner_radius=8,
            command=self.handle_stock_adjust
        )
        btn_update.pack(fill="x", padx=12, pady=(6, 6))

        btn_del = ctk.CTkButton(
            left,
            text="Delete Item",
            fg_color=PALETTE["danger"],
            hover_color="#f85149",
            font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            height=32,
            corner_radius=8,
            command=self.handle_delete_item
        )
        btn_del.pack(fill="x", padx=12, pady=(0, 12))

        # Right Panel: Modern Styled Table
        right = ctk.CTkFrame(grid, fg_color="transparent")
        right.pack(side="right", fill="both", expand=True)

        cols = ("ID", "SKU", "Name", "Category", "Quantity", "Price", "Reorder")
        self.inv_tree = self.create_modern_treeview(right, cols)

    def build_tracker_tab(self):
        frame = ctk.CTkFrame(self.tab_tracker, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        header_box = ctk.CTkFrame(frame, fg_color="#12161f", corner_radius=10, border_width=1, border_color=PALETTE["card_border"])
        header_box.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            header_box,
            text="Real-time Defect Detection & Root Cause Capture (Poka-Yoke & Exception Logs)",
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=PALETTE["text_muted"]
        ).pack(side="left", padx=15, pady=10)

        btn_refresh = ctk.CTkButton(
            header_box,
            text="Sync Logs",
            fg_color="#21262d",
            hover_color="#30363d",
            font=ctk.CTkFont(size=11),
            width=90,
            command=self.refresh_all_data
        )
        btn_refresh.pack(side="right", padx=12, pady=8)

        cols = ("ID", "Timestamp", "Module", "Defect Type", "Severity", "Status", "Details")
        self.bug_tree = self.create_modern_treeview(frame, cols)

    def create_styled_entry(self, parent, placeholder):
        ent = ctk.CTkEntry(
            parent,
            placeholder_text=placeholder,
            height=32,
            corner_radius=8,
            border_width=1,
            border_color=PALETTE["card_border"],
            fg_color="#0d1117",
            placeholder_text_color="#484f58",
            font=ctk.CTkFont(family="Inter", size=12)
        )
        ent.pack(fill="x", padx=12, pady=4)
        return ent

    def create_modern_treeview(self, parent, columns):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background="#0d1117",
            foreground="#f0f6fc",
            fieldbackground="#0d1117",
            rowheight=32,
            font=("Segoe UI", 10),
            borderwidth=0
        )
        style.configure("Treeview.Heading", background="#161b22", foreground="#58a6ff", font=("Segoe UI", 10, "bold"), relief="flat")
        style.map("Treeview", background=[("selected", "#1f6feb")])

        tree = ttk.Treeview(parent, columns=columns, show="headings", selectmode="browse")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, anchor="center", stretch=True, width=100)

        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        return tree

    # 4. Logical Handlers
    def handle_add_item(self):
        sku = self.ent_sku.get()
        name = self.ent_name.get()
        cat = self.ent_category.get()
        qty = self.ent_qty.get()
        price = self.ent_price.get()

        success, msg = add_item(sku, name, cat, qty, price)
        if success:
            messagebox.showinfo("Quality Verified", msg)
            self.ent_sku.delete(0, 'end')
            self.ent_name.delete(0, 'end')
            self.ent_category.delete(0, 'end')
            self.ent_qty.delete(0, 'end')
            self.ent_price.delete(0, 'end')
        else:
            messagebox.showerror("Poka-Yoke Trap", f"Entry Rejected:\n{msg}")
        self.refresh_all_data()

    def handle_stock_adjust(self):
        selected = self.inv_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Missing", "Please select an item from table.")
            return

        delta_val = self.ent_delta.get().strip()
        try:
            delta = int(delta_val)
        except ValueError:
            messagebox.showerror("Type Fault", "Enter valid integer for adjustment (+/-).")
            return

        sku = self.inv_tree.item(selected[0])["values"][1]
        success, msg = update_stock(sku, delta)
        if success:
            messagebox.showinfo("Stock Updated", msg)
            self.ent_delta.delete(0, 'end')
        else:
            messagebox.showerror("Constraint Violation", msg)
        self.refresh_all_data()

    def handle_delete_item(self):
        selected = self.inv_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Missing", "Please select an item from table.")
            return

        sku = self.inv_tree.item(selected[0])["values"][1]
        if messagebox.askyesno("Confirm Delete", f"Delete record {sku}?"):
            delete_item(sku)
            self.refresh_all_data()

    def refresh_all_data(self):
        # Refresh Inventory Table
        for r in self.inv_tree.get_children():
            self.inv_tree.delete(r)

        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT id, sku, name, category, quantity, unit_price, reorder_level FROM items ORDER BY id DESC")
        items = c.fetchall()

        total_items = len(items)
        total_qty = sum(item[4] for item in items)
        low_stock_count = sum(1 for item in items if item[4] <= item[6])

        for item in items:
            self.inv_tree.insert("", "end", values=item)

        # Refresh Bug Tracker Table
        for r in self.bug_tree.get_children():
            self.bug_tree.delete(r)

        bugs = get_all_bugs()
        for bug in bugs:
            self.bug_tree.insert("", "end", values=bug)
        conn.close()

        # Update KPI Indicators
        self.card_total.configure(text=str(total_items))
        self.card_stock.configure(text=str(total_qty))
        self.card_low.configure(text=str(low_stock_count))
        self.card_defects.configure(text=str(len(bugs)))

if __name__ == "__main__":
    app = InventoryApp()
    app.mainloop()