import argparse
import csv
import math
import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path


@dataclass
class AlarmWindow:
    code: str
    severity: str
    message: str
    active_from: datetime
    active_to: datetime


def _iso(ts: datetime) -> str:
    return ts.replace(microsecond=0).isoformat().replace("+00:00", "+00:00")


def build_alarm_windows(now_utc: datetime) -> list[AlarmWindow]:
    e204_start = now_utc - timedelta(hours=6)
    e221_start = now_utc - timedelta(hours=3)
    e301_start = now_utc - timedelta(hours=1, minutes=30)

    return [
        AlarmWindow(
            code="E204",
            severity="CRIT",
            message="Wire break detected on line section A.",
            active_from=e204_start,
            active_to=e204_start + timedelta(minutes=5),
        ),
        AlarmWindow(
            code="E221",
            severity="WARN",
            message="Slip detected on spool drive.",
            active_from=e221_start,
            active_to=e221_start + timedelta(minutes=7),
        ),
        AlarmWindow(
            code="E301",
            severity="CRIT",
            message="Gearbox temperature above threshold.",
            active_from=e301_start,
            active_to=e301_start + timedelta(minutes=4),
        ),
    ]


def is_active(ts: datetime, window: AlarmWindow) -> bool:
    return window.active_from <= ts <= window.active_to


def make_telemetry_row(ts: datetime, machine_id: str, i: int, windows: list[AlarmWindow], rng: random.Random) -> list[tuple[str, float, str]]:
    day_phase = 2.0 * math.pi * ((i % 8640) / 8640.0)

    line_speed = 180.0 + 15.0 * math.sin(day_phase) + rng.uniform(-2.0, 2.0)
    tension = 42.0 + 4.0 * math.sin(day_phase + 0.5) + rng.uniform(-0.6, 0.6)
    spool_rpm = 1220.0 + 45.0 * math.sin(day_phase + 1.1) + rng.uniform(-8.0, 8.0)
    spool_diameter = max(80.0, 540.0 - (i * 0.02) + rng.uniform(-0.5, 0.5))
    motor_current = 38.0 + 3.0 * math.sin(day_phase + 0.9) + rng.uniform(-0.8, 0.8)
    vibration = 1.7 + 0.25 * math.sin(day_phase + 2.4) + rng.uniform(-0.08, 0.08)
    temp_gearbox = 63.0 + 2.5 * math.sin(day_phase + 0.2) + rng.uniform(-0.4, 0.4)
    temp_motor = 58.0 + 2.1 * math.sin(day_phase + 0.7) + rng.uniform(-0.4, 0.4)
    machine_state = 1.0
    wire_break = 0.0
    slip_detected = 0.0

    for w in windows:
        if is_active(ts, w):
            if w.code == "E204":
                wire_break = 1.0
                line_speed = max(0.0, line_speed - 120.0)
                tension = max(0.0, tension - 20.0)
                vibration += 1.0
            elif w.code == "E221":
                slip_detected = 1.0
                spool_rpm += 130.0
                tension = max(0.0, tension - 10.0)
                vibration += 0.7
            elif w.code == "E301":
                temp_gearbox += 14.0
                temp_motor += 6.0
                motor_current += 4.0

    tags = [
        ("LineSpeed_mpm", round(line_speed, 3), "m/min"),
        ("Tension_N", round(tension, 3), "N"),
        ("SpoolRPM", round(spool_rpm, 3), "rpm"),
        ("SpoolDiameter_mm", round(spool_diameter, 3), "mm"),
        ("MainMotorCurrent_A", round(motor_current, 3), "A"),
        ("Vibration_mm_s", round(vibration, 3), "mm/s"),
        ("TempGearbox_C", round(temp_gearbox, 3), "C"),
        ("TempMotor_C", round(temp_motor, 3), "C"),
        ("MachineState", machine_state, "state"),
        ("WireBreak", wire_break, "flag"),
        ("SlipDetected", slip_detected, "flag"),
    ]

    return tags


def generate_csv(output_dir: Path, machine_id: str, hours: int, step_seconds: int, seed: int) -> tuple[Path, Path, int, int]:
    output_dir.mkdir(parents=True, exist_ok=True)
    telemetry_path = output_dir / "telemetry.csv"
    alarms_path = output_dir / "alarms.csv"

    now_utc = datetime.now(timezone.utc)
    start_utc = now_utc - timedelta(hours=hours)
    windows = build_alarm_windows(now_utc)

    rng = random.Random(seed)

    telemetry_count = 0
    with telemetry_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ts", "machine_id", "tag", "value", "unit"])

        i = 0
        ts = start_utc
        while ts <= now_utc:
            for tag, value, unit in make_telemetry_row(ts, machine_id, i, windows, rng):
                writer.writerow([_iso(ts), machine_id, tag, value, unit])
                telemetry_count += 1
            i += 1
            ts += timedelta(seconds=step_seconds)

    alarm_count = 0
    with alarms_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ts", "machine_id", "alarm_code", "severity", "message", "state"])

        for w in windows:
            writer.writerow([_iso(w.active_from), machine_id, w.code, w.severity, w.message, "ACTIVE"])
            writer.writerow([_iso(w.active_to), machine_id, w.code, w.severity, w.message, "CLEARED"])
            alarm_count += 2

    return telemetry_path, alarms_path, telemetry_count, alarm_count


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate demo telemetry and alarms CSV files for LNK-01.")
    parser.add_argument("--output-dir", default=".", help="Directory where telemetry.csv and alarms.csv will be created.")
    parser.add_argument("--machine-id", default="LNK-01", help="Machine ID to generate data for.")
    parser.add_argument("--hours", type=int, default=24, help="Time range in hours.")
    parser.add_argument("--step-seconds", type=int, default=10, help="Telemetry sampling step in seconds.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for deterministic output.")
    args = parser.parse_args()

    telemetry_path, alarms_path, telemetry_count, alarm_count = generate_csv(
        output_dir=Path(args.output_dir),
        machine_id=args.machine_id,
        hours=args.hours,
        step_seconds=args.step_seconds,
        seed=args.seed,
    )

    print(f"[OK] telemetry: {telemetry_path} rows={telemetry_count}")
    print(f"[OK] alarms:    {alarms_path} rows={alarm_count}")


if __name__ == "__main__":
    main()
