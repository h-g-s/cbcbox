# cbcbox

[![](https://img.shields.io/pypi/v/cbcbox.svg?color=brightgreen)](https://pypi.org/pypi/cbcbox/)

Python wheel distribution of pre-built binaries for the
[CBC](https://github.com/coin-or/Cbc) MILP solver (COIN-OR Branch and Cut),
built from the latest master branch of the COIN-OR repositories.

Supported platforms:
- Linux (x86\_64, aarch64) — manylinux2014
- macOS (x86\_64, arm64)

Built with:
- **OpenBLAS** — optimised BLAS/LAPACK (libgfortran bundled in the wheel)
- **AMD** (SuiteSparse) — sparse matrix reordering for the simplex factorisation
- **Nauty** — symmetry detection
- **zlib** — read compressed MPS/LP files

```
pip install cbcbox
```

After installation, invoke the `cbc` command-line solver via:

```
python -m cbcbox mymodel.lp
```

The paths to the installed binary, headers and libraries are available
from the Python module:

```python
>>> import cbcbox
>>> cbcbox.cbc_bin_path()
'/home/user/.venv/lib/python3.13/site-packages/cbcbox/cbc_dist/bin/cbc'
>>> cbcbox.cbc_lib_dir()
'/home/user/.venv/lib/python3.13/site-packages/cbcbox/cbc_dist/lib'
>>> cbcbox.cbc_include_dir()
'/home/user/.venv/lib/python3.13/site-packages/cbcbox/cbc_dist/include/coin'
```
