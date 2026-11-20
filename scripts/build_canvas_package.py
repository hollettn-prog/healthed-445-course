
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import xml.etree.ElementTree as ET
import hashlib
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
MODULES = ROOT / "modules"
DIST = ROOT / "dist"
OUTPUT = DIST / "HEALTHED-445-canvas-pages.imscc"

CC = "http://www.imsglobal.org/xsd/imsccv1p1/imscp_v1p1"
CV = "http://canvas.instructure.com/xsd/cccv1p0"

ET.register_namespace("", CC)

def node(parent, name, text=None, ns=None, **attrs):
    element = ET.SubElement(
        parent, f"{{{ns or CC}}}{name}", attrs
    )
    if text is not None:
        element.text = str(text)
    return element

def stable_id(value):
    digest = hashlib.md5(
        value.encode("utf-8")
    ).hexdigest()
    return "g" + digest

def module_number(path):
    match = re.fullmatch(r"module-(\d+)", path.name)
    return int(match.group(1)) if match else None

def page_title(path, number):
    if path.stem == "introduction":
        return f"M{number} Introduction, Resources, To-Dos"
    return f"M{number} " + path.stem.replace(
        "-", " "
    ).replace("_", " ").title()

def xml_bytes(element):
    return ET.tostring(
        element,
        encoding="utf-8",
        xml_declaration=True
    )

def main():
    pages = sorted(MODULES.glob("module-*/*.html"))

    if not pages:
        sys.exit("ERROR: No module HTML pages found.")

    DIST.mkdir(parents=True, exist_ok=True)

    manifest = ET.Element(
        f"{{{CC}}}manifest",
        {"identifier": stable_id("HEALTHED445-manifest")}
    )

    metadata = node(manifest, "metadata")
    node(metadata, "schema", "IMS Common Cartridge")
    node(metadata, "schemaversion", "1.1.0")

    organizations = node(manifest, "organizations")
    organization = node(
        organizations, "organization",
        identifier="org_1",
        structure="rooted-hierarchy"
    )
    wrapper = node(
        organization, "item",
        identifier="LearningModules"
    )
    node(wrapper, "title", "Learning Modules")

    resources = node(manifest, "resources")

    module_root = ET.Element(f"{{{CV}}}modules")
    grouped = {}

    for page in pages:
        number = module_number(page.parent)
        if number is None:
            continue
        grouped.setdefault(number, []).append(page)

    if not grouped:
        sys.exit("ERROR: No valid module folders found.")

    contents = {}

    for number, files in sorted(grouped.items()):
        module_title = f"Module {number}"
        module_id = stable_id(
            f"HEALTHED445-module-{number}"
        )

        org_module = node(
            wrapper, "item",
            identifier=module_id
        )
        node(org_module, "title", module_title)

        canvas_module = node(
            module_root, "module",
            ns=CV,
            identifier=module_id
        )
        node(canvas_module, "title", module_title, ns=CV)
        node(
            canvas_module, "workflow_state",
            "unpublished", ns=CV
        )
        node(canvas_module, "position", number, ns=CV)
        items = node(canvas_module, "items", ns=CV)

        for position, page in enumerate(files, 1):
            title = page_title(page, number)
            relative = page.relative_to(MODULES).as_posix()
            page_id = stable_id("page:" + relative)
            item_id = stable_id("item:" + relative)

            slug = re.sub(
                r"[^a-z0-9]+", "-",
                title.lower()
            ).strip("-")

            href = f"wiki_content/{slug}.html"

            resource = node(
                resources, "resource",
                identifier=page_id,
                type="webcontent",
                href=href
            )
            node(resource, "file", href=href)

            org_item = node(
                org_module, "item",
                identifier=item_id,
                identifierref=page_id
            )
            node(org_item, "title", title)

            canvas_item = node(
                items, "item",
                ns=CV,
                identifier=item_id
            )
            for key, value in [
                ("content_type", "WikiPage"),
                ("workflow_state", "active"),
                ("title", title),
                ("identifierref", page_id),
                ("position", position),
                ("indent", 0)
            ]:
                node(canvas_item, key, value, ns=CV)

            body = page.read_text(encoding="utf-8")

            head = (
                "<!DOCTYPE html><html><head>"
                '<meta charset="utf-8">'
                f"<title>{title}</title>"
                f'<meta name="identifier" content="{page_id}">'
                '<meta name="editing_roles" content="teachers">'
                '<meta name="workflow_state" '
                'content="unpublished">'
                "</head><body>"
            )
            contents[href] = (
                head + body + "</body></html>"
            )

    settings_root = ET.Element(
        f"{{{CV}}}course",
        {"identifier": stable_id("HEALTHED445-course")}
    )
    node(
        settings_root, "title",
        "HEALTHED 445 Sandbox Content", ns=CV
    )
    node(
        settings_root, "course_code",
        "HEALTHED 445", ns=CV
    )
    node(
        settings_root, "default_view",
        "modules", ns=CV
    )

    settings = {
        "course_settings/course_settings.xml":
            xml_bytes(settings_root),
        "course_settings/module_meta.xml":
            xml_bytes(module_root),
        "course_settings/canvas_export.txt":
            "Q: What did the panda say when he was "
            "forced out of his natural habitat?\n"
            "A: This is un-BEAR-able\n"
    }

    bundle = node(
        resources, "resource",
        identifier=stable_id("course-settings-bundle"),
        type=(
            "associatedcontent/imscc_xmlv1p1/"
            "learning-application-resource"
        ),
        href="course_settings/canvas_export.txt"
    )

    for path in settings:
        node(bundle, "file", href=path)

    with ZipFile(OUTPUT, "w", ZIP_DEFLATED) as archive:
        archive.writestr(
            "imsmanifest.xml", xml_bytes(manifest)
        )
        for path, content in contents.items():
            archive.writestr(path, content)
        for path, content in settings.items():
            archive.writestr(path, content)

    print(f"Created: {OUTPUT}")
    print(f"Modules: {len(grouped)}")
    print(f"Pages: {len(contents)}")

if __name__ == "__main__":
    main()
