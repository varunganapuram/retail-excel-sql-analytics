import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Workbook, SpreadsheetFile} from '@oai/artifact-tool';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const work=path.join(root,'docs/previews');
await fs.mkdir(work,{recursive:true});
const d=JSON.parse(await fs.readFile(path.join(root,'data/processed/workbook_inputs.json'),'utf8'));
const wb=Workbook.create();
const names=['Dashboard','Customers','Market pivots','Source','Audit','Readme'];
const sheets=Object.fromEntries(names.map(n=>[n,wb.worksheets.add(n)]));
const cash='"£"#,##0;("£"#,##0);"£"0';
const num='#,##0';const pct='0.0%';
const serial=s=>Date.parse(s+'T00:00:00Z')/86400000+25569;
const end=6+d.source_rows.length;
const lastCustomer=8+d.customers.length;
const lastMarket=6+d.markets.length;
const blue='#2563EB',red='#DC2626',green='#16A34A';
const source=sheets.Source,dash=sheets.Dashboard,cust=sheets.Customers,piv=sheets['Market pivots'],audit=sheets.Audit,readme=sheets.Readme;
function text(sheet,cell,value){sheet.getRange(cell).values=[[value]];}
function formula(sheet,cell,value){sheet.getRange(cell).formulas=[[value]];}
function heading(sheet,title,range='A1:K50'){
  sheet.showGridLines=false;
  sheet.getRange(range).format.font={name:'Arial',size:11,color:'#000000'};
  sheet.getRange(range).format.rowHeight=22;
  sheet.getRange(range).format.columnWidth=17;
  text(sheet,'A2',title);
  sheet.getRange('A2').format.font={name:'Arial',size:16,bold:true,color:'#000000'};
  sheet.getRange('A3:K3').format.borders={bottom:{style:'thin',color:'#A3A3A3'}};
}
function header(sheet,address){sheet.getRange(address).format={fill:'#262626',font:{name:'Arial',size:11,bold:true,color:'#FFFFFF'},rowHeight:30,horizontalAlignment:'center',verticalAlignment:'center',wrapText:true};}
function input(sheet,address){sheet.getRange(address).format.fill='#FFF2CC';sheet.getRange(address).format.font.color='#1D4ED8';}
function styleChart(chart,title,start,end,color){
  chart.title=title;chart.titleTextStyle.typeface='Arial';chart.titleTextStyle.fontSize=15;
  chart.hasLegend=false;chart.xAxis={axisType:'textAxis',textStyle:{typeface:'Arial',fontSize:12}};
  chart.yAxis={numberFormatCode:'"£"0.0,,"M"',numberFormatSourceLinked:false,textStyle:{typeface:'Arial',fontSize:12}};
  chart.series.items[0].fill=color;
  chart.series.items[0].line={fill:color,style:'solid',width:3};
  chart.setPosition(start,end);
}

