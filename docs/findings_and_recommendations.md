# Findings and proposed actions

## Account concentration

Forty-two customers account for 30.82% of gross value among identified buyers. Known customer IDs cover 84.97% of gross value. An account review can start with this concentrated group, then inspect credits and net value before assigning priority. For example, customer 12346 has a large positive invoice offset by an equally large credit and therefore zero net invoice value; gross sales alone would overstate the account's net contribution.

Suggested owner in the simulated brief: CRM lead. Proposed next evidence: order/credit linkage, service history, margin and account contacts. No retention uplift or profitability claim is supported by this dataset.

## Sales and credits

The eleven-month period records GBP 9.204 million gross value, GBP 0.617 million credits and GBP 8.587 million net invoice value. January's credit share is 19.0%, versus 6.70% for the full period. Review large credit notes before concluding that customer demand or delivery quality deteriorated. Credits can represent cancellation and other adjustments; the source cannot establish a physical return rate.

Suggested owner: Finance lead. Proposed next evidence: credit reason, original invoice ID, fulfillment date and margin. The source's incomplete December 2011 is excluded from monthly comparisons.

## Market mix

The UK contributes 83.20% of net value. November is the peak observed full month at GBP 1.462 million. These figures justify a market-level and seasonal capacity review, but one partial historical year cannot establish a stable seasonal forecast or prove future growth.

## Statistical comparison

The comparison uses each customer's average positive invoice value, not every invoice as an independent observation. It includes 3,774 UK customers and 392 non-UK customers with positive invoices and a consistent observed market. Seven customers spanning multiple markets are excluded from this comparison.

Median customer-level AOV is GBP 286.90 in the UK and GBP 430.34 outside the UK. The difference is GBP 143.44, with a 95% percentile interval of GBP 112.98-181.60 from 2,000 customer-level bootstrap resamples (seed 42). A two-sided asymptotic Mann-Whitney U test with tie and continuity corrections gives U = 1,006,940.5 and p = 4.37e-32. The rank-based probability-of-superiority estimate is 0.681.

Mann-Whitney U tests distributional ordering, not a difference in means or, without additional distributional assumptions, a pure difference in medians. The bootstrap interval separately describes the median difference. Country mix, wholesale customers and selection differ across groups. Treat the result as an observational historical association, not a causal market effect or a representative estimate for current customers.

Method reference: [SciPy's Mann-Whitney U documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.mannwhitneyu.html). The supplied implementation was independently checked against SciPy on 100 generated tied-value examples.
