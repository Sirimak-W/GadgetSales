# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## What this repo is

A **Power BI Project (PBIP)** named `GadgetSales`, hand-generated from scratch (not saved from Power BI Desktop). It is a text-based Power BI report + semantic model, not a conventional application. There is no compiler, package manager, or test runner. The "build artifact" is the `.pbip` opened in Power BI Desktop.

`_generate_pbip.py` is the **source of truth** for the entire project. Every TMDL and PBIR file is emitted by this script. Prefer editing the script and regenerating over editing generated files by hand (TMDL is tab-indented and whitespace-sensitive; hand edits break easily). When you must hand-edit a generated file to fix something, **mirror the same fix back into `_generate_pbip.py`** or the next regenerate silently reverts it.

## Commands

```bash
# Regenerate the whole project (semantic model + report). The script self-validates
# that every emitted JSON parses and prints "All JSON valid!" on success.
python _generate_pbip.py
```

**Use `python`, not `python3`** — on this Windows machine `python3` is not on PATH (it lives at `…/Programs/Python/Python312/python`). The validation `find … -exec python3` snippet some docs show will silently no-op here.

To view/edit visually: open `GadgetSales.pbip` in **Power BI Desktop**. Desktop processes the inline data and calculated tables on open.

**Critical workflow rules:**
- Power BI Desktop must be **CLOSED** before regenerating or editing files on disk, then reopened. Desktop holds locks and will overwrite on-disk changes otherwise.
- The project lives under **OneDrive** — let sync settle after edits before reopening Desktop, or Desktop may read a stale copy.
- Desktop validates **one issue at a time** on open: it reports the first blocking error, you fix it, reopen, it reports the next. Expect to iterate.

## Architecture (two layers)

PBIP splits into two sibling folders. Names referenced across layers are **case-sensitive and must match exactly**.

1. **`GadgetSales.SemanticModel/`** — the data model, in TMDL (`definition/tables/*.tmdl`, `relationships.tmdl`, `model.tmdl`, `database.tmdl`). Entry point is `definition.pbism` (JSON), NOT a `.tmdl`.
   - `Sales.tmdl` — fact table. Data is **inline** (Power Query `Table.FromRows`), no external source. 24 rows = 4 products × 3 months × 2 years. The data is defined in the `PRODUCTS` list in `_generate_pbip.py`.
   - `DimDate.tmdl` — contiguous **calculated** date table (`ADDCOLUMNS(CALENDAR(2025-01-01, 2026-12-31), …)`) required for time-intelligence (`SAMEPERIODLASTYEAR`). Columns: `Date`, `Year`, `MonthNo` (hidden), `MonthName` (sorted by `MonthNo`), `YearMonth`.
   - `_Measures.tmdl` — all DAX measures live here (Total Sales/Units, their PY versions, YoY %, and KPI color measures). The table itself is a placeholder calculated table (`{BLANK()}`) with a hidden `Value` column.
   - Relationship: `Sales[Date]` → `DimDate[Date]` (in `relationships.tmdl`).

2. **`GadgetSales.Report/`** — the report/visuals, in PBIR JSON under `definition/`. Entry point is `definition.pbir`, which links to the semantic model `byPath`. One page (`pages/pg01Overview/`) with seven visuals under `visuals/<name>/visual.json` (two KPI `cardVisual`s, column/clustered-column/bar charts, a `tableEx`, and a donut). Each `visual.json` `name` must match its folder name; the page must be listed in `pages/pages.json` `pageOrder`.

**Cross-layer binding:** visuals reference model objects by `Entity` (table) + `Property` (measure/column). A measure or column renamed in the model must be renamed in every `visual.json` that uses it, or the visual breaks silently.

## TMDL authoring rules (each of these blocks Desktop from opening if violated)

These are non-obvious and were learned by debugging open failures. The generator now encodes all of them.

