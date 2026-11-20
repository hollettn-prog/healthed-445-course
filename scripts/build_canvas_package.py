
def title(path, number):
    names = {
        'introduction': 'Introduction, Resources, To-Dos',
        'learning-materials': 'Learning Materials',
        'discussion': 'Discussion',
    }
    return f'M{number} ' + names.get(path.stem, path.stem.replace('-', ' ').title())

def serialize(node):
    return ET.tostring(node, encoding='utf-8', xml_declaration=True)

def build():
    found = []
    for path in sorted(MODULES.glob('module-*/*.html')):
        match = re.fullmatch(r'module-(\d+)', path.parent.name)
        if match:
            found.append((int(match.group(1)), path))
    if not found:
        sys.exit('ERROR: No HTML pages found under modules/module-XX/')

    grouped = {}
    for number, path in found:
        grouped.setdefault(number, []).append(path)

    manifest = ET.Element('{%s}manifest' % CC, {'identifier': ident('manifest:healthed445')})
    metadata = elem(manifest, 'metadata')
    elem(metadata, 'schema', 'IMS Common Cartridge')
    elem(metadata, 'schemaversion', '1.1.0')
    orgs = elem(manifest, 'organizations')
    org = elem(orgs, 'organization', identifier='org_1', structure='rooted-hierarchy')
    root_item = elem(org, 'item', identifier='LearningModules')
    resources = elem(manifest, 'resources')
    module_meta = ET.Element('{%s}modules' % CV, {
        '{%s}schemaLocation' % XSI: CV + ' https://canvas.instructure.com/xsd/cccv1p0.xsd'
    })
    entries = {}
    page_count = 0
    used_slugs = set()
    for number, paths in sorted(grouped.items()):
        module_id = ident(f'module:{number}')
        org_module = elem(root_item, 'item', identifier=module_id)
        elem(org_module, 'title', f'Module {number}')
        cm = elem(module_meta, 'module', namespace=CV, identifier=module_id)
        elem(cm, 'title', f'Module {number}', namespace=CV)
        elem(cm, 'workflow_state', 'unpublished', namespace=CV)
        elem(cm, 'position', number, namespace=CV)
        elem(cm, 'require_sequential_progress', 'false', namespace=CV)
        elem(cm, 'locked', 'false', namespace=CV)
        items = elem(cm, 'items', namespace=CV)
        # Explicit pedagogical sequence, then remaining filenames.
        priority = {'introduction': 0, 'learning-materials': 1, 'discussion': 3}
        paths.sort(key=lambda p: (priority.get(p.stem, 2), p.name))
        for position, path in enumerate(paths, 1):
            name = title(path, number)
            relative = path.relative_to(MODULES).as_posix()
            resource_id = ident('page:' + relative)
            item_id = ident('item:' + relative)
            page_slug = slug(name)
            if page_slug in used_slugs:
                sys.exit('ERROR: duplicate page slug: ' + page_slug)
            used_slugs.add(page_slug)
            href = f'wiki_content/{page_slug}.html'
            resource = elem(resources, 'resource', identifier=resource_id, type='webcontent', href=href)
            elem(resource, 'file', href=href)
            oi = elem(org_module, 'item', identifier=item_id, identifierref=resource_id)
            elem(oi, 'title', name)
            ci = elem(items, 'item', namespace=CV, identifier=item_id)
            for key, value in (
                ('content_type', 'WikiPage'), ('workflow_state', 'unpublished'),
                ('title', name), ('identifierref', resource_id),
                ('position', position), ('indent', 0),
            ):
                elem(ci, key, value, namespace=CV)
            elem(ci, 'new_tab', namespace=CV)
            elem(ci, 'link_settings_json', 'null', namespace=CV)
            body = path.read_text(encoding='utf-8')
            if not body.strip():
                sys.exit('ERROR: Empty page: ' + relative)
            head = ('<html><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>'
                    f'<title>{html.escape(name)}</title>'
                    f'<meta name="identifier" content="{resource_id}"/>'
                    '<meta name="editing_roles" content="teachers"/>'
                    '<meta name="workflow_state" content="unpublished"/>'
                    '<meta name="editor_type" content="rce"/>'
                    '</head><body>')
            entries[href] = (head + body + '</body></html>').encode('utf-8')
            page_count += 1

    course_id = ident('course:healthed445')
    course = ET.Element('{%s}course' % CV, {
        'identifier': course_id,
        '{%s}schemaLocation' % XSI: CV + ' https://canvas.instructure.com/xsd/cccv1p0.xsd'
    })
    elem(course, 'title', 'HEALTHED 445 Sandbox Content', namespace=CV)
    elem(course, 'course_code', 'HEALTHED 445', namespace=CV)
    # Do not set default_view: never alter sandbox home page during a test import.
    settings = {
        'course_settings/course_settings.xml': serialize(course),
        'course_settings/module_meta.xml': serialize(module_meta),
        'course_settings/canvas_export.txt': b'Canvas export package\n',
    }
    assoc = elem(resources, 'resource', identifier=ident('course:settings'),
                 type='associatedcontent/imscc_xmlv1p1/learning-application-resource',
                 href='course_settings/canvas_export.txt')
    for name in settings:
        elem(assoc, 'file', href=name)
    DIST.mkdir(parents=True, exist_ok=True)
    with ZipFile(OUTPUT, 'w', ZIP_DEFLATED) as archive:
        archive.writestr('imsmanifest.xml', serialize(manifest))
        for name, content in entries.items():
            archive.writestr(name, content)
        for name, content in settings.items():
            archive.writestr(name, content)
    if not is_zipfile(OUTPUT):
        sys.exit('ERROR: IMSCC is not a ZIP archive')
    with ZipFile(OUTPUT) as archive:
        if archive.testzip() is not None:
            sys.exit('ERROR: corrupt archive member')
        ET.fromstring(archive.read('imsmanifest.xml'))
        ET.fromstring(archive.read('course_settings/module_meta.xml'))
        for name in entries:
            if name not in archive.namelist():
                sys.exit('ERROR: missing page: ' + name)
    print(f'SUCCESS: {OUTPUT}')
    print(f'Modules: {len(grouped)}; pages: {page_count}')
    print('Canvas import still requires sandbox verification.')

if __name__ == "__main__":
    build()

