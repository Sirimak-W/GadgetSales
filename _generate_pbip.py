#!/usr/bin/env python3
"""Generate a complete PBIP project (GadgetSales) from scratch:
semantic model (TMDL) with inline gadget sales data + report (PBIR) with visuals.
Data covers 2025-01..03 and 2026-01..03 for a few gadget products."""

import json, os, uuid

BASE = os.path.dirname(os.path.abspath(__file__))
PROJ = "GadgetSales"
REPORT = os.path.join(BASE, f"{PROJ}.Report")
MODEL = os.path.join(BASE, f"{PROJ}.SemanticModel")
RDEF = os.path.join(REPORT, "definition")
MDEF = os.path.join(MODEL, "definition")

def w(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def wj(path, obj):
    w(path, json.dumps(obj, indent=2))

# ---------------------------------------------------------------------------
# 1. DATA
# ---------------------------------------------------------------------------
PRODUCTS = [
    # name,      category,     price, 2025 units (Jan,Feb,Mar), 2026 units
    ("Phone",   "Mobile",     800, [100, 120, 110], [130, 150, 140]),
    ("Earbuds", "Audio",      120, [200, 250, 220], [280, 320, 300]),
    ("Watch",   "Wearable",   250, [80,  90,  85],  [110, 120, 115]),
    ("Charger", "Accessory",  30,  [300, 350, 320], [400, 420, 410]),
]
MONTHS = [1, 2, 3]

rows = []  # (year, month, name, category, units, price)
for name, cat, price, u25, u26 in PRODUCTS:
    for i, m in enumerate(MONTHS):
        rows.append((2025, m, name, cat, u25[i], price))
        rows.append((2026, m, name, cat, u26[i], price))

# ---------------------------------------------------------------------------
# 2. PBIP ENTRY + PLATFORM FILES
# ---------------------------------------------------------------------------
wj(os.path.join(BASE, f"{PROJ}.pbip"), {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
    "version": "1.0",
    "artifacts": [{"report": {"path": f"{PROJ}.Report"}}],
    "settings": {"enableAutoRecovery": True},
})

w(os.path.join(BASE, ".gitignore"),
  "*.pbix\n.pbi/localSettings.json\n.pbi/cache.abf\n.pbi/unappliedChanges.json\n")

def platform(kind):
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": kind, "displayName": PROJ},
        "config": {"version": "2.0", "logicalId": str(uuid.uuid4())},
    }

wj(os.path.join(REPORT, ".platform"), platform("Report"))
wj(os.path.join(MODEL, ".platform"), platform("SemanticModel"))

# ---------------------------------------------------------------------------
# 3. REPORT BOILERPLATE
# ---------------------------------------------------------------------------
wj(os.path.join(REPORT, "definition.pbir"), {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/1.0.0/schema.json",
    "version": "4.0",
    "datasetReference": {"byPath": {"path": f"../{PROJ}.SemanticModel"}},
})

wj(os.path.join(RDEF, "version.json"), {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json",
    "version": "2.0.0",
})

# AIA corporate-identity custom theme (AIA Red #D31145 on white, dark text, gold accent)
wj(os.path.join(REPORT, "StaticResources", "RegisteredResources", "AIA.json"), {
    "name": "AIA",
    "dataColors": ["#D31145", "#8E0C30", "#F2849E", "#C8A04B", "#6E2436", "#5B6770", "#ED7373", "#2B2B2B"],
    "background": "#FFFFFF",
    "secondaryBackground": "#F7F2F3",
    "foreground": "#2B2B2B",
    "tableAccent": "#D31145",
    "good": "#44C088", "neutral": "#C8A04B", "bad": "#ED7373",
    "maximum": "#8E0C30", "center": "#F2849E", "minimum": "#FBE0E6",
    "null": "#5B6770", "hyperlink": "#D31145",
    "textClasses": {
        "title": {"color": "#D31145", "fontFace": "Segoe UI Semibold"},
        "header": {"color": "#2B2B2B", "fontFace": "Segoe UI Semibold"},
        "label": {"color": "#2B2B2B", "fontFace": "Segoe UI"},
        "callout": {"color": "#D31145", "fontFace": "Segoe UI Semibold"}
    }
})

