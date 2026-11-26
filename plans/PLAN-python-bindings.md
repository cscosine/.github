# Plan: Python bindings of the C++ libraries

Date: 2026-11-26 · Status: **not started** (nanobind is a package of third_party_base_libs, from its release 0.1.1)

## What exists

nanobind (upstream 3.1.0, fork `cscosine/nanobind`) is a package of third_party_base_libs: the headers, its sources and
`nanobind-config.cmake`, compiled by the consumer. Building the package needs no Python (its tests are off).

A consumer:

```cmake
find_package(Python 3.12 COMPONENTS Interpreter Development.Module REQUIRED)   # before nanobind
find_package(nanobind CONFIG REQUIRED)
nanobind_add_module(<name> STABLE_ABI NB_STATIC <sources>)
```

Eigen ↔ NumPy through `nanobind/eigen/dense.h`. With `STABLE_ABI` one module serves every Python ≥ 3.12.

## Steps

| # | Step | Content | Status |
|---|---|---|---|
| P1 | Decisions | which libraries first (csLie, csCamera: Eigen in, Eigen out); the minimum Python (3.12 for the stable ABI); where the binding code lives (a `python/` folder in each library, or one project of bindings) | todo |
| P2 | csCMake | `cs_add_python_module(<name> SOURCES … LINK …)` around `nanobind_add_module` (the compile profiles of csCMake, install into a Python package folder of the project's layout); `cs_find_package(nanobind)` as the other packages. Generic: no project names | todo |
| P3 | csorchestrator | Python (with its headers) on every variant of a project that builds bindings (setup-python on the runners); a smoke test `python -c "import <module>"` from the archive | todo |
| P4 | First bindings | the libraries of P1, released through their distribution | todo |
| P5 | Wheels (`pip install`) | scikit-build-core in the `pyproject.toml` of the project that ships them, cibuildwheel in its CI. A separate decision: the archives of csorchestrator stay the C++ delivery | todo |
