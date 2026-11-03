"""Reproducible retail analysis: unchanged UCI source -> SQLite -> Excel inputs."""
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
from urllib.request import urlopen
from zipfile import ZipFile
from io import BytesIO
import argparse
import hashlib
import json
import math
import sqlite3
import sys
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
START='2011-01-01'
END='2011-12-01'

def money_cents(quantity,price):
    return int((Decimal(str(quantity))*Decimal(str(price))*100).quantize(Decimal('1'),rounding=ROUND_HALF_UP))

def mann_whitney_asymptotic(x,y):
    """Two-sided U test, pooled average ranks, tie and continuity corrections."""
    x=np.asarray(x,dtype=float);y=np.asarray(y,dtype=float)
    if not len(x) or not len(y) or not np.isfinite(np.r_[x,y]).all():
        raise ValueError('Both comparison groups need finite observations')
    n,m=len(x),len(y);combined=np.r_[x,y]
    ranks=pd.Series(combined).rank(method='average').to_numpy()
    u=float(ranks[:n].sum()-n*(n+1)/2)
    counts=np.unique(combined,return_counts=True)[1].astype(float)
    size=n+m
    variance=n*m/12*((size+1)-float(np.sum(counts**3-counts))/(size*(size-1)))
    z=max(0.,abs(u-n*m/2)-.5)/math.sqrt(variance) if variance>0 else 0.
    return u,math.erfc(z/math.sqrt(2))

def write_json(path,value):
    (ROOT/path).write_text(json.dumps(value,indent=2,default=str,allow_nan=False)+'\n',encoding='utf-8')

def fetch():
    path=ROOT/'data/raw/Online Retail.xlsx'
    path.parent.mkdir(parents=True,exist_ok=True)
    if not path.exists():
        with urlopen('https://archive.ics.uci.edu/static/public/352/online+retail.zip',timeout=180) as response:
            data=response.read()
        with ZipFile(BytesIO(data)) as archive:
            path.write_bytes(archive.read('Online Retail.xlsx'))
    return path

