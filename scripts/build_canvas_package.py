
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import xml.etree.ElementTree as ET
import uuid
import sys

ROOT = Path(__file__).resolve().parent.parent
MODULES = ROOT / "modules"
DIST = ROOT / "dist"
OUTPUT = DIST / "HEALTHED-445-sandbox-test.imscc"

NS = "http://www.imsglobal.org/xsd/imsccv1p1/imscp_v1p1"
ET.register_namespace("", NS)

def tag(name):
    return f"{{{NS}}}{name}"

def main():
    pages = sorted(MODULES.glob("**/*.html"))

    if not pages:
        print("ERROR: No HTML pages found in modules/")
        print("Add a Module 2 HTML page before building.")
        sys.exit(1)

    DIST.mkdir(parents=True, exist_ok=True)

    manifest = ET.Element(tag("manifest"), {
        "identifier": "HEALTHED445"
    })

    metadata = ET.SubElement(manifest, tag("metadata"))
    ET.SubElement(metadata, tag("schema")).text = (
        "IMS Common Cartridge"
    )
    ET.SubElement(metadata, tag("schemaversion")).text = (
        "1.1.0"
    )

    organizations = ET.SubElement(
        manifest, tag("organizations")
    )
    resources = ET.SubElement(
        manifest, tag("resources")
    )

    with ZipFile(OUTPUT, "w", ZIP_DEFLATED) as archive:
        for page in pages:
            relative = page.relative_to(MODULES)
            archive_path = (
                "web_resources/" + relative.as_posix()
            )

            resource = ET.SubElement(resources, tag("resource"), {
                "identifier": "RES_" + uuid.uuid4().hex,
                "type": "webcontent",
                "href": archive_path
            })

            ET.SubElement(resource, tag("file"), {
                "href": archive_path
            })

            archive.write(page, archive_path)
            print(f"Added: {relative}")

        manifest_xml = ET.tostring(
            manifest,
            encoding="utf-8",
            xml_declaration=True
        )

        archive.writestr(
            "imsmanifest.xml",
            manifest_xml
        )

    print(f"SUCCESS: Created {OUTPUT}")

if __name__ == "__main__":
    main()
