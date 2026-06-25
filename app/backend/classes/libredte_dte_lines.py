"""Build Detalle lines (LibreDTE JSON → SII XML) for grouped invoice/ticket items."""


_NMB_ITEM_MAX = 80
_DSC_ITEM_MAX = 500
_VLR_CODIGO_MAX = 64
_UNMD_MAX = 32


def libredte_detail_line_from_group_item(item: dict, *, include_line_amount: bool = True) -> dict:
    """
    Map a normalized item to a Detalle dict compatible with emitir?normalizar=1.

    - NmbItem: short name (item_name, or description, or «Item n»).
    - DscItem: extended description — prefers dsc_item column; else ``description``.
    - CdgItem: only when item_code is set (TpoCodigo + VlrCodigo object).
    - UnmdItem: only when unit_measure is set.

    Electronic ticket (39): use ``include_line_amount=False`` — same keys as a simple
    ticket (QtyItem + PrcItem only). Sending MontoItem with normalizar=1 may duplicate totals.
    """
    qty = int(item["quantity"])
    raw_unit = int(item["unit_amount"])
    line_amount = int(item["total_amount"])
    if qty > 0 and line_amount != qty * raw_unit:
        unit_price = max(0, round(line_amount / qty))
    else:
        unit_price = raw_unit

    detail_text = (item.get("description") or "").strip()
    dsc_column = ""
    raw_dsc = item.get("dsc_item")
    if raw_dsc is not None:
        s = str(raw_dsc).strip()
        if s:
            dsc_column = s[:_DSC_ITEM_MAX]

    item_name = (item.get("item_name") or "").strip()
    raw_code = item.get("item_code")
    item_code = (str(raw_code).strip() if raw_code is not None else "")[:_VLR_CODIGO_MAX]
    raw_unit_measure = item.get("unit_measure")
    unit_measure = (str(raw_unit_measure).strip() if raw_unit_measure is not None else "")[:_UNMD_MAX]

    if item_name:
        name_field = item_name[:_NMB_ITEM_MAX]
    elif detail_text:
        name_field = detail_text[:_NMB_ITEM_MAX]
    else:
        name_field = f"Item {item.get('line_number', 1)}"

    line: dict = {
        "NmbItem": name_field,
        "QtyItem": qty,
        "PrcItem": unit_price,
    }
    if include_line_amount:
        line["MontoItem"] = line_amount

    dsc_out = dsc_column if dsc_column else (detail_text[:_DSC_ITEM_MAX] if detail_text else "")
    if dsc_out and dsc_out.strip() not in ("", "-"):
        line["DscItem"] = dsc_out

    if item_code:
        line["CdgItem"] = {"TpoCodigo": "INT1", "VlrCodigo": item_code}

    if unit_measure:
        line["UnmdItem"] = unit_measure

    return line
