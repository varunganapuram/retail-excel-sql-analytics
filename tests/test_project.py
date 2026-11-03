from pathlib import Path
import importlib.util
import json
import sqlite3
import unittest
from zipfile import ZipFile
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('retail_pipeline',ROOT/'src/pipeline.py')
pipeline=importlib.util.module_from_spec(spec);spec.loader.exec_module(pipeline)

class RetailTests(unittest.TestCase):
    def test_half_away_currency_rounding(self):
        for quantity,price,result in [(1,.005,1),(-1,.005,-1),(3,1.235,371),(-3,1.235,-371),(1,0,0)]:
            self.assertEqual(pipeline.money_cents(quantity,price),result)

    def test_u_test_ties_and_direction(self):
        self.assertEqual(pipeline.mann_whitney_asymptotic([1,1],[1,1]),(2.,1.))
        u,p=pipeline.mann_whitney_asymptotic([4,5,6],[1,2,3])
        self.assertEqual(u,9.)
        self.assertAlmostEqual(p,0.08085559837005224,places=12)
        u2,p2=pipeline.mann_whitney_asymptotic([1,2,3],[4,5,6])
        self.assertEqual(u2,0.);self.assertAlmostEqual(p,p2,places=12)
        with self.assertRaises(ValueError):pipeline.mann_whitney_asymptotic([], [1])

    def test_period_and_invoice_grain(self):
        with sqlite3.connect(ROOT/'data/processed/retail.sqlite') as con:
            dates=con.execute('SELECT MIN(invoice_date),MAX(invoice_date),COUNT(*) FROM invoice_lines').fetchone()
            self.assertGreaterEqual(dates[0],'2011-01-01');self.assertLess(dates[1],'2011-12-01')
            counts=con.execute('SELECT COUNT(*),COUNT(DISTINCT invoice_no) FROM invoices').fetchone()
            self.assertEqual(counts[0],counts[1])
            self.assertEqual(dates[2],471713)

    def test_sql_months_reconcile_to_independent_controls(self):
        k=json.loads((ROOT/'reports/kpis.json').read_text())
        with sqlite3.connect(ROOT/'data/processed/retail.sqlite') as con:
            for table in ['invoices','monthly_country','market_controls']:
                totals=con.execute(f'SELECT SUM(gross_cents),SUM(credit_cents),SUM(net_cents) FROM {table}').fetchone()
                self.assertEqual(totals,(k['gross_cents'],k['credit_cents'],k['net_cents']))
            known=con.execute("SELECT SUM(MAX(line_cents,0)) FROM invoice_lines WHERE customer_id<>''").fetchone()[0]
            customers=con.execute('SELECT SUM(gross_cents) FROM customer_review').fetchone()[0]
            self.assertEqual(known,customers)
            self.assertLess(customers,k['gross_cents'])

    def test_customer_concentration_population(self):
        d=json.loads((ROOT/'data/processed/workbook_inputs.json').read_text())
        values=np.array([r[4] for r in d['customers']])
        self.assertTrue(np.all(values[:-1]>=values[1:]))
        n=d['kpis']['top_one_percent_customer_count']
        self.assertEqual(n,42)
        self.assertAlmostEqual(values[:n].sum()/values.sum(),d['kpis']['top_one_percent_gross_share'],places=12)

    def test_interactive_workbook_controls(self):
        r=json.loads((ROOT/'reports/workbook_calculation_checks.json').read_text())
        self.assertTrue(r['blank_market_checked'] and r['unknown_market_checked'] and r['unknown_customer_checked'])
        self.assertAlmostEqual(r['germany_filter_value'],r['germany_independent_value'],places=2)
        self.assertNotEqual(r['customer_rule_before'],r['customer_rule_after'])
        self.assertEqual(r['reconciliations'],['PASS']*8)
        self.assertIn('matched 0 entries',r['formula_scan'])

    def test_native_pivot_parts_and_formula_caches(self):
        ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        f=ROOT/'workbook/Retail_Sales_Customer_Analytics.xlsx'
        with ZipFile(f) as z:
            self.assertIsNone(z.testzip())
            for i,name in [(1,'GrossByMarket'),(2,'NetByMonth')]:
                pivot=ET.fromstring(z.read(f'xl/pivotTables/pivotTable{i}.xml'))
                self.assertEqual(pivot.attrib['name'],name)
                self.assertEqual(pivot.attrib['cacheId'],'0')
            records=ET.fromstring(z.read('xl/pivotCache/pivotCacheRecords1.xml'))
            self.assertEqual(len(records),407)
            self.assertTrue(all(len(r)==8 for r in records))
            for path in z.namelist():
                if path.startswith('xl/worksheets/') and path.endswith('.xml'):
                    root=ET.fromstring(z.read(path))
                    errors=[c.attrib['r'] for c in root.findall('.//s:c',ns) if c.attrib.get('t')=='e']
                    self.assertEqual(errors,[],path)
            charts=[p for p in z.namelist() if '/charts/' in p and Path(p).name.startswith('chart') and p.endswith('.xml')]
            self.assertEqual(len(charts),1)

    def test_inferential_population_and_interval(self):
        r=json.loads((ROOT/'reports/statistics.json').read_text())
        self.assertEqual(r['uk_customers']+r['non_uk_customers'],4166)
        low,high=r['difference_95pct_customer_bootstrap_gbp']
        self.assertLess(low,r['median_difference_gbp']);self.assertGreater(high,r['median_difference_gbp'])
        self.assertGreater(r['p_value'],0.);self.assertLess(r['p_value'],.05)
        self.assertEqual(r['resamples'],2000)

    def test_saved_excel_statistics_match_analysis(self):
        from openpyxl import load_workbook
        r=json.loads((ROOT/'reports/statistics.json').read_text())
        w=load_workbook(ROOT/'workbook/Retail_Sales_Customer_Analytics.xlsx',data_only=True)
        self.assertAlmostEqual(w['Dashboard']['F42'].value,r['difference_95pct_customer_bootstrap_gbp'][0],places=8)
        self.assertAlmostEqual(w['Dashboard']['G42'].value,r['difference_95pct_customer_bootstrap_gbp'][1],places=8)
        self.assertAlmostEqual(w['Dashboard']['D25'].value,8587247.02,places=2)
        self.assertEqual(len(w['Market pivots']._pivots),2)
        self.assertEqual(len(w['Dashboard']._charts),1)
        w.close()

if __name__=='__main__':unittest.main()