heading(source,'Prepared source data','A1:R'+Math.max(end,50));
source.getRange('A6:H6').values=[['Month','Country','Gross GBP','Credits GBP','Net GBP','Positive invoices','Credit invoices','Eligible lines']];
source.getRange('A7:H'+end).values=d.source_rows.map(r=>[serial(r[0]),r[1],r[2],r[3],r[2]-r[3],r[4],r[5],r[6]]);
source.getRange('A7:A'+end).setNumberFormat('mmm yyyy');source.getRange('C7:E'+end).setNumberFormat(cash);
source.getRange('F7:H'+end).setNumberFormat(num);source.getRange('B6:B'+end).format.columnWidth=23;
header(source,'A6:H6');source.freezePanes.freezeRows(6);
source.tables.add('A6:H'+end,true,'RetailMonthlySource');
text(source,'A4','UCI Online Retail. SQL aggregation of eligible January-November 2011 lines. GBP, not profit.');
source.getRange('J6:N6').values=[['Market','Gross GBP','Credits GBP','Net GBP','Positive invoices']];
source.getRange('J7:N'+lastMarket).values=d.markets;header(source,'J6:N6');
source.getRange('J6:J'+lastMarket).format.columnWidth=23;source.getRange('K7:M'+lastMarket).setNumberFormat(cash);
const controls=[['Gross GBP',d.kpis.gross_sales_gbp],['Credits GBP',d.kpis.credits_gbp],['Net GBP',d.kpis.net_invoice_value_gbp],['Eligible lines',d.kpis.lines],['Positive invoices',d.kpis.positive_invoices],['Source rows',d.kpis.source_rows],['Identified customers',d.kpis.identified_customers],['Known-customer gross GBP',d.customers.reduce((s,r)=>s+r[4],0)],['Top 1% gross share',d.kpis.top_one_percent_gross_share],['Top 1% customer count',d.kpis.top_one_percent_customer_count]];
source.getRange('P6:Q6').values=[['Independent SQL control','Value']];source.getRange('P7:Q16').values=controls;header(source,'P6:Q6');
source.getRange('P6:P40').format.columnWidth=32;source.getRange('Q6:Q40').format.columnWidth=20;
const stats=[['UK median customer AOV',d.statistics.uk_median_customer_aov_gbp],['Non-UK median customer AOV',d.statistics.non_uk_median_customer_aov_gbp],['Median difference GBP',d.statistics.median_difference_gbp],['95% lower GBP',d.statistics.difference_95pct_customer_bootstrap_gbp[0]],['95% upper GBP',d.statistics.difference_95pct_customer_bootstrap_gbp[1]],['Mann-Whitney p-value',d.statistics.p_value]];
source.getRange('P23:Q28').values=stats;source.getRange('Q23:Q27').setNumberFormat('"£"#,##0.00');source.getRange('Q28').setNumberFormat('0.00E+00');
text(source,'P31','Source: https://archive.ics.uci.edu/dataset/352/online-retail');
text(source,'P33','Prepared values: data/processed CSV files. Original source stays unchanged.');

