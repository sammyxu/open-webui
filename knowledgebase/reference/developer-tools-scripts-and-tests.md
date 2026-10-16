# Developer Tools, Scripts, CI and Tests

## At a Glance

- **Provisional.** This document covers the commands a developer runs on the MedIT GPT repository:
  the `npm` scripts in `package.json` (development server, build, type check, lint, format, i18n
  sync, tests) and the Python packaging and lint settings in `pyproject.toml`.
- **Continuous integration** is the upstream GitHub Actions set in `.github/workflows/`; none of it
  is triggered by the `uoft` branch.
- **Tests.** The repository holds no automated test files; the regression suite lives in an
  external upstream repository.
- **Two repository scripts**: `scripts/prepare-pyodide.js` (downloads Pyodide before every
  development run and build) and `scripts/generate-sbom.sh`.
