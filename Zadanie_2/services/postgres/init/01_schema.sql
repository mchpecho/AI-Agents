-- Minimal schema per assignment
CREATE TABLE IF NOT EXISTS machines (
  machine_id TEXT PRIMARY KEY,
  model TEXT
);

CREATE TABLE IF NOT EXISTS telemetry (
  ts TIMESTAMPTZ NOT NULL,
  machine_id TEXT NOT NULL,
  tag TEXT NOT NULL,
  value DOUBLE PRECISION,
  unit TEXT,
  PRIMARY KEY (ts, machine_id, tag),
  FOREIGN KEY (machine_id) REFERENCES machines(machine_id)
);

CREATE TABLE IF NOT EXISTS alarms (
  ts TIMESTAMPTZ NOT NULL,
  machine_id TEXT NOT NULL,
  alarm_code TEXT NOT NULL,
  severity TEXT NOT NULL,
  message TEXT NOT NULL,
  state TEXT NOT NULL, -- ACTIVE/CLEARED
  PRIMARY KEY (ts, machine_id, alarm_code, state),
  FOREIGN KEY (machine_id) REFERENCES machines(machine_id)
);

CREATE INDEX IF NOT EXISTS idx_telemetry_machine_ts ON telemetry(machine_id, ts DESC);
CREATE INDEX IF NOT EXISTS idx_alarms_machine_ts ON alarms(machine_id, ts DESC);
