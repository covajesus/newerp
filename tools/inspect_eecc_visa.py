import fitz

path = r"C:\Users\jesus\Downloads\EECCTarjetaVisa.pdf"
doc = fitz.open(path)
assert doc.authenticate("1399"), "bad password"
print("pages", doc.page_count)
for i in range(doc.page_count):
    page = doc.load_page(i)
    print(f"\n===== PAGE {i+1} =====")
    print(page.get_text("text"))
# also save page 1 preview
pix = doc.load_page(0).get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
pix.save(r"C:\Users\jesus\Desktop\proyecto_jisparking\escritorio\newerp\tools\eecc_p1.png")
doc.close()
print("DONE")
