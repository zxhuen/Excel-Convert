import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import numpy as np
import csv
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
        # 1. Read Source File
        if source_path.endswith(".csv"):
            df_source = pd.read_csv(source_path, encoding="latin1")
            if (
                "OR REGISTER" in str(df_source.iloc[0, 0]).upper()
                or "OR Date" not in df_source.columns
            ):
                df_source = pd.read_csv(source_path, skiprows=9, encoding="latin1")
        else:
            df_source = pd.read_excel(source_path, skiprows=9)

        # Clean up unnamed/empty columns
        df_source = df_source.loc[:, ~df_source.columns.str.contains("^Unnamed")]

        # 2. Read Target Template File (CSV format)
        if target_path.endswith(".csv"):
            df_target = pd.read_csv(target_path, encoding="latin1")
        else:
            df_target = pd.read_excel(target_path, sheet_name=0)

        # 3. Validate columns in source file
        name_col = "Student Name"
        no_col = "Student No"

        if name_col not in df_source.columns or no_col not in df_source.columns:
            messagebox.showerror(
                "Error",
                f"Could not find '{name_col}' or '{no_col}' columns in the source file.\nFound columns: {list(df_source.columns)}",
            )
            return

        # Drop rows where Student Name or Student No are empty
        df_source = df_source.dropna(subset=[name_col, no_col])

        # Clean Student No and Student Name
        df_source[no_col] = (
            df_source[no_col]
            .astype(str)
            .str.replace(r"\.0$", "", regex=True)
            .str.strip()
        )
        df_source[name_col] = df_source[name_col].astype(str).str.strip()

        ter_fee_cols = ["TER-Tuition Fee", "TER-Other School Fee", "Misc Fee"]
        shs_and_revenue_cols = [
            "SHS-Tuition Fee",
            "SHS-Misc Fee",
            "SHS-Other School Fee",
            "Other Revenue",
        ]
        all_fee_cols = ter_fee_cols + shs_and_revenue_cols

        fee_code_mapping = {
            "TER-Tuition Fee": "tf",
            "TER-Other School Fee": "osf",
            "Misc Fee": "mf",
            "SHS-Tuition Fee": "tf",
            "SHS-Misc Fee": "mf",
            "SHS-Other School Fee": "osf",
            "Other Revenue": "tor",
        }

        expanded_rows = []

        for _, row in df_source.iterrows():
            student_name = row[name_col]
            student_no = row[no_col]
            contact_str = f"{student_name} - {student_no}"

            # Metadata fields
            invoice_no = row.get("OR No", "")
            reference = row.get("Reference", "")
            date = row.get("OR Date", "")
            tracking_option = row.get("Program", "")

            # Helper function to parse numeric values safely
            def get_val(col_name):
                val = row.get(col_name, 0)
                if pd.isna(val):
                    return 0.0
                if isinstance(val, str):
                    val = val.replace(",", "").strip()
                try:
                    return float(val)
                except (ValueError, TypeError):
                    return 0.0

            # Calculate total sum across all fee columns for this student
            total_sum = sum(
                get_val(col) for col in all_fee_cols if col in df_source.columns
            )
            if total_sum == 0:
                total_sum = get_val("TOTAL Register")

            # Check SHS & Other Revenue columns
            shs_rev_fees = []
            for col in shs_and_revenue_cols:
                if col in df_source.columns:
                    val_float = get_val(col)
                    if val_float > 0:
                        item_code = fee_code_mapping.get(col, "tf")
                        shs_rev_fees.append((item_code, val_float))

            # Check TER columns (can be split/reduplicated if multiple TER fees are present)
            ter_fees = []
            for col in ter_fee_cols:
                if col in df_source.columns:
                    val_float = get_val(col)
                    if val_float > 0:
                        item_code = fee_code_mapping.get(col, "mf")
                        ter_fees.append((item_code, val_float))

            fees_to_output = []
            if shs_rev_fees:
                for item_code, amount in shs_rev_fees:
                    fees_to_output.append((item_code, amount))
            if ter_fees:
                for item_code, amount in ter_fees:
                    fees_to_output.append((item_code, amount))

            if not fees_to_output and total_sum > 0:
                fees_to_output.append(("mf", total_sum))

            # Generate row(s) with InventoryItemCode empty and Description holding the fee code
            for item_code, fee_amount in fees_to_output:
                new_row = {
                    "ContactName": contact_str,
                    "InvoiceNumber": invoice_no,
                    "Reference": reference,
                    "InvoiceDate": date,
                    "DueDate": date,
                    "  Total  ": f"{float(total_sum):,.2f}",
                    "InvoiceAmountPaid": "0.00",
                    "  InvoiceAmountDue  ": f"{float(total_sum):,.2f}",
                    "InventoryItemCode": "",  # Inventory left empty
                    "Description": item_code,  # Description holds tf, osf, mf, tor
                    "Quantity": 1,
                    " UnitAmount ": f"{float(fee_amount):,.2f}",
                    " LineAmount ": f"{float(fee_amount):,.2f}",
                    "TrackingOption1": tracking_option,
                    "Currency": "PHP",
                    "Type": "Sales invoice",
                    "Sent": "Unsent",
                    "Status": "Awaiting Payment",
                }
                expanded_rows.append(new_row)

        df_expanded = pd.DataFrame(expanded_rows)

        if df_expanded.empty:
            messagebox.showwarning("Warning", "No fee data found to extract!")
            return

        # 5. Map into target template structure
        for col in df_target.columns:
            if col not in df_expanded.columns:
                df_expanded[col] = np.nan

        df_final = df_expanded[df_target.columns]

        # 6. Save strictly as CSV format
        output_path = (
            target_path if target_path.endswith(".csv") else target_path + ".csv"
        )
        df_final.to_csv(
            output_path, index=False, encoding="latin1", quoting=csv.QUOTE_NONNUMERIC
        )

        messagebox.showinfo(
            "Success",
            f"Successfully processed {len(df_final)} line items and saved to CSV!\nPath: {output_path}",
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
        title="Select Target Sales Invoice CSV Template",
        filetypes=[("CSV files", "*.csv")],
    )
    entry_target.delete(0, tk.END)
    entry_target.insert(0, filename)


# --- GUI Setup ---
root = tk.Tk()
root.title("OR Register CSV Fee Automation")
root.geometry("520x280")
root.resizable(False, False)

tk.Label(root, text="CSV Fee Automation Processor", font=("Arial", 13, "bold")).pack(
    pady=10
)

# Source File Selection
frame_source = tk.Frame(root)
frame_source.pack(fill="x", padx=20, pady=5)
tk.Label(frame_source, text="Source File:", width=12, anchor="w").pack(side="left")
entry_source = tk.Entry(frame_source, width=42)
entry_source.pack(side="left", padx=5)
tk.Button(frame_source, text="Browse", command=browse_source).pack(side="left")

# Target File Selection
frame_target = tk.Frame(root)
frame_target.pack(fill="x", padx=20, pady=5)
tk.Label(frame_target, text="Target File:", width=12, anchor="w").pack(side="left")
entry_target = tk.Entry(frame_target, width=42)
entry_target.pack(side="left", padx=5)
tk.Button(frame_target, text="Browse", command=browse_target).pack(side="left")

# Run Button
tk.Button(
    root,
    text="Run Automation",
    command=process_files,
    bg="#2196F3",
    fg="white",
    font=("Arial", 11, "bold"),
    width=22,
    height=2,
).pack(pady=20)

root.mainloop()
