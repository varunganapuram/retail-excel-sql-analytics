# Retail Sales and Customer Analytics

[![Validate retail analysis](https://github.com/varunganapuram/retail-excel-sql-analytics/actions/workflows/validate.yml/badge.svg)](https://github.com/varunganapuram/retail-excel-sql-analytics/actions/workflows/validate.yml)

An Excel and SQL portfolio project for a simulated monthly commercial review. The working report answers three questions: how much was billed after credits, which markets account for the value, and which identified customers merit closer account review?

Open `workbook/Retail_Sales_Customer_Analytics.xlsx`. Select a market on Dashboard, look up a customer on Customers, or change the illustrative customer-review thresholds. The file contains two native PivotTables, SUMIFS/COUNTIFS calculations, exact INDEX/MATCH lookups, data validation, conditional formatting and an editable trend chart.

## Findings

- January-November 2011 contains **471,713 eligible lines**, **17,582 positive invoices**, and **37 markets**, drawn from 541,909 original source rows.
- Gross positive invoice value is **GBP 9,204,145.72**. Credits total **GBP 616,898.70**, leaving **GBP 8,587,247.02** net invoice value. Credit value is **6.70%** of gross value. These are invoice values, not profit or a physical product-return rate.
- **42 customers**, the ceiling of 1% of 4,173 identified customers with positive sales, account for **30.82% of identified-customer gross sales**. Identified customers cover 84.97% of gross value, so the concentration result excludes anonymous sales.
- Customer-level median average positive invoice value is **GBP 286.90 in the UK** and **GBP 430.34 outside the UK**. The median difference is GBP 143.44, with a 95% customer-bootstrap interval of GBP 112.98-181.60. The observational U-test result does not establish a causal country effect.

These findings support a proposed high-value account review and a review of large credits before interpreting billed value as customer value. No actual revenue uplift, customer retention improvement or stakeholder implementation is claimed.

## Business brief and evidence

- `docs/business_requirements.md`: simulated Finance, Sales and CRM requirements, KPI contracts and acceptance mapping.
- `docs/findings_and_recommendations.md`: findings, proposed actions and statistical interpretation.
- `docs/interview_notes.md`: how to explain the Excel, SQL and statistical choices.
- `reports/`: currency reconciliation, statistical outputs, formula/control checks, native PivotTable structure and Microsoft Open XML validation.
- `sql/analysis.sql`: invoice aggregation, CTEs, market/month summaries and customer window functions.

## Reproduce the analysis

Use Python 3.12 or a compatible Python environment:

```bash
python -m pip install -r requirements.txt
python src/pipeline.py
python -m unittest discover -s tests -v
```

The pipeline downloads the public source only when absent. It rebuilds this project's SQLite tables under `data/processed/retail.sqlite`. It does not connect to another database. The source workbook remains unchanged. Monetary values are rounded to GBP pence per line using half-away-from-zero rounding, then summed as integer pence.

The supplied Excel file is ready to use. To rebuild its layout in a Codex environment with the bundled `@oai/artifact-tool` package:

```bash
node src/build_workbook.mjs
python src/package_pivots.py
python -m unittest discover -s tests -v
```

Make the bundled package available through a local `node_modules` junction or normal package resolution. Workbook authorship uses artifact-tool. A narrow Open XML compatibility step adds the native PivotTable cache/definition parts because the bundled pivot-export interface is unavailable. All other cells, formulas, tables and the chart are authored with artifact-tool.

Rendering is separate from export because the Windows graphics renderer can terminate its process during cleanup after saving previews. The ordinary calculation/export path exits successfully. Existing previews are supplied in `docs/previews/`; use `RETAIL_RENDER=1` only when regenerating previews in a supported rendering environment.

After changing source-table values in Excel, refresh both PivotTables. If new periods, countries or customer rows are added, rebuild the analysis and workbook so bounded formulas and source ranges extend together. This is a historical analysis, not an automatic live data connection.

## Verification and boundaries

Ten automated tests pass. SQL/Python monetary totals reconcile to the penny, and 8,394 distinct quantity/price combinations are checked against Decimal rounding. The U-test implementation agrees with SciPy on 100 independently generated test cases including ties. The workbook's market filter, missing-market guard, customer lookup and customer-rule changes are recalculation-tested in artifact-tool. Cached formula results and both native PivotTable caches are checked after export. Microsoft Open XML SDK 3.3.0 reports zero validation errors.

Native Excel screen capture/input automation was unavailable in this Windows session. A native Excel refresh and full click-through acceptance are therefore not claimed. This is separate from the successful calculation, saved-file, cache and Open XML checks.

## Data and attribution

Daqing Chen (2015), **Online Retail**, UCI Machine Learning Repository, [DOI 10.24432/C5BW33](https://doi.org/10.24432/C5BW33), [source page](https://archive.ics.uci.edu/dataset/352/online-retail). The dataset is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The original source spans December 2010 to 9 December 2011; this project uses complete January-November 2011 months.

Nonpositive unit prices and zero quantities are excluded from monetary KPIs. Missing customer IDs remain in market totals. Identical source signatures are retained because no line ID establishes that they are erroneous duplicates. Credits cannot be reliably linked back to original purchases. These choices and all counts are published in `reports/data_quality.json`.

The public portfolio source is [varunganapuram/retail-excel-sql-analytics](https://github.com/varunganapuram/retail-excel-sql-analytics). GitHub Actions rebuilds the source analysis and tests the delivered Excel workbook. It does not regenerate the Excel layout or perform native Excel UI automation.
