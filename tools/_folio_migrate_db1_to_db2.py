#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Mueve 395.000 folios tipo 39 (used_id=0) de DB1 a DB2 (segmentos 1, 2, 3)
y los elimina de DB1 para evitar choque SII.
"""
from dotenv import load_dotenv
import os
import sys
from datetime import datetime
import pymysql

load_dotenv()

TOTAL = 395_000
BATCH = 2000
DRY_RUN = "--dry-run" in sys.argv
PER = [TOTAL // 3 + (1 if i < TOTAL % 3 else 0) for i in range(3)]  # 131667, 131667, 131666
NOW = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def connect_db1():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3309")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME", "jisparking"),
        connect_timeout=60,
        autocommit=False,
        charset="utf8mb4",
    )


def connect_db2():
    return pymysql.connect(
        host=os.getenv("DB2_HOST"),
        port=int(os.getenv("DB2_PORT", "3307")),
        user=os.getenv("DB2_USER"),
        password=os.getenv("DB2_PASSWORD"),
        database=os.getenv("DB2_NAME", "jisparking"),
        connect_timeout=60,
        autocommit=False,
        charset="utf8mb4",
    )


def main():
    print("=" * 60)
    print(f"MODE: {'DRY-RUN' if DRY_RUN else 'LIVE'}")
    print(f"Total={TOTAL} split={PER} sum={sum(PER)}")
    print("=" * 60)

    c1 = connect_db1()
    c2 = connect_db2()
    cur1 = c1.cursor()
    cur2 = c2.cursor()

    cur1.execute(
        "SELECT COUNT(*) FROM folios WHERE used_id = 0 AND document_type_id = 39"
    )
    available = cur1.fetchone()[0]
    print(f"DB1 unused 39 available: {available}")
    if available < TOTAL:
        raise SystemExit(f"No hay suficientes folios en DB1 ({available} < {TOTAL})")

    print("Selecting folios from DB1 (ASC)...")
    cur1.execute(
        "SELECT folio FROM folios WHERE used_id = 0 AND document_type_id = 39 "
        "ORDER BY folio ASC LIMIT %s",
        (TOTAL,),
    )
    folios = [int(r[0]) for r in cur1.fetchall()]
    if len(folios) != TOTAL:
        raise SystemExit(f"Se esperaban {TOTAL}, se obtuvieron {len(folios)}")
    print(f"Selected min={folios[0]} max={folios[-1]}")

    # Split into segments
    chunks = {}
    offset = 0
    for seg_idx, qty in enumerate(PER, start=1):
        chunks[seg_idx] = folios[offset : offset + qty]
        offset += qty
        print(f"  seg {seg_idx}: {len(chunks[seg_idx])} "
              f"({chunks[seg_idx][0]} .. {chunks[seg_idx][-1]})")

    if DRY_RUN:
        print("DRY-RUN: no inserts/deletes. OK.")
        c1.close()
        c2.close()
        return

    inserted_total = 0
    insert_sql = (
        "INSERT IGNORE INTO folios ("
        "folio, branch_office_id, cashier_id, folio_segment_id, "
        "requested_status_id, used_status_id, billed_status_id, "
        "added_date, updated_date"
        ") VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
    )

    for seg_id, seg_folios in chunks.items():
        print(f"Inserting segment {seg_id} ({len(seg_folios)}) into DB2...")
        for i in range(0, len(seg_folios), BATCH):
            batch = seg_folios[i : i + BATCH]
            rows = [
                (str(f), "0", "0", str(seg_id), "0", "0", "0", NOW, NOW)
                for f in batch
            ]
            cur2.executemany(insert_sql, rows)
            inserted_total += cur2.rowcount if cur2.rowcount and cur2.rowcount > 0 else 0
            if (i // BATCH) % 25 == 0:
                c2.commit()
                print(f"  seg{seg_id} progress {i + len(batch)}/{len(seg_folios)} "
                      f"(rowcount acum ~{inserted_total})")
        c2.commit()
        print(f"  seg {seg_id} done")

    print(f"DB2 insert rowcount (IGNORE may undercount duplicates): {inserted_total}")

    # Verify how many of selected are now in DB2
    print("Verifying presence in DB2...")
    present = 0
    for i in range(0, len(folios), BATCH):
        chunk = folios[i : i + BATCH]
        ph = ",".join(["%s"] * len(chunk))
        cur2.execute(
            f"SELECT COUNT(*) FROM folios WHERE CAST(folio AS UNSIGNED) IN ({ph})",
            chunk,
        )
        present += cur2.fetchone()[0]
    print(f"Selected folios present in DB2: {present}/{TOTAL}")
    if present < TOTAL:
        raise SystemExit(
            f"ABORT delete: solo {present}/{TOTAL} en DB2. "
            "Revisa e intenta de nuevo. DB1 intacta."
        )

    print("Deleting from DB1...")
    deleted = 0
    for i in range(0, len(folios), BATCH):
        chunk = folios[i : i + BATCH]
        ph = ",".join(["%s"] * len(chunk))
        cur1.execute(
            f"DELETE FROM folios WHERE document_type_id = 39 AND used_id = 0 "
            f"AND folio IN ({ph})",
            chunk,
        )
        deleted += cur1.rowcount
        if (i // BATCH) % 25 == 0:
            c1.commit()
            print(f"  delete progress {i + len(chunk)}/{TOTAL} deleted={deleted}")
    c1.commit()
    print(f"Deleted from DB1: {deleted}")

    # Final counts
    cur1.execute(
        "SELECT COUNT(*) FROM folios WHERE used_id = 0 AND document_type_id = 39"
    )
    db1_left = cur1.fetchone()[0]
    cur2.execute(
        "SELECT folio_segment_id, requested_status_id, COUNT(*) "
        "FROM folios GROUP BY folio_segment_id, requested_status_id ORDER BY 1, 2"
    )
    print("DB1 unused 39 remaining:", db1_left)
    print("DB2 stock after:")
    for r in cur2.fetchall():
        print(" ", r)

    c1.close()
    c2.close()
    print("DONE")


if __name__ == "__main__":
    main()
