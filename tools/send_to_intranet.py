import requests
import json
from datetime import datetime, timedelta
import logging
from sql import DataBase

logging.basicConfig(level=logging.INFO)

db = DataBase()
today = datetime.now().date()


def row_get(row, key, index):
    """Funciona si row es dict o tupla/lista."""
    if isinstance(row, dict):
        return row[key]
    if hasattr(row, "keys"):
        try:
            return row[key]
        except Exception:
            return row[index]
    return row[index]


def settings_val(settings, index):
    """settings por índice (como antes), aunque venga como dict ordenado."""
    if isinstance(settings, dict):
        return list(settings.values())[index]
    return settings[index]


total_ticket_number = db.select_count("stored_tickets", "added_date", today)
print("Inicio del envio total de folios " + str(total_ticket_number))

data_settings = db.select("settings")
print("settings type:", type(data_settings))
if isinstance(data_settings, dict):
    print("settings keys:", list(data_settings.keys()))

iva = float(settings_val(data_settings, 7))

if total_ticket_number > 0:
    data = {
        "branch_office_id": settings_val(data_settings, 1),
        "cashier_id": settings_val(data_settings, 2),
        "total_ticket_number": total_ticket_number,
        "created_at": today.strftime("%Y-%m-%d 00:00:00"),
    }
    print(data)

    url = settings_val(data_settings, 12)
    headers = {"accept": "application/json"}
    intranet_response = requests.post(url, json=data, headers=headers)
    logging.info("Intento de envío del total de tickets: %s.", intranet_response.status_code)
    print(intranet_response.text)

two_days_ago = today - timedelta(days=2)
status = 0

tickets = db.select_all_between(
    "stored_tickets", "DATE(added_date)", status, two_days_ago, today
)
logging.info("Obtenidos %s tickets entre %s y %s.", len(tickets), two_days_ago, today)

if tickets:
    print("ticket type:", type(tickets[0]))
    print("ticket sample:", tickets[0])

for ticket in tickets:
    ticket_id = row_get(ticket, "id", 0)
    folio = row_get(ticket, "folio", 5)
    raw_added = row_get(ticket, "added_date", 21)
    cash_gross_amount = row_get(ticket, "cash_gross_amount", 6)
    card_gross_amount = row_get(ticket, "card_gross_amount", 8)

    if isinstance(raw_added, str):
        added_date = datetime.strptime(raw_added[:10], "%Y-%m-%d")
    elif isinstance(raw_added, datetime):
        added_date = raw_added
    else:
        # date u otro
        added_date = datetime.strptime(str(raw_added)[:10], "%Y-%m-%d")

    if cash_gross_amount != 0:
        total = cash_gross_amount
    else:
        total = card_gross_amount

    subtotal = round(total / iva)
    tax = total - subtotal

    if total > 0:
        db.update("stored_tickets", "intranet_status_id", 1, "id", ticket_id)

        print("Folio " + str(folio) + " processing.")

        data = {
            "branch_office_id": row_get(ticket, "branch_office_id", 1),
            "cashier_id": row_get(ticket, "cashier_id", 2),
            "dte_type_id": 39,
            "sii_send_status_id": "0",
            "sii_status_id": "0",
            "sii_track_id": "0",
            "dte_code": str(row_get(ticket, "dte_code", 4)),
            "folio": str(folio),
            "cash_amount": row_get(ticket, "cash_gross_amount", 6),
            "card_amount": row_get(ticket, "card_gross_amount", 8),
            "subtotal": subtotal,
            "tax": tax,
            "discount": 0,
            "total": total,
            "ticket_serial_number": row_get(ticket, "ticket_serial_number", 10),
            "ticket_hour": str(row_get(ticket, "ticket_hour", 11)),
            "ticket_transaction_number": row_get(ticket, "ticket_transaction_number", 12),
            "ticket_dispenser_number": row_get(ticket, "ticket_dispenser_number", 13),
            "ticket_station_number": row_get(ticket, "ticket_station_number", 15),
            "ticket_sa": str(row_get(ticket, "ticket_sa", 16)),
            "ticket_number": row_get(ticket, "ticket_number", 14),
            "ticket_correlative": row_get(ticket, "ticket_correlative", 17),
            "entrance_hour": str(row_get(ticket, "entrance_hour", 18)),
            "exit_hour": str(row_get(ticket, "exit_hour", 19)),
            "item_quantity": row_get(ticket, "item_quantity", 20),
            "sii_date": "2024-01-01",
            "added_date": str(row_get(ticket, "added_date", 21)),
        }

        url = settings_val(data_settings, 8)
        print(url)

        headers = {"accept": "application/json"}
        intranet_response = requests.post(url, json=data, headers=headers)
        intranet_response_data = json.loads(intranet_response.text)
        print(intranet_response.text)
        print(intranet_response_data["message"])

        if intranet_response_data["message"] == 1:
            print(f"Ticket {folio} sent successfully intranet.")

            intranet_update_url = str(settings_val(data_settings, 10)) + "/" + str(folio)
            print(intranet_update_url)
            requests.get(intranet_update_url, headers=headers)
            print(f"Folio {folio} updated successfully.")
            print(settings_val(data_settings, 15))

            if settings_val(data_settings, 16) == 1:
                data_old = {
                    "branch_office_id": row_get(ticket, "branch_office_id", 1),
                    "cashier_id": row_get(ticket, "cashier_id", 2),
                    "folio": folio,
                    "dte_code": row_get(ticket, "dte_code", 4),
                    "cash_amount": row_get(ticket, "cash_gross_amount", 6),
                    "card_amount": row_get(ticket, "card_gross_amount", 8),
                    "subtotal": subtotal,
                    "tax": tax,
                    "total": total,
                    "ticket_serial_number": row_get(ticket, "ticket_serial_number", 10),
                    "ticket_hour": row_get(ticket, "ticket_hour", 11),
                    "ticket_transaction_number": row_get(ticket, "ticket_transaction_number", 12),
                    "ticket_dispenser_number": row_get(ticket, "ticket_dispenser_number", 13),
                    "ticket_station_number": row_get(ticket, "ticket_station_number", 15),
                    "ticket_sa": row_get(ticket, "ticket_sa", 16),
                    "ticket_number": row_get(ticket, "ticket_number", 14),
                    "ticket_correlative": row_get(ticket, "ticket_correlative", 17),
                    "entrance_hour": row_get(ticket, "entrance_hour", 18),
                    "exit_hour": row_get(ticket, "exit_hour", 19),
                    "item_quantity": row_get(ticket, "item_quantity", 20),
                    "created_at": row_get(ticket, "added_date", 21),
                }

                old_intranet_url = settings_val(data_settings, 11)
                print(old_intranet_url)
                old_intranet_response = requests.post(
                    old_intranet_url, json=data_old, headers=headers
                )
                old_intranet_response_data = json.loads(old_intranet_response.text)
                print(old_intranet_response.text)
                print(old_intranet_response_data)

                if old_intranet_response_data.get("message") == 1:
                    print("Updated status folio.")
                    db.update("stored_tickets", "intranet_status_id", 2, "folio", folio)

print("Fin.")
