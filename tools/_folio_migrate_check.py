#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Pre-check before moving 395k folios DB1 -> DB2."""
from dotenv import load_dotenv
import os
import pymysql

load_dotenv()

TOTAL = 395_000
PER = [TOTAL // 3 + (1 if i < TOTAL % 3 else 0) for i in range(3)]  # 131667, 131667, 131666


def connect_db1():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3309")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME", "jisparking"),
        connect_timeout=30,
        autocommit=False,
    )


def connect_db2():
    return pymysql.connect(
        host=os.getenv("DB2_HOST"),
        port=int(os.getenv("DB2_PORT", "3307")),
        user=os.getenv("DB2_USER"),
        password=os.getenv("DB2_PASSWORD"),
        database=os.getenv("DB2_NAME", "jisparking"),
        connect_timeout=30,
        autocommit=False,
    )


def main():
    print("Split per segment:", PER, "sum=", sum(PER))
    c1 = connect_db1()
    cur1 = c1.cursor()
    cur1.execute(
        "SELECT COUNT(*), MIN(folio), MAX(folio) FROM folios "
        "WHERE used_id = 0 AND document_type_id = 39"
    )
    print("DB1 unused 39:", cur1.fetchone())

    cur1.execute(
        "SELECT folio FROM folios WHERE used_id = 0 AND document_type_id = 39 "
        "ORDER BY folio ASC LIMIT %s",
        (TOTAL,),
    )
    folios = [int(r[0]) for r in cur1.fetchall()]
    print("Selected:", len(folios), "min=", folios[0], "max=", folios[-1])

    c2 = connect_db2()
    cur2 = c2.cursor()
    cur2.execute(
        "SELECT COUNT(*), MIN(CAST(folio AS UNSIGNED)), MAX(CAST(folio AS UNSIGNED)) FROM folios"
    )
    print("DB2 all:", cur2.fetchone())

    # overlap with selected set via temp approach: check min/max window
    mn, mx = folios[0], folios[-1]
    cur2.execute(
        "SELECT COUNT(*) FROM folios WHERE CAST(folio AS UNSIGNED) BETWEEN %s AND %s",
        (mn, mx),
    )
    print("DB2 rows in selected range window:", cur2.fetchone()[0])

    # precise overlap sample using IN batches
    overlap = 0
    batch = 5000
    for i in range(0, len(folios), batch):
        chunk = folios[i : i + batch]
        placeholders = ",".join(["%s"] * len(chunk))
        cur2.execute(
            f"SELECT COUNT(*) FROM folios WHERE CAST(folio AS UNSIGNED) IN ({placeholders})",
            chunk,
        )
        overlap += cur2.fetchone()[0]
        if i % 50000 == 0:
            print(f"  overlap scan {i}/{len(folios)} -> {overlap}")
    print("Exact overlap with DB2:", overlap)

    # free stock by segment
    cur2.execute(
        "SELECT folio_segment_id, requested_status_id, COUNT(*) "
        "FROM folios GROUP BY folio_segment_id, requested_status_id "
        "ORDER BY 1, 2"
    )
    print("DB2 stock:")
    for r in cur2.fetchall():
        print(" ", r)

    c1.close()
    c2.close()


if __name__ == "__main__":
    main()
