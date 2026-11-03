# Simulated commercial reporting brief

This is a self-directed portfolio brief. Finance, Sales and CRM are hypothetical report users, not clients or employers who commissioned this project.

The decision is how to review monthly invoice performance and prioritize account investigation. The reporting period is 1 January to 30 November 2011, the last eleven complete calendar months available in the source year. The audience needs a repeatable Excel report, clear definitions, traceable SQL calculations and restrained business recommendations.

| ID | Simulated user need | KPI or behavior | Implementation | Acceptance evidence |
|---|---|---|---|---|
| R1 | Finance needs reconciled sales and credits | Gross positive billed value, absolute negative billed value, net = gross - credits | Dashboard monthly table; integer-pence SQL aggregates | SQL/Python and workbook controls agree within GBP 0.005 |
| R2 | Sales needs market comparisons | One authoritative market selector updates monthly values and the trend | Validated Dashboard market cell; SUMIFS | Germany totals match independent SQL; all-market value is restored |
| R3 | Finance must not interpret credits as product returns | Credit value / positive billed value; no unsupported return-rate denominator | Credit share column and nearby definition | Report uses value-based labels and discloses missing original-invoice linkage |
| R4 | CRM needs a traceable customer review list | Recency, positive-invoice frequency, gross/credit/net value | SQL customer table; configurable Excel IF/AND rule | Changing minimum orders changes the example customer's category |
| R5 | CRM needs exact customer retrieval | Unique customer ID, net value and review category | INDEX/MATCH with an explicit missing-ID result | An unknown ID returns No customer |
| R6 | A business analyst needs reusable summaries | Native market-gross and monthly-net PivotTables | Two PivotTable definitions sharing a prepared-source cache | Cached results reconcile; Microsoft Open XML validation passes |
| R7 | A manager needs an explanation of account concentration | Ceiling of top 1% of identified positive-sale customers; share of identified gross value | Sorted customer values and SUMIFS; explicit coverage denominator | 42 customers and 30.82% independently reproduced |
| R8 | The analyst needs an appropriate order-value comparison | One customer-level AOV per known consistent-market customer | Two-sided tie-corrected Mann-Whitney U and 2,000 customer bootstrap resamples | Published sample sizes, interval, effect size and 100 SciPy comparisons |

## KPI contract

| Measure | Population and formula |
|---|---|
| Eligible line | Invoice date within reporting period, positive unit price and nonzero quantity |
| Gross sales value | Sum of positive eligible line values, including invoice charges |
| Credit value | Absolute sum of negative eligible line values |
| Net invoice value | Gross sales value minus credit value; not profit |
| Positive invoice count | Distinct invoice number with positive billed value |
| Mean positive invoice value | Gross sales value divided by positive invoice count |
| Credit value share | Credit value divided by gross sales value; not number of returned orders |
| Customer recency | Days from the most recent positive invoice date to 1 December 2011 |
| Customer frequency | Number of positive invoices during the reporting period |
| Customer concentration | Gross value of the first ceil(1% x identified positive-sale customers), sorted by gross value then ID, divided by all identified-customer gross value |

Editable account-review thresholds are examples: at most 60 days recency, at least five positive invoices and at least GBP 1,000 net value. The rules are not a churn model. Missing customer IDs cannot enter customer segmentation. Requirements are mapped to the artifact and tests; no stakeholder sign-off or realized intervention outcome is claimed.