wj(os.path.join(RDEF, "report.json"), {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/1.3.0/schema.json",
    "themeCollection": {
        "baseTheme": {"name": "CY24SU10", "reportVersionAtImport": "5.55", "type": "SharedResources"},
        "customTheme": {"name": "AIA", "reportVersionAtImport": "5.55", "type": "RegisteredResources"}
    },
    "resourcePackages": [
        {"name": "RegisteredResources", "type": "RegisteredResources",
         "items": [{"name": "AIA", "path": "AIA.json", "type": "CustomTheme"}]}
    ],
    "layoutOptimization": "None",
})

# ---------------------------------------------------------------------------
# 4. SEMANTIC MODEL BOILERPLATE
# ---------------------------------------------------------------------------
wj(os.path.join(MODEL, "definition.pbism"), {
    "version": "4.2",
    "settings": {},
})

w(os.path.join(MDEF, "database.tmdl"), "database\n\tcompatibilityLevel: 1601\n")

w(os.path.join(MDEF, "model.tmdl"),
  "model Model\n"
  "\tculture: en-US\n"
  "\tdefaultPowerBIDataSourceVersion: powerBI_V3\n"
  "\tsourceQueryCulture: en-US\n"
  "\tdataAccessOptions\n"
  "\t\tlegacyRedirects\n"
  "\t\treturnErrorValuesAsNull\n"
  "\n"
  "annotation __PBI_TimeIntelligenceEnabled = 0\n"
  "\n"
  "ref table Sales\n"
  "ref table DimDate\n"
  "ref table _Measures\n")

# ---- Sales.tmdl (M partition with inline data) ----
def m_row(r):
    year, month, name, cat, units, price = r
    return f'\t\t\t\t\t{{#date({year},{month},1), \"{name}\", \"{cat}\", {units}, {price}}}'

m_rows = ",\n".join(m_row(r) for r in rows)

sales_tmdl = (
    "table Sales\n"
    f"\tlineageTag: {uuid.uuid4()}\n"
    "\n"
    "\tcolumn Date\n"
    "\t\tdataType: dateTime\n"
    "\t\tformatString: yyyy-mm-dd\n"
    f"\t\tlineageTag: {uuid.uuid4()}\n"
    "\t\tsummarizeBy: none\n"
    "\t\tsourceColumn: Date\n"
    "\n"
    "\tcolumn ProductName\n"
    "\t\tdataType: string\n"
    f"\t\tlineageTag: {uuid.uuid4()}\n"
    "\t\tsummarizeBy: none\n"
    "\t\tsourceColumn: ProductName\n"
    "\n"
    "\tcolumn Category\n"
    "\t\tdataType: string\n"
    f"\t\tlineageTag: {uuid.uuid4()}\n"
    "\t\tsummarizeBy: none\n"
    "\t\tsourceColumn: Category\n"
    "\n"
    "\tcolumn Units\n"
    "\t\tdataType: int64\n"
    "\t\tformatString: #,0\n"
    f"\t\tlineageTag: {uuid.uuid4()}\n"
    "\t\tsummarizeBy: sum\n"
    "\t\tsourceColumn: Units\n"
    "\n"
    "\tcolumn UnitPrice\n"
    "\t\tdataType: double\n"
    "\t\tformatString: \\$#,0\n"
    f"\t\tlineageTag: {uuid.uuid4()}\n"
    "\t\tsummarizeBy: none\n"
    "\t\tsourceColumn: UnitPrice\n"
    "\n"
    "\tcolumn SalesAmount\n"
    "\t\tdataType: double\n"
    "\t\tformatString: \\$#,0\n"
    f"\t\tlineageTag: {uuid.uuid4()}\n"
    "\t\tsummarizeBy: sum\n"
    "\t\tsourceColumn: SalesAmount\n"
    "\n"
    "\tpartition Sales = m\n"
    "\t\tmode: import\n"
    "\t\tsource =\n"
    "\t\t\t\tlet\n"
    "\t\t\t\t    Source = Table.FromRows({\n"
    f"{m_rows}\n"
    '\t\t\t\t    }, {"Date", "ProductName", "Category", "Units", "UnitPrice"}),\n'
    '\t\t\t\t    Typed = Table.TransformColumnTypes(Source, {{"Date", type date}, {"ProductName", type text}, {"Category", type text}, {"Units", Int64.Type}, {"UnitPrice", type number}}),\n'
    '\t\t\t\t    WithSales = Table.AddColumn(Typed, "SalesAmount", each [Units] * [UnitPrice], type number)\n'
    "\t\t\t\tin\n"
    "\t\t\t\t    WithSales\n"
    "\n"
)
w(os.path.join(MDEF, "tables", "Sales.tmdl"), sales_tmdl)