heading(dash,'Retail sales and customer review','A1:O49');dash.tabColor='#262626';
text(dash,'A4','January-November 2011. Complete months. Invoice values in GBP.');
text(dash,'A5','Selected market');text(dash,'B5','All markets');input(dash,'B5');
dash.getRange('B5').format.columnWidth=24;
dash.getRange('B5').dataValidation={rule:{type:'list',formula1:`Source!$J$7:$J$${lastMarket}`}};
formula(dash,'D5',`=IF(COUNTIFS(Source!$J$7:$J$${lastMarket},B5)=1,"Ready","Choose a valid market")`);
text(dash,'I4','Customer review rule');dash.getRange('I4').format.font.bold=true;
text(dash,'I5','Recency at most (days)');text(dash,'M5',60);text(dash,'I6','At least this many orders');text(dash,'M6',5);text(dash,'I7','Net value at least (GBP)');text(dash,'M7',1000);
input(dash,'M5:M7');dash.getRange('M5:M6').dataValidation={rule:{type:'whole',operator:'between',formula1:0,formula2:365}};
dash.getRange('M7').dataValidation={rule:{type:'decimal',operator:'greaterThanOrEqual',formula1:0}};
text(dash,'A8','Gross sales');text(dash,'C8','Credits');text(dash,'E8','Net invoice value');
formula(dash,'A9','=B25');formula(dash,'C9','=C25');formula(dash,'E9','=D25');
for(const address of ['A9','C9','E9']){dash.getRange(address).setNumberFormat(cash);dash.getRange(address).format.font={size:16,bold:true,name:'Arial',color:'#000000'};}
dash.getRange('A13:G13').values=[['Month','Gross GBP','Credits GBP','Net GBP','Positive invoices','Mean invoice GBP','Credit share']];header(dash,'A13:G13');
for(let i=0;i<d.months.length;i++){
  const row=14+i;text(dash,'A'+row,serial(d.months[i]));
  for(const [dest,src] of [['B','C'],['C','D'],['E','F']]) formula(dash,dest+row,`=IF($D$5<>"Ready","n.a.",SUMIFS(Source!$${src}$7:$${src}$${end},Source!$A$7:$A$${end},$A${row},Source!$B$7:$B$${end},IF($B$5="All markets","*",$B$5)))`);
  formula(dash,'D'+row,`=IF($D$5<>"Ready","n.a.",B${row}-C${row})`);
  formula(dash,'F'+row,`=IF($D$5<>"Ready","n.a.",IF(E${row}=0,"n.a.",B${row}/E${row}))`);
  formula(dash,'G'+row,`=IF($D$5<>"Ready","n.a.",IF(B${row}=0,"n.a.",C${row}/B${row}))`);
}
text(dash,'A25','Total');
for(const col of ['B','C','D','E']) formula(dash,col+'25',`=IF($D$5<>"Ready","n.a.",SUM(${col}14:${col}24))`);
formula(dash,'F25','=IF($D$5<>"Ready","n.a.",IF(E25=0,"n.a.",B25/E25))');
formula(dash,'G25','=IF($D$5<>"Ready","n.a.",IF(B25=0,"n.a.",C25/B25))');
dash.getRange('A14:A24').setNumberFormat('mmm yyyy');dash.getRange('B14:D25').setNumberFormat(cash);dash.getRange('E14:E25').setNumberFormat(num);dash.getRange('F14:F25').setNumberFormat('"£"#,##0.00');dash.getRange('G14:G25').setNumberFormat(pct);
dash.getRange('A25:G25').format.font.bold=true;dash.getRange('A25:G25').format.borders={top:{style:'thin',color:'#777777'}};
dash.getRange('G14:G24').conditionalFormats.add('colorScale',{colors:['#FFFFFF','#FDE68A','#FCA5A5'],thresholds:['min','50%','max']});
// Text month labels avoid date-serial rendering in chart previews.
source.getRange('S6:T6').values=[['Chart month','Selected net GBP']];
source.getRange('S7:T17').values=d.months.map(s=>[new Date(s+'T00:00:00Z').toLocaleString('en-GB',{month:'short',year:'numeric',timeZone:'UTC'}),null]);
for(let i=0;i<11;i++)formula(source,'T'+(7+i),'=Dashboard!D'+(14+i));
source.getRange('S6:T17').format.font={name:'Arial',size:11,color:'#000000'};source.getRange('S6:T17').format.columnWidth=22;source.getRange('T7:T17').setNumberFormat(cash);header(source,'S6:T6');
const trend=dash.charts.add('line',source.getRange('S6:T17'));
styleChart(trend,'Monthly net invoice value (GBP)','I10','P25',blue);
text(dash,'A29','Customer concentration');dash.getRange('A29').format.font={size:14,bold:true};
text(dash,'A30','All markets. Identified customers only.');
text(dash,'A32','Top 1% customer count');formula(dash,'C32',`=ROUNDUP(COUNTIFS(Customers!$E$9:$E$${lastCustomer},">0")*1%,0)`);
text(dash,'A33','Share of identified sales');formula(dash,'C33',`=SUMIFS(Customers!$E$9:$E$${lastCustomer},Customers!$J$9:$J$${lastCustomer},"<="&C32)/Customers!$K$2`);dash.getRange('C33').setNumberFormat(pct);
text(dash,'A34','Identified sales coverage');formula(dash,'C34','=Customers!$K$2/Source!K7');dash.getRange('C34').setNumberFormat(pct);
text(dash,'A36','Prioritize a review of the high-value accounts. No retention uplift is assumed.');
text(dash,'A39','Customer-level order value');dash.getRange('A39').format.font={size:14,bold:true};
text(dash,'A40','UK median AOV');formula(dash,'C40','=Source!Q23');text(dash,'A41','Non-UK median AOV');formula(dash,'C41','=Source!Q24');
text(dash,'A42','Median difference');formula(dash,'C42','=Source!Q25');text(dash,'E42','95% interval');formula(dash,'F42','=Source!Q26');formula(dash,'G42','=Source!Q27');
dash.getRange('C40:C42').setNumberFormat(cash);dash.getRange('F42:G42').setNumberFormat(cash);
text(dash,'A44','One value per customer. Observational comparison. Country differences are not causal.');
text(dash,'A47','Credit share = credit value / gross positive invoice value. It is not a physical return rate.');
dash.getRange('A4:O49').format.wrapText=false;

