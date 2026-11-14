# 0003 Add saved results and post hoc experiments

Date: 2026-11-14. Status: accepted.

Context: the saved outputs of the evaluated runs were git-ignored, and the public-EPD
run, the DMN decision tables and the MCP connection were built after v0.3.2 in separate
folders without version control.
Decision: add them unchanged under results/ and experiments/, without third-party EPD
PDFs or vendored copies of this repository.
Consequence: the evaluated code and test documents are untouched. The thesis must not
claim that these folders were version-controlled at the time of the runs.
