# HEALTHED 445 Course Development

Course HTML and experimental Canvas Common Cartridge package builder. Keep student data out of this repository.

## Get started

1. Upload the contents of this ZIP to the root of `hollettn-prog/healthed-445-course` using GitHub **Add file → Upload files**. GitHub may not accept folder uploads through every browser; extracting and dragging the folders into the upload page is easiest. Ensure `.github/workflows/build-canvas.yml` is uploaded (hidden folders may require using Git locally).
2. Open **Actions → Build Canvas Package → Run workflow**. Enable Actions if prompted.
3. Open the completed run, download the `healthed-445-canvas-package` artifact, and unzip it to find `HEALTHED-445-sandbox-test.imscc`.
4. In your **Canvas sandbox**, go to **Settings → Import Course Content → Common Cartridge 1.x Package** and upload the `.imscc` file.
5. Inspect **Files**, **Pages**, and **Modules**. This starter uses standard Common Cartridge `webcontent` resources, so Canvas may import the HTML as Files rather than native Canvas Pages. **It has not been tested in your Canvas instance.** Do not use on a live course until native Pages/Modules behavior is verified and adjusted.

## Editing

Edit `modules/module-02/introduction.html` and commit. The workflow builds a new test package. Other module folders are placeholders, not approved course content.

## Important

This is a **sandbox prototype**, not a validated native Canvas Pages importer. Links and video placeholders need instructor review. Existing `healthed445-interactives` stays unchanged. No Canvas API token needed.
