#!/usr/bin/env python3

import argparse
import base64
import json
import re
from pathlib import Path


def extract_figures(notebook_path: Path, output_dir: Path) -> int:
    notebook = json.loads(notebook_path.read_text())
    output_dir.mkdir(parents=True, exist_ok=True)

    current_figure = None
    extracted = 0

    for cell in notebook.get("cells", []):
        cell_type = cell.get("cell_type")
        source = "".join(cell.get("source", []))

        if cell_type == "markdown":
            match = re.search(r"## Figure (\d+)", source)
            if match:
                current_figure = match.group(1)
            continue

        if cell_type != "code" or current_figure is None:
            continue

        for output in cell.get("outputs", []):
            png_data = output.get("data", {}).get("image/png")
            if not png_data:
                continue

            if isinstance(png_data, list):
                png_data = "".join(png_data)

            target = output_dir / f"figure{current_figure}.png"
            target.write_bytes(base64.b64decode(png_data))
            extracted += 1
            break

    return extracted


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract embedded figure PNGs from a Jupyter notebook."
    )
    parser.add_argument(
        "notebook",
        nargs="?",
        default=Path(__file__).with_name("plotting.ipynb"),
        type=Path,
        help="Path to the notebook file.",
    )
    parser.add_argument(
        "--output-dir",
        default=Path(__file__).with_name("figures"),
        type=Path,
        help="Directory where extracted PNGs will be written.",
    )
    args = parser.parse_args()

    extracted = extract_figures(args.notebook, args.output_dir)
    print(f"Extracted {extracted} figure(s) to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
