import pandas as pd

path = r"C:\Users\jesus\Downloads\Saldo_y_Mov_No_Facturado (4).xls"
df = pd.read_excel(path, engine="xlrd", sheet_name="Saldo y Mov No Facturado", header=None)

# movements start at row 18 (0-indexed), cols: fecha=1, tarjeta=2, desc=4, ciudad=5, cuotas=6?, monto label=7?, monto=10
# Looking at data again:
# Fecha col1, Tipo tarjeta col2, Descripcion col4, Ciudad col5?, something col6, Monto ($) somehow
# Row18: fecha 21/08, tarjeta, desc Pago Pesos TAR, empty, empty?, 01/01, 1/0, empty, -570000
# columns: 1=fecha, 2=tipo, 4=desc, 5=ciudad?, 6=?, 7=cuotas?, 8=?, 10=monto

mov = df.iloc[18:].copy()
mov = mov.dropna(how="all")
# filter rows with date-like in col1
rows = []
for _, r in mov.iterrows():
    fecha = r[1]
    monto = r[10]
    if pd.isna(fecha) or pd.isna(monto):
        # maybe section headers
        if pd.notna(r[1]) and isinstance(r[1], str) and "Movimiento" in r[1]:
            print("SECTION", r[1])
        continue
    rows.append(
        {
            "fecha": str(fecha)[:10] if not isinstance(fecha, str) else fecha,
            "desc": r[4],
            "ciudad": r[5],
            "cuotas": r[7] if pd.notna(r[7]) else r[6],
            "monto": float(monto),
        }
    )

m = pd.DataFrame(rows)
print("movimientos", len(m))
print("suma montos", m["monto"].sum())
print("cargos (+)", m.loc[m["monto"] > 0, "monto"].sum(), "n", (m["monto"] > 0).sum())
print("abonos (-)", m.loc[m["monto"] < 0, "monto"].sum(), "n", (m["monto"] < 0).sum())
print("\nTop cargos:")
print(m[m["monto"] > 0].sort_values("monto", ascending=False).head(15).to_string(index=False))
print("\nAbonos/pagos:")
print(m[m["monto"] < 0].to_string(index=False))
print("\nTodas desc unique sample:")
print(m["desc"].value_counts().head(20))
