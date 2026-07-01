# Contoso Sales Report Writing Guidelines

These guidelines describe how to write sales reports for the Contoso product catalog.
They ensure that revenue, volume, and performance figures are presented consistently
across teams and reporting periods.

## 1. Reporting Period and Scope

- State the reporting period at the top using the ISO format `YYYY-MM-DD` to
  `YYYY-MM-DD`.
- Specify the scope: global, by region, by product line, or by sales channel.
- Compare each period against the previous equivalent period (month over month or
  quarter over quarter) and against target.

## 2. Required Metrics

Every sales report must present the following core metrics:

1. **Units Sold** — Total quantity sold during the period.
2. **Gross Revenue** — Total revenue before discounts and returns.
3. **Net Revenue** — Revenue after discounts, returns, and refunds.
4. **Average Selling Price (ASP)** — Net revenue divided by units sold.
5. **Attainment** — Actual net revenue as a percentage of the period target.
6. **Top and Bottom Performers** — The three best- and worst-selling SKUs.

Present the core metrics in a table so each period can be compared at a glance. Use the
following layout:

| Metric          | Current period | Previous period | Target      | Variance |
| --------------- | -------------- | --------------- | ----------- | -------- |
| Units sold      | 12,480         | 11,020          | 12,000      | +4.0%    |
| Gross revenue   | 1,248,000.00   | 1,102,000.00    | 1,200,000.00| +4.0%    |
| Net revenue     | 1,180,500.00   | 1,050,300.00    | 1,140,000.00| +3.6%    |
| ASP             | 94.59          | 95.31           | 95.00       | -0.4%    |
| Attainment      | 103.6%         | 92.1%           | 100.0%      | +11.5 pts|

## 3. Presentation and Formatting

- Report all monetary values in the reporting currency and state that currency clearly.
- Use thousands separators and keep decimal precision consistent (two decimals for
  currency, whole numbers for units).
- Express growth and attainment as percentages with a leading sign (`+12.5%`,
  `-3.0%`).
- Provide a table for numeric data and a short narrative for context.

## 4. Analysis and Commentary

- Do not present numbers without commentary. Explain the main drivers behind notable
  increases or decreases.
- Separate observed facts from interpretation. Label forward-looking statements as
  `Forecast` or `Projection`.
- Highlight anomalies (returns spikes, channel outages, seasonal effects) so readers
  do not misread the trend.

## 5. Data Quality and Sources

- Cite the source system for each figure (order management, finance ledger, or CRM).
- Reconcile net revenue against the finance ledger before publishing.
- Mark any provisional figure with the label `(unaudited)` until it is confirmed.

## 6. Confidentiality and Distribution

- Classify each report as `Internal`, `Confidential`, or `Restricted`.
- Do not include individual customer identifiers in aggregated reports.
- Record the author, the approver, and the publication date at the end of the document.
