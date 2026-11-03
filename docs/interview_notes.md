# Explain the project

The business question was how a small retail team could review invoice performance and identify high-value accounts worth investigating. I used a simulated Finance/Sales/CRM reporting brief and mapped each requirement to a KPI, Excel output and acceptance check.

SQL prepares invoice-grain, monthly-market and customer tables. Aggregating once at the correct grain prevents line-item joins from inflating invoice counts. CTEs and window functions calculate customer rankings and cumulative shares. Currency is stored as integer pence after an explicit per-line rounding policy.

The Excel workbook demonstrates PivotTables, SUMIFS/COUNTIFS, exact INDEX/MATCH, IF/AND review logic, validation, conditional formatting and an editable chart. Changing the market updates the monthly report. A separate all-market customer view avoids mixing population definitions. All primary outputs trace to source aggregates and independent controls.

The strongest finding is concentration: 42 customers account for 30.8% of identified-customer sales. I also reviewed credits before proposing account priority. One prominent account has its positive invoice fully offset by a credit, illustrating why gross sales and net value answer different questions.

For statistics, I compared one AOV value per customer to avoid treating repeat invoices as independent customers. A rank-based U test accommodates skewed values. A customer bootstrap describes uncertainty in the median difference. Neither method establishes causality or present-day market performance.

The project demonstrates reporting requirements mapping, not paid stakeholder work. I would need real user feedback, credit reason codes, margin and current transactions before deploying it operationally. The resume should describe a completed portfolio project and measured historical findings, not invented client work or savings.
