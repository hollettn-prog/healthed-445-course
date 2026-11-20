#!/usr/bin/env python3
"""Build experimental Common Cartridge with webcontent resources (not guaranteed Canvas Pages)."""
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile, ZIP_DEFLATED
root=Path(__file__).resolve().parents[1]
files=sorted((root/'modules').glob('module-*/**/*.html'))
if not files: raise SystemExit('No HTML files found')
ns='http://www.imsglobal.org/xsd/imsccv1p1/imscp_v1p1'
ET.register_namespace('',ns)
q=lambda tag:f'{{{ns}}}{tag}'
manifest=ET.Element(q('manifest'),{'identifier':'healthed445-course'})
meta=ET.SubElement(manifest,q('metadata'))
ET.SubElement(meta,q('schema')).text='IMS Common Cartridge'
ET.SubElement(meta,q('schemaversion')).text='1.1.0'
orgs=ET.SubElement(manifest,q('organizations'))
org=ET.SubElement(orgs,q('organization'),{'identifier':'course-outline','structure':'rooted-hierarchy'})
ET.SubElement(org,q('title')).text='HEALTHED 445 (sandbox test)'
resources=ET.SubElement(manifest,q('resources'))
for i,f in enumerate(files,1):
    rel=f.relative_to(root).as_posix()
    rid=f'resource-{i}'
    item=ET.SubElement(org,q('item'),{'identifier':f'item-{i}','identifierref':rid})
    ET.SubElement(item,q('title')).text=f'{f.parent.name}: {f.stem.replace("-"," ").title()}'
    resource=ET.SubElement(resources,q('resource'),{'identifier':rid,'type':'webcontent','href':rel})
    ET.SubElement(resource,q('file'),{'href':rel})
out=root/'dist/HEALTHED-445-sandbox-test.imscc';out.parent.mkdir(exist_ok=True)
with ZipFile(out,'w',ZIP_DEFLATED) as z:
    z.writestr('imsmanifest.xml',ET.tostring(manifest,encoding='utf-8',xml_declaration=True))
    for f in files:z.write(f,f.relative_to(root).as_posix())
print(f'Built {out} with {len(files)} HTML resource(s)')
