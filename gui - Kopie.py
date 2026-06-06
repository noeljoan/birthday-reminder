"""CustomTkinter GUI for Birthday Reminder.

Implements an MVC architecture:
- **Model** – thin wrapper around :pymod:`birthday_reminder.database`.
- **View**  – builds the CustomTkinter UI (main window, table, dashboard cards).
- **Controller** – connects UI events to model actions.

Features:
* Table view with CRUD buttons.
* Dashboard page showing:
  - Birthdays today
  - Birthdays in the next 10 days
  - Next upcoming birthday (with age after the birthday)
  - Total contacts
* Modal dialogs for adding / editing a birthday.
"""

import datetime
from typing import List, Tuple, Optional

import customtkinter as ctk
from customtkinter import (
    CTk,
    CTkButton,
    CTkEntry,
    CTkLabel,
    CTkFrame,
    CTkTextbox,
    CTkComboBox,
)
from tkinter import ttk, messagebox

# Local import – database layer implements all persistence logic.
import database

# ---------------------------------------------------------------------------
# Model – thin wrapper around the ``database`` module.
# ---------------------------------------------------------------------------
class Model:
    """Encapsulate all data‑access operations for the GUI.

    The model does not know anything about the UI; it simply forwards calls
    to :pymod:`birthday_reminder.database` and returns plain Python data.
    """

    @staticmethod
    def add_birthday(
        first_name: str,
        last_name: str,
        birthday: datetime.date,
        email: Optional[str] = None,
        notes: Optional[str] = None,
        category: Optional[str] = None,
    ) -> int:
        return database.add_birthday(first_name, last_name, birthday, email, notes, category)

    @staticmethod
    def update_birthday(
        birthday_id: int,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        birthday: Optional[datetime.date] = None,
        email: Optional[str] = None,
        notes: Optional[str] = None,
        category: Optional[str] = None,
    ) -> bool:
        return database.update_birthday(
            birthday_id,
            first_name=first_name,
            last_name=last_name,
            birthday=birthday,
            email=email,
            notes=notes,
            category=category,
        )

    @staticmethod
    def delete_birthday(birthday_id: int) -> bool:
        return database.delete_birthday(birthday_id)

    @staticmethod
    def get_all_birthdays() -> List[Tuple[int, str, str, datetime.date, Optional[str], Optional[str], Optional[str], int, int]]:
        return database.get_all_birthdays()

    @staticmethod
    def get_upcoming_birthdays(limit: int = 10) -> List[Tuple[int, str, str, datetime.date, Optional[str], Optional[str], Optional[str], int, int]]:
        return database.get_upcoming_birthdays(limit)

    @staticmethod
    def birthdays_today() -> List[Tuple[int, str, str, datetime.date, Optional[str], Optional[str], Optional[str], int, int]]:
        return database.birthdays_today()

    @staticmethod
    def calculate_age(birth: datetime.date, as_of: datetime.date = None) -> int:
        return database.calculate_age(birth, as_of)

    @staticmethod
    def import_csv(file_path: str) -> int:
        """Delegate CSV import to the database layer."""
        return database.import_csv(file_path)

    @staticmethod
    def export_csv(file_path: str) -> int:
        """Delegate CSV export to the database layer."""
        return database.export_csv(file_path)

