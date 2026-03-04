#!/usr/bin/env python3
"""
measure_deps.py - Measure wheel download size and installed site-packages size
for a set of Python dependencies.

Usage:
    python measure_deps.py [--requirements requirements.txt] [--python PYTHON]

The script:
1. Downloads all wheels (and their transitive dependencies) into a temp dir
   using `pip download`, and reports total download size.
2. Installs the packages into an isolated temp virtualenv and reports the
   total installed size in site-packages.
3. Prints a summary table with per-package and grand-total sizes.

Requirements:
    Python 3.8+ with pip available.
"""

import argparse
import subprocess
import sys
import tempfile
import venv
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(cmd: list, **kwargs) -> subprocess.CompletedProcess:
    """Run a subprocess command and raise on failure."""
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kwargs)


def _dir_size_mb(path: Path) -> float:
    """Return the total size of all files under *path* in megabytes."""
    total = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
    return total / (1024 * 1024)


def _format_mb(value: float) -> str:
    return f"{value:.1f} MB"


# ---------------------------------------------------------------------------
# Core measurement functions
# ---------------------------------------------------------------------------

def measure_download_size(pip_cmd: list, packages: list, work_dir: Path) -> dict:
    """
    Download wheels for *packages* (including dependencies) and return a dict
    mapping wheel filename -> size (MB).  The 'TOTAL' key holds the grand total.
    """
    dl_dir = work_dir / "wheels"
    dl_dir.mkdir()

    _run(pip_cmd + ["download", "--dest", str(dl_dir)] + packages)

    sizes = {}
    for f in sorted(dl_dir.iterdir()):
        sizes[f.name] = f.stat().st_size / (1024 * 1024)

    sizes["TOTAL"] = sum(v for k, v in sizes.items() if k != "TOTAL")
    return sizes


def measure_installed_size(pip_cmd: list, packages: list, work_dir: Path) -> dict:
    """
    Install *packages* into an isolated venv and return a dict with the total
    installed size of site-packages in MB.
    """
    venv_dir = work_dir / "venv"
    venv.create(str(venv_dir), with_pip=True)

    if sys.platform == "win32":
        venv_pip = [str(venv_dir / "Scripts" / "pip")]
        site_packages_matches = list((venv_dir / "Lib").glob("site-packages"))
        if not site_packages_matches:
            raise RuntimeError(f"Could not find site-packages under {venv_dir / 'Lib'}")
        site_packages = site_packages_matches[0]
    else:
        venv_pip = [str(venv_dir / "bin" / "pip")]
        lib_dir = venv_dir / "lib"
        lib_children = list(lib_dir.iterdir())
        if not lib_children:
            raise RuntimeError(f"Could not find Python directory under {lib_dir}")
        python_dir = lib_children[0]  # e.g. python3.11
        site_packages = python_dir / "site-packages"

    _run(venv_pip + ["install", "--quiet"] + packages)

    total_mb = _dir_size_mb(site_packages)
    return {"site-packages (all installed)": total_mb, "TOTAL": total_mb}


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def print_summary_table(download_sizes: dict, installed_sizes: dict) -> None:
    print()
    print("=" * 70)
    print("  WHEEL DOWNLOAD SIZES (including transitive dependencies)")
    print("=" * 70)
    col_w = max(len(k) for k in download_sizes) + 2
    for name, size in sorted(download_sizes.items(), key=lambda x: -x[1]):
        if name == "TOTAL":
            continue
        print(f"  {name:<{col_w}} {_format_mb(size):>10}")
    print("-" * 70)
    print(f"  {'TOTAL':<{col_w}} {_format_mb(download_sizes['TOTAL']):>10}")

    print()
    print("=" * 70)
    print("  INSTALLED SITE-PACKAGES SIZE")
    print("=" * 70)
    for name, size in installed_sizes.items():
        if name == "TOTAL":
            continue
        print(f"  {name:<60} {_format_mb(size):>10}")
    print("-" * 70)
    print(f"  {'TOTAL':<60} {_format_mb(installed_sizes['TOTAL']):>10}")
    print()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Measure wheel download and installed sizes for Python packages."
    )
    parser.add_argument(
        "--requirements", "-r",
        default="requirements.txt",
        help="Path to a requirements file (default: requirements.txt)",
    )
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Python interpreter to use for pip operations (default: current interpreter)",
    )
    args = parser.parse_args()

    # Build the pip command using the chosen Python interpreter
    pip_cmd = [args.python, "-m", "pip"]

    # Read package specs
    req_file = Path(args.requirements)
    if not req_file.exists():
        print(f"ERROR: requirements file not found: {req_file}", file=sys.stderr)
        sys.exit(1)

    packages = [
        line.strip()
        for line in req_file.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]
    if not packages:
        print("ERROR: no packages found in requirements file.", file=sys.stderr)
        sys.exit(1)

    print(f"Measuring sizes for {len(packages)} package spec(s) from '{req_file}'...")

    with tempfile.TemporaryDirectory(prefix="dep_size_") as tmp:
        work_dir = Path(tmp)

        print("  [1/2] Downloading wheels ...")
        download_sizes = measure_download_size(pip_cmd, packages, work_dir)

        print("  [2/2] Installing into isolated venv ...")
        installed_sizes = measure_installed_size(pip_cmd, packages, work_dir)

    print_summary_table(download_sizes, installed_sizes)


if __name__ == "__main__":
    main()
