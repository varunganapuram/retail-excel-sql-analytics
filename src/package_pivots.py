"""Add native PivotTable parts where artifact-tool's pivot export is unsupported.

Normal sheets, cells, styles, formulas and charts are authored by artifact-tool.
This compatibility step adds only PivotTable definitions, caches and relationships.
Reference: learn.microsoft.com/office/open-xml/spreadsheet/working-with-pivottables
"""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import json
import xml.etree.ElementTree as ET
from datetime import datetime

ROOT=Path(__file__).resolve().parents[1]
S='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
P='http://schemas.openxmlformats.org/package/2006/relationships'
C='http://schemas.openxmlformats.org/package/2006/content-types'
ET.register_namespace('',S);ET.register_namespace('r',R)
def tag(name):return '{'+S+'}'+name
def sub(parent,element_name,**attrs):return ET.SubElement(parent,tag(element_name),{k:str(v) for k,v in attrs.items()})
def xml(element):
    # OPC readers expect unprefixed Types/Relationships roots with default namespaces.
    ET.register_namespace('',element.tag.split('}')[0].lstrip('{'))
    return ET.tostring(element,encoding='utf-8',xml_declaration=True)
def serial(value):return (datetime.fromisoformat(value)-datetime(1899,12,30)).days

def main():
    path=ROOT/'workbook/Retail_Sales_Customer_Analytics.xlsx'
    with ZipFile(path) as z:parts={n:z.read(n) for n in z.namelist()}
    if 'xl/pivotTables/pivotTable1.xml' in parts:
        raise ValueError('PivotTables already packaged. Rebuild the workbook before packaging again.')
    d=json.loads((ROOT/'data/processed/workbook_inputs.json').read_text())
    rows=[[serial(r[0]),r[1],r[2],r[3],round(r[2]-r[3],2),r[4],r[5],r[6]] for r in d['source_rows']]
    labels=['Month','Country','Gross GBP','Credits GBP','Net GBP','Positive invoices','Credit invoices','Eligible lines']
    months=[serial(s) for s in d['months']];countries=sorted(d['countries'])
    shared={0:months,1:countries}
    cache=ET.Element(tag('pivotCacheDefinition'),{
        '{'+R+'}id':'rId1','recordCount':str(len(rows)),'saveData':'1','refreshOnLoad':'0',
        'enableRefresh':'1','createdVersion':'6','refreshedVersion':'6','minRefreshableVersion':'3'})
    origin=sub(cache,'cacheSource',type='worksheet');sub(origin,'worksheetSource',name='RetailMonthlySource',sheet='Source')
    fields=sub(cache,'cacheFields',count=len(labels))
    for i,label in enumerate(labels):
        field=sub(fields,'cacheField',name=label,**({'numFmtId':'17'} if i==0 else {}))
        if i in shared:
            si=sub(field,'sharedItems',count=len(shared[i]),containsString=int(i==1),containsNumber=int(i==0),containsBlank='0',containsSemiMixedTypes='0',containsNonDate='1',containsInteger=int(i==0))
            for value in shared[i]:sub(si,'s' if i==1 else 'n',v=value)
        else:
            sub(field,'sharedItems',count='0',containsString='0',containsNumber='1',containsBlank='0',containsSemiMixedTypes='0',containsNonDate='1',containsInteger=int(i>=5))
    records=ET.Element(tag('pivotCacheRecords'),{'count':str(len(rows))})
    for row in rows:
        record=sub(records,'r')
        for i,value in enumerate(row):
            sub(record,'x' if i in shared else 'n',v=shared[i].index(value) if i in shared else value)
    parts['xl/pivotCache/pivotCacheDefinition1.xml']=xml(cache)
    parts['xl/pivotCache/pivotCacheRecords1.xml']=xml(records)
    relations=ET.Element('{'+P+'}Relationships')
    ET.SubElement(relations,'{'+P+'}Relationship',Id='rId1',Type=R+'/pivotCacheRecords',Target='pivotCacheRecords1.xml')
    parts['xl/pivotCache/_rels/pivotCacheDefinition1.xml.rels']=xml(relations)

    workbook=ET.fromstring(parts['xl/workbook.xml'])
    rels=ET.fromstring(parts['xl/_rels/workbook.xml.rels'])
    rid='rIdRetailPivotCache'
    ET.SubElement(rels,'{'+P+'}Relationship',Id=rid,Type=R+'/pivotCacheDefinition',Target='pivotCache/pivotCacheDefinition1.xml')
    caches=ET.Element(tag('pivotCaches'));sub(caches,'pivotCache',cacheId='0',**{'{'+R+'}id':rid})
    # Pivot caches follow definedNames/calcPr in SpreadsheetML's workbook sequence.
    children=list(workbook)
    after={'sheets','functionGroups','externalReferences','definedNames','calcPr','oleSize','customWorkbookViews'}
    position=max((i+1 for i,c in enumerate(children) if c.tag.split('}')[-1] in after),default=len(children))
    workbook.insert(position,caches)
    parts['xl/workbook.xml']=xml(workbook);parts['xl/_rels/workbook.xml.rels']=xml(rels)
    # Sheet 3 is the existing materialized PivotTable output, authored by artifact-tool.
    sheet=ET.fromstring(parts['xl/worksheets/sheet3.xml'])
    sheetrels=ET.Element('{'+P+'}Relationships') if 'xl/worksheets/_rels/sheet3.xml.rels' not in parts else ET.fromstring(parts['xl/worksheets/_rels/sheet3.xml.rels'])
    configs=[('GrossByMarket',1,2,'Gross sales GBP',f'A6:B{7+len(countries)}'),('NetByMonth',0,4,'Net invoice value GBP','D6:E18')]
    for number,(name,row_field,value_field,caption,location) in enumerate(configs,1):
        definition=ET.Element(tag('pivotTableDefinition'),{
            'name':name,'cacheId':'0','dataCaption':caption,'rowGrandTotals':'1','colGrandTotals':'1',
            'compact':'0','compactData':'0','outline':'0','outlineData':'0','gridDropZones':'0',
            'preserveFormatting':'1','useAutoFormatting':'1','createdVersion':'6','updatedVersion':'6','minRefreshableVersion':'3'})
        sub(definition,'location',ref=location,firstHeaderRow='1',firstDataRow='1',firstDataCol='1')
        pfields=sub(definition,'pivotFields',count=len(labels))
        for i in range(len(labels)):
            attrs={'showAll':'0','defaultSubtotal':'0'}
            if i==row_field:attrs['axis']='axisRow'
            if i==value_field:attrs['dataField']='1'
            if i==0:attrs['numFmtId']='17'
            pf=sub(pfields,'pivotField',**attrs)
            if i==row_field:
                items=sub(pf,'items',count=len(shared[i])+1)
                for index in range(len(shared[i])):sub(items,'item',x=index)
                sub(items,'item',t='default')
        rfields=sub(definition,'rowFields',count='1');sub(rfields,'field',x=row_field)
        ritems=sub(definition,'rowItems',count=len(shared[row_field])+1)
        for index in range(len(shared[row_field])):sub(sub(ritems,'i'),'x',v=index)
        sub(sub(ritems,'i',t='grand'),'x')
        columns=sub(definition,'colItems',count='1');sub(columns,'i')
        datafields=sub(definition,'dataFields',count='1');sub(datafields,'dataField',name=caption,fld=value_field,subtotal='sum',baseField='0',baseItem='0',numFmtId='4')
        sub(definition,'pivotTableStyleInfo',name='PivotStyleLight16',showRowHeaders='1',showColHeaders='1',showRowStripes='0',showColStripes='0')
        parts[f'xl/pivotTables/pivotTable{number}.xml']=xml(definition)
        pr=ET.Element('{'+P+'}Relationships')
        ET.SubElement(pr,'{'+P+'}Relationship',Id='rId1',Type=R+'/pivotCacheDefinition',Target='../pivotCache/pivotCacheDefinition1.xml')
        parts[f'xl/pivotTables/_rels/pivotTable{number}.xml.rels']=xml(pr)
        link=f'rIdNativePivot{number}'
        ET.SubElement(sheetrels,'{'+P+'}Relationship',Id=link,Type=R+'/pivotTable',Target=f'../pivotTables/pivotTable{number}.xml')
    parts['xl/worksheets/sheet3.xml']=xml(sheet)
    parts['xl/worksheets/_rels/sheet3.xml.rels']=xml(sheetrels)
    ctypes=ET.fromstring(parts['[Content_Types].xml'])
    for name,kind in [('pivotCache/pivotCacheDefinition1.xml','pivotCacheDefinition'),('pivotCache/pivotCacheRecords1.xml','pivotCacheRecords'),('pivotTables/pivotTable1.xml','pivotTable'),('pivotTables/pivotTable2.xml','pivotTable')]:
        ET.SubElement(ctypes,'{'+C+'}Override',PartName='/xl/'+name,ContentType='application/vnd.openxmlformats-officedocument.spreadsheetml.'+kind+'+xml')
    parts['[Content_Types].xml']=xml(ctypes)
    # A readable opening zoom is an exported sheet-view setting, not a change to data.
    for name in list(parts):
        if name.startswith('xl/worksheets/sheet') and name.endswith('.xml'):
            element=ET.fromstring(parts[name])
            for view in element.findall('.//'+tag('sheetView')):view.set('zoomScale','75')
            parts[name]=xml(element)
    temporary=path.with_suffix('.tmp.xlsx')
    with ZipFile(temporary,'w',compression=ZIP_DEFLATED) as z:
        for name,data in parts.items():z.writestr(name,data)
    temporary.replace(path)
    with ZipFile(path) as z:assert z.testzip() is None
    (ROOT/'reports/native_pivot_structure.json').write_text(json.dumps(dict(pivot_tables=2,cache_records=len(rows),source_table='RetailMonthlySource',names=[c[0] for c in configs],verification='Open XML structure and cache reconciliation; native Excel refresh is checked separately'),indent=2))
    print('Packaged 2 native PivotTables and '+str(len(rows))+' cache records')

if __name__=='__main__':main()