heading(cust,'Customer review','A1:L'+lastCustomer);
text(cust,'A4','Customer ID');text(cust,'B4',d.customers[0][0]);input(cust,'B4');
text(cust,'D4','Net invoice value');formula(cust,'F4',`=IF(COUNTIFS($A$9:$A$${lastCustomer},$B$4)=0,"No customer",INDEX($G$9:$G$${lastCustomer},MATCH($B$4,$A$9:$A$${lastCustomer},0)))`);cust.getRange('F4').setNumberFormat(cash);
text(cust,'D5','Review category');formula(cust,'F5',`=IF(COUNTIFS($A$9:$A$${lastCustomer},$B$4)=0,"No customer",INDEX($H$9:$H$${lastCustomer},MATCH($B$4,$A$9:$A$${lastCustomer},0)))`);
text(cust,'I1','Identified gross sales GBP');formula(cust,'K2',`=SUM(E9:E${lastCustomer})`);cust.getRange('K2').setNumberFormat(cash);
text(cust,'A6','Snapshot: 1 December 2011. Review thresholds are editable on Dashboard.');
cust.getRange('A8:J8').values=[['Customer ID','Market','Recency days','Positive invoices','Gross GBP','Credits GBP','Net GBP','Review category','Gross share','Value order']];header(cust,'A8:J8');
cust.getRange('A9:F'+lastCustomer).values=d.customers;
cust.getRange('J9:J'+lastCustomer).values=d.customers.map((_,i)=>[i+1]);
const formulas=d.customers.map((r,i)=>{let row=i+9;return [`=E${row}-F${row}`,`=IF(C${row}="","No positive order",IF(AND(C${row}<=Dashboard!$M$5,D${row}>=Dashboard!$M$6,G${row}>=Dashboard!$M$7),"Review for retention","Monitor"))`,`=E${row}/$K$2`];});
cust.getRange('G9:I'+lastCustomer).formulas=formulas;
cust.getRange('E9:G'+lastCustomer).setNumberFormat(cash);cust.getRange('I9:I'+lastCustomer).setNumberFormat(pct);
cust.getRange('B8:B'+lastCustomer).format.columnWidth=23;cust.getRange('H8:H'+lastCustomer).format.columnWidth=25;
cust.freezePanes.freezeRows(8);cust.tables.add('A8:J'+lastCustomer,true,'CustomerReviewTable');
cust.getRange('H9:H'+lastCustomer).conditionalFormats.add('containsText',{text:'Review for retention',format:{fill:'#DCFCE7'}});

