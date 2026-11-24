
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import difflib
import webbrowser
from pathlib import Path


# ----------------------------- Mosque class -----------------------------

class Mosque:
    """Represents one mosque record."""

    def __init__(self, ID, name, mosque_type, address, coordinates, Imam_name):
        self.ID = int(ID)
        self.name = str(name)
        self.type = str(mosque_type)
        self.address = str(address)
        self.coordinates = str(coordinates)
        self.Imam_name = str(Imam_name)

    def to_tuple(self):
        return (
            self.ID,
            self.name,
            self.type,
            self.address,
            self.coordinates,
            self.Imam_name
        )

    @classmethod
    def from_record(cls, record):
        return cls(*record)

    def __str__(self):
        return (
            f"ID: {self.ID} | Name: {self.name} | Type: {self.type} | "
            f"Address: {self.address} | Coordinates: {self.coordinates} | "
            f"Imam: {self.Imam_name}"
        )


# ---------------------------- Database class ----------------------------

class MosqueDatabase:
    """Handles all SQLite operations for the Mosq table."""

    def __init__(self, db_name="mosques.db"):
        self.connection = sqlite3.connect(db_name)
        self.cursor = self.connection.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Mosq (
                ID INTEGER PRIMARY KEY,
                Name TEXT NOT NULL,
                Type TEXT NOT NULL,
                Address TEXT NOT NULL,
                Coordinates TEXT NOT NULL,
                Imam_Name TEXT NOT NULL
            )
        """)
        self.connection.commit()

    def Display(self):
        self.cursor.execute("""
            SELECT ID, Name, Type, Address, Coordinates, Imam_Name
            FROM Mosq ORDER BY ID
        """)
        return self.cursor.fetchall()

    def Search(self, name):
        self.cursor.execute("""
            SELECT ID, Name, Type, Address, Coordinates, Imam_Name
            FROM Mosq
            WHERE Name = ? COLLATE NOCASE
            LIMIT 1
        """, (name.strip(),))
        return self.cursor.fetchone()

    def Insert(self, ID, name, mosque_type, address, coordinates, Imam_name):
        self.cursor.execute("""
            INSERT INTO Mosq (ID, Name, Type, Address, Coordinates, Imam_Name)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (ID, name, mosque_type, address, coordinates, Imam_name))
        self.connection.commit()

    def Delete(self, ID):
        self.cursor.execute("DELETE FROM Mosq WHERE ID = ?", (ID,))
        self.connection.commit()
        return self.cursor.rowcount

    # Extra feature: update only the Imam_Name field.
    def Update_Imam(self, name, new_imam):
        self.cursor.execute("""
            UPDATE Mosq SET Imam_Name = ?
            WHERE Name = ? COLLATE NOCASE
        """, (new_imam, name.strip()))
        self.connection.commit()
        return self.cursor.rowcount

    def __del__(self):
        try:
            if getattr(self, "connection", None) is not None:
                self.connection.close()
        except sqlite3.Error:
            pass


# ------------------------------- GUI class -------------------------------

class MosqueManagementApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Mosques Management System")
        self.root.geometry("1120x650")
        self.root.minsize(900, 560)

        self.database = MosqueDatabase()
        self.mosque_objects = []
        self.selected_mosque = None

        self._build_interface()
        self.display_all()

    def _build_interface(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        main = ttk.Frame(self.root, padding=12)
        main.grid(row=0, column=0, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(1, weight=1)

        title = ttk.Label(
            main,
            text="Mosques Management System",
            font=("Arial", 18, "bold")
        )
        title.grid(row=0, column=0, columnspan=2, pady=(0, 12))

        # Part 1: input fields
        form = ttk.LabelFrame(main, text="Mosque Information", padding=12)
        form.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)

        self.entries = {}
        fields = [
            ("ID", "ID"),
            ("Name", "Name"),
            ("Address", "Address"),
            ("Coordinates", "Coordinates"),
            ("Imam_Name", "Imam Name"),
        ]

        # Two-column layout similar to the assignment illustration.
        positions = {
            "ID": (0, 0),
            "Name": (0, 2),
            "Address": (1, 2),
            "Coordinates": (2, 0),
            "Imam_Name": (2, 2),
        }

        for key, label_text in fields:
            row, col = positions[key]
            ttk.Label(form, text=label_text + ":").grid(
                row=row, column=col, sticky="w", padx=5, pady=8
            )
            entry = ttk.Entry(form, width=25)
            entry.grid(row=row, column=col + 1, sticky="ew", padx=5, pady=8)
            self.entries[key] = entry

        ttk.Label(form, text="Type:").grid(
            row=1, column=0, sticky="w", padx=5, pady=8
        )
        self.type_var = tk.StringVar(value="Local Mosque")
        type_menu = ttk.OptionMenu(
            form, self.type_var, "Local Mosque",
            "Local Mosque", "Friday Mosque", "Eid Mosque"
        )
        type_menu.grid(row=1, column=1, sticky="ew", padx=5, pady=8)

        note = ttk.Label(
            form,
            text="Coordinates format: latitude,longitude  (e.g. 24.7136,46.6753)",
            foreground="#555555",
            wraplength=430
        )
        note.grid(row=3, column=0, columnspan=4, sticky="w", padx=5, pady=(5, 12))

        # Part 3: operation buttons
        buttons = ttk.LabelFrame(form, text="Operations", padding=10)
        buttons.grid(row=4, column=0, columnspan=4, sticky="ew", padx=5, pady=8)
        for col in range(2):
            buttons.columnconfigure(col, weight=1)

        ttk.Button(buttons, text="Display_All", command=self.display_all).grid(
            row=0, column=0, sticky="ew", padx=5, pady=5
        )
        ttk.Button(buttons, text="Search", command=self.search_mosque).grid(
            row=0, column=1, sticky="ew", padx=5, pady=5
        )
        ttk.Button(buttons, text="Add_Entry", command=self.add_mosque).grid(
            row=1, column=0, sticky="ew", padx=5, pady=5
        )
        ttk.Button(buttons, text="Delete_Entry", command=self.delete_mosque).grid(
            row=1, column=1, sticky="ew", padx=5, pady=5
        )

        # Part 4: extra features
        extras = ttk.LabelFrame(form, text="Extra Features", padding=10)
        extras.grid(row=5, column=0, columnspan=4, sticky="ew", padx=5, pady=8)
        for col in range(2):
            extras.columnconfigure(col, weight=1)

        ttk.Button(extras, text="Update Imam", command=self.update_imam).grid(
            row=0, column=0, sticky="ew", padx=5, pady=5
        )
        ttk.Button(extras, text="Display on Map", command=self.display_on_map).grid(
            row=0, column=1, sticky="ew", padx=5, pady=5
        )
        ttk.Label(
            extras,
            text="Enhanced Search: similar mosque names are suggested automatically.",
            foreground="#555555",
            wraplength=420
        ).grid(row=1, column=0, columnspan=2, sticky="w", padx=5, pady=5)

        # Part 2: ListBox
        list_frame = ttk.LabelFrame(main, text="Mosque Records", padding=10)
        list_frame.grid(row=1, column=1, sticky="nsew", padx=(8, 0))
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)

        self.listbox = tk.Listbox(
            list_frame,
            font=("Courier New", 9),
            activestyle="dotbox",
            selectmode=tk.SINGLE
        )
        self.listbox.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(
            list_frame, orient="vertical", command=self.listbox.yview
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.listbox.configure(yscrollcommand=scrollbar.set)
        self.listbox.bind("<<ListboxSelect>>", self.on_record_select)

        ttk.Button(
            list_frame, text="Clear Fields", command=self.clear_fields
        ).grid(row=1, column=0, sticky="ew", pady=(10, 0))

        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(main, textvariable=self.status_var, relief="sunken", anchor="w").grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0)
        )

    def _get_form_values(self):
        values = {key: entry.get().strip() for key, entry in self.entries.items()}
        mosque_type = self.type_var.get().strip()

        missing = [key for key, value in values.items() if not value]
        if missing:
            messagebox.showwarning(
                "Missing Information",
                "Please fill in all fields: " + ", ".join(missing)
            )
            return None

        try:
            mosque_id = int(values["ID"])
            if mosque_id <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid ID", "ID must be a positive integer.")
            return None

        # Validate coordinates as latitude,longitude.
        try:
            parts = [part.strip() for part in values["Coordinates"].split(",")]
            if len(parts) != 2:
                raise ValueError
            latitude, longitude = float(parts[0]), float(parts[1])
            if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Invalid Coordinates",
                "Enter coordinates as latitude,longitude (example: 24.7136,46.6753)."
            )
            return None

        return Mosque(
            mosque_id,
            values["Name"],
            mosque_type,
            values["Address"],
            values["Coordinates"],
            values["Imam_Name"]
        )

    def _refresh_list(self, records):
        self.listbox.delete(0, tk.END)
        self.mosque_objects = [Mosque.from_record(record) for record in records]
        for mosque in self.mosque_objects:
            self.listbox.insert(
                tk.END,
                f"{mosque.ID:<6} | {mosque.name:<24} | {mosque.type:<16} | "
                f"Imam: {mosque.Imam_name}"
            )

    def display_all(self):
        records = self.database.Display()
        self._refresh_list(records)
        self.status_var.set(f"Displayed {len(records)} mosque record(s).")

    def search_mosque(self):
        name = self.entries["Name"].get().strip()
        if not name:
            messagebox.showwarning("Search", "Enter the mosque name in the Name field.")
            return

        record = self.database.Search(name)
        if record:
            self._refresh_list([record])
            self.status_var.set(f"Found mosque: {record[1]}")
            return

        # Extra feature: suggest similar names using difflib.
        all_names = [row[1] for row in self.database.Display()]
        suggestions = difflib.get_close_matches(name, all_names, n=5, cutoff=0.45)

        if suggestions:
            suggestion_text = "\n".join(
                f"{index + 1}. {suggestion}"
                for index, suggestion in enumerate(suggestions)
            )
            chosen = messagebox.askyesno(
                "Mosque Not Found",
                f"No exact match was found for '{name}'.\n\n"
                f"Similar names:\n{suggestion_text}\n\n"
                f"Search for the closest match: {suggestions[0]}?"
            )
            if chosen:
                self.entries["Name"].delete(0, tk.END)
                self.entries["Name"].insert(0, suggestions[0])
                found = self.database.Search(suggestions[0])
                if found:
                    self._refresh_list([found])
                    self.status_var.set(f"Found suggested match: {found[1]}")
                    return

        self._refresh_list([])
        messagebox.showinfo("Search", "No matching mosque was found.")
        self.status_var.set("No matching mosque found.")

    def add_mosque(self):
        mosque = self._get_form_values()
        if mosque is None:
            return
        try:
            self.database.Insert(*mosque.to_tuple())
            messagebox.showinfo("Success", "Mosque record added successfully.")
            self.clear_fields()
            self.display_all()
        except sqlite3.IntegrityError:
            messagebox.showerror(
                "Duplicate ID",
                f"A mosque with ID {mosque.ID} already exists."
            )
        except sqlite3.Error as error:
            messagebox.showerror("Database Error", str(error))

    def delete_mosque(self):
        mosque_id_text = self.entries["ID"].get().strip()
        if not mosque_id_text:
            messagebox.showwarning("Delete", "Enter the mosque ID in the ID field.")
            return
        try:
            mosque_id = int(mosque_id_text)
        except ValueError:
            messagebox.showerror("Invalid ID", "ID must be an integer.")
            return

        if not messagebox.askyesno(
            "Confirm Delete", f"Are you sure you want to delete mosque ID {mosque_id}?"
        ):
            return

        deleted = self.database.Delete(mosque_id)
        if deleted:
            messagebox.showinfo("Success", "Mosque record deleted.")
        else:
            messagebox.showinfo("Delete", "No mosque was found with that ID.")
        self.clear_fields()
        self.display_all()

    def update_imam(self):
        name = self.entries["Name"].get().strip()
        new_imam = self.entries["Imam_Name"].get().strip()
        if not name or not new_imam:
            messagebox.showwarning(
                "Update Imam",
                "Search/select a mosque and enter the new Imam_Name."
            )
            return

        updated = self.database.Update_Imam(name, new_imam)
        if updated:
            messagebox.showinfo("Success", "Imam name updated successfully.")
            self.display_all()
        else:
            messagebox.showinfo(
                "Update Imam", "No mosque with that exact name was found."
            )

    def display_on_map(self):
        name = self.entries["Name"].get().strip()
        if not name:
            messagebox.showwarning(
                "Display on Map", "Search/select a mosque first."
            )
            return

        record = self.database.Search(name)
        if not record:
            messagebox.showerror(
                "Display on Map", "Mosque not found. Search for it first."
            )
            return

        try:
            parts = [part.strip() for part in record[4].split(",")]
            latitude, longitude = float(parts[0]), float(parts[1])
        except (ValueError, IndexError):
            messagebox.showerror(
                "Coordinates Error",
                "The saved coordinates are not in latitude,longitude format."
            )
            return

        try:
            import folium
        except ImportError:
            messagebox.showerror(
                "Missing Library",
                "The map feature needs folium.\nInstall it using:\n"
                "python -m pip install folium"
            )
            return

        map_object = folium.Map(location=[latitude, longitude], zoom_start=16)
        folium.Marker(
            [latitude, longitude],
            popup=record[1],
            tooltip=record[1]
        ).add_to(map_object)

        map_path = Path("mosque_location.html").resolve()
        map_object.save(str(map_path))
        webbrowser.open(map_path.as_uri())
        self.status_var.set(f"Map opened for {record[1]}.")

    def on_record_select(self, _event=None):
        selection = self.listbox.curselection()
        if not selection:
            return
        index = selection[0]
        if index >= len(self.mosque_objects):
            return

        mosque = self.mosque_objects[index]
        self.selected_mosque = mosque
        self.entries["ID"].delete(0, tk.END)
        self.entries["ID"].insert(0, str(mosque.ID))
        self.entries["Name"].delete(0, tk.END)
        self.entries["Name"].insert(0, mosque.name)
        self.entries["Address"].delete(0, tk.END)
        self.entries["Address"].insert(0, mosque.address)
        self.entries["Coordinates"].delete(0, tk.END)
        self.entries["Coordinates"].insert(0, mosque.coordinates)
        self.entries["Imam_Name"].delete(0, tk.END)
        self.entries["Imam_Name"].insert(0, mosque.Imam_name)
        self.type_var.set(mosque.type)
        self.status_var.set(f"Selected mosque: {mosque.name}")

    def clear_fields(self):
        for entry in self.entries.values():
            entry.delete(0, tk.END)
        self.type_var.set("Local Mosque")
        self.selected_mosque = None
        self.listbox.selection_clear(0, tk.END)

    def close(self):
        try:
            self.database.connection.close()
        except sqlite3.Error:
            pass
        self.root.destroy()


def main():
    root = tk.Tk()
    app = MosqueManagementApp(root)
    root.protocol("WM_DELETE_WINDOW", app.close)
    root.mainloop()


if __name__ == "__main__":
    main()