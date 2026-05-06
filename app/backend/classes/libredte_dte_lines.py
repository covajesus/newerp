"""Construcción de líneas Detalle (JSON LibreDTE → XML SII) para facturas/boletas con ítems agrupados."""


_NMB_ITEM_MAX = 80
_DSC_ITEM_MAX = 500
_VLR_CODIGO_MAX = 64
_UNMD_MAX = 32


def libredte_detalle_line_from_group_item(item: dict) -> dict:
    """
    Mapea un ítem normalizado a un dict Detalle compatible con emitir?normalizar=1.

    - NmbItem: nombre breve (item_name, o description, o «Ítem n»).
    - DscItem: descripción extendida — prioriza columna dsc_item; si no, ``description`` (detalle),
      para que el payload no quede sin DscItem cuando solo se llenó el detalle y no dsc_item.
    - CdgItem: solo si hay item_code (objeto TpoCodigo + VlrCodigo, no array; el array rompe el XML del SII).
    - UnmdItem: solo si hay unit_measure.
    """
    qty = int(item["quantity"])
    prc = int(item["unit_amount"])
    monto = int(item["total_amount"])

    dsc_full = (item.get("description") or "").strip()
    dsc_col = ""
    raw_dsc = item.get("dsc_item")
    if raw_dsc is not None:
        s = str(raw_dsc).strip()
        if s:
            dsc_col = s[:_DSC_ITEM_MAX]

    item_name = (item.get("item_name") or "").strip()
    raw_code = item.get("item_code")
    code = (str(raw_code).strip() if raw_code is not None else "")[:_VLR_CODIGO_MAX]
    raw_um = item.get("unit_measure")
    um = (str(raw_um).strip() if raw_um is not None else "")[:_UNMD_MAX]

    if item_name:
        nm = item_name[:_NMB_ITEM_MAX]
    elif dsc_full:
        nm = dsc_full[:_NMB_ITEM_MAX]
    else:
        nm = f"Ítem {item.get('line_number', 1)}"

    line: dict = {
        "NmbItem": nm,
        "QtyItem": qty,
        "PrcItem": prc,
        "MontoItem": monto,
    }

    # DscItem: columna dsc_item o detalle (no enviar solo el guion placeholder de BD)
    dsc_out = dsc_col if dsc_col else (dsc_full[:_DSC_ITEM_MAX] if dsc_full else "")
    if dsc_out and dsc_out.strip() not in ("", "-"):
        line["DscItem"] = dsc_out

    if code:
        line["CdgItem"] = {"TpoCodigo": "INT1", "VlrCodigo": code}

    if um:
        line["UnmdItem"] = um

    return line
