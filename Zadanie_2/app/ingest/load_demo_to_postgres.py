import argparse
import csv
import os
from pathlib import Path

import psycopg2


def pg_dsn() -> dict:
    return {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": int(os.getenv("POSTGRES_PORT", "5432")),
        "dbname": os.getenv("POSTGRES_DB", "lankovacka"),
        "user": os.getenv("POSTGRES_USER", "langflow"),
        "password": os.getenv("POSTGRES_PASSWORD", "langflow"),
    }


def load_csv(conn, telemetry_csv: Path, alarms_csv: Path, machine_id: str) -> tuple[int, int]:
    telemetry_rows = 0
    alarms_rows = 0

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO machines(machine_id, model)
            VALUES (%s, %s)
            ON CONFLICT (machine_id) DO NOTHING;
            """,
            (machine_id, "Lankovacka-MVP"),
        )

        cur.execute("DELETE FROM telemetry WHERE machine_id = %s;", (machine_id,))
        cur.execute("DELETE FROM alarms WHERE machine_id = %s;", (machine_id,))

        with telemetry_csv.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            telemetry_batch = []
            for row in reader:
                telemetry_batch.append(
                    (
                        row["ts"],
                        row["machine_id"],
                        row["tag"],
                        float(row["value"]),
                        row["unit"],
                    )
                )
                if len(telemetry_batch) >= 5000:
                    cur.executemany(
                        """
                        INSERT INTO telemetry(ts, machine_id, tag, value, unit)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (ts, machine_id, tag) DO UPDATE
                        SET value = EXCLUDED.value,
                            unit = EXCLUDED.unit;
                        """,
                        telemetry_batch,
                    )
                    telemetry_rows += len(telemetry_batch)
                    telemetry_batch.clear()

            if telemetry_batch:
                cur.executemany(
                    """
                    INSERT INTO telemetry(ts, machine_id, tag, value, unit)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (ts, machine_id, tag) DO UPDATE
                    SET value = EXCLUDED.value,
                        unit = EXCLUDED.unit;
                    """,
                    telemetry_batch,
                )
                telemetry_rows += len(telemetry_batch)

        with alarms_csv.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            alarms_batch = [
                (
                    row["ts"],
                    row["machine_id"],
                    row["alarm_code"],
                    row["severity"],
                    row["message"],
                    row["state"],
                )
                for row in reader
            ]

            if alarms_batch:
                cur.executemany(
                    """
                    INSERT INTO alarms(ts, machine_id, alarm_code, severity, message, state)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (ts, machine_id, alarm_code, state) DO UPDATE
                    SET severity = EXCLUDED.severity,
                        message = EXCLUDED.message;
                    """,
                    alarms_batch,
                )
                alarms_rows = len(alarms_batch)

    conn.commit()
    return telemetry_rows, alarms_rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Load generated demo CSV files into PostgreSQL.")
    parser.add_argument("--telemetry", default="./demo_data/telemetry.csv")
    parser.add_argument("--alarms", default="./demo_data/alarms.csv")
    parser.add_argument("--machine-id", default="LNK-01")
    args = parser.parse_args()

    telemetry_csv = Path(args.telemetry)
    alarms_csv = Path(args.alarms)

    if not telemetry_csv.exists() or not alarms_csv.exists():
        raise SystemExit("Missing input CSV files. Generate them first with generate_demo_data.py")

    with psycopg2.connect(**pg_dsn()) as conn:
        telemetry_rows, alarms_rows = load_csv(conn, telemetry_csv, alarms_csv, args.machine_id)

    print(f"[OK] Loaded telemetry rows: {telemetry_rows}")
    print(f"[OK] Loaded alarms rows:    {alarms_rows}")


if __name__ == "__main__":
    main()
