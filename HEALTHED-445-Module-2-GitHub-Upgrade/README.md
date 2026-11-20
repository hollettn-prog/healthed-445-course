# HEALTHED 445 course package upgrade

This ZIP is a **draft development package**, not a verified export of your live Canvas course.

## Included
- Module 2 Introduction, Learning Materials, and Discussion draft pages.
- `course-map.json` controls page sequence and navigation.
- Python IMSCC exporter and GitHub Actions workflow.
- Empty development folders for Modules 1 and 3 through 9.

## Upload to GitHub
1. Unzip this package. Upload its **contents**, not the enclosing folder, into `hollettn-prog/healthed-445-course` on `main`. Preserve `.github/workflows/`.
2. Replace the existing `scripts/build_canvas_package.py` and workflow file when prompted. Keep your existing repository history.
3. Run Actions > Build Canvas Package and download the artifact ZIP. Extract the `.imscc`.
4. Import into a **fresh Canvas sandbox** using Settings > Import Course Content > Common Cartridge 1.x Package.
5. Inspect Pages and Modules. Verify page order, formatting, UP NEXT links, and unpublished status. Some Canvas imports may rewrite page slugs; if links fail, use the actual Canvas page URLs.

## Content and platform boundaries
- The M2 Learning Materials page is a new **draft**, not a transcription of existing course materials.
- The discussion is an instructional draft page, **not a Canvas Discussion assignment**. Create the actual graded/ungraded Canvas discussion separately and link it.
- The existing knowledge check remains in `healthed445-interactives`; this package does not recreate or alter it.
- Video and NHES links require instructor setup. No dates, grading rules, or NHES indicator numbers are invented.
- The exporter uses Canvas-specific Common Cartridge extensions; successful native page and module import must be verified in your sandbox.
- Generated navigation uses `/courses/{course_id}/pages/<slug>` placeholders, which Canvas may or may not resolve during import. Verify before publishing.
- No student data or API token is required.
