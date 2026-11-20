from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED, is_zipfile
import xml.etree.ElementTree as ET
import hashlib, html, re, sys

ROOT = Path(__file__).resolve().parent.parent
MODULES = ROOT / 'modules'
DIST = ROOT / 'dist'
OUTPUT = DIST / 'HEALTHED-445-native-pages.imscc'
CC = 'http://www.imsglobal.org/xsd/imsccv1p1/imscp_v1p1'
CV = 'http://canvas.instructure.com/xsd/cccv1p0'
ET.register_namespace('', CC)
ET.register_namespace('canvas', CV)

def el(parent, name, value=None, ns=CC, **attrs):
    item = ET.SubElement(parent, '{%s}%s' % (ns, name), attrs)
    if value is not None:
        item.text = str(value)
    return item

def sid(value):
    return 'g' + hashlib.sha256(value.encode('utf-8')).hexdigest()[:24]

def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')

def title_for(path, num):
    names = {'introduction': 'Introduction, Resources, To-Dos',
             'learning-materials': 'Learning Materials',
             'discussion': 'Discussion'}
    return 'M%d %s' % (num, names.get(path.stem, path.stem.replace('-', ' ').title()))

def xml(root):
    return ET.tostring(root, encoding='utf-8', xml_declaration=True)

def build():
    files = sorted(MODULES.glob('module-*/*.html'))
    pages = []
    for file in files:
        match = re.fullmatch(r'module-(\d+)', file.parent.name)
        if match:
            pages.append((int(match.group(1)), file))
    if not pages:
        sys.exit('ERROR: No HTML files in modules/module-XX/ folders.')

    manifest = ET.Element('{%s}manifest' % CC, {'identifier': sid('HEALTHED445')})
    md = el(manifest, 'metadata')
    el(md, 'schema', 'IMS Common Cartridge')
    el(md, 'schemaversion', '1.1.0')
    orgs = el(manifest, 'organizations')
    org = el(orgs, 'organization', identifier='org1', structure='rooted-hierarchy')
    root_item = el(org, 'item', identifier='LearningModules')
    el(root_item, 'title', 'Learning Modules')
    resources = el(manifest, 'resources')
    canvas_modules = ET.Element('{%s}modules' % CV)
    grouped = {}
    for n, p in pages:
        grouped.setdefault(n, []).append(p)

    entries = {}
    for number, module_files in sorted(grouped.items()):
        mid = sid('module-%d' % number)
        org_module = el(root_item, 'item', identifier=mid)
        el(org_module, 'title', 'Module %d' % number)
        cm = el(canvas_modules, 'module', ns=CV, identifier=mid)
        el(cm, 'title', 'Module %d' % number, ns=CV)
        el(cm, 'workflow_state', 'unpublished', ns=CV)
        el(cm, 'position', number, ns=CV)
        items = el(cm, 'items', ns=CV)
        for position, path in enumerate(module_files, 1):
            title = title_for(path, number)
            rel = path.relative_to(MODULES).as_posix()
            pid = sid('page:' + rel)
            iid = sid('item:' + rel)
            slug = slugify(title)
            href = 'wiki_content/%s.html' % slug
            resource = el(resources, 'resource', identifier=pid, type='webcontent', href=href)
            el(resource, 'file', href=href)
            org_item = el(org_module, 'item', identifier=iid, identifierref=pid)
            el(org_item, 'title', title)
            ci = el(items, 'item', ns=CV, identifier=iid)
            for key, val in [('content_type', 'WikiPage'), ('workflow_state', 'active'),
                             ('title', title), ('identifierref', pid), ('position', position), ('indent', 0)]:
                el(ci, key, val, ns=CV)
            body = path.read_text(encoding='utf-8')
            head = ('<!DOCTYPE html><html><head><meta charset="utf-8">'
                    '<title>%s</title><meta name="identifier" content="%s">'
                    '<meta name="editing_roles" content="teachers">'
                    '<meta name="workflow_state" content="unpublished">'
                    '</head><body>') % (html.escape(title), pid)
            entries[href] = (head + body + '</body></html>').encode('utf-8')

    course = ET.Element('{%s}course' % CV, {'identifier': sid('course')})
    el(course, 'title', 'HEALTHED 445 Sandbox Content', ns=CV)
    el(course, 'course_code', 'HEALTHED 445', ns=CV)
    el(course, 'default_view', 'modules', ns=CV)
    settings = {
        'course_settings/course_settings.xml': xml(course),
        'course_settings/module_meta.xml': xml(canvas_modules),
        'course_settings/canvas_export.txt': b'Canvas export package\n',
    }
    assoc = el(resources, 'resource', identifier=sid('settings'),
               type='associatedcontent/imscc_xmlv1p1/learning-application-resource',
               href='course_settings/canvas_export.txt')
    for name in settings:
        el(assoc, 'file', href=name)

    DIST.mkdir(parents=True, exist_ok=True)
    with ZipFile(OUTPUT, 'w', ZIP_DEFLATED) as z:
        z.writestr('imsmanifest.xml', xml(manifest))
        for name, data in entries.items():
            z.writestr(name, data)
        for name, data in settings.items():
            z.writestr(name, data)
    if not is_zipfile(OUTPUT):
        sys.exit('ERROR: output is not a valid ZIP container')
    with ZipFile(OUTPUT) as z:
        if z.testzip() is not None:
            sys.exit('ERROR: corrupt ZIP member')
        ET.fromstring(z.read('imsmanifest.xml'))
        ET.fromstring(z.read('course_settings/module_meta.xml'))
        for name in entries:
            assert name in z.namelist(), 'Missing page: ' + name
    print('SUCCESS:', OUTPUT)
    print('Native pages:', len(entries), '| Modules:', len(grouped))
    print('Upload the .imscc file inside the GitHub artifact ZIP, not the artifact ZIP itself.')

if __name__ == '__main__':