# ---- DimDate.tmdl (calculated date table) ----
dimdate_tmdl = (
    "table DimDate\n"
    f"\tlineageTag: {uuid.uuid4()}\n"
    "\n"
    "\tcolumn Date\n"
    "\t\tdataType: dateTime\n"
    "\t\tisKey\n"
    "\t\tformatString: yyyy-mm-dd\n"
    f"\t\tlineageTag: {uuid.uuid4()}\n"
    "\t\tsummarizeBy: none\n"
    "\t\tsourceColumn: [Date]\n"
    "\n"
    "\tcolumn Year\n"
    "\t\tdataType: int64\n"
    "\t\tformatString: 0\n"
    f"\t\tlineageTag: {uuid.uuid4()}\n"
    "\t\tsummarizeBy: none\n"
    "\t\tsourceColumn: [Year]\n"
    "\n"
    "\tcolumn MonthNo\n"
    "\t\tdataType: int64\n"
    "\t\tformatString: 0\n"
    f"\t\tlineageTag: {uuid.uuid4()}\n"
    "\t\tsummarizeBy: none\n"
    "\t\tisHidden\n"
    "\t\tsourceColumn: [MonthNo]\n"
    "\n"
    "\tcolumn MonthName\n"
    "\t\tdataType: string\n"
    f"\t\tlineageTag: {uuid.uuid4()}\n"
    "\t\tsummarizeBy: none\n"
    "\t\tsortByColumn: MonthNo\n"
    "\t\tsourceColumn: [MonthName]\n"
    "\n"
    "\tcolumn YearMonth\n"
    "\t\tdataType: string\n"
    f"\t\tlineageTag: {uuid.uuid4()}\n"
    "\t\tsummarizeBy: none\n"
    "\t\tsourceColumn: [YearMonth]\n"
    "\n"
    "\tpartition DimDate = calculated\n"
    "\t\tmode: import\n"
    "\t\tsource =\n"
    "\t\t\t\tADDCOLUMNS(\n"
    "\t\t\t\t    CALENDAR(DATE(2025, 1, 1), DATE(2026, 12, 31)),\n"
    '\t\t\t\t    "Year", YEAR([Date]),\n'
    '\t\t\t\t    "MonthNo", MONTH([Date]),\n'
    '\t\t\t\t    "MonthName", FORMAT([Date], "mmm"),\n'
    '\t\t\t\t    "YearMonth", FORMAT([Date], "yyyy-MM")\n'
    "\t\t\t\t)\n"
    "\n"
)
w(os.path.join(MDEF, "tables", "DimDate.tmdl"), dimdate_tmdl)

