import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import os


def process_files():
    source_path = entry_source.get()
    target_path = entry_target.get()

    if not source_path or not target_path:
        messagebox.showerror(
            "Error", "Please select both the Source file and Target file!"
        )
        return

    try:
        # 1. Read Source File (skipping the top 9 metadata rows)
        if source_path.endswith(".csv"):
            df_source = pd.read_csv(source_path, skiprows=9)
        else:
            df_source = pd.read_excel(source_path, skiprows=9)

        # Clean up any unnamed or empty columns
        df_source = df_source.loc[:, ~df_source.columns.str.contains("^Unnamed")]

        # 2. Read Target File
        if target_path.endswith(".csv"):
            df_target = pd.read_csv(target_path)
        else:
            df_target = pd.read_excel(target_path, sheet_name=0)

        # 3. Validate Columns in Source File
        name_col = "Student Name"
        no_col = "Student No"

        if name_col not in df_source.columns or no_col not in df_source.columns:
            messagebox.showerror(
                "Error",
                f"Could not find '{name_col}' or '{no_col}' columns.\nFound columns: {list(df_source.columns)}",
            )
            return

        # Drop rows where Student Name or Student No are completely empty
        df_source = df_source.dropna(subset=[name_col, no_col])

        # Clean Student No (convert to string, remove trailing .0 if read as float)
        df_source[no_col] = (
            df_source[no_col]
            .astype(str)
            .str.replace(r"\.0$", "", regex=True)
            .str.strip()
        )
        df_source[name_col] = df_source[name_col].astype(str).str.strip()

        # 4. Format as: student name - student no (e.g., DE LUNA, HAZEL SHANE - 2000370634)
        formatted_contacts = df_source[name_col] + " - " + df_source[no_col]

        # 5. Insert/Update into 'ContactName' column of target (convert dtype to string first to prevent float64 error)
        if "ContactName" not in df_target.columns:
            df_target["ContactName"] = ""

        df_target["ContactName"] = df_target["ContactName"].astype(str)

        # Assign the formatted strings to the ContactName column
        rows_to_fill = min(len(formatted_contacts), len(df_target))
        df_target.loc[: rows_to_fill - 1, "ContactName"] = formatted_contacts.iloc[
            :rows_to_fill
        ].values

        # 6. Save the updated target file
        if target_path.endswith(".csv"):
            df_target.to_csv(target_path, index=False)
        else:
            df_target.to_excel(target_path, index=False, sheet_name="ContactName")

        messagebox.showinfo(
            "Success",
            "Data successfully extracted and updated on the ContactName column!",
        )

    except Exception as e:
        messagebox.showerror("An Error Occurred", str(e))


def browse_source():
    filename = filedialog.askopenfilename(
        title="Select Source OR Register File",
        filetypes=[("Excel & CSV files", "*.xlsx *.xls *.csv")],
    )
    entry_source.delete(0, tk.END)
    entry_source.insert(0, filename)


def browse_target():
    filename = filedialog.askopenfilename(
        title="Select Target Template File",
        filetypes=[("Excel & CSV files", "*.xlsx *.xls *.csv")],
    )
    entry_target.delete(0, tk.END)
    entry_target.insert(0, filename)


# --- GUI Setup ---
root = tk.Tk()
root.title("Student Data Extractor")
root.geometry("500x260")
root.resizable(False, False)

tk.Label(
    root, text="Student Data Extractor to ContactName", font=("Arial", 12, "bold")
).pack(pady=10)

# Source File Selection
frame_source = tk.Frame(root)
frame_source.pack(fill="x", padx=20, pady=5)
tk.Label(frame_source, text="Source File:", width=12, anchor="w").pack(side="left")
entry_source = tk.Entry(frame_source, width=40)
entry_source.pack(side="left", padx=5)
tk.Button(frame_source, text="Browse", command=browse_source).pack(side="left")

# Target File Selection
frame_target = tk.Frame(root)
frame_target.pack(fill="x", padx=20, pady=5)
tk.Label(frame_target, text="Target File:", width=12, anchor="w").pack(side="left")
entry_target = tk.Entry(frame_target, width=40)
entry_target.pack(side="left", padx=5)
tk.Button(frame_target, text="Browse", command=browse_target).pack(side="left")

# Run Button
tk.Button(
    root,
    text="Extract & Update",
    command=process_files,
    bg="#4CAF50",
    fg="white",
    font=("Arial", 10, "bold"),
    width=20,
    height=2,
).pack(pady=20)

root.mainloop()