- **`ref` lines and model-level annotations sit at column 0** in `model.tmdl` — NOT indented. The model's scalar properties (`culture`, `dataAccessOptions`, …) ARE tab-indented at level 2, but `ref table X`, `ref cultureInfo`, and `annotation …` are flush-left as direct children of the implicit root. Indenting a `ref` line one tab triggers `InvalidLineType — Unexpected line type: ReferenceObject`.
- **Every column needs a `sourceColumn`** or open fails with "Column 'X' … is missing the SourceColumn property." For import (M) tables use the bare query column name (`sourceColumn: Date`); for **calculated** tables (DimDate, `_Measures`) use bracket notation referencing the DAX result column (`sourceColumn: [Date]`, `sourceColumn: [Value]`).
- **Keep Auto date/time OFF** via the model annotation `annotation __PBI_TimeIntelligenceEnabled = 0`. If it's on, Desktop spawns hidden `LocalDateTable_<guid>` / `DateTableTemplate_<guid>` tables, **persists them as `.tmdl` files in `tables/`** plus a `.pbi/cache.abf`, and they fail variation validation. **TMDL auto-loads any `.tmdl` file in `tables/` even if `model.tmdl` doesn't `ref` it** — so if these orphans ever appear, delete the `LocalDateTable_*`/`DateTableTemplate_*` files and `.pbi/cache.abf`. Time intelligence here is served by the explicit `DimDate` table, so auto date/time is redundant.
- TMDL files are **tab-indented**; do not let an editor convert tabs to spaces.

## Theming

A custom **AIA corporate-identity** theme (AIA Red `#D31145` on white, dark text, gold accent) lives at `GadgetSales.Report/StaticResources/RegisteredResources/AIA.json`. Applying a PBIR custom theme requires **three** things in sync (all emitted by the generator):
1. the theme file under `StaticResources/RegisteredResources/`;
2. a `themeCollection.customTheme` entry in `report.json` with `name`, `reportVersionAtImport`, and `type: RegisteredResources` (the `reportVersionAtImport` field is **required** on every theme entry);
3. a matching `resourcePackages` entry (`type: RegisteredResources`, item `type: CustomTheme`, `path: AIA.json`) — *"every resource file must have a corresponding entry in report.json."*

Registered resources only load **after a Desktop restart**. To test a theme file quickly without the plumbing: Desktop → View → Themes → Browse for themes → pick the JSON.

## The domain data

Gadget sales for two comparable quarters — **2025-01..03 vs 2026-01..03** — so the report is built around actual-vs-prior-year (YoY) variance. Products: Phone, Earbuds, Watch, Charger. To change products, prices, or units, edit the `PRODUCTS` list (and `MONTHS`) in `_generate_pbip.py` and rerun; `DimDate`'s `CALENDAR` range must stay wide enough to cover all `Sales` dates plus a full prior year.

## Conventions

- **IBCS colors only** in KPI color measures: green `#44C088`, red `#ED7373`. Do not introduce `#00B050`/`#FF0000`. (These measure-driven colors are independent of the AIA report theme.)
- **Page/visual naming:** `pg##Name` and `v##Name` (e.g. `pg01Overview`, `v01KpiTotalSales`); names max 50 chars.
- Building/adding report visuals is governed by the **`pbir-report-builder`** skill, and KPI cards by **`pbi-kpicard-builder`** — consult them (and their `references/`) for visual.json patterns, query roles, and schema versions before adding visuals.

## Known caveats (this project was not Desktop-generated)

- Schema versions and theme are best-effort: `visualContainer 2.9.0`, `report 1.3.0`, base theme `CY24SU10`. A newer Desktop may upgrade/rewrite them on first open.
- `.platform` and `definition.pbism` boilerplate may be normalized by Desktop.
- If Desktop reports an error on a specific file at open, that file's schema/structure is the thing to fix. Blocking errors name the offending file; "could not be resolved" warnings (with a Continue button) are usually report-side schema nits, not model errors.