def run():
    for folder in ['data/processed','reports']:
        (ROOT/folder).mkdir(parents=True,exist_ok=True)
    source=fetch()
    f=pd.read_excel(source,engine='openpyxl')
    assert list(f.columns)==['InvoiceNo','StockCode','Description','Quantity','InvoiceDate','UnitPrice','CustomerID','Country']
    f['source_row']=np.arange(2,len(f)+2)
    exact_duplicates=int(f.drop(columns='source_row').duplicated().sum())
    f['InvoiceDate']=pd.to_datetime(f.InvoiceDate)
    for c in ['InvoiceNo','StockCode','Country']:
        f[c]=f[c].astype(str).str.strip()
    f['customer_id']=f.CustomerID.map(lambda x:'' if pd.isna(x) else str(int(x)))
    # Currency precision is explicit. The raw workbook stays unchanged.
    price_map={x:int((Decimal(str(x))*1_000_000).quantize(Decimal('1'))) for x in f.UnitPrice.unique()}
    f['unit_price_micro']=f.UnitPrice.map(price_map).astype('int64')
    amount_micro=f.Quantity.astype('int64')*f.unit_price_micro
    f['line_cents']=(np.sign(amount_micro)*((np.abs(amount_micro)+5000)//10000)).astype('int64')
    valid=(f.InvoiceDate>=START)&(f.InvoiceDate<END)&f.UnitPrice.gt(0)&f.Quantity.ne(0)
    rows=f.loc[valid].copy()
    rows['invoice_no']=rows.InvoiceNo
    rows['stock_code']=rows.StockCode
    rows['country']=rows.Country
    rows['invoice_date']=rows.InvoiceDate.dt.strftime('%Y-%m-%d')
    rows['month']=rows.InvoiceDate.dt.strftime('%Y-%m-01')
    rows['quantity']=rows.Quantity.astype(int)
    rows['is_credit']=rows.invoice_no.str.upper().str.startswith('C').astype(int)
    export=rows[['source_row','invoice_no','stock_code','invoice_date','month','customer_id','country','quantity','unit_price_micro','line_cents','is_credit']]
    db=ROOT/'data/processed/retail.sqlite'
    with sqlite3.connect(db) as con:
        export.to_sql('invoice_lines',con,if_exists='replace',index=False)
        con.executescript('CREATE INDEX IF NOT EXISTS ix_invoice ON invoice_lines(invoice_no); CREATE INDEX IF NOT EXISTS ix_customer ON invoice_lines(customer_id);')
        con.executescript((ROOT/'sql/analysis.sql').read_text())
        invoices=pd.read_sql_query('SELECT * FROM invoices ORDER BY invoice_no',con)
        monthly=pd.read_sql_query('SELECT * FROM monthly_country ORDER BY month,country',con)
        customers=pd.read_sql_query('SELECT * FROM customer_review ORDER BY gross_cents DESC,customer_id',con)
        market=pd.read_sql_query('SELECT * FROM market_controls ORDER BY net_cents DESC,country',con)
        top_products=pd.read_sql_query('SELECT * FROM product_review ORDER BY net_cents DESC LIMIT 25',con)
        controls=pd.read_sql_query('SELECT SUM(MAX(line_cents,0)) gross_cents,SUM(MAX(-line_cents,0)) credit_cents,SUM(line_cents) net_cents,COUNT(*) lines FROM invoice_lines',con).iloc[0].to_dict()
    # An independent pandas roll-up must agree with the SQL, to the penny.
    pandas_totals={'gross_cents':int(rows.line_cents.clip(lower=0).sum()),'credit_cents':int((-rows.line_cents.clip(upper=0)).sum()),'net_cents':int(rows.line_cents.sum()),'lines':len(rows)}
    assert controls==pandas_totals,(controls,pandas_totals)
    assert not invoices.invoice_no.duplicated().any()
    for frame,name in [(invoices,'invoices'),(monthly,'monthly_country'),(customers,'customer_review'),(market,'market_controls'),(top_products,'top_products')]:
        frame.to_csv(ROOT/f'data/processed/{name}.csv',index=False)
    # Test every distinct quantity/price pair against a Decimal calculation.
    pairs=f[['Quantity','UnitPrice','line_cents']].drop_duplicates()
    assert all(money_cents(q,p)==c for q,p,c in pairs.itertuples(index=False,name=None))
    # One predeclared observational comparison, with customers as the sampling unit.
    # This avoids treating repeated invoices from one customer as independent people.
    eligible=customers[(customers.positive_orders>0)&customers.country.ne('Multiple markets')].sort_values('customer_id').copy()
    uk=(eligible.loc[eligible.country.eq('United Kingdom'),'gross_cents']/eligible.loc[eligible.country.eq('United Kingdom'),'positive_orders']/100).to_numpy()
    other=(eligible.loc[eligible.country.ne('United Kingdom'),'gross_cents']/eligible.loc[eligible.country.ne('United Kingdom'),'positive_orders']/100).to_numpy()
    u,p_value=mann_whitney_asymptotic(other,uk)
    rng=np.random.default_rng(42)
    diffs=[float(np.median(rng.choice(other,len(other),replace=True))-np.median(rng.choice(uk,len(uk),replace=True))) for _ in range(2000)]
    statistics=dict(question='Do customer-level average positive invoice values differ between UK and non-UK customers?',
        sample_unit='Customer, not invoice. Consistent-country customers with positive invoices only.',
        uk_customers=len(uk),non_uk_customers=len(other),uk_median_customer_aov_gbp=float(np.median(uk)),
        non_uk_median_customer_aov_gbp=float(np.median(other)),median_difference_gbp=float(np.median(other)-np.median(uk)),
        difference_95pct_customer_bootstrap_gbp=np.quantile(diffs,[.025,.975]).tolist(),
        mann_whitney_u=u,p_value=p_value,
        test_method='Two-sided asymptotic Mann-Whitney U, average ranks, tie correction and continuity correction',
        probability_non_uk_aov_exceeds_uk=float(u/(len(uk)*len(other))),
        resamples=2000,seed=42,
        interpretation='Historical association. Markets, customer mix and wholesale behavior differ; this is not a causal country effect or a representative current-market experiment.')
    write_json('reports/statistics.json',statistics)
    positive_customers=customers[customers.gross_cents>0].sort_values(['gross_cents','customer_id'],ascending=[False,True])
    n_top=max(1,math.ceil(.01*len(positive_customers)))
    top_share=float(positive_customers.head(n_top).gross_cents.sum()/positive_customers.gross_cents.sum())
    all_months=monthly.groupby('month',sort=True)[['gross_cents','credit_cents','net_cents','positive_orders']].sum().reset_index()
    peak=all_months.loc[all_months.net_cents.idxmax()]
    uk_market=market[market.country.eq('United Kingdom')].iloc[0]
    quality=dict(source_rows=len(f),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        exact_duplicate_signatures=exact_duplicates,duplicate_policy='Retained. No source line ID establishes that identical rows are erroneous duplicates.',
        reporting_start=START,reporting_end_exclusive=END,eligible_line_rows=len(rows),
        outside_reporting_period=int(((f.InvoiceDate<START)|(f.InvoiceDate>=END)).sum()),
        nonpositive_price_in_period=int(((f.InvoiceDate>=START)&(f.InvoiceDate<END)&f.UnitPrice.le(0)).sum()),
        zero_quantity_in_period=int(((f.InvoiceDate>=START)&(f.InvoiceDate<END)&f.Quantity.eq(0)).sum()),
        missing_customer_lines=int(rows.customer_id.eq('').sum()),
        precision_policy='Round quantity x unit price to GBP pence per line, half away from zero. Preserve raw source.',
        cancellation_sign_anomalies=int((rows.is_credit.eq(1)&rows.line_cents.gt(0)).sum()),
        decimal_pair_checks=len(pairs),sql_python_reconciliation='passed')
    kpis=dict(**pandas_totals,source_rows=len(f),positive_invoices=int((invoices.gross_cents>0).sum()),
        credit_invoices=int((invoices.credit_cents>0).sum()),countries=len(market),identified_customers=len(customers),
        gross_sales_gbp=controls['gross_cents']/100,credits_gbp=controls['credit_cents']/100,net_invoice_value_gbp=controls['net_cents']/100,
        credit_value_share=float(controls['credit_cents']/controls['gross_cents']),
        uk_net_value_share=float(uk_market.net_cents/controls['net_cents']),
        known_customer_gross_coverage=float(positive_customers.gross_cents.sum()/controls['gross_cents']),
        top_one_percent_customer_count=n_top,positive_identified_customers=len(positive_customers),top_one_percent_gross_share=top_share,
        peak_month=str(peak['month']),peak_month_net_gbp=float(peak.net_cents/100),
        reporting_start=START,reporting_end_exclusive=END)
    write_json('reports/data_quality.json',quality);write_json('reports/kpis.json',kpis)
    # Typed JSON values feed the artifact-tool builder, never preformatted strings.
    months=pd.date_range(START,'2011-11-01',freq='MS').strftime('%Y-%m-01').tolist()
    countries=sorted(market.country.tolist())
    lookup=monthly.set_index(['month','country'])
    source_rows=[]
    for month in months:
        for country in countries:
            key=(month,country)
            g=lookup.loc[key] if key in lookup.index else None
            source_rows.append([month,country,*([float(g.gross_cents)/100,float(g.credit_cents)/100,int(g.positive_orders),int(g.credit_invoices),int(g.line_count)] if g is not None else [0,0,0,0,0])])
    customer_rows=[[str(r.customer_id),str(r.country),int(r.recency_days) if pd.notna(r.recency_days) else None,int(r.positive_orders),float(r.gross_cents)/100,float(r.credit_cents)/100] for r in customers.itertuples()]
    markets=[[str(r.country),r.gross_cents/100,r.credit_cents/100,r.net_cents/100,int(r.positive_orders)] for r in market.itertuples()]
    all_market=['All markets',kpis['gross_sales_gbp'],kpis['credits_gbp'],kpis['net_invoice_value_gbp'],kpis['positive_invoices']]
    prepared=dict(months=months,countries=countries,source_rows=source_rows,customers=customer_rows,markets=[all_market]+markets,kpis=kpis,statistics=statistics,quality=quality)
    write_json('data/processed/workbook_inputs.json',prepared)
    print(json.dumps({'kpis':kpis,'statistics':statistics,'quality':quality},indent=2))

if __name__=='__main__':run()
