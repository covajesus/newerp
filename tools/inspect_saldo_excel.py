import pandas as pd

path = r"C:\Users\jesus\Downloads\Saldo_y_Mov_No_Facturado (4).xls"
xl = pd.ExcelFile(path, engine="xlrd")

for sheet in xl.sheet_names:
    df0 = pd.read_excel(xl, sheet_name=sheet, header=None)
    print(f"\n===== SHEET: {sheet} shape={df0.shape} =====")
    # show first 25 rows raw
    pd.set_option("display.max_columns", 30)
    pd.set_option("display.width", 200)
    pd.set_option("display.max_colwidth", 40)
    print(df0.head(25).to_string())
    print("--- non-empty rows", int(df0.dropna(how="all").shape[0]))

# Try with header detection on main sheet
df = pd.read_excel(xl, sheet_name="Saldo y Mov No Facturado", header=None)
# find header row: first row with several non-null
for i in range(min(15, len(df))):
    vals = [str(v).strip() for v in df.iloc[i].tolist() if pd.notna(v)]
    print(f"ROW{i}: {vals[:12]}")
