# test

## Dependency Size Measurement

This repository includes a script to estimate the **wheel download size** and
**installed site-packages size** for the Python dependencies listed in
[`requirements.txt`](requirements.txt).

### Dependencies

| Package | Version constraint |
|---|---|
| langchain | >=0.3.0 |
| langchain-community | >=0.3.0 |
| langchain-google-genai | >=2.0.0 |
| chromadb | >=0.5.0 |
| pypdf | >=4.0.0 |
| python-docx | >=1.1.0 |
| unstructured | >=0.15.0 |

### Estimated sizes (approximate, Python 3.11, Linux x86-64)

These are rough estimates based on typical PyPI release sizes.  
Run the script below to obtain exact numbers for your environment.

| Package | Wheel download (approx.) | Installed size (approx.) |
|---|---|---|
| langchain | ~2 MB | ~10 MB |
| langchain-community | ~3 MB | ~15 MB |
| langchain-google-genai | ~0.5 MB | ~3 MB |
| chromadb | ~5 MB | ~40 MB |
| pypdf | ~0.5 MB | ~2 MB |
| python-docx | ~0.5 MB | ~2 MB |
| unstructured | ~2 MB | ~20 MB |
| **Transitive dependencies** | **~100–200 MB** | **~500–900 MB** |
| **Grand total (estimate)** | **~120–220 MB** | **~600–1000 MB** |

> Note: The totals include all transitive dependencies (numpy, pydantic,
> grpc, onnxruntime, etc.) and vary significantly between platforms and
> Python versions.

---

### Measuring precisely

#### Prerequisites

- Python 3.8 or later (3.11 recommended)
- `pip` available in the active Python environment

#### Run locally

```bash
# Clone the repository
git clone https://github.com/miuersaisi521/test.git
cd test

# Run the measurement script (uses the current Python interpreter)
python measure_deps.py

# Or specify a different Python version / requirements file
python measure_deps.py --python python3.11 --requirements requirements.txt
```

The script will:
1. **Download all wheels** (including transitive dependencies) into a
   temporary directory and report each file's size.
2. **Install** the packages into an isolated temporary virtualenv and measure
   the total `site-packages` disk footprint.
3. **Print a summary table** to stdout.

#### Run in CI (GitHub Actions example)

```yaml
- name: Measure dependency sizes
  run: python measure_deps.py
```

#### Interpreting the output

```
======================================================================
  WHEEL DOWNLOAD SIZES (including transitive dependencies)
======================================================================
  chromadb-0.5.x-py3-none-any.whl            5.0 MB
  ...
----------------------------------------------------------------------
  TOTAL                                     150.0 MB

======================================================================
  INSTALLED SITE-PACKAGES SIZE
======================================================================
  site-packages (all installed)             750.0 MB
----------------------------------------------------------------------
  TOTAL                                     750.0 MB
```

- **Wheel download size** reflects network bandwidth needed to install the
  packages (e.g. in a fresh CI environment without a cache).
- **Installed size** reflects actual disk usage after installation.
