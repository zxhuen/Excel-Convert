import pandas as pd
import os

input_file = r""

output_file = r""


def convert():
    if not os.path.exists(input_file):
        print(f"Error: Could not find '{input_file}'. Please check the file name.")
        return

    if input_file.endswith(".csv"):
        try:
            df = pd.read_csv(input_file, encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(input_file, encoding="latin1")
    else:
        df = pd.read_excel(input_file, sheet_name=0)

    df.to_json(output_file, orient="records", indent=4, force_ascii=False)
    print(f"Success! '{input_file}' has been converted and saved as '{output_file}'.")


if __name__ == "__main__":
    convert()
