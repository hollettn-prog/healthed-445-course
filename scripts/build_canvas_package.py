"""Compatibility entry point for the explicit course-map exporter."""
from pathlib import Path
from canvas_workflow import build
if __name__ == '__main__':
    output, report = build(Path(__file__).resolve().parents[1])
    print(output)
    print(f"{report['pages']} pages; Canvas import not yet verified")