heading(piv,'Market and monthly PivotTables','A1:K55');
text(piv,'A4','All markets. Native PivotTables use the prepared source table. Refresh after replacing source rows.');
const sortedMarkets=d.markets.slice(1).sort((a,b)=>a[0]<b[0]?-1:a[0]>b[0]?1:0);
piv.getRange('A6:B6').values=[['Market','Gross sales GBP']];header(piv,'A6:B6');
piv.getRange('A7:B'+(6+sortedMarkets.length)).values=sortedMarkets.map(r=>[r[0],r[1]]);
text(piv,'A'+(7+sortedMarkets.length),'Grand Total');text(piv,'B'+(7+sortedMarkets.length),d.kpis.gross_sales_gbp);
piv.getRange('A6:A45').format.columnWidth=24;piv.getRange('B7:B45').setNumberFormat(cash);
piv.getRange('D6:E6').values=[['Month','Net invoice value GBP']];header(piv,'D6:E6');
piv.getRange('D7:E17').values=d.months.map(m=>[serial(m),d.source_rows.filter(r=>r[0]===m).reduce((s,r)=>s+r[2]-r[3],0)]);
piv.getRange('D7:D17').setNumberFormat('mmm yyyy');piv.getRange('E7:E18').setNumberFormat(cash);
text(piv,'D18','Grand Total');text(piv,'E18',d.kpis.net_invoice_value_gbp);piv.getRange('E6:E18').format.columnWidth=25;

heading(audit,'Reconciliation checks','A1:G22');
audit.getRange('A6:E6').values=[['Check','Calculated','Independent control','Difference','Result']];header(audit,'A6:E6');
const checkRows=[
 ['Source gross total',`=SUM(Source!C7:C${end})`,'=Source!K7'],
 ['Source credit total',`=SUM(Source!D7:D${end})`,'=Source!L7'],
 ['Source net total',`=SUM(Source!E7:E${end})`,'=Source!M7'],
 ['Selected monthly net','=Dashboard!D25',`=IF(Dashboard!D5<>"Ready","n.a.",INDEX(Source!$M$7:$M$${lastMarket},MATCH(Dashboard!B5,Source!$J$7:$J$${lastMarket},0)))`],
 ['Identified gross',`=SUM(Customers!E9:E${lastCustomer})`,'=Source!Q14'],
 ['Top 1% gross share','=Dashboard!C33','=Source!Q15'],
 ['Market PivotTable total',`='Market pivots'!B${7+sortedMarkets.length}`,'=Source!K7'],
 ['Month PivotTable total',"='Market pivots'!E18",'=Source!M7']
];
checkRows.forEach((r,i)=>{let row=i+7;text(audit,'A'+row,r[0]);formula(audit,'B'+row,r[1]);formula(audit,'C'+row,r[2]);formula(audit,'D'+row,`=IF(AND(ISNUMBER(B${row}),ISNUMBER(C${row})),B${row}-C${row},"n.a.")`);formula(audit,'E'+row,`=IF(ISNUMBER(D${row}),IF(ABS(D${row})<0.005,"PASS","CHECK"),"CHECK")`);});
audit.getRange('A6:A18').format.columnWidth=30;audit.getRange('B7:D14').setNumberFormat('#,##0.000000');
audit.getRange('E7:E14').conditionalFormats.add('containsText',{text:'CHECK',format:{fill:'#FEE2E2',font:{color:'#B91C1C',bold:true}}});
text(audit,'A18','Checks read business calculations. No report or customer rule depends on this sheet.');

heading(readme,'Definitions and refresh','A1:J33');readme.getRange('A1:J33').format.columnWidth=15;
const lines=[
 ['A5','Purpose: simulated monthly commercial review for Finance, Sales and CRM users.'],
 ['A7','Reporting period: 1 January 2011 to 30 November 2011. December 2011 is incomplete.'],
 ['A9','Gross sales: sum of positive line values. Credits: absolute value of negative line values.'],
 ['A10','Net invoice value = gross sales less credits. Values include invoice charges and are not profit.'],
 ['A12','A positive invoice counts once when it contains positive value. Credits are not linked to original orders.'],
 ['A14','Missing customer IDs stay in market totals. Customer concentration uses identified customers only.'],
 ['A15','Identical source rows are retained because the source has no unique line ID proving duplication.'],
 ['A17','Customer AOV: positive billed value / positive invoices for each identified customer.'],
 ['A18','Mann-Whitney U compares those customer-level values. Bootstrap intervals resample customers.'],
 ['A19','The comparison is observational and does not establish a causal market effect.'],
 ['A21','The retention review rule is a configurable example, not a trained or validated churn model.'],
 ['A23','Refresh: run src/pipeline.py, then the artifact-tool workbook builder and PivotTable packaging step.'],
 ['A24','Source CSVs, SQL, tests and the simulated requirements matrix are supplied in the project.'],
 ['A26','Native PivotTables are supported with explicit Open XML caches. See validation evidence for scope.'],
 ['A28','Source: D. Chen (2015), Online Retail, UCI Machine Learning Repository. CC BY 4.0.'],
 ['A29','https://archive.ics.uci.edu/dataset/352/online-retail'],
 ['A31','Historical portfolio analysis. Recommendations are proposed actions, not measured business outcomes.']
];lines.forEach(r=>text(readme,r[0],r[1]));