# ---- _Measures.tmdl ----
def measure(name, expr, fmt, folder="Measures"):
    return (
        f"\tmeasure '{name}' = {expr}\n"
        f"\t\tformatString: {fmt}\n"
        f"\t\tdisplayFolder: {folder}\n"
        f"\t\tlineageTag: {uuid.uuid4()}\n"
        "\n"
    )

measures = "".join([
    measure("Total Sales", "SUM(Sales[SalesAmount])", "\\$#,0"),
    measure("Total Units", "SUM(Sales[Units])", "#,0"),
    measure("Total Sales PY", "CALCULATE([Total Sales], SAMEPERIODLASTYEAR(DimDate[Date]))", "\\$#,0"),
    measure("Total Units PY", "CALCULATE([Total Units], SAMEPERIODLASTYEAR(DimDate[Date]))", "#,0"),
    measure("Sales YoY", "[Total Sales] - [Total Sales PY]", "\\$#,0"),
    measure("Sales YoY %", "DIVIDE([Sales YoY], [Total Sales PY])", "0.0%"),
    measure("Units YoY %", "DIVIDE([Total Units] - [Total Units PY], [Total Units PY])", "0.0%"),
    measure("Sales KPI Color", 'IF([Sales YoY %] >= 0, "#44C088", "#ED7373")', '"#000000"'),
    measure("Units KPI Color", 'IF([Units YoY %] >= 0, "#44C088", "#ED7373")', '"#000000"'),
])

measures_tmdl = (
    "table _Measures\n"
    f"\tlineageTag: {uuid.uuid4()}\n"
    "\n"
    f"{measures}"
    "\tcolumn Value\n"
    "\t\tdataType: int64\n"
    "\t\tisHidden\n"
    f"\t\tlineageTag: {uuid.uuid4()}\n"
    "\t\tsummarizeBy: none\n"
    "\t\tsourceColumn: [Value]\n"
    "\n"
    "\tpartition _Measures = calculated\n"
    "\t\tmode: import\n"
    "\t\tsource = {BLANK()}\n"
    "\n"
)
w(os.path.join(MDEF, "tables", "_Measures.tmdl"), measures_tmdl)

# ---- relationships.tmdl ----
w(os.path.join(MDEF, "relationships.tmdl"),
  f"relationship {uuid.uuid4()}\n"
  "\tfromColumn: Sales.Date\n"
  "\ttoColumn: DimDate.Date\n")

# ---------------------------------------------------------------------------
# 5. REPORT PAGES + VISUALS
# ---------------------------------------------------------------------------
VC_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.0.0/schema.json"
M = "_Measures"

def meas(name):
    return {"field": {"Measure": {"Expression": {"SourceRef": {"Entity": M}}, "Property": name}},
            "queryRef": f"{M}.{name}", "nativeQueryRef": name}

def col(table, name):
    return {"field": {"Column": {"Expression": {"SourceRef": {"Entity": table}}, "Property": name}},
            "queryRef": f"{table}.{name}", "nativeQueryRef": name}

def kpi_card(name, x, z, tab, cy, py, yoy, color):
    return {
        "$schema": VC_SCHEMA, "name": name,
        "position": {"x": x, "y": 20, "z": z, "width": 300, "height": 150, "tabOrder": tab},
        "visual": {
            "visualType": "cardVisual",
            "objects": {
                "calloutValue": [{"properties": {"color": {"solid": {"color": {"expr": {
                    "Measure": {"Expression": {"SourceRef": {"Entity": M}}, "Property": color}}}}}}}],
                "cards": [{"properties": {"showLabel": {"expr": {"Literal": {"Value": "true"}}}}}],
                "referenceLabel": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}}}],
            },
            "query": {"queryState": {
                "Data": {"projections": [meas(cy)]},
                "ReferenceLabels": {"projections": [meas(py)]},
                "AdditionalMeasure": {"projections": [meas(yoy)]},
            }},
            "drillFilterOtherVisuals": True,
        },
    }

