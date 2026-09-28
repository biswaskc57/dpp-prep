# Traceability: framework -> requirement -> component -> test (v0.3)

| Framework element | Requirement | Component | Tests |
|---|---|---|---|
| Element profile, requirement context | R01 | `config/elements_w100.yaml`, `profile.py` | T01 |
| Response allocation: AI or not | R01 | `route` in profile, `StructuredImporter` | T01b |
| Evidence and provenance | R02, R03 | `verify.py`, `Evidence` (page, quote, position, fingerprint) | T01, T02b, T14, P02 |
| Absence is not a plausible value | R04 | `service.prepare_product` -> unresolved | T02, T02b |
| Evidence must support the value | R03 | `checks.support` | T11, audit 01 |
| Readiness gaps: identity, unit, scope | R05 | `checks.identity`, `unit`, `scope` | T04, T05 |
| Readiness gap: composition | R05 | `checks.composition_sum` | T06, audit 02 |
| Readiness gap: conflicting sources | R06 | `checks.conflict`, reviewer choice | T03 |
| Automation-bias measure | R07 | review screen: value beside highlighted quote, no pre-selection, inspection box | T07c, U01–U04 |
| Authority principle | R08 | `states.py` guards, `service.approve` | T07, T07b, rule-layer tests, audit 03 |
| Version-bound approval | R08 | `Record.version`, `Approval.record_version` | T12, T13 |
| Audit trail | R09 | `audit.py` | T02b, T14 |
| Controlled handover | R10 | `export.py`, `schemas/handover_v0.2.schema.json` | T08, T12 |
| AI output treated as untrusted | R03, R04 | `LangExtractExtractor`: anchored, non-empty spans only; raw output logged | L01–L05 |
| Real AI evaluation, repeated runs | method | `scripts/evaluate.py`, scenarios written in advance | E01 |
| Tests detect removed safeguards | method | `scripts/fault_injection.py` | 12 of 12 |
