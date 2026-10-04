---
description: Run the acceptance gate for a phase and report pass/fail with evidence
argument-hint: <phase, e.g. P4>
---
Run the gate for phase $ARGUMENTS as defined in the "Phased build plan" table in `docs/LLD.md` and in `config/gates.yaml`.

- Bring the stack up if needed (`make up`), run the required commands (tests, `make seed`, `make eval`, `make gate`), and capture key numbers.
- Report each gate item as PASS or FAIL with its measured value and threshold.
- For any FAIL, list the failing questions or tests and your diagnosis from the stage traces. Do not change code in this command; propose fixes instead.