# ---------------------------------------------------------------------------
# View – builds the CustomTkinter widgets.
# ---------------------------------------------------------------------------
class View:
    """Construct and expose UI components.

    The view contains **no business logic** – it only knows how to display
    data and emit widget events. Callers (the controller) bind the events to
    callbacks.
    """

    def __init__(self, root: CTk) -> None:
        self.root = root
        self.root.title("Birthday Reminder")
        self.root.geometry("1000x700")
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # Main container
        self.main_frame = CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # ----- Toolbar with CRUD + Dashboard button -----
        self.toolbar = CTkFrame(self.main_frame)
        self.toolbar.pack(fill="x", side="top", pady=(0, 10))

        self.btn_add = CTkButton(self.toolbar, text="Add", width=80)
        self.btn_edit = CTkButton(self.toolbar, text="Edit", width=80)
        self.btn_delete = CTkButton(self.toolbar, text="Delete", width=80)
        self.btn_refresh = CTkButton(self.toolbar, text="Refresh", width=90)
        self.btn_dashboard = CTkButton(self.toolbar, text="Dashboard", width=100)
        self.btn_import = CTkButton(self.toolbar, text="Import CSV", width=120)
        self.btn_export = CTkButton(self.toolbar, text="Export CSV", width=120)
        self.btn_birthdays = CTkButton(self.toolbar, text="Birthdays", width=100)
        # Search entry (placed after buttons, will be packed separately)
        self.search_var = ctk.StringVar()
        # Search label and entry – clearly indicate purpose
        self.lbl_search = CTkLabel(self.toolbar, text="Search:")
        self.entry_search = CTkEntry(self.toolbar, placeholder_text="Search birthdays...", textvariable=self.search_var)
        # Layout toolbar using grid – buttons keep natural size, entry expands
        toolbar_buttons = [
            self.btn_add,
            self.btn_edit,
            self.btn_delete,
            self.btn_refresh,
            self.btn_import,
            self.btn_export,
            self.btn_dashboard,
            self.btn_birthdays,
        ]
        for idx, btn in enumerate(toolbar_buttons):
            btn.grid(row=0, column=idx, padx=3, pady=2, sticky="w")
            # Buttons keep their natural size
            self.toolbar.columnconfigure(idx, weight=0)
        # Search label and entry
        search_label_col = len(toolbar_buttons)
        self.lbl_search.grid(row=0, column=search_label_col, padx=3, pady=2, sticky="w")
        self.entry_search.grid(row=0, column=search_label_col + 1, padx=3, pady=2, sticky="ew")
        # Give entry column a weight so it expands, others stay compact
        self.toolbar.columnconfigure(search_label_col, weight=0)
        self.toolbar.columnconfigure(search_label_col + 1, weight=1)

        # ----- Two primary views: table and dashboard -----
        self.table_view = CTkFrame(self.main_frame)
        self.dashboard_view = CTkFrame(self.main_frame)
        self.table_view.pack(fill="both", expand=True)  # start with table visible

        # ----- Table view -----
        self.columns = (
            "id",
            "first_name",
            "last_name",
            "birthday",
            "email",
            "category",
            "notes",
            "days_remaining",
        )
        self.tree = ttk.Treeview(self.table_view, columns=self.columns, show="headings")
        for col in self.columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
            # Reasonable column widths
            if col == "id":
                self.tree.column(col, width=50, anchor="center")
            elif col == "birthday":
                self.tree.column(col, width=110, anchor="center")
            elif col in ("first_name", "last_name"):
                self.tree.column(col, width=120)
            elif col == "email":
                self.tree.column(col, width=180)
            elif col == "category":
                self.tree.column(col, width=100)
            elif col == "days_remaining":
                self.tree.column(col, width=130, anchor="center")
            else:
                self.tree.column(col, width=200)
        self.tree.pack(fill="both", expand=True)

        # ----- Dashboard view -----
        self.cards_frame = CTkFrame(self.dashboard_view)
        self.cards_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Placeholder cards – will be updated by the controller
        self.card_today = self._create_card(self.cards_frame, "Birthdays Today", "0")
        self.card_next10 = self._create_card(self.cards_frame, "Next 10 Days", "0")
        self.card_next = self._create_card(self.cards_frame, "Next Birthday", "—")
        self.card_total = self._create_card(self.cards_frame, "Total Contacts", "0")

        # Arrange cards in a 2×2 grid
        self.card_today.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.card_next10.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.card_next.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.card_total.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        for i in range(2):
            self.cards_frame.grid_columnconfigure(i, weight=1)
            self.cards_frame.grid_rowconfigure(i, weight=1)

    # ---------------------------------------------------------------------
    # Helper: create a dashboard card
    # ---------------------------------------------------------------------
    def _create_card(self, parent: CTkFrame, title: str, value: str) -> CTkFrame:
        """Create a dashboard card.

        ``value`` is shown in a read‑only multiline textbox so we can display
        names, dates, or other details without being constrained to a single line.
        """
        card = CTkFrame(parent, corner_radius=10)
        CTkLabel(card, text=title, font=("Helvetica", 14)).pack(pady=(10, 5))
        txt = CTkTextbox(card, height=6, width=30, font=("Helvetica", 12))
        txt.insert("1.0", value)
        txt.configure(state="disabled")
        txt.pack(pady=(0, 10), fill="both", expand=True)
        # Store for later updates
        card.value_widget = txt  # type: ignore
        return card

    # ---------------------------------------------------------------------
    # Table view helpers
    # ---------------------------------------------------------------------
    def clear_table(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

    def insert_row(self, data: Tuple) -> None:
        self.tree.insert("", "end", values=data)

    def get_selected_id(self) -> Optional[int]:
        sel = self.tree.selection()
        if not sel:
            return None
        item = self.tree.item(sel[0])
        return int(item["values"][0])

    def refresh_table(self, data: List[Tuple]) -> None:
        self.clear_table()
        for row in data:
            self.tree.insert("", "end", values=row)

    # ---------------------------------------------------------------------
    # Dashboard view helpers
    # ---------------------------------------------------------------------
    def show_dashboard(self) -> None:
        self.table_view.pack_forget()
        self.dashboard_view.pack(fill="both", expand=True)

    def show_table(self) -> None:
        self.dashboard_view.pack_forget()
        self.table_view.pack(fill="both", expand=True)

    def update_card(self, card: CTkFrame, new_content: str) -> None:
        """Update the textbox content inside a dashboard card.

        ``new_content`` may contain newlines; it replaces the entire text.
        """
        # The card stores the textbox widget as ``value_widget`` (see _create_card)
        txt: CTkTextbox = getattr(card, "value_widget")
        txt.configure(state="normal")
        txt.delete("1.0", "end")
        txt.insert("1.0", new_content)
        txt.configure(state="disabled")

# ---------------------------------------------------------------------------
# Dialog used for adding / editing a birthday.
# ---------------------------------------------------------------------------
class _BirthdayDialog(ctk.CTkToplevel):
    """Modal dialog for entering all birthday fields.

    Returns ``None`` if the user cancels; otherwise returns a tuple:
    ``(first_name, last_name, birthday_date, email, notes, category)``.
    """

    def __init__(
        self,
        master,
        title: str,
        first_name: str = "",
        last_name: str = "",
        birthday: datetime.date = None,
        email: str = "",
        notes: str = "",
        category: str = "",
    ) -> None:
        super().__init__(master)
        self.title(title)
        self.resizable(False, False)
        self.result: Optional[Tuple[str, str, datetime.date, str, str, str]] = None
        self.transient(master)
        self.grab_set()

        form = CTkFrame(self)
        form.pack(padx=20, pady=20)

        # First Name
        CTkLabel(form, text="First Name:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.ent_first = CTkEntry(form)
        self.ent_first.grid(row=0, column=1, padx=5, pady=5)
        self.ent_first.insert(0, first_name)

        # Last Name
        CTkLabel(form, text="Last Name:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.ent_last = CTkEntry(form)
        self.ent_last.grid(row=1, column=1, padx=5, pady=5)
        self.ent_last.insert(0, last_name)

        # Birthday (YYYY‑MM‑DD)
        CTkLabel(form, text="Birthday (YYYY‑MM‑DD):").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.ent_bdate = CTkEntry(form)
        self.ent_bdate.grid(row=2, column=1, padx=5, pady=5)
        if birthday:
            self.ent_bdate.insert(0, birthday.isoformat())
        else:
            self.ent_bdate.insert(0, datetime.date.today().isoformat())

        # Email
        CTkLabel(form, text="Email:").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        self.ent_email = CTkEntry(form)
        self.ent_email.grid(row=3, column=1, padx=5, pady=5)
        self.ent_email.insert(0, email)

        # Notes (multi‑line)
        CTkLabel(form, text="Notes:").grid(row=4, column=0, sticky="ne", padx=5, pady=5)
        self.txt_notes = CTkTextbox(form, height=6)
        self.txt_notes.grid(row=4, column=1, padx=5, pady=5)
        self.txt_notes.insert("1.0", notes)

        # Category (combobox)
        CTkLabel(form, text="Category:").grid(row=5, column=0, sticky="e", padx=5, pady=5)
        self.cmb_category = CTkComboBox(form, values=["family", "friend", "colleague", "other"])
        self.cmb_category.grid(row=5, column=1, padx=5, pady=5)
        self.cmb_category.set(category)

        # Action buttons
        btn_frame = CTkFrame(self)
        btn_frame.pack(pady=10)
        CTkButton(btn_frame, text="OK", width=80, command=self._apply).grid(row=0, column=0, padx=5)
        CTkButton(btn_frame, text="Cancel", width=80, command=self._cancel).grid(row=0, column=1, padx=5)

        self.wait_window(self)

    def _apply(self) -> None:
        try:
            first = self.ent_first.get().strip()
            last = self.ent_last.get().strip()
            bdate_str = self.ent_bdate.get().strip()
            email = self.ent_email.get().strip()
            notes = self.txt_notes.get("1.0", "end").strip()
            category = self.cmb_category.get().strip()
            if not first or not last or not bdate_str:
                raise ValueError
            bdate = datetime.date.fromisoformat(bdate_str)
        except Exception:
            messagebox.showerror(title="Invalid input", message="Please provide valid values.", parent=self)
            return
        self.result = (first, last, bdate, email, notes, category)
        self.destroy()

    def _cancel(self) -> None:
        self.result = None
        self.destroy()

# ---------------------------------------------------------------------------
# Controller – connects UI events to model actions.
# ---------------------------------------------------------------------------
import json
import threading
from pathlib import Path

import notifications

class Controller:

    """Orchestrates interaction between the ``Model`` and ``View``.

    The controller binds callbacks, drives data refreshes, and updates the
    dashboard cards. It also handles CSV import/export, search filtering, and
    the countdown column. Additionally it implements startup dashboard view,
    daily birthday pop‑up, and system‑tray integration.
    """
    def _handle_startup_popup(self):
        birthdays = self.model.birthdays_today()

        if not birthdays:
            return

        lines = []

        for row in birthdays:
            first_name = row[1]
            last_name = row[2]
            lines.append(f"{first_name} {last_name}")

        messagebox.showinfo(
            "🎂 Birthdays Today",
            "\n".join(lines)
        )
    def __init__(self, root: CTk) -> None:
        self.model = Model()
        self.view = View(root)
        self._bind_events()
        # Start on Dashboard view and populate it
        self.show_dashboard()
        self.update_dashboard()
        # Populate initial table view (used when switching back)
        self.refresh_table(self.model.get_all_birthdays())
        # Hook up search variable changes for live filtering
        self.view.search_var.trace_add("write", self._on_search_change)
        # Daily popup logic
        self.view.root.after(1000, self._handle_startup_popup)
        # self._handle_startup_popup()
        # Bind minimize/close events for tray behavior
        # self.view.root.protocol("WM_DELETE_WINDOW", self._on_close)
        # self.view.root.bind("<Unmap>", self._on_minimize)
        # Start system tray in background
        threading.Thread(target=notifications.start_tray_if_needed, daemon=True).start()

    # ---------------------------------------------------------------------
    # Event binding
    # ---------------------------------------------------------------------
    def _bind_events(self) -> None:
        self.view.btn_add.configure(command=self.on_add)
        self.view.btn_edit.configure(command=self.on_edit)
        self.view.btn_delete.configure(command=self.on_delete)
        self.view.btn_refresh.configure(
            command=lambda: self.refresh_table(self.model.get_all_birthdays())
        )
        self.view.btn_dashboard.configure(command=self.show_dashboard)
        self.view.btn_birthdays.configure(command=lambda: self.view.show_table())
        # New CSV buttons
        self.view.btn_import.configure(command=self.on_import_csv)
        self.view.btn_export.configure(command=self.on_export_csv)

    # ---------------------------------------------------------------------
    # CRUD callbacks
    # ---------------------------------------------------------------------
    def on_add(self) -> None:
        dlg = _BirthdayDialog(self.view.root, "Add Birthday")
        if not dlg.result:
            return
        fn, ln, bdate, email, notes, cat = dlg.result
        self.model.add_birthday(fn, ln, bdate, email=email, notes=notes, category=cat)
        self.refresh_table(self.model.get_all_birthdays())

    def on_edit(self) -> None:
        b_id = self.view.get_selected_id()
        if b_id is None:
            self._show_msg("Please select a birthday to edit.")
            return
        all_rows = self.model.get_all_birthdays()
        rec = next(r for r in all_rows if r[0] == b_id)
        _, fn, ln, bdate, email, notes, cat, _, _ = rec
        dlg = _BirthdayDialog(
            self.view.root,
            "Edit Birthday",
            first_name=fn,
            last_name=ln,
            birthday=bdate,
            email=email,
            notes=notes,
            category=cat,
        )
        if not dlg.result:
            return
        fn2, ln2, bdate2, email2, notes2, cat2 = dlg.result
        self.model.update_birthday(
            b_id,
            first_name=fn2,
            last_name=ln2,
            birthday=bdate2,
            email=email2,
            notes=notes2,
            category=cat2,
        )
        self.refresh_table(self.model.get_all_birthdays())

    def on_delete(self) -> None:
        b_id = self.view.get_selected_id()
        if b_id is None:
            self._show_msg("Please select a birthday to delete.")
            return
        if not self._confirm("Delete this birthday?"):
            return
        self.model.delete_birthday(b_id)
        self.refresh_table(self.model.get_all_birthdays())

    # ---------------------------------------------------------------------
    # CSV import / export
    # ---------------------------------------------------------------------
    def on_import_csv(self) -> None:
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(
            title="Import CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not file_path:
            return
        try:
            imported = self.model.import_csv(file_path)
            self._show_msg(f"Successfully imported {imported} records.")
            self.refresh_table(self.model.get_all_birthdays())
        except Exception as e:
            self._show_msg(f"Import failed: {e}")

    def on_export_csv(self) -> None:
        from tkinter import filedialog
        file_path = filedialog.asksaveasfilename(
            title="Export CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not file_path:
            return
        try:
            exported = self.model.export_csv(file_path)
            self._show_msg(f"Exported {exported} records to {file_path}.")
        except Exception as e:
            self._show_msg(f"Export failed: {e}")

    # ---------------------------------------------------------------------
    # Search handling
    # ---------------------------------------------------------------------
    def _on_search_change(self, *_) -> None:
        """Filter table rows based on the search entry.

        The search matches first name, last name, or email fields case‑insensitively.
        """
        query = self.view.search_var.get().strip().lower()
        all_data = self.model.get_all_birthdays()
        if not query:
            filtered = all_data
        else:
            filtered = [
                row
                for row in all_data
                if query in row[1].lower() or query in row[2].lower() or (row[4] and query in row[4].lower())
            ]
        self.refresh_table(filtered)

    # ---------------------------------------------------------------------
    # Dashboard handling
    # ---------------------------------------------------------------------
    def show_dashboard(self) -> None:
        self.view.show_dashboard()
        self.update_dashboard()

    def update_dashboard(self) -> None:
        # ---------- Birthdays Today ----------
        today = self.model.birthdays_today()
        today_names = [f"{r[1]} {r[2]}" for r in today]
        today_content = f"Count: {len(today)}\n" + "\n".join(today_names) if today_names else "Count: 0"
        self.view.update_card(self.view.card_today, today_content)

        # ---------- Next 10 Days ----------
        next10 = self.model.get_upcoming_birthdays(10)
        next10_lines = []
        for rec in next10:
            # rec: (id, first, last, bdate, email, notes, cat, month, day)
            name = f"{rec[1]} {rec[2]}"
            bdate: datetime.date = rec[3]
            date_str = bdate.strftime('%d %b %Y')
            next10_lines.append(f"{name} – {date_str}")
        next10_content = f"Count: {len(next10)}\n" + "\n".join(next10_lines) if next10_lines else "Count: 0"
        self.view.update_card(self.view.card_next10, next10_content)

        # ---------- Next Birthday ----------
        if next10:
            next_birth = next10[0]
            name = f"{next_birth[1]} {next_birth[2]}"
            bdate: datetime.date = next_birth[3]
            # Days remaining calculation
            today_date = datetime.date.today()
            # Compute next occurrence (handles year wrap)
            next_occurrence = datetime.date(year=today_date.year, month=next_birth[7], day=next_birth[8])
            if next_occurrence < today_date:
                next_occurrence = datetime.date(year=today_date.year + 1, month=next_birth[7], day=next_birth[8])
            days_rem = (next_occurrence - today_date).days
            age_after = self.model.calculate_age(bdate) + 1
            next_content = (
                f"{name}\n"
                f"{bdate.strftime('%d %b %Y')}\n"
                f"{days_rem} days remaining\n"
                f"Turns {age_after}"
            )
            self.view.update_card(self.view.card_next, next_content)
        else:
            self.view.update_card(self.view.card_next, "—")

        # ---------- Total Contacts ----------
        total = len(self.model.get_all_birthdays())
        self.view.update_card(self.view.card_total, f"Total: {total}")

    # ---------------------------------------------------------------------
    # UI helper methods
    # ---------------------------------------------------------------------
    def refresh_table(self, data: List[Tuple]) -> None:
        """Refresh the table view, adding a ``days_remaining`` column.

        ``data`` is a list of birthday tuples as returned by the model.
        """
        # Compute days remaining for each record
        today = datetime.date.today()
        enriched = []
        for row in data:
            _, first, last, bdate, email, notes, category, month, day = row
            # Determine next occurrence of the birthday
            next_bday = datetime.date(year=today.year, month=month, day=day)
            if next_bday < today:
                next_bday = datetime.date(year=today.year + 1, month=month, day=day)
            days_rem = (next_bday - today).days
            enriched.append((*row, days_rem))
        # Update Treeview rows
        self.view.clear_table()
        for rec in enriched:
            # Convert date to ISO string for display
            display_row = list(rec)
            # Replace datetime.date with ISO format string for the birthday column (index 3)
            if isinstance(display_row[3], datetime.date):
                display_row[3] = display_row[3].isoformat()
            self.view.insert_row(display_row)

    def _show_msg(self, msg: str) -> None:
        messagebox.showinfo(title="Info", message=msg, parent=self.view.root)

    def _confirm(self, msg: str) -> bool:
        return messagebox.askyesno(title="Confirm", message=msg, parent=self.view.root)

# ---------------------------------------------------------------------------
# Entry point – start the application if this file is executed directly.
# ---------------------------------------------------------------------------
def main() -> None:
    app = CTk()
    Controller(app)
    app.mainloop()

if __name__ == "__main__":
    main()
