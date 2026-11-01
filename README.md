# Cold-chain shipment compliance: synthetic evidence project

Python 3.10+ standard library only. All data is fabricated; no third-party data or personal information.

## Commands

```bash
python coldchain.py generate --out starter --shipments 20 --loggers 5
python coldchain.py generate --out full --shipments 5000 --loggers 1000 --seed 20261022
python coldchain.py generate --out full_again --shipments 5000 --loggers 1000 --seed 20261022
python coldchain.py verify full full_again
```

Each run creates SQLite, 12 CSV entity tables, `ground_truth.csv`, `ground_truth.json`, `seed.sql`, `source_manifest.json` and `validation_summary.json`. CSVs are independent of ground truth. To inspect the database, use SQLite Browser or Python sqlite3.

## Relational design

Product 1:N Lot, Product 1:N ThresholdPolicy; Lot 1:N Shipment; Packaging 1:N Shipment; ThresholdPolicy 1:N Shipment; Shipment N:M Logger through ShipmentLogger (time-bounded); Shipment 1:N RouteStop, CustodyEvent, TemperatureReading and StateEvent; Logger 1:N TemperatureReading; Shipment 1:1 ExcursionReport. ShipmentLogger is optional for an intentionally invalid shipment. Policy effective_to is optional; other references are required unless explicitly described. IDs never change. Logger assignments cannot overlap in time.

All time values are ISO 8601 local synthetic times without offsets. All temperature values are Celsius, durations minutes except `hold_hours`. Primary keys are unique TEXT fields, foreign keys are enforced in SQLite, dates are chronological, and `state` values follow the lifecycle described below. The schema is executable in `coldchain.py` under `SCHEMA` and its column constraints.

## Rules

* Product policies: vaccine 2–8 °C, 20-minute excursion allowance; biologic 2–8 °C, 30 minutes; frozen therapy -25 to -15 °C, 10 minutes; ambient diagnostics 15–25 °C, 40 minutes. These are illustrative synthetic policies, **not real pharmaceutical handling guidance**.
* Readings expected at departure and every 10 minutes through arrival, inclusive. Missing intervals trigger REVIEW or FAIL if other serious problems exist.
* Excursions use the first outside-range sample to the next inside-range sample; an unresolved excursion is measured through one sampling interval after planned arrival. All duration calculations are shipment-scoped.
* Missing logger assignment, mismatched product policy, invalid calibration or excessive excursion produce FAIL. Missing readings or custody gaps alone produce REVIEW. Only fully supported shipments PASS.
* A custody gap is detected when the time between successive recorded handoffs exceeds the policy's `max_custody_gap_min`. This is a simple proxy, not a formal chain-of-custody assurance.
* Calibrated logger pool is reused only across nonoverlapping shipment windows. Synthetic readings are always linked to a physical logger, even for the deliberate unassigned-logger case.
* Shipment state events: PLANNED → IN_TRANSIT → DELIVERED. Event rows are append-only evidence of these transitions; `Shipment.state` is the current snapshot.

## Deliberate negative cases

First five shipments are reserved: unassigned logger, wrong product policy, missing data that must not silently pass, omitted custody handoff that must be detected, and an excursion intended to expose accidental cross-shipment aggregation. Ground truth is stored separately. `CROSS_SHIPMENT_DURATION` describes the prohibited implementation behavior, not an actual cross-shipment reading corruption. The compliant evaluator scopes readings by shipment.

## Validation and limitations

Generation enforces SQLite primary/foreign keys, unique readings, non-overlapping logger assignments, and replay of all report decisions from persisted readings and policies. `source_manifest.json` records counts and SHA-256 hashes for all CSV exports. Generate twice and run `verify` to compare checksums.

Limitations: this is a command-line generator and evaluator, not a deployed interactive dashboard; it does not implement authenticated deviation closure or corrective-action approvals. Policies are synthetic and not regulatory specifications. CSV/SQLite data are consistent but `seed.sql` contains INSERT statements only: apply it to a database with the schema already created. Packaging hold hours are reference metadata, not a thermal simulation. Calibration uncertainty is recorded but no measurement uncertainty propagation is performed. Full-dataset creation can take several minutes and consumes substantial disk space.
