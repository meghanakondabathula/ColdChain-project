# Data dictionary

All IDs are immutable. ISO timestamps `YYYY-MM-DDTHH:MM:SS`; Celsius and minutes as named. `TEXT NOT NULL` required, otherwise optional. Primary keys unique; references are FK constraints. See `full/schema.sql` for executable checks.

## Product

| Field | SQL type and constraints | Units / values / validation |
|---|---|---|
| `product_id` | `TEXT PRIMARY KEY` | ID; immutable |
| `name` | `TEXT NOT NULL` | String / numeric; see business rules |
| `category` | `TEXT NOT NULL` | String / numeric; see business rules |
| `active_from` | `TEXT NOT NULL` | ISO timestamp; ordered by lifecycle |
| `state` | `TEXT NOT NULL` | Enumerated: see README |

## Packaging

| Field | SQL type and constraints | Units / values / validation |
|---|---|---|
| `packaging_id` | `TEXT PRIMARY KEY` | ID; immutable |
| `name` | `TEXT NOT NULL` | String / numeric; see business rules |
| `hold_hours` | `INTEGER NOT NULL CHECK(hold_hours>0)` | hours |
| `state` | `TEXT NOT NULL` | Enumerated: see README |

## ThresholdPolicy

| Field | SQL type and constraints | Units / values / validation |
|---|---|---|
| `policy_id` | `TEXT PRIMARY KEY` | ID; immutable |
| `product_id` | `TEXT NOT NULL REFERENCES Product(product_id)` | ID; immutable |
| `min_c` | `REAL NOT NULL` | °C |
| `max_c` | `REAL NOT NULL` | °C |
| `allowed_excursion_min` | `INTEGER NOT NULL` | minutes |
| `max_gap_min` | `INTEGER NOT NULL` | minutes |
| `max_custody_gap_min` | `INTEGER NOT NULL` | minutes |
| `effective_from` | `TEXT NOT NULL` | ISO timestamp; ordered by lifecycle |
| `effective_to` | `TEXT` | ISO timestamp; ordered by lifecycle |
| `state` | `TEXT NOT NULL` | Enumerated: see README |

## Lot

| Field | SQL type and constraints | Units / values / validation |
|---|---|---|
| `lot_id` | `TEXT PRIMARY KEY` | ID; immutable |
| `product_id` | `TEXT NOT NULL REFERENCES Product(product_id)` | ID; immutable |
| `manufactured_at` | `TEXT NOT NULL` | ISO timestamp; ordered by lifecycle |
| `expires_at` | `TEXT NOT NULL` | ISO timestamp; ordered by lifecycle |
| `state` | `TEXT NOT NULL` | Enumerated: see README |

## Logger

| Field | SQL type and constraints | Units / values / validation |
|---|---|---|
| `logger_id` | `TEXT PRIMARY KEY` | ID; immutable |
| `serial` | `TEXT NOT NULL UNIQUE` | String / numeric; see business rules |
| `calibrated_at` | `TEXT NOT NULL` | ISO timestamp; ordered by lifecycle |
| `calibration_due_at` | `TEXT NOT NULL` | ISO timestamp; ordered by lifecycle |
| `uncertainty_c` | `REAL NOT NULL` | °C |
| `state` | `TEXT NOT NULL` | Enumerated: see README |

## Shipment

| Field | SQL type and constraints | Units / values / validation |
|---|---|---|
| `shipment_id` | `TEXT PRIMARY KEY` | ID; immutable |
| `lot_id` | `TEXT NOT NULL REFERENCES Lot(lot_id)` | ID; immutable |
| `packaging_id` | `TEXT NOT NULL REFERENCES Packaging(packaging_id)` | ID; immutable |
| `policy_id` | `TEXT NOT NULL REFERENCES ThresholdPolicy(policy_id)` | ID; immutable |
| `planned_departure` | `TEXT NOT NULL` | ISO timestamp; ordered by lifecycle |
| `planned_arrival` | `TEXT NOT NULL` | ISO timestamp; ordered by lifecycle |
| `route` | `TEXT NOT NULL` | String / numeric; see business rules |
| `state` | `TEXT NOT NULL` | Enumerated: see README |

## ShipmentLogger

