#!/usr/bin/env python3
"""Generate high-resolution application icons for macOS (.icns), Windows (.ico), and Linux (.png)."""

import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw


def draw_master_icon(size: int = 1024) -> Image.Image:
    """Draw a professional enterprise audit/financial emblem."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    margin = int(size * 0.08)
    box = [margin, margin, size - margin, size - margin]

    # Rounded outer shield / squircle background (Dark Slate)
    radius = int(size * 0.22)
    draw.rounded_rectangle(box, radius=radius, fill=(15, 23, 42, 255))

    # Subtle inner gradient border (Emerald accent)
    border_width = max(2, int(size * 0.015))
    inner_box = [margin + border_width, margin + border_width, size - margin - border_width, size - margin - border_width]
    draw.rounded_rectangle(inner_box, radius=int(radius * 0.95), outline=(16, 185, 129, 230), width=border_width)

    # Central emblem: Shield / Ledger & Geometric Audit Star
    center_x = size / 2
    center_y = size / 2

    # Draw Ledger / Shield polygon
    shield_top = int(size * 0.25)
    shield_bottom = int(size * 0.72)
    shield_left = int(size * 0.26)
    shield_right = int(size * 0.74)

    shield_points = [
        (shield_left, shield_top),
        (shield_right, shield_top),
        (shield_right, int(shield_top + (shield_bottom - shield_top) * 0.55)),
        (center_x, shield_bottom),
        (shield_left, int(shield_top + (shield_bottom - shield_top) * 0.55)),
    ]
    # Deep navy fill for shield
    draw.polygon(shield_points, fill=(30, 41, 59, 255), outline=(59, 130, 246, 255))

    # Draw golden / emerald audit check & data bars inside shield
    bar_y_start = int(size * 0.34)
    bar_h = int(size * 0.035)
    bar_gap = int(size * 0.05)

    # Bar 1 (Blue)
    draw.rounded_rectangle(
        [int(size * 0.35), bar_y_start, int(size * 0.65), bar_y_start + bar_h],
        radius=int(bar_h / 2),
        fill=(96, 165, 250, 255),
    )
    # Bar 2 (Emerald)
    draw.rounded_rectangle(
        [int(size * 0.35), bar_y_start + bar_gap, int(size * 0.58), bar_y_start + bar_gap + bar_h],
        radius=int(bar_h / 2),
        fill=(52, 211, 153, 255),
    )
    # Bar 3 (Gold / Amber)
    draw.rounded_rectangle(
        [int(size * 0.35), bar_y_start + bar_gap * 2, int(size * 0.50), bar_y_start + bar_gap * 2 + bar_h],
        radius=int(bar_h / 2),
        fill=(251, 191, 36, 255),
    )

    # Prominent Emerald Verification Tick
    check_pts = [
        (int(size * 0.44), int(size * 0.55)),
        (int(size * 0.50), int(size * 0.61)),
        (int(size * 0.64), int(size * 0.45)),
    ]
    draw.line(check_pts, fill=(16, 185, 129, 255), width=max(4, int(size * 0.04)), joint="curve")

    # Bottom text badge
    banner_y = int(size * 0.78)
    banner_w = int(size * 0.48)
    banner_h = int(size * 0.09)
    draw.rounded_rectangle(
        [int(center_x - banner_w / 2), banner_y, int(center_x + banner_w / 2), banner_y + banner_h],
        radius=int(banner_h / 2),
        fill=(16, 185, 129, 255),
    )

    # Banner inner highlight text
    draw.text(
        (center_x, banner_y + banner_h / 2),
        "FINAUDITPRO",
        fill=(255, 255, 255, 255),
        anchor="mm",
        font_size=int(size * 0.045),
    )

    return img


def generate_all_icons(output_dir: Path) -> dict[str, Path]:
    """Generate master PNG, Windows .ico, and macOS .icns."""
    output_dir.mkdir(parents=True, exist_ok=True)
    master = draw_master_icon(1024)

    # 1. Master PNG
    master_png = output_dir / "finauditpro_icon.png"
    master.save(master_png, format="PNG")
    print(f"  ✓ Saved master PNG: {master_png}")

    # Standard PNG sizes for Linux desktop & web
    for sz in (512, 256, 128, 64, 32, 16):
        resized = master.resize((sz, sz), Image.Resampling.LANCZOS)
        resized.save(output_dir / f"icon_{sz}x{sz}.png", format="PNG")

    # 2. Windows .ico
    ico_path = output_dir / "FinAuditPro.ico"
    ico_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    master.save(ico_path, format="ICO", sizes=ico_sizes)
    print(f"  ✓ Saved Windows ICO: {ico_path}")

    # 3. macOS .icns
    icns_path = output_dir / "FinAuditPro.icns"
    if sys.platform == "darwin":
        with tempfile.TemporaryDirectory() as tmp_iconset:
            iconset_path = Path(tmp_iconset) / "FinAuditPro.iconset"
            iconset_path.mkdir()

            mac_sizes = [
                ("icon_16x16.png", 16),
                ("icon_16x16@2x.png", 32),
                ("icon_32x32.png", 32),
                ("icon_32x32@2x.png", 64),
                ("icon_128x128.png", 128),
                ("icon_128x128@2x.png", 256),
                ("icon_256x256.png", 256),
                ("icon_256x256@2x.png", 512),
                ("icon_512x512.png", 512),
                ("icon_512x512@2x.png", 1024),
            ]
            for filename, dim in mac_sizes:
                res_img = master.resize((dim, dim), Image.Resampling.LANCZOS)
                res_img.save(iconset_path / filename, "PNG")

            try:
                subprocess.run(
                    ["iconutil", "-c", "icns", str(iconset_path), "-o", str(icns_path)],
                    check=True,
                    capture_output=True,
                )
                print(f"  ✓ Saved macOS ICNS (native iconutil): {icns_path}")
            except Exception as e:
                print(f"  ⚠ iconutil fallback: {e}")
                master.save(icns_path, format="ICNS")
    else:
        try:
            master.save(icns_path, format="ICNS")
            print(f"  ✓ Saved macOS ICNS (PIL): {icns_path}")
        except Exception:
            pass

    return {
        "png": master_png,
        "ico": ico_path,
        "icns": icns_path,
    }


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    target_dir = project_root / "assets" / "icons"
    print(f"Generating FinAuditPro application icons into: {target_dir}")
    generate_all_icons(target_dir)
