# Contributing to NEXUS

Thank you for your interest in contributing to NEXUS!

## Development Workflow

1. **Fork and clone the repository**.
2. **Set up virtual environment**:
   ```bash
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
3. **Generate local certificates**:
   ```bash
   python scripts/generate_certs.py
   ```
4. **Run tests before making changes**:
   ```bash
   pytest -v
   ```
5. **Code Style & Formatting**:
   - Python code must use modern type annotations.
   - Run `pytest` and ensure all 23 tests pass.
   - Keep functions concise, modular, and well-documented.
6. **Submitting Changes**:
   - Open a pull request describing the change, motivation, and test coverage.