| Field | SQL type and constraints | Units / values / validation |
|---|---|---|
| `assignment_id` | `TEXT PRIMARY KEY` | ID; immutable |
| `shipment_id` | `TEXT NOT NULL REFERENCES Shipment(shipment_id)` | ID; immutable |
| `logger_id` | `TEXT NOT NULL REFERENCES Logger(logger_id)` | ID; immutable |
| `assigned_at` | `TEXT NOT NULL` | ISO timestamp; ordered by lifecycle |
| `unassigned_at` | `TEXT NOT NULL` | ISO timestamp; ordered by lifecycle |
| `state` | `TEXT NOT NULL` | Enumerated: see README |

## RouteStop

| Field | SQL type and constraints | Units / values / validation |
|---|---|---|
| `stop_id` | `TEXT PRIMARY KEY` | ID; immutable |
| `shipment_id` | `TEXT NOT NULL REFERENCES Shipment(shipment_id)` | ID; immutable |
| `sequence_no` | `INTEGER NOT NULL` | String / numeric; see business rules |
| `location` | `TEXT NOT NULL` | String / numeric; see business rules |
| `arrived_at` | `TEXT NOT NULL` | ISO timestamp; ordered by lifecycle |
| `departed_at` | `TEXT NOT NULL` | ISO timestamp; ordered by lifecycle |
| `dwell_min` | `INTEGER NOT NULL` | minutes |

## CustodyEvent

| Field | SQL type and constraints | Units / values / validation |
|---|---|---|
| `custody_id` | `TEXT PRIMARY KEY` | ID; immutable |
| `shipment_id` | `TEXT NOT NULL REFERENCES Shipment(shipment_id)` | ID; immutable |
| `event_at` | `TEXT NOT NULL` | ISO timestamp; ordered by lifecycle |
| `actor` | `TEXT NOT NULL` | Enumerated: see README |
| `event_type` | `TEXT NOT NULL` | Enumerated: see README |
| `location` | `TEXT NOT NULL` | String / numeric; see business rules |

## TemperatureReading

| Field | SQL type and constraints | Units / values / validation |
|---|---|---|
| `reading_id` | `TEXT PRIMARY KEY` | ID; immutable |
| `shipment_id` | `TEXT NOT NULL REFERENCES Shipment(shipment_id)` | ID; immutable |
| `logger_id` | `TEXT NOT NULL REFERENCES Logger(logger_id)` | ID; immutable |
| `recorded_at` | `TEXT NOT NULL` | ISO timestamp; ordered by lifecycle |
| `temperature_c` | `REAL NOT NULL` | °C |
| `quality` | `TEXT NOT NULL` | Enumerated: see README |

## ExcursionReport

| Field | SQL type and constraints | Units / values / validation |
|---|---|---|
| `report_id` | `TEXT PRIMARY KEY` | ID; immutable |
| `shipment_id` | `TEXT NOT NULL UNIQUE REFERENCES Shipment(shipment_id)` | ID; immutable |
| `policy_id` | `TEXT NOT NULL REFERENCES ThresholdPolicy(policy_id)` | ID; immutable |
| `decision` | `TEXT NOT NULL` | Enumerated: see README |
| `issue_types` | `TEXT NOT NULL` | String / numeric; see business rules |
| `excursion_minutes` | `INTEGER NOT NULL` | minutes |
| `missing_intervals` | `INTEGER NOT NULL` | String / numeric; see business rules |
| `evidence_json` | `TEXT NOT NULL` | String / numeric; see business rules |
| `generated_at` | `TEXT NOT NULL` | ISO timestamp; ordered by lifecycle |

## StateEvent

| Field | SQL type and constraints | Units / values / validation |
|---|---|---|
| `state_event_id` | `TEXT PRIMARY KEY` | ID; immutable |
| `entity_type` | `TEXT NOT NULL` | String / numeric; see business rules |
| `entity_id` | `TEXT NOT NULL` | ID; immutable |
| `event_at` | `TEXT NOT NULL` | ISO timestamp; ordered by lifecycle |
| `from_state` | `TEXT` | String / numeric; see business rules |
| `to_state` | `TEXT NOT NULL` | String / numeric; see business rules |
| `reason` | `TEXT NOT NULL` | String / numeric; see business rules |

