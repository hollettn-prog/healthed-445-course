from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED, is_zipfile
import hashlib
import html
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
MODULES = ROOT / 'modules'
DIST = ROOT / 'dist'
OUTPUT = DIST / 'HEALTHED-445-native-pages.imscc'
CC = 'http://www.imsglobal.org/xsd/imsccv1p1/imscp_v1p1'
CV = 'http://canvas.instructure.com/xsd/cccv1p0'
ET.register_namespace('', CC)

def element(parent, name, value=None, namespace=CC, **attributes):
    result = ET.SubElement(parent, f'{{{namespace}}}{name}', attributes)
    if value is not None:
        result.text = str(value)
    return result

def stable_id(value):
    return 'g' + hashlib.sha256(value.encode('utf-8')).hexdigest()[:32]

def slugify(value):
    return re.sub(r'[^a-z0-9]+', '-', value.lower()).strip('-')

def page_title(path, number):
    names = {
        'introduction': 'Introduction, Resources, To-Dos',
        'learning-materials': 'Learning Materials',
        'discussion': 'Discussion',
    }
    return f'M{number} {names.get(path.stem, path.stem.replace("-", " ").title())}'

def xml_bytes(root):
    return ET.tostring(root, encoding='utf-8', xml_declaration=True)

def build():
    pages = []
    for path in sorted(MODULES.glob('module-*/*.html')):
        match = re.fullmatch(r'module-(\d+)', path.parent.name)
        if match:
            pages.append((int(match.group(1)), path))
    if not pages:
        sys.exit('ERROR: No HTML pages found under modules/module-XX/.')

    manifest = ET.Element(f'{{{CC}}}manifest', {'identifier': stable_id('healthed445')})
    metadata = element(manifest, 'metadata')
    element(metadata, 'schema', 'IMS Common Cartridge')
    element(metadata, 'schemaversion', '1.1.0')
    organizations = element(manifest, 'organizations')
    organization = element(organizations, 'organization', identifier='org_1', structure='rooted-hierarchy')
    root_item = element(organization, 'item', identifier='LearningModules')
    resources = element(manifest, 'resources')
    canvas_modules = ET.Element(f'{{{CV}}}modules')
    grouped = {}
    for number, path in pages:
        grouped.setdefault(number, []).append(path)

    files = {}
    for module_position, (number, module_pages) in enumerate(sorted(grouped.items()), 1):
        module_id = stable_id(f'module:{number}')
        module_title = f'Module {number}'
        org_module = element(root_item, 'item', identifier=module_id)
        element(org_module, 'title', module_title)
        canvas_module = element(canvas_modules, 'module', namespace=CV, identifier=module_id)
        for name, value in [('title', module_title), ('workflow_state', 'unpublished'),
                            ('position', module_position), ('require_sequential_progress', 'false'),
                            ('locked', 'false')]:
            element(canvas_module, name, value, namespace=CV)
        items = element(canvas_module, 'items', namespace=CV)

        preferred = {'introduction': 0, 'learning-materials': 1, 'discussion': 3}
        module_pages.sort(key=lambda p: (preferred.get(p.stem, 2), p.name))
        for position, path in enumerate(module_pages, 1):
            relative = path.relative_to(MODULES).as_posix()
            title = page_title(path, number)
            page_id = stable_id('page:' + relative)
            item_id = stable_id('item:' + relative)
            href = f'wiki_content/{slugify(title)}-{page_id[-8:]}.html'

            resource = element(resources, 'resource', identifier=page_id, type='webcontent', href=href)
            element(resource, 'file', href=href)
            org_item = element(org_module, 'item', identifier=item_id, identifierref=page_id)
            element(org_item, 'title', title)
            canvas_item = element(items, 'item', namespace=CV, identifier=item_id)
            for key, value in [('content_type', 'WikiPage'), ('workflow_state', 'unpublished'),
                               ('title', title), ('identifierref', page_id), ('position', position)]:
                element(canvas_item, key, value, namespace=CV)
            element(canvas_item, 'new_tab', namespace=CV)
            element(canvas_item, 'indent', 0, namespace=CV)
            element(canvas_item, 'link_settings_json', 'null', namespace=CV)

            body = path.read_text(encoding='utf-8')
            head = ('<!DOCTYPE html><html><head><meta charset="utf-8">'
                    f'<title>{html.escape(title)}</title>'
                    f'<meta name="identifier" content="{page_id}">'
                    '<meta name="editing_roles" content="teachers">'
                    '<meta name="workflow_state" content="unpublished">'
                    '</head><body>')
            files[href] = (head + body + '</body></html>').encode('utf-8')

    settings = {
        'course_settings/module_meta.xml': xml_bytes(canvas_modules),
        'course_settings/canvas_export.txt': b'Canvas export package\n',
    }
    course = ET.Element(f'{{{CV}}}course', {'identifier': stable_id('course')})
    element(course, 'title', 'HEALTHED 445 Sandbox Content', namespace=CV)
    element(course, 'course_code', 'HEALTHED 445', namespace=CV)
    settings['course_settings/course_settings.xml'] = xml_bytes(course)
    associated = element(resources, 'resource', identifier=stable_id('settings'),
                         type='associatedcontent/imscc_xmlv1p1/learning-application-resource',
                         href='course_settings/canvas_export.txt')
    for path in settings:
        element(associated, 'file', href=path)

    DIST.mkdir(parents=True, exist_ok=True)
    with ZipFile(OUTPUT, 'w', ZIP_DEFLATED) as archive:
        archive.writestr('imsmanifest.xml', xml_bytes(manifest))
        for name, data in files.items():
            archive.writestr(name, data)
        for name, data in settings.items():
            archive.writestr(name, data)

    if not is_zipfile(OUTPUT):
        sys.exit('ERROR: Output is not a ZIP archive.')
    with ZipFile(OUTPUT) as archive:
        if archive.testzip() is not None:
            sys.exit('ERROR: ZIP contains a damaged member.')
        names = set(archive.namelist())
        root = ET.fromstring(archive.read('imsmanifest.xml'))
        ET.fromstring(archive.read('course_settings/module_meta.xml'))
        for resource in root.findall(f'.//{{{CC}}}resource'):
            for file in resource.findall(f'{{{CC}}}file'):
                if file.attrib['href'] not in names:
                    sys.exit('ERROR: Missing cartridge file: ' + file.attrib['href'])
    print('SUCCESS:', OUTPUT)
    print('Pages:', len(files), 'Modules:', len(grouped))
    print('Download the GitHub artifact ZIP, extract it, and upload the .imscc file to Canvas.')

if __name__ == '__main__':
    build()
