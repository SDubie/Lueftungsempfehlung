# Contributing

Thanks for your interest in improving Lüftungsempfehlung.

## Before you start

- Open an issue or discussion for larger changes.
- Keep changes focused and small when possible.
- Follow the existing code style and Home Assistant integration patterns.

## Development notes

- This is a Home Assistant custom integration.
- Changes should be tested locally in a Home Assistant development environment.
- Keep translations and documentation in sync when user-facing text changes.

## Local setup

Use a virtual environment for local development and tests.

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
```

## Running tests

Run the coordinator logic tests:

```bash
pytest tests/test_coordinator_logic.py
```

If you add new behavior, please add or update tests accordingly.

## Pull requests

Please include:

- A short description of the change
- Any related issue or context
- Testing notes, especially if behavior changed

## Commit messages

Use short, descriptive commit messages.
Examples:

- `fix: handle config reload`
- `docs: expand README`
- `feat: add new ventilation state`
