#!/usr/bin/env python3
"""Create contact sheets from exported Ref-GS buffers when they exist."""

import argparse
from pathlib import Path

from PIL import Image, ImageDraw


BUFFER_NAMES = [
    "gt_image.png",
    "rendered_image.png",
    "pbr_rgb.png",
    "full_rgb.png",
    "spec_light.png",
    "diff_light.png",
    "roughness.png",
    "render_normal.png",
    "surf_normal.png",
    "surf_depth.png",
    "in.png",
    "out.png",
]


def load_thumb(path: Path, size=(220, 220)):
    if not path.exists():
        img = Image.new("RGB", size, (245, 245, 245))
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), "missing", fill=(140, 0, 0))
        return img
    img = Image.open(path).convert("RGB")
    img.thumbnail(size)
    canvas = Image.new("RGB", size, (255, 255, 255))
    canvas.paste(img, ((size[0] - img.width) // 2, (size[1] - img.height) // 2))
    return canvas


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", default="result")
    parser.add_argument("--out", default="experiments/ref_gs_limitation_analysis/output_contact_sheet.png")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    out = Path(args.out)
    thumbs = []
    for name in BUFFER_NAMES:
        thumb = load_thumb(input_dir / name)
        draw = ImageDraw.Draw(thumb)
        draw.rectangle((0, 198, 220, 220), fill=(255, 255, 255))
        draw.text((5, 202), name[:28], fill=(0, 0, 0))
        thumbs.append(thumb)

    cols = 4
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 220, rows * 220), (255, 255, 255))
    for idx, thumb in enumerate(thumbs):
        sheet.paste(thumb, ((idx % cols) * 220, (idx // cols) * 220))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    missing = [name for name in BUFFER_NAMES if not (input_dir / name).exists()]
    if missing:
        print("Missing buffers; export or render at iteration % 500 == 0 first:")
        for name in missing:
            print(f"  - {name}")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
