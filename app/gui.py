import os
import csv
import re
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk

from app.inventory_logic import (
    add_item,
    update_stock,
    delete_item,
    update_item_details,
    get_all_items,
    get_all_categories,
    get_inventory_statistics,
    validate_item_data
)
from app.bug_tracker import (
    get_all_bugs,
    update_bug_status,
    delete_bug,
    clear_resolved_bugs,
    get_bug_statistics,
    log_bug_to_db,
    log_system_error
)
from app.database import get_connection

# Configure CustomTkinter Appearance (Light Theme)
ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("green")

# Clean Light Theme Palette
PALETTE = {
    "bg_light": "#ffffff",
    "sidebar_bg": "#f8fafc",
    "card_bg": "#ffffff",
    "card_bg_elevated": "#f1f5f9",
    "card_border": "#e2e8f0",
    "card_border_light": "#cbd5e1",
    "accent_emerald": "#10b981",
    "accent_emerald_dark": "#059669",
    "accent_emerald_light": "#ecfdf5",
    "accent_blue": "#2563eb",
    "accent_purple": "#7c3aed",
    "warning": "#d97706",
    "danger": "#e11d48",
    "text_primary": "#0f172a",
    "text_secondary": "#334155",
    "text_muted": "#64748b",
    "input_bg": "#f8fafc",
    "input_border": "#e2e8f0",
    "table_header": "#f8fafc",
    "table_bg": "#ffffff",
    "table_row_alt": "#f8fafc",
    "table_selected": "#d1fae5"
}

FONT_FAMILY = "Segoe UI"


class InventoryApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("INVENTORY MANAGEMENT SYSTEM")
        self.geometry("1280x820")
        self.minsize(1120, 720)
        self.configure(fg_color=PALETTE["bg_light"])

        # State Variables
        self.current_user = "Lokesh Maurya"
        self.active_nav = "inventory"
        self.selected_inventory_item = None
        self.selected_bug_item = None
        self.sort_column = None
        self.sort_reverse = False
        self.all_inventory_data = []
        self.all_bugs_data = []

        # Setup Overall UI Layout
        self.setup_ui_shell()
        self.refresh_all_data()

    def setup_ui_shell(self):
        """Constructs the sidebar rail and primary content viewport."""
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # 1. Left Navigation Sidebar
        self.sidebar = ctk.CTkFrame(
            self,
            width=250,
            corner_radius=0,
            fg_color=PALETTE["sidebar_bg"],
            border_width=1,
            border_color=PALETTE["card_border"]
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.build_sidebar()

        # 2. Main Right Content Container
        self.main_content = ctk.CTkFrame(self, fg_color=PALETTE["bg_light"])
        self.main_content.grid(row=0, column=1, sticky="nsew", padx=20, pady=16)
        self.main_content.grid_rowconfigure(2, weight=1)
        self.main_content.grid_columnconfigure(0, weight=1)

        # Top Header & Action Bar
        self.build_top_header()

        # KPI Metric Strip
        self.build_kpi_strip()

        # Content Views Container
        self.view_container = ctk.CTkFrame(self.main_content, fg_color="transparent")
        self.view_container.grid(row=2, column=0, sticky="nsew", pady=(10, 0))
        self.view_container.grid_rowconfigure(0, weight=1)
        self.view_container.grid_columnconfigure(0, weight=1)

        # Instantiate Sub-views (Removed TQM SQC Analytics and Knowledge Base)
        self.views = {
            "inventory": self.create_inventory_view(),
            "bugs": self.create_bug_tracker_view(),
            "logs": self.create_logs_view(),
        }

        # Show Initial View
        self.show_view("inventory")

    # =========================================================================
    # SIDEBAR BUILDER
    # =========================================================================
    def build_sidebar(self):
        # Brand Header
        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.pack(fill="x", padx=16, pady=(18, 16))

        lbl_logo = ctk.CTkLabel(
            brand_frame,
            text="◈ INVENTORY SYSTEM",
            font=ctk.CTkFont(family=FONT_FAMILY, size=18, weight="bold"),
            text_color=PALETTE["text_primary"]
        )
        lbl_logo.pack(anchor="w")

        lbl_sub = ctk.CTkLabel(
            brand_frame,
            text="Inventory & Quality Suite",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=PALETTE["text_muted"]
        )
        lbl_sub.pack(anchor="w", pady=(1, 0))

        # Divider
        ctk.CTkFrame(self.sidebar, fg_color=PALETTE["card_border"], height=1).pack(fill="x", padx=14, pady=(12, 12))

        # Nav Buttons Section (Removed TQM SQC Analytics and Knowledge Base)
        self.nav_buttons = {}
        nav_items = [
            ("inventory", "📦  Inventory Master"),
            ("bugs", "🛡️  Defect Tracker"),
            ("logs", "🖥️  Live System Logs"),
        ]

        for key, label in nav_items:
            btn_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
            btn_frame.pack(fill="x", padx=10, pady=2.5)

            btn = ctk.CTkButton(
                btn_frame,
                text=label,
                font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
                anchor="w",
                height=38,
                corner_radius=10,
                fg_color="transparent",
                text_color=PALETTE["text_secondary"],
                hover_color=PALETTE["card_bg_elevated"],
                command=lambda k=key: self.show_view(k)
            )
            btn.pack(side="left", fill="x", expand=True)
            self.nav_buttons[key] = btn

        # Spacer to push footer down
        spacer = ctk.CTkLabel(self.sidebar, text="")
        spacer.pack(fill="both", expand=True)

        # Clean System Status Footer (Replaces Academic Metadata Profile Card)
        footer = ctk.CTkFrame(
            self.sidebar,
            fg_color=PALETTE["card_bg"],
            corner_radius=10,
            border_width=1,
            border_color=PALETTE["card_border"]
        )
        footer.pack(fill="x", padx=12, pady=16)

        status_pill = ctk.CTkLabel(
            footer,
            text="🟢 System Online",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            text_color=PALETTE["accent_emerald_dark"]
        )
        status_pill.pack(anchor="w", padx=12, pady=(10, 2))

        ctk.CTkLabel(
            footer,
            text="Database: SQLite 3.x",
            font=ctk.CTkFont(family=FONT_FAMILY, size=10),
            text_color=PALETTE["text_muted"]
        ).pack(anchor="w", padx=12, pady=(0, 10))

    # =========================================================================
    # TOP HEADER & ACTION BAR
    # =========================================================================
    def build_top_header(self):
        header = ctk.CTkFrame(self.main_content, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        # Title & Clean Greeting Badge Left
        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left")

        # Greeting Badge: "Hello, Lokesh Maurya"
        self.lbl_greeting = ctk.CTkLabel(
            title_box,
            text=f"Hello, {self.current_user}",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            fg_color=PALETTE["accent_emerald_light"],
            text_color=PALETTE["accent_emerald_dark"],
            corner_radius=12,
            padx=14,
            pady=4
        )
        self.lbl_greeting.pack(side="left", padx=(0, 12))

        self.lbl_view_title = ctk.CTkLabel(
            title_box,
            text="Inventory Master",
            font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"),
            text_color=PALETTE["text_primary"]
        )
        self.lbl_view_title.pack(side="left")

        # Action Buttons Right
        actions_box = ctk.CTkFrame(header, fg_color="transparent")
        actions_box.pack(side="right")

        self.btn_header_add = ctk.CTkButton(
            actions_box,
            text="+ Add Verified Item",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            fg_color=PALETTE["accent_emerald"],
            hover_color=PALETTE["accent_emerald_dark"],
            text_color="#ffffff",
            height=34,
            corner_radius=8,
            command=self.open_add_item_modal
        )
        self.btn_header_add.pack(side="left", padx=4)

        btn_export = ctk.CTkButton(
            actions_box,
            text="📥 Export CSV",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            fg_color=PALETTE["card_bg_elevated"],
            hover_color="#e2e8f0",
            text_color=PALETTE["text_secondary"],
            border_width=1,
            border_color=PALETTE["card_border"],
            height=34,
            corner_radius=8,
            command=self.handle_export_csv
        )
        btn_export.pack(side="left", padx=4)

        btn_refresh = ctk.CTkButton(
            actions_box,
            text="🔄 Refresh",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            fg_color=PALETTE["card_bg_elevated"],
            hover_color="#e2e8f0",
            text_color=PALETTE["text_secondary"],
            border_width=1,
            border_color=PALETTE["card_border"],
            height=34,
            corner_radius=8,
            command=self.refresh_all_data
        )
        btn_refresh.pack(side="left", padx=4)

        # Logout Button
        btn_logout = ctk.CTkButton(
            actions_box,
            text="🚪 Logout",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            fg_color="#fff1f2",
            hover_color="#ffe4e6",
            text_color=PALETTE["danger"],
            border_width=1,
            border_color="#fecdd3",
            height=34,
            corner_radius=8,
            command=self.handle_logout
        )
        btn_logout.pack(side="left", padx=4)

    def handle_logout(self):
        if messagebox.askyesno("Sign Out", "Are you sure you want to sign out of Inventory Management System?"):
            self.open_login_modal()

    def open_login_modal(self):
        modal = ctk.CTkToplevel(self)
        modal.title("INVENTORY MANAGEMENT SYSTEM // Sign In")
        modal.geometry("380x360")
        modal.resizable(False, False)
        modal.configure(fg_color=PALETTE["bg_light"])
        modal.transient(self)
        modal.grab_set()

        ctk.CTkLabel(
            modal,
            text="◈ INVENTORY SYSTEM",
            font=ctk.CTkFont(family=FONT_FAMILY, size=18, weight="bold"),
            text_color=PALETTE["text_primary"]
        ).pack(pady=(24, 2))

        ctk.CTkLabel(
            modal,
            text="Sign in to your inventory workspace",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=PALETTE["text_muted"]
        ).pack(pady=(0, 16))

        form = ctk.CTkFrame(modal, fg_color=PALETTE["card_bg_elevated"], corner_radius=10, border_width=1, border_color=PALETTE["card_border"])
        form.pack(fill="x", padx=24, pady=0)

        ctk.CTkLabel(form, text="Username:", font=ctk.CTkFont(size=11, weight="bold"), text_color=PALETTE["text_secondary"]).pack(anchor="w", padx=16, pady=(12, 2))
        ent_u = ctk.CTkEntry(form, height=32, fg_color="#ffffff", border_color=PALETTE["card_border"])
        ent_u.insert(0, self.current_user)
        ent_u.pack(fill="x", padx=16, pady=(0, 8))

        ctk.CTkLabel(form, text="Password:", font=ctk.CTkFont(size=11, weight="bold"), text_color=PALETTE["text_secondary"]).pack(anchor="w", padx=16, pady=(2, 2))
        ent_p = ctk.CTkEntry(form, height=32, fg_color="#ffffff", border_color=PALETTE["card_border"], show="•")
        ent_p.insert(0, "password")
        ent_p.pack(fill="x", padx=16, pady=(0, 14))

        def do_signin():
            u = ent_u.get().strip()
            if u:
                self.current_user = u
                self.lbl_greeting.configure(text=f"Hello, {self.current_user}")
                modal.destroy()
                messagebox.showinfo("Signed In", f"Welcome back, {self.current_user}!")
            else:
                messagebox.showerror("Error", "Please enter a valid username.")

        ctk.CTkButton(
            modal,
            text="Sign In",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=PALETTE["accent_emerald"],
            hover_color=PALETTE["accent_emerald_dark"],
            height=34,
            command=do_signin
        ).pack(fill="x", padx=24, pady=16)

    # =========================================================================
    # DYNAMIC KPI METRICS STRIP
    # =========================================================================
    def build_kpi_strip(self):
        kpi_bar = ctk.CTkFrame(self.main_content, fg_color="transparent")
        kpi_bar.grid(row=1, column=0, sticky="ew", pady=(0, 8))

        self.card_skus = self.create_metric_card(kpi_bar, "TOTAL SKUs", "0", "Catalog Items", PALETTE["text_primary"])
        self.card_units = self.create_metric_card(kpi_bar, "TOTAL STOCK", "0", "Warehouse Units", PALETTE["accent_blue"])
        self.card_valuation = self.create_metric_card(kpi_bar, "VALUATION", "₹ 0.00", "Asset Value", PALETTE["accent_purple"])
        self.card_low_stock = self.create_metric_card(kpi_bar, "LOW STOCK ALERTS", "0", "≤ Reorder Limit", PALETTE["warning"])
        self.card_trapped_bugs = self.create_metric_card(kpi_bar, "TRAPPED BUGS", "0", "Quality Interceptions", PALETTE["danger"])

    def create_metric_card(self, parent, title, value, subtitle, accent_color):
        card = ctk.CTkFrame(
            parent,
            fg_color=PALETTE["card_bg"],
            corner_radius=10,
            border_width=1,
            border_color=PALETTE["card_border"]
        )
        card.pack(side="left", fill="both", expand=True, padx=4)

        lbl_title = ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"),
            text_color=PALETTE["text_muted"]
        )
        lbl_title.pack(anchor="w", padx=12, pady=(8, 0))

        lbl_value = ctk.CTkLabel(
            card,
            text=value,
            font=ctk.CTkFont(family=FONT_FAMILY, size=20, weight="bold"),
            text_color=accent_color
        )
        lbl_value.pack(anchor="w", padx=12, pady=(1, 0))

        lbl_sub = ctk.CTkLabel(
            card,
            text=subtitle,
            font=ctk.CTkFont(family=FONT_FAMILY, size=9),
            text_color=PALETTE["text_muted"]
        )
        lbl_sub.pack(anchor="w", padx=12, pady=(0, 8))

        return {"title": lbl_title, "value": lbl_value, "sub": lbl_sub}

    # =========================================================================
    # VIEW NAVIGATION SYSTEM
    # =========================================================================
    def show_view(self, view_key):
        self.active_nav = view_key

        for key, frame in self.views.items():
            frame.grid_forget()

        if view_key in self.views:
            self.views[view_key].grid(row=0, column=0, sticky="nsew")

        for key, btn in self.nav_buttons.items():
            if key == view_key:
                btn.configure(
                    fg_color=PALETTE["accent_emerald_light"],
                    text_color=PALETTE["accent_emerald_dark"],
                    border_width=1,
                    border_color="#a7f3d0"
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=PALETTE["text_secondary"],
                    border_width=0
                )

        titles = {
            "inventory": "Inventory Master",
            "bugs": "Defect Tracker",
            "logs": "Live System Logs"
        }
        self.lbl_view_title.configure(text=titles.get(view_key, "Workspace"))

    # =========================================================================
    # VIEW 1: INVENTORY MASTER
    # =========================================================================
    def create_inventory_view(self):
        view = ctk.CTkFrame(self.view_container, fg_color="transparent")
        view.grid_rowconfigure(1, weight=1)
        view.grid_columnconfigure(0, weight=1)

        # Toolbar
        toolbar = ctk.CTkFrame(
            view,
            fg_color=PALETTE["card_bg"],
            corner_radius=10,
            border_width=1,
            border_color=PALETTE["card_border"]
        )
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 8), padx=2)

        lbl_search = ctk.CTkLabel(toolbar, text="🔍", font=ctk.CTkFont(size=13))
        lbl_search.pack(side="left", padx=(12, 4), pady=8)

        self.ent_search = ctk.CTkEntry(
            toolbar,
            placeholder_text="Search by SKU, Name, or Category...",
            width=280,
            height=32,
            fg_color=PALETTE["input_bg"],
            border_color=PALETTE["input_border"],
            text_color=PALETTE["text_primary"],
            font=ctk.CTkFont(family=FONT_FAMILY, size=11)
        )
        self.ent_search.pack(side="left", padx=4, pady=8)
        self.ent_search.bind("<KeyRelease>", lambda e: self.apply_inventory_filters())

        self.cbo_category = ctk.CTkComboBox(
            toolbar,
            values=["All Categories"],
            width=150,
            height=32,
            fg_color=PALETTE["input_bg"],
            border_color=PALETTE["input_border"],
            text_color=PALETTE["text_primary"],
            button_color=PALETTE["card_bg_elevated"],
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            command=lambda v: self.apply_inventory_filters()
        )
        self.cbo_category.set("All Categories")
        self.cbo_category.pack(side="left", padx=8, pady=8)

        self.status_filter_var = tk.StringVar(value="All")
        self.seg_status = ctk.CTkSegmentedButton(
            toolbar,
            values=["All", "Low Stock", "Healthy", "Out of Stock"],
            variable=self.status_filter_var,
            selected_color=PALETTE["accent_emerald"],
            selected_hover_color=PALETTE["accent_emerald_dark"],
            unselected_color=PALETTE["input_bg"],
            unselected_hover_color=PALETTE["card_bg_elevated"],
            text_color="#ffffff",
            font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"),
            command=lambda v: self.apply_inventory_filters()
        )
        self.seg_status.pack(side="right", padx=12, pady=8)

        # Table Container
        table_frame = ctk.CTkFrame(
            view,
            fg_color=PALETTE["card_bg"],
            corner_radius=10,
            border_width=1,
            border_color=PALETTE["card_border"]
        )
        table_frame.grid(row=1, column=0, sticky="nsew", padx=2)

        cols = ("ID", "SKU", "Item Name", "Category", "Stock Qty", "Unit Price", "Total Value", "Reorder Level", "Stock Health")
        self.inv_tree = self.create_modern_treeview(table_frame, cols, sort_callback=self.handle_inventory_sort)
        self.inv_tree.bind("<<TreeviewSelect>>", self.on_inventory_select)
        self.inv_tree.bind("<Double-1>", lambda e: self.open_edit_item_modal())

        # Action Drawer
        self.inv_action_drawer = ctk.CTkFrame(
            view,
            fg_color=PALETTE["card_bg"],
            corner_radius=10,
            border_width=1,
            border_color=PALETTE["card_border"]
        )
        self.inv_action_drawer.grid(row=2, column=0, sticky="ew", pady=(8, 0), padx=2)

        self.lbl_selected_inv = ctk.CTkLabel(
            self.inv_action_drawer,
            text="👉 Select an item in the table above to adjust stock or edit details.",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=PALETTE["text_muted"]
        )
        self.lbl_selected_inv.pack(side="left", padx=14, pady=10)

        action_box = ctk.CTkFrame(self.inv_action_drawer, fg_color="transparent")
        action_box.pack(side="right", padx=10, pady=6)

        btn_m5 = ctk.CTkButton(action_box, text="-5", width=34, height=30, fg_color=PALETTE["card_bg_elevated"], text_color=PALETTE["text_secondary"], hover_color="#e2e8f0", command=lambda: self.quick_stock_adjust(-5))
        btn_m5.pack(side="left", padx=2)

        btn_m1 = ctk.CTkButton(action_box, text="-1", width=34, height=30, fg_color=PALETTE["card_bg_elevated"], text_color=PALETTE["text_secondary"], hover_color="#e2e8f0", command=lambda: self.quick_stock_adjust(-1))
        btn_m1.pack(side="left", padx=2)

        btn_p1 = ctk.CTkButton(action_box, text="+1", width=34, height=30, fg_color=PALETTE["accent_emerald_light"], text_color=PALETTE["accent_emerald_dark"], hover_color="#a7f3d0", command=lambda: self.quick_stock_adjust(1))
        btn_p1.pack(side="left", padx=2)

        btn_p5 = ctk.CTkButton(action_box, text="+5", width=34, height=30, fg_color=PALETTE["accent_emerald_light"], text_color=PALETTE["accent_emerald_dark"], hover_color="#a7f3d0", command=lambda: self.quick_stock_adjust(5))
        btn_p5.pack(side="left", padx=2)

        self.ent_delta = ctk.CTkEntry(
            action_box,
            placeholder_text="+/- Qty",
            width=70,
            height=30,
            fg_color=PALETTE["input_bg"],
            border_color=PALETTE["input_border"],
            font=ctk.CTkFont(size=11)
        )
        self.ent_delta.pack(side="left", padx=4)

        btn_apply = ctk.CTkButton(
            action_box,
            text="Apply",
            width=50,
            height=30,
            fg_color=PALETTE["accent_emerald"],
            hover_color=PALETTE["accent_emerald_dark"],
            text_color="#ffffff",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.handle_custom_delta
        )
        btn_apply.pack(side="left", padx=2)

        btn_edit = ctk.CTkButton(
            action_box,
            text="✏️ Edit",
            width=65,
            height=30,
            fg_color=PALETTE["card_bg_elevated"],
            text_color=PALETTE["text_secondary"],
            hover_color="#e2e8f0",
            border_width=1,
            border_color=PALETTE["card_border"],
            font=ctk.CTkFont(size=11),
            command=self.open_edit_item_modal
        )
        btn_edit.pack(side="left", padx=4)

        btn_del = ctk.CTkButton(
            action_box,
            text="🗑️ Delete",
            width=65,
            height=30,
            fg_color="#fff1f2",
            text_color=PALETTE["danger"],
            hover_color="#ffe4e6",
            border_width=1,
            border_color="#fecdd3",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.handle_delete_item
        )
        btn_del.pack(side="left", padx=2)

        return view

    # =========================================================================
    # VIEW 2: DEFECT TRACKER
    # =========================================================================
    def create_bug_tracker_view(self):
        view = ctk.CTkFrame(self.view_container, fg_color="transparent")
        view.grid_rowconfigure(1, weight=1)
        view.grid_columnconfigure(0, weight=1)

        toolbar = ctk.CTkFrame(
            view,
            fg_color=PALETTE["card_bg"],
            corner_radius=10,
            border_width=1,
            border_color=PALETTE["card_border"]
        )
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 8), padx=2)

        ctk.CTkLabel(
            toolbar,
            text="🛡️ Quality Defect Log (Poka-Yoke & Exception Trapping)",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            text_color=PALETTE["text_primary"]
        ).pack(side="left", padx=14, pady=10)

        self.bug_status_filter_var = tk.StringVar(value="All")
        self.seg_bug_status = ctk.CTkSegmentedButton(
            toolbar,
            values=["All", "Open", "In-Progress", "Resolved"],
            variable=self.bug_status_filter_var,
            selected_color=PALETTE["accent_emerald"],
            selected_hover_color=PALETTE["accent_emerald_dark"],
            unselected_color=PALETTE["input_bg"],
            unselected_hover_color=PALETTE["card_bg_elevated"],
            font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"),
            command=lambda v: self.apply_bug_filters()
        )
        self.seg_bug_status.pack(side="right", padx=12, pady=8)

        table_frame = ctk.CTkFrame(
            view,
            fg_color=PALETTE["card_bg"],
            corner_radius=10,
            border_width=1,
            border_color=PALETTE["card_border"]
        )
        table_frame.grid(row=1, column=0, sticky="nsew", padx=2)

        cols = ("Bug ID", "Timestamp", "Origin Module", "Defect Type", "Severity", "Resolution Status", "Failure Details")
        self.bug_tree = self.create_modern_treeview(table_frame, cols)
        self.bug_tree.bind("<<TreeviewSelect>>", self.on_bug_select)

        # Action Drawer
        self.bug_action_drawer = ctk.CTkFrame(
            view,
            fg_color=PALETTE["card_bg"],
            corner_radius=10,
            border_width=1,
            border_color=PALETTE["card_border"]
        )
        self.bug_action_drawer.grid(row=2, column=0, sticky="ew", pady=(8, 0), padx=2)

        self.lbl_selected_bug = ctk.CTkLabel(
            self.bug_action_drawer,
            text="👉 Select a defect record above to inspect or update resolution state.",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=PALETTE["text_muted"]
        )
        self.lbl_selected_bug.pack(side="left", padx=14, pady=10)

        btn_box = ctk.CTkFrame(self.bug_action_drawer, fg_color="transparent")
        btn_box.pack(side="right", padx=10, pady=6)

        btn_open = ctk.CTkButton(btn_box, text="Open ⏳", width=80, height=30, fg_color=PALETTE["card_bg_elevated"], text_color=PALETTE["text_secondary"], hover_color="#e2e8f0", command=lambda: self.handle_update_bug_status("Open"))
        btn_open.pack(side="left", padx=3)

        btn_prog = ctk.CTkButton(btn_box, text="In-Progress 🛠️", width=105, height=30, fg_color="#eff6ff", text_color=PALETTE["accent_blue"], border_width=1, border_color="#bfdbfe", hover_color="#dbeafe", command=lambda: self.handle_update_bug_status("In-Progress"))
        btn_prog.pack(side="left", padx=3)

        btn_res = ctk.CTkButton(btn_box, text="Resolve ✅", width=95, height=30, fg_color=PALETTE["accent_emerald_light"], text_color=PALETTE["accent_emerald_dark"], border_width=1, border_color="#a7f3d0", hover_color="#6ee7b7", command=lambda: self.handle_update_bug_status("Resolved"))
        btn_res.pack(side="left", padx=3)

        btn_clr = ctk.CTkButton(btn_box, text="🧹 Clear Resolved", width=110, height=30, fg_color=PALETTE["card_bg_elevated"], text_color=PALETTE["text_secondary"], border_width=1, border_color=PALETTE["card_border"], hover_color="#e2e8f0", command=self.handle_clear_resolved_bugs)
        btn_clr.pack(side="left", padx=4)

        return view

    # =========================================================================
    # VIEW 3: LIVE SYSTEM LOGS
    # =========================================================================
    def create_logs_view(self):
        view = ctk.CTkFrame(self.view_container, fg_color="transparent")
        view.grid_rowconfigure(1, weight=1)
        view.grid_columnconfigure(0, weight=1)

        toolbar = ctk.CTkFrame(view, fg_color=PALETTE["card_bg"], corner_radius=10, border_width=1, border_color=PALETTE["card_border"])
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 8), padx=2)

        ctk.CTkLabel(
            toolbar,
            text="🖥️ File Stream: logs/system_errors.log",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            text_color=PALETTE["text_primary"]
        ).pack(side="left", padx=14, pady=10)

        btn_box = ctk.CTkFrame(toolbar, fg_color="transparent")
        btn_box.pack(side="right", padx=10, pady=6)

        btn_refresh = ctk.CTkButton(
            btn_box,
            text="🔄 Refresh Logs",
            width=100,
            height=30,
            fg_color=PALETTE["card_bg_elevated"],
            text_color=PALETTE["text_secondary"],
            border_width=1,
            border_color=PALETTE["card_border"],
            hover_color="#e2e8f0",
            font=ctk.CTkFont(size=11),
            command=self.load_log_file_content
        )
        btn_refresh.pack(side="left", padx=4)

        btn_clear = ctk.CTkButton(
            btn_box,
            text="🗑️ Clear Logs",
            width=90,
            height=30,
            fg_color="#fff1f2",
            text_color=PALETTE["danger"],
            border_width=1,
            border_color="#fecdd3",
            hover_color="#ffe4e6",
            font=ctk.CTkFont(size=11),
            command=self.handle_clear_log_file
        )
        btn_clear.pack(side="left", padx=4)

        self.txt_logs = ctk.CTkTextbox(
            view,
            fg_color="#0f172a",
            text_color="#34d399",
            font=ctk.CTkFont(family="Consolas", size=11),
            corner_radius=10,
            border_width=1,
            border_color=PALETTE["card_border"],
            wrap="none"
        )
        self.txt_logs.grid(row=1, column=0, sticky="nsew", padx=2)

        self.load_log_file_content()
        return view

    def load_log_file_content(self):
        log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "system_errors.log")
        if os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.txt_logs.delete("1.0", "end")
                self.txt_logs.insert("end", content if content.strip() else "[INFO] Log buffer is clean.")
                self.txt_logs.see("end")
            except Exception as e:
                self.txt_logs.delete("1.0", "end")
                self.txt_logs.insert("end", f"Error: {e}")

    def handle_clear_log_file(self):
        if messagebox.askyesno("Confirm Clear", "Clear system_errors.log?"):
            log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "system_errors.log")
            try:
                with open(log_path, "w", encoding="utf-8") as f:
                    f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [INFO] Log buffer cleared.\n")
                self.load_log_file_content()
            except Exception as e:
                messagebox.showerror("Error", f"Failed: {e}")

    # =========================================================================
    # TREEVIEW HELPER (CLEAN LIGHT THEME)
    # =========================================================================
    def create_modern_treeview(self, parent, columns, sort_callback=None):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Custom.Treeview",
            background="#ffffff",
            foreground="#0f172a",
            fieldbackground="#ffffff",
            rowheight=32,
            font=(FONT_FAMILY, 10),
            borderwidth=0
        )
        style.configure(
            "Custom.Treeview.Heading",
            background="#f8fafc",
            foreground="#334155",
            font=(FONT_FAMILY, 10, "bold"),
            relief="flat",
            padding=(6, 8)
        )
        style.map(
            "Custom.Treeview",
            background=[("selected", "#d1fae5")],
            foreground=[("selected", "#065f46")]
        )

        tree = ttk.Treeview(parent, columns=columns, show="headings", selectmode="browse", style="Custom.Treeview")
        
        for col in columns:
            tree.heading(col, text=col, command=lambda c=col: sort_callback(c) if sort_callback else None)
            if col in ("ID", "Bug ID"):
                tree.column(col, anchor="center", stretch=False, width=60)
            elif col in ("SKU", "Severity", "Resolution Status", "Stock Health"):
                tree.column(col, anchor="center", stretch=False, width=120)
            elif col in ("Stock Qty", "Reorder Level"):
                tree.column(col, anchor="center", stretch=False, width=90)
            elif col in ("Unit Price", "Total Value"):
                tree.column(col, anchor="e", stretch=False, width=110)
            elif col in ("Failure Details", "Item Name"):
                tree.column(col, anchor="w", stretch=True, width=220)
            else:
                tree.column(col, anchor="w", stretch=True, width=120)

        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        return tree

    # =========================================================================
    # INVENTORY SELECTION & ACTIONS
    # =========================================================================
    def on_inventory_select(self, event):
        selected = self.inv_tree.selection()
        if not selected:
            self.selected_inventory_item = None
            self.lbl_selected_inv.configure(text="👉 Select an item in the table above to adjust stock or edit details.")
            return

        values = self.inv_tree.item(selected[0])["values"]
        self.selected_inventory_item = {
            "id": values[0],
            "sku": values[1],
            "name": values[2],
            "category": values[3],
            "quantity": int(values[4]),
            "price": values[5],
            "total_val": values[6],
            "reorder": int(values[7]),
            "health": values[8]
        }
        self.lbl_selected_inv.configure(
            text=f"Selected: [{self.selected_inventory_item['sku']}] {self.selected_inventory_item['name']} | Stock: {self.selected_inventory_item['quantity']} | Price: {self.selected_inventory_item['price']}"
        )

    def quick_stock_adjust(self, delta):
        if not self.selected_inventory_item:
            messagebox.showwarning("Selection Missing", "Please select an inventory item first.")
            return

        sku = self.selected_inventory_item["sku"]
        success, msg = update_stock(sku, delta)
        if success:
            self.refresh_all_data()
            self.resync_inventory_selection(sku)
        else:
            messagebox.showerror("Poka-Yoke Stock Violation", f"Defect Caught:\n{msg}")
            self.refresh_all_data()

    def handle_custom_delta(self):
        if not self.selected_inventory_item:
            messagebox.showwarning("Selection Missing", "Please select an inventory item first.")
            return

        delta_val = self.ent_delta.get().strip()
        try:
            delta = int(delta_val)
        except ValueError:
            messagebox.showerror("Type Error", "Please enter a valid integer for delta adjustment (+/-).")
            return

        sku = self.selected_inventory_item["sku"]
        success, msg = update_stock(sku, delta)
        if success:
            messagebox.showinfo("Stock Updated", msg)
            self.ent_delta.delete(0, 'end')
            self.refresh_all_data()
            self.resync_inventory_selection(sku)
        else:
            messagebox.showerror("Poka-Yoke Stock Violation", f"Defect Caught:\n{msg}")
            self.refresh_all_data()

    def resync_inventory_selection(self, target_sku):
        for item_id in self.inv_tree.get_children():
            vals = self.inv_tree.item(item_id)["values"]
            if vals and len(vals) > 1 and str(vals[1]) == str(target_sku):
                self.inv_tree.selection_set(item_id)
                self.inv_tree.see(item_id)
                self.on_inventory_select(None)
                break

    def handle_delete_item(self):
        if not self.selected_inventory_item:
            messagebox.showwarning("Selection Missing", "Please select an item to delete.")
            return

        sku = self.selected_inventory_item["sku"]
        name = self.selected_inventory_item["name"]
        if messagebox.askyesno("Confirm Deletion", f"Permanently delete item [{sku}] {name}?"):
            success, msg = delete_item(sku)
            if success:
                messagebox.showinfo("Item Removed", msg)
                self.selected_inventory_item = None
                self.refresh_all_data()
            else:
                messagebox.showerror("Deletion Error", msg)

    # =========================================================================
    # BUG SELECTION & ACTIONS
    # =========================================================================
    def on_bug_select(self, event):
        selected = self.bug_tree.selection()
        if not selected:
            self.selected_bug_item = None
            self.lbl_selected_bug.configure(text="👉 Select a defect record above to inspect or update resolution state.")
            return

        values = self.bug_tree.item(selected[0])["values"]
        self.selected_bug_item = {
            "id": values[0],
            "timestamp": values[1],
            "module": values[2],
            "type": values[3],
            "severity": values[4],
            "status": values[5],
            "details": values[6]
        }
        self.lbl_selected_bug.configure(
            text=f"Bug #{self.selected_bug_item['id']} ({self.selected_bug_item['type']}) | Origin: {self.selected_bug_item['module']}"
        )

    def handle_update_bug_status(self, new_status):
        if not self.selected_bug_item:
            messagebox.showwarning("Selection Missing", "Please select a defect record from the table first.")
            return

        bug_id = self.selected_bug_item["id"]
        success, msg = update_bug_status(bug_id, new_status)
        if success:
            self.refresh_all_data()
            for r in self.bug_tree.get_children():
                if self.bug_tree.item(r)["values"][0] == bug_id:
                    self.bug_tree.selection_set(r)
                    self.on_bug_select(None)
                    break
        else:
            messagebox.showerror("Error", msg)

    def handle_clear_resolved_bugs(self):
        if messagebox.askyesno("Confirm Purge", "Purge all defect records marked as 'Resolved'?"):
            clear_resolved_bugs()
            self.selected_bug_item = None
            self.refresh_all_data()

    # =========================================================================
    # MODAL DIALOGS: ADD & EDIT
    # =========================================================================
    def open_add_item_modal(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Add Inventory Item (Poka-Yoke)")
        modal.geometry("450x540")
        modal.resizable(False, False)
        modal.configure(fg_color=PALETTE["bg_light"])
        modal.transient(self)
        modal.grab_set()

        ctk.CTkLabel(
            modal,
            text="Add Verified Inventory Item",
            font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"),
            text_color=PALETTE["text_primary"]
        ).pack(anchor="w", padx=24, pady=(20, 2))

        ctk.CTkLabel(
            modal,
            text="Poka-Yoke validation rules active",
            font=ctk.CTkFont(family=FONT_FAMILY, size=10),
            text_color=PALETTE["text_muted"]
        ).pack(anchor="w", padx=24, pady=(0, 14))

        form = ctk.CTkFrame(modal, fg_color=PALETTE["card_bg_elevated"], corner_radius=10, border_width=1, border_color=PALETTE["card_border"])
        form.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        ctk.CTkLabel(form, text="SKU Code (Pattern: SKU-XXXX):", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=16, pady=(12, 2))
        ent_sku = ctk.CTkEntry(form, placeholder_text="e.g. SKU-101", height=32, fg_color="#ffffff", border_color=PALETTE["card_border"])
        ent_sku.pack(fill="x", padx=16, pady=(0, 6))

        ctk.CTkLabel(form, text="Item Name:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=16, pady=(2, 2))
        ent_name = ctk.CTkEntry(form, placeholder_text="Item name", height=32, fg_color="#ffffff", border_color=PALETTE["card_border"])
        ent_name.pack(fill="x", padx=16, pady=(0, 6))

        ctk.CTkLabel(form, text="Category:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=16, pady=(2, 2))
        existing_cats = get_all_categories()
        cbo_cat = ctk.CTkComboBox(form, values=existing_cats, height=32, fg_color="#ffffff", border_color=PALETTE["card_border"])
        cbo_cat.pack(fill="x", padx=16, pady=(0, 6))

        row = ctk.CTkFrame(form, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(2, 6))

        col_q = ctk.CTkFrame(row, fg_color="transparent")
        col_q.pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkLabel(col_q, text="Quantity (≥ 0):", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", pady=(0, 2))
        ent_qty = ctk.CTkEntry(col_q, placeholder_text="25", height=32, fg_color="#ffffff", border_color=PALETTE["card_border"])
        ent_qty.pack(fill="x")

        col_p = ctk.CTkFrame(row, fg_color="transparent")
        col_p.pack(side="right", fill="x", expand=True, padx=(6, 0))
        ctk.CTkLabel(col_p, text="Unit Price ₹ (> 0):", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", pady=(0, 2))
        ent_price = ctk.CTkEntry(col_p, placeholder_text="1499.00", height=32, fg_color="#ffffff", border_color=PALETTE["card_border"])
        ent_price.pack(fill="x")

        ctk.CTkLabel(form, text="Reorder Alert Level:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=16, pady=(2, 2))
        ent_reorder = ctk.CTkEntry(form, placeholder_text="5", height=32, fg_color="#ffffff", border_color=PALETTE["card_border"])
        ent_reorder.insert(0, "5")
        ent_reorder.pack(fill="x", padx=16, pady=(0, 10))

        btn_box = ctk.CTkFrame(modal, fg_color="transparent")
        btn_box.pack(fill="x", padx=20, pady=(0, 16))

        def submit():
            sku = ent_sku.get()
            name = ent_name.get()
            cat = cbo_cat.get()
            qty = ent_qty.get()
            price = ent_price.get()
            reorder = ent_reorder.get() or "5"

            success, msg = add_item(sku, name, cat, qty, price, reorder)
            if success:
                messagebox.showinfo("Verified", msg)
                modal.destroy()
                self.refresh_all_data()
                self.resync_inventory_selection(sku)
            else:
                messagebox.showerror("Poka-Yoke Rejection", msg)
                self.refresh_all_data()

        btn_cancel = ctk.CTkButton(btn_box, text="Cancel", font=ctk.CTkFont(size=11), fg_color=PALETTE["card_bg_elevated"], text_color=PALETTE["text_secondary"], hover_color="#e2e8f0", height=34, command=modal.destroy)
        btn_cancel.pack(side="left", padx=4, fill="x", expand=True)

        btn_save = ctk.CTkButton(btn_box, text="Verify & Add", font=ctk.CTkFont(size=11, weight="bold"), fg_color=PALETTE["accent_emerald"], hover_color=PALETTE["accent_emerald_dark"], height=34, command=submit)
        btn_save.pack(side="right", padx=4, fill="x", expand=True)

    def open_edit_item_modal(self):
        if not self.selected_inventory_item:
            messagebox.showwarning("Selection Missing", "Please select an item to edit.")
            return

        item = self.selected_inventory_item
        modal = ctk.CTkToplevel(self)
        modal.title(f"Edit Item [{item['sku']}]")
        modal.geometry("420x440")
        modal.resizable(False, False)
        modal.configure(fg_color=PALETTE["bg_light"])
        modal.transient(self)
        modal.grab_set()

        ctk.CTkLabel(
            modal,
            text=f"Edit Item: {item['sku']}",
            font=ctk.CTkFont(family=FONT_FAMILY, size=15, weight="bold"),
            text_color=PALETTE["text_primary"]
        ).pack(anchor="w", padx=20, pady=(18, 4))

        form = ctk.CTkFrame(modal, fg_color=PALETTE["card_bg_elevated"], corner_radius=10, border_width=1, border_color=PALETTE["card_border"])
        form.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        ctk.CTkLabel(form, text="Item Name:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=16, pady=(12, 2))
        ent_name = ctk.CTkEntry(form, height=32, fg_color="#ffffff", border_color=PALETTE["card_border"])
        ent_name.insert(0, item["name"])
        ent_name.pack(fill="x", padx=16, pady=(0, 6))

        ctk.CTkLabel(form, text="Category:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=16, pady=(2, 2))
        existing_cats = get_all_categories()
        cbo_cat = ctk.CTkComboBox(form, values=existing_cats, height=32, fg_color="#ffffff", border_color=PALETTE["card_border"])
        cbo_cat.set(item["category"])
        cbo_cat.pack(fill="x", padx=16, pady=(0, 6))

        ctk.CTkLabel(form, text="Unit Price (₹):", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=16, pady=(2, 2))
        price_clean = str(item["price"]).replace("₹", "").replace(",", "").strip()
        ent_price = ctk.CTkEntry(form, height=32, fg_color="#ffffff", border_color=PALETTE["card_border"])
        ent_price.insert(0, price_clean)
        ent_price.pack(fill="x", padx=16, pady=(0, 6))

        ctk.CTkLabel(form, text="Reorder Alert Level:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=16, pady=(2, 2))
        ent_reorder = ctk.CTkEntry(form, height=32, fg_color="#ffffff", border_color=PALETTE["card_border"])
        ent_reorder.insert(0, str(item["reorder"]))
        ent_reorder.pack(fill="x", padx=16, pady=(0, 10))

        btn_box = ctk.CTkFrame(modal, fg_color="transparent")
        btn_box.pack(fill="x", padx=20, pady=(0, 18))

        def save_changes():
            name = ent_name.get()
            cat = cbo_cat.get()
            price = ent_price.get()
            reorder = ent_reorder.get()

            success, msg = update_item_details(item["sku"], name, cat, price, reorder)
            if success:
                messagebox.showinfo("Success", msg)
                modal.destroy()
                self.refresh_all_data()
                self.resync_inventory_selection(item["sku"])
            else:
                messagebox.showerror("Error", msg)
                self.refresh_all_data()

        btn_cancel = ctk.CTkButton(btn_box, text="Cancel", font=ctk.CTkFont(size=11), fg_color=PALETTE["card_bg_elevated"], text_color=PALETTE["text_secondary"], hover_color="#e2e8f0", height=34, command=modal.destroy)
        btn_cancel.pack(side="left", padx=4, fill="x", expand=True)

        btn_save = ctk.CTkButton(btn_box, text="Save Updates", font=ctk.CTkFont(size=11, weight="bold"), fg_color=PALETTE["accent_emerald"], hover_color=PALETTE["accent_emerald_dark"], height=34, command=save_changes)
        btn_save.pack(side="right", padx=4, fill="x", expand=True)

    # =========================================================================
    # EXPORT CSV HANDLER
    # =========================================================================
    def handle_export_csv(self):
        items = get_all_items()
        if not items:
            messagebox.showwarning("Empty Dataset", "No inventory data available to export.")
            return

        export_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files (*.csv)", "*.csv"), ("All Files (*.*)", "*.*")],
            initialfile=f"inventory_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        if not export_path:
            return

        try:
            with open(export_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Item ID", "SKU", "Item Name", "Category", "Quantity", "Unit Price", "Total Value", "Reorder Level", "Created At"])
                for item in items:
                    item_id, sku, name, cat, qty, price, reorder, created = item
                    total_val = qty * price
                    writer.writerow([item_id, sku, name, cat, qty, f"{price:.2f}", f"{total_val:.2f}", reorder, created])
            messagebox.showinfo("Export Successful", f"CSV report saved to:\n{export_path}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Failed to write CSV: {e}")

    # =========================================================================
    # TABLE SORTING & FILTERING
    # =========================================================================
    def handle_inventory_sort(self, col):
        if self.sort_column == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = col
            self.sort_reverse = False

        self.apply_inventory_filters()

    def apply_inventory_filters(self):
        query = self.ent_search.get().strip().lower()
        cat_filter = self.cbo_category.get()
        status_filter = self.status_filter_var.get()

        filtered = []
        for item in self.all_inventory_data:
            item_id, sku, name, cat, qty, price, total_val, reorder, health = item

            if query and not (query in sku.lower() or query in name.lower() or query in cat.lower()):
                continue

            if cat_filter != "All Categories" and cat != cat_filter:
                continue

            if status_filter == "Low Stock" and "Low" not in health:
                continue
            elif status_filter == "Healthy" and "Healthy" not in health:
                continue
            elif status_filter == "Out of Stock" and "Out of Stock" not in health:
                continue

            filtered.append(item)

        if self.sort_column:
            col_idx_map = {
                "ID": 0, "SKU": 1, "Item Name": 2, "Category": 3,
                "Stock Qty": 4, "Unit Price": 5, "Total Value": 6,
                "Reorder Level": 7, "Stock Health": 8
            }
            idx = col_idx_map.get(self.sort_column, 0)

            def sort_key(row):
                val = row[idx]
                if isinstance(val, (int, float)):
                    return val
                cleaned = str(val).replace("₹", "").replace(",", "").strip()
                try:
                    return float(cleaned)
                except ValueError:
                    return str(val).lower()

            filtered.sort(key=sort_key, reverse=self.sort_reverse)

        for r in self.inv_tree.get_children():
            self.inv_tree.delete(r)

        for row in filtered:
            self.inv_tree.insert("", "end", values=row)

    def apply_bug_filters(self):
        status_filter = self.bug_status_filter_var.get()

        for r in self.bug_tree.get_children():
            self.bug_tree.delete(r)

        for bug in self.all_bugs_data:
            b_id, ts, mod, dtype, sev, status, desc = bug

            if status_filter != "All" and status != status_filter:
                continue

            self.bug_tree.insert("", "end", values=bug)

    # =========================================================================
    # DATA REFRESH ENGINE
    # =========================================================================
    def refresh_all_data(self):
        raw_items = get_all_items()
        self.all_inventory_data = []

        categories_set = set()
        for item in raw_items:
            item_id, sku, name, cat, qty, price, reorder, created = item
            categories_set.add(cat)
            total_val = qty * price

            if qty == 0:
                health = "❌ Out of Stock"
            elif qty <= reorder:
                health = "⚠️ Low Stock"
            else:
                health = "✅ Healthy"

            self.all_inventory_data.append((
                item_id,
                sku,
                name,
                cat,
                qty,
                f"₹ {price:,.2f}",
                f"₹ {total_val:,.2f}",
                reorder,
                health
            ))

        cat_list = ["All Categories"] + sorted(list(categories_set))
        self.cbo_category.configure(values=cat_list)
        self.apply_inventory_filters()

        raw_bugs = get_all_bugs()
        self.all_bugs_data = []
        for bug in raw_bugs:
            b_id, mod, dtype, sev, desc, status, logged_at = bug
            sev_tag = f"⚡ Sev {sev}" if sev <= 2 else (f"⚠️ Sev {sev}" if sev == 3 else f"🔥 Sev {sev}")
            self.all_bugs_data.append((
                b_id,
                logged_at,
                mod,
                dtype,
                sev_tag,
                status,
                desc
            ))

        self.apply_bug_filters()

        inv_stats = get_inventory_statistics()
        bug_stats = get_bug_statistics()

        self.card_skus["value"].configure(text=f"{inv_stats['total_skus']}")
        self.card_units["value"].configure(text=f"{inv_stats['total_units']:,}")
        self.card_valuation["value"].configure(text=f"₹ {inv_stats['total_valuation']:,.2f}")
        
        low_count = inv_stats["low_stock_count"]
        self.card_low_stock["value"].configure(
            text=f"{low_count}",
            text_color=PALETTE["danger"] if low_count > 0 else PALETTE["accent_emerald_dark"]
        )

        trapped_count = bug_stats["total_bugs"]
        open_count = bug_stats["open_bugs"]
        self.card_trapped_bugs["value"].configure(
            text=f"{trapped_count}",
            text_color=PALETTE["danger"] if open_count > 0 else PALETTE["accent_emerald_dark"]
        )
        self.card_trapped_bugs["sub"].configure(
            text=f"{open_count} Open • {bug_stats['resolved_bugs']} Resolved"
        )


if __name__ == "__main__":
    app = InventoryApp()
    app.mainloop()
