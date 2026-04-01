#!/usr/bin/env python3
"""Build script for Aster DEX Python SDK.

Usage:
    python scripts/build.py           # Build wheel and tarball
    python scripts/build.py --wheel   # Build wheel only
    python scripts/build.py --sdist    # Build tarball only
    python scripts/build.py --clean    # Clean build artifacts
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"
EGG_INFO_DIR = PROJECT_ROOT / "asterdex.egg-info"


def clean():
    """Clean build artifacts."""
    print("Cleaning build artifacts...")

    artifacts = [DIST_DIR, BUILD_DIR, EGG_INFO_DIR]

    for artifact in artifacts:
        if artifact.exists():
            if artifact.is_dir():
                shutil.rmtree(artifact)
            else:
                artifact.unlink()
            print(f"  Removed: {artifact}")

    # Also clean __pycache__ in src
    for pycache in PROJECT_ROOT.rglob("__pycache__"):
        shutil.rmtree(pycache)
        print(f"  Removed: {pycache}")

    print("Clean complete.")


def build_wheel():
    """Build wheel package using UV."""
    print("Building wheel...")
    subprocess.run(["uv", "build", "--wheel", "--out-dir", "dist"], cwd=PROJECT_ROOT, check=True)
    print("Wheel built successfully.")


def build_sdist():
    """Build source distribution using UV."""
    print("Building source tarball...")
    subprocess.run(["uv", "build", "--sdist", "--out-dir", "dist"], cwd=PROJECT_ROOT, check=True)
    print("Source tarball built successfully.")


def build_all():
    """Build both wheel and source distribution using UV."""
    print("Building wheel and source tarball...")
    subprocess.run(["uv", "build", "--out-dir", "dist"], cwd=PROJECT_ROOT, check=True)
    print("Build complete.")


def list_artifacts():
    """List built artifacts in dist directory."""
    if not DIST_DIR.exists():
        print("No artifacts found in dist/")
        return

    print("\nBuilt artifacts:")
    for f in sorted(DIST_DIR.iterdir()):
        size = f.stat().st_size
        if size > 1024 * 1024:
            size_str = f"{size / (1024 * 1024):.1f} MB"
        elif size > 1024:
            size_str = f"{size / 1024:.1f} KB"
        else:
            size_str = f"{size} bytes"
        print(f"  {f.name} ({size_str})")


def main():
    parser = argparse.ArgumentParser(description="Build Aster DEX Python SDK")
    parser.add_argument("--wheel", action="store_true", help="Build wheel only")
    parser.add_argument("--sdist", action="store_true", help="Build source tarball only")
    parser.add_argument("--clean", action="store_true", help="Clean build artifacts")
    parser.add_argument("--list", action="store_true", help="List built artifacts")

    args = parser.parse_args()

    if args.clean:
        clean()
        return

    if args.list:
        list_artifacts()
        return

    if args.wheel:
        build_wheel()
    elif args.sdist:
        build_sdist()
    else:
        build_all()

    list_artifacts()


if __name__ == "__main__":
    main()
