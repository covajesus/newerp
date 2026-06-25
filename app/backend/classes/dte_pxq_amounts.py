"""Montos DTE para documentos con líneas precio×cantidad (neto + IVA 19 %)."""

from typing import Optional


def pxq_net_total_from_items(items) -> Optional[int]:
    """Suma el neto de líneas PXQ normalizadas (campo total_amount por línea)."""
    if not items:
        return None
    total = 0
    for item in items:
        try:
            total += int(item.get("total_amount") or 0)
        except (TypeError, ValueError):
            continue
    return total if total > 0 else None


def dte_totals_from_net(net: int) -> tuple[int, int, int, int]:
    """Retorna (subtotal, tax, total, cash_amount). total/cash_amount incluyen IVA."""
    net = int(net)
    gross = round(net * 1.19)
    tax = gross - net
    return net, tax, gross, gross
