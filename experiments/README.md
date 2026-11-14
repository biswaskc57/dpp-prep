# Results and post hoc experiments

The evaluated demonstrator is tag v0.3.2. Nothing in src/, config/, data/ or schemas/
was changed after it. The folders below were kept outside version control at the time
and were added to this repository on 14 November 2026 with their contents unchanged,
except that the SHA-256 column of public-epd/SOURCES.md was filled in and the
public-EPD run outputs were unpacked into public-epd/results/ on the same day.
Commit dates are the date of adding, not the dates of the work.

- ../results/evaluation_2026-10-17/  Saved outputs of the evaluated runs (17-18 Oct 2026):
  result CSVs, model responses, run log, and the analysis before and after the
  correction in commit 9e7d08e (analysis_before_fix/, analysis/). The SQLite event
  diaries are not included.
- ../out_interrupted_2250/  A run started at 22:47 on 17 Oct, stopped and restarted at
  23:01. Not used in the results.
- public-epd/  Supplementary run on five public window EPDs (29-30 Oct 2026), not
  pre-registered. Source PDFs are not included; see SOURCES.md for URLs and SHA-256.
  results/run_2026-10-29/ is the reported run (also in real_results.zip, as found);
  results/run_2026-10-30/ is a second execution with identical states, with the
  overnight log. The folder's own README describes the intended procedure; the
  expected states in config/real_scenarios.yaml were drafted on 29 Oct and were not
  committed before the run.
- dmn/  DMN readiness decision tables executed on saved outputs (27-29 Oct 2026),
  pyDMNrules 1.4.5 and pySFeel 1.4.2.
- mcp/  Experimental MCP connection, built after the evaluation. Not evaluated.
