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

        self.btn_add = CTkButton(self.toolbar, text="Add")
        self.btn_edit = CTkButton(self.toolbar, text="Edit")
        self.btn_delete = CTkButton(self.toolbar, text="Delete")
        self.btn_refresh = CTkButton(self.toolbar, text="Refresh")
        self.btn_dashboard = CTkButton(self.toolbar, text="Dashboard")
        # New button to return to the birthdays list view
        self.btn_birthdays = CTkButton(self.toolbar, text="Birthdays")
        for btn in (
            self.btn_add,
            self.btn_edit,
            self.btn_delete,
            self.btn_refresh,
            self.btn_dashboard,
            self.btn_birthdays,
        ):
            btn.pack(side="left", padx=5)

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
        card = CTkFrame(parent, corner_radius=10)
        CTkLabel(card, text=title, font=("Helvetica", 14)).pack(pady=(10, 5))
        value_lbl = CTkLabel(card, text=value, font=("Helvetica", 24, "bold"))
        value_lbl.pack(pady=(0, 10))
        # Store for later updates
        card.value_label = value_lbl  # type: ignore
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

    def update_card(self, card: CTkFrame, new_value: str) -> None:
        """Update the numeric/value label inside a dashboard card."""
        card.value_label.configure(text=new_value)

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
class Controller:
    """Orchestrates interaction between the ``Model`` and ``View``.

    The controller binds callbacks, drives data refreshes, and updates the
    dashboard cards.
    """

    def __init__(self, root: CTk) -> None:
        self.model = Model()
        self.view = View(root)
        self._bind_events()
        self.refresh_table(self.model.get_all_birthdays())

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
    # Dashboard handling
    # ---------------------------------------------------------------------
    def show_dashboard(self) -> None:
        self.view.show_dashboard()
        self.update_dashboard()

    def update_dashboard(self) -> None:
        # Birthdays today count
        today = self.model.birthdays_today()
        self.view.update_card(self.view.card_today, str(len(today)))

        # Next 10 days count
        next10 = self.model.get_upcoming_birthdays(10)
        self.view.update_card(self.view.card_next10, str(len(next10)))

        # Next birthday (first upcoming after today)
        if next10:
            next_birth = next10[0]
            name = f"{next_birth[1]} {next_birth[2]}"
            # Age after the upcoming birthday
            age = self.model.calculate_age(next_birth[3]) + 1
            self.view.update_card(self.view.card_next, f"{name} ({age})")
        else:
            self.view.update_card(self.view.card_next, "—")

        # Total contacts
        total = len(self.model.get_all_birthdays())
        self.view.update_card(self.view.card_total, str(total))

    # ---------------------------------------------------------------------
    # UI helper methods
    # ---------------------------------------------------------------------
    def refresh_table(self, data: List[Tuple]) -> None:
        self.view.refresh_table(data)

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
