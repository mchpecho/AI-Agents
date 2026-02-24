import argparse
import os

import psycopg2


def pg_dsn() -> dict:
    return {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": int(os.getenv("POSTGRES_PORT", "5432")),
        "dbname": os.getenv("POSTGRES_DB", "lankovacka"),
        "user": os.getenv("POSTGRES_USER", "langflow"),
        "password": os.getenv("POSTGRES_PASSWORD", "langflow"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Sanity check for last 2h telemetry stats.")
    parser.add_argument("--machine-id", default="LNK-01")
    parser.add_argument("--hours", type=int, default=2)
    args = parser.parse_args()

    sql = """
    WITH base AS (
      SELECT ts, tag, value
      FROM telemetry
      WHERE machine_id = %s
        AND ts >= (now() at time zone 'utc') - (%s::text || ' hours')::interval
        AND tag IN ('LineSpeed_mpm','Tension_N','TempGearbox_C','TempMotor_C','Vibration_mm_s')
    ),
    rng AS (
      SELECT min(ts) AS ts_min, max(ts) AS ts_max, count(*) AS cnt
      FROM base
    ),
    stats AS (
      SELECT
        tag,
        min(value) AS min_v,
        avg(value) AS avg_v,
        max(value) AS max_v,
        (array_agg(value ORDER BY ts DESC))[1] AS last_v,
        (array_agg(value ORDER BY ts ASC))[1] AS first_v
      FROM base
      GROUP BY tag
    )
    SELECT
      r.ts_min,
      r.ts_max,
      r.cnt,
      s.tag,
      s.min_v,
      s.avg_v,
      s.max_v,
      CASE
        WHEN s.last_v > s.first_v + 0.01 THEN 'rastie'
        WHEN s.last_v < s.first_v - 0.01 THEN 'klesá'
        ELSE 'stabilné'
      END AS trend
    FROM rng r
    LEFT JOIN stats s ON TRUE
    ORDER BY s.tag;
    """

    with psycopg2.connect(**pg_dsn()) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (args.machine_id, args.hours))
            rows = cur.fetchall()

    if not rows:
        print("[WARN] No rows returned.")
        return

    ts_min, ts_max, cnt = rows[0][0], rows[0][1], rows[0][2]
    if cnt == 0 or ts_min is None or ts_max is None:
        print(f"[WARN] Nedostatok dát pre machine_id={args.machine_id} za posledných {args.hours}h.")
        return

    print("=== Sanity Check: Telemetry Last 2h ===")
    print(f"machine_id: {args.machine_id}")
    print(f"range_utc:  {ts_min} .. {ts_max}")
    print(f"rows:       {cnt}")
    print()

    for _, _, _, tag, min_v, avg_v, max_v, trend in rows:
        if tag is None:
            continue
        print(f"- {tag}: min={min_v:.3f}, avg={avg_v:.3f}, max={max_v:.3f}, trend={trend}")


if __name__ == "__main__":
    main()
