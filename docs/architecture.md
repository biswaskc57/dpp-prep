# Architecture (v0.3)

Gray: existing tools, reused. Purple: the preparation layer built in this thesis.

```mermaid
flowchart TD
    IN[Inputs: wish list + documents + ERP record] --> RD[1 Reader<br/>Markdown and PDF with pages; Docling later]
    RD --> SG[2 Suggester, AI<br/>LangExtract adapter or stand-in]
    IN --> IM[2b Importer, no AI<br/>structured record]
    subgraph YOURS[Preparation layer built in this thesis]
      FC[3 Fact-checker<br/>quote in source, value in quote]
      RC[4 Rule checker<br/>unit, product, scope, conflict]
      RV[5 Reviewer, person<br/>review screen: value beside evidence]
      AP[6 Approver, other person<br/>only if all conditions hold]
      DY[(Diary<br/>append-only SQLite)]
    end
    SG --> FC
    IM --> FC
    FC --> RC --> RV --> AP
    AP --> EX[7 Handover<br/>schema-checked JSON; CIRPASS-2 later]
    FC -. unsupported .-> UN[Unresolved: nothing invented]
    RC -. failed .-> FL[Flagged: correct or leave]
    classDef built fill:#EEEDFE,stroke:#534AB7,color:#26215C
    classDef reused fill:#F1EFE8,stroke:#5F5E5A,color:#2C2C2A
    class FC,RC,RV,AP,DY built
    class IN,RD,SG,IM,EX reused
```

## Layers in the code

| Layer | File | Responsibility |
|---|---|---|
| Configuration | `config/*.yaml` | What is needed, and how it is checked |
| Sources | `sources.py` | Load documents and records, fingerprint them |
| Suggestion | `extract.py` | Produce candidate values with evidence |
| Evidence | `verify.py` | Find the quote in the source; record position and fingerprint |
| Rules | `checks.py` | Support, identity, unit, scope, type, composition, conflict |
| Authority | `states.py` | Who may move a record, and under which conditions |
| Workflow | `service.py` | The only entry point; calls everything in the right order |
| Diary | `audit.py` | Append-only record of every step |
| Handover | `export.py`, `schemas/` | Build and validate the package |
| Review screen | `app/review_app.py` | Streamlit; calls the service only |
| Evaluation | `scripts/evaluate.py`, `config/evaluation_scenarios.yaml` | Scenarios, repeated runs, outcome vs expectation |
