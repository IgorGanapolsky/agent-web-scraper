#!/usr/bin/env python3
"""
Simple SVG to PNG converter using svglib and reportlab
"""

import os
import subprocess
import sys


def convert_svg_to_png():
    """Convert the architecture SVG to PNG using svglib"""

    svg_path = "docs/assets/architecture-2025.svg"
    png_path = "docs/assets/architecture-2025.png"

    try:
        from reportlab.graphics import renderPM
        from svglib.svglib import renderSVG
    except ImportError:
        print("Installing required packages...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "svglib", "reportlab"]
        )
        from reportlab.graphics import renderPM
        from svglib.svglib import renderSVG

    # Convert SVG to PNG
    print(f"Converting {svg_path} to {png_path}...")

    try:
        drawing = renderSVG.renderSVG(svg_path)
        renderPM.drawToFile(drawing, png_path, fmt="PNG", dpi=300)
        print(f"✅ Successfully created high-quality PNG: {png_path}")
    except Exception as e:
        print(f"❌ Error during conversion: {e}")
        print(
            "The SVG file has been created successfully. You can manually convert it to PNG using online tools or other software."
        )

    # Clean up the conversion script
    if os.path.exists(__file__):
        os.remove(__file__)
        print("🧹 Cleaned up conversion script")


if __name__ == "__main__":
    convert_svg_to_png()