// Test live business controls before restoring the saved state.
const baseline=dash.getRange('D25').values[0][0];
text(dash,'B5','Germany');wb.recalculate();
const german=dash.getRange('D25').values[0][0];const expectedGermany=d.markets.find(r=>r[0]==='Germany')[3];
if(Math.abs(german-expectedGermany)>.005)throw new Error('Germany filter reconciliation failed: '+german);
text(dash,'B5','');wb.recalculate();if(dash.getRange('D25').values[0][0]!=='n.a.')throw new Error('Blank market was hidden as zero');
text(dash,'B5','NOT_A_MARKET');wb.recalculate();if(dash.getRange('A9').values[0][0]!=='n.a.')throw new Error('Invalid market guard failed');
text(dash,'B5','All markets');
const firstCustomer=cust.getRange('B4').values[0][0];text(cust,'B4','UNKNOWN');wb.recalculate();if(cust.getRange('F4').values[0][0]!=='No customer')throw new Error('Unknown ID not exposed');text(cust,'B4',firstCustomer);
const before=cust.getRange('H9').values[0][0];text(dash,'M6',365);wb.recalculate();const after=cust.getRange('H9').values[0][0];text(dash,'M6',5);
wb.recalculate();
if(Math.abs(dash.getRange('D25').values[0][0]-d.kpis.net_invoice_value_gbp)>.005)throw new Error('Net total mismatch');
if(Math.abs(dash.getRange('C33').values[0][0]-d.kpis.top_one_percent_gross_share)>1e-10)throw new Error('Customer concentration mismatch');
const statuses=audit.getRange('E7:E14').values.flat();if(!statuses.every(x=>x==='PASS'))throw new Error('Audit failed '+JSON.stringify(statuses));
const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:30},summary:'Formula error scan'});
await fs.writeFile(path.join(work,'formula-scan.ndjson'),errors.ndjson);
await fs.writeFile(path.join(root,'reports/workbook_calculation_checks.json'),JSON.stringify({engine:'artifact-tool',net_value:dash.getRange('D25').values[0][0],germany_filter_value:german,germany_independent_value:expectedGermany,blank_market_checked:true,unknown_market_checked:true,unknown_customer_checked:true,customer_rule_before:before,customer_rule_after:after,reconciliations:statuses,formula_scan:errors.ndjson},null,2));
if(process.env.RETAIL_RENDER==='1'){
  for(const [sheetName,range] of [['Dashboard','A1:P49'],['Customers','A1:L19'],['Market pivots','A1:F45'],['Source','A1:H19'],['Audit','A1:F20'],['Readme','A1:J33']]){
    const png=await wb.render({sheetName,range,scale:1.4,format:'png'});
    await fs.writeFile(path.join(work,sheetName.replaceAll(' ','-')+'.png'),new Uint8Array(await png.arrayBuffer()));
  }
}
const output=await SpreadsheetFile.exportXlsx(wb);await output.save(path.join(root,'workbook/Retail_Sales_Customer_Analytics.xlsx'));
console.log('Workbook exported. Net GBP '+dash.getRange('D25').values[0][0]+'. Germany filter and all reconciliation checks passed.');