visuals = [
    kpi_card("v01KpiTotalSales", 20, 1000, 0, "Total Sales", "Total Sales PY", "Sales YoY %", "Sales KPI Color"),
    kpi_card("v02KpiTotalUnits", 340, 1001, 1, "Total Units", "Total Units PY", "Units YoY %", "Units KPI Color"),
    {
        "$schema": VC_SCHEMA, "name": "v03ColSalesByMonth",
        "position": {"x": 20, "y": 190, "z": 2000, "width": 610, "height": 250, "tabOrder": 2},
        "visual": {"visualType": "columnChart",
                   "query": {"queryState": {
                       "Category": {"projections": [col("DimDate", "YearMonth")]},
                       "Y": {"projections": [meas("Total Sales")]}}},
                   "drillFilterOtherVisuals": True},
    },
    {
        "$schema": VC_SCHEMA, "name": "v04ColMonthByYear",
        "position": {"x": 650, "y": 190, "z": 2001, "width": 610, "height": 250, "tabOrder": 3},
        "visual": {"visualType": "clusteredColumnChart",
                   "query": {"queryState": {
                       "Category": {"projections": [col("DimDate", "MonthName")]},
                       "Series": {"projections": [col("DimDate", "Year")]},
                       "Y": {"projections": [meas("Total Sales")]}}},
                   "drillFilterOtherVisuals": True},
    },
    {
        "$schema": VC_SCHEMA, "name": "v05BarByProduct",
        "position": {"x": 20, "y": 455, "z": 2002, "width": 610, "height": 245, "tabOrder": 4},
        "visual": {"visualType": "clusteredBarChart",
                   "query": {"queryState": {
                       "Category": {"projections": [col("Sales", "ProductName")]},
                       "Y": {"projections": [meas("Total Sales")]}}},
                   "drillFilterOtherVisuals": True},
    },
    {
        "$schema": VC_SCHEMA, "name": "v06TableProduct",
        "position": {"x": 650, "y": 455, "z": 2003, "width": 610, "height": 245, "tabOrder": 5},
        "visual": {"visualType": "tableEx",
                   "query": {"queryState": {"Values": {"projections": [
                       col("Sales", "ProductName"),
                       meas("Total Sales"),
                       meas("Total Sales PY"),
                       meas("Sales YoY %")]}}},
                   "drillFilterOtherVisuals": True},
    },
    {
        "$schema": VC_SCHEMA, "name": "v07DonutUnitsByProduct",
        "position": {"x": 20, "y": 715, "z": 2004, "width": 1240, "height": 245, "tabOrder": 6},
        "visual": {
            "visualType": "donutChart",
            "query": {"queryState": {
                "Category": {"projections": [col("Sales", "ProductName")]},
                "Y": {"projections": [meas("Total Units")]},
            }},
            "drillFilterOtherVisuals": True,
        },
    },
]

PAGE = "pg01Overview"
wj(os.path.join(RDEF, "pages", "pages.json"), {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json",
    "pageOrder": [PAGE],
    "activePageName": PAGE,
})

wj(os.path.join(RDEF, "pages", PAGE, "page.json"), {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.0.0/schema.json",
    "name": PAGE, "displayName": "Gadget Sales Overview",
    "displayOption": "FitToPage", "width": 1280, "height": 980,
})

for v in visuals:
    wj(os.path.join(RDEF, "pages", PAGE, "visuals", v["name"], "visual.json"), v)

# ---------------------------------------------------------------------------
# 6. VALIDATE
# ---------------------------------------------------------------------------
ok = True
for root, _, files in os.walk(BASE):
    for fn in files:
        if fn.endswith(".json"):
            p = os.path.join(root, fn)
            try:
                with open(p) as f:
                    json.load(f)
            except Exception as e:
                ok = False
                print("INVALID JSON:", p, e)

print(f"\nRows of sales data: {len(rows)}")
print("All JSON valid!" if ok else "FIX INVALID JSON ABOVE")
