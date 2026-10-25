# Coding Standards & Engineering Conventions

## 1. Minimal Code Philosophy ("Ponytail Lazy Senior Dev")
Before writing any code, we follow the efficiency ladder:
1. Does this need to be built at all? (YAGNI)
2. Does it already exist in this codebase? Reuse existing helpers.
3. Does the standard library already do this? Use standard library.
4. Does an installed dependency solve it? Use it.
5. Can this be one line? Keep it simple.
6. Only then write the minimum code that works.

## 2. Invariants & Strict Rules
- **Pure Standard ASCII Terminal Output**:
  - All CLI prints, banners, tables, and progress messages MUST strictly use standard ASCII characters (codes 32 to 126).
  - Unicode box characters (`┌`, `─`, `✔`, `✖`) and emojis are forbidden in stdout/stderr to prevent crashes in Windows consoles running `cp1252` or `cp437`.
  - Use `[OK]`, `[FAIL]`, `[WARN]`, `+---+`, `|`, `-` instead.
- **Terminal Width Constraints**:
  - Banners and default CLI outputs must not exceed 71 columns to safely fit standard 80-column terminal windows without line-wrapping.
- **Zero Untrusted Execution**:
  - Never execute untrusted code. Never use `shell=True`, `eval()`, or `exec()` on untrusted input.
  - Package inspection is strictly static: parse `setup.py` via Python's `ast` module; parse `package.json` with `json`.
- **Secret Redaction**:
  - Discovered credentials (API keys, passwords, bearer tokens) must never be logged or rendered in full. Show the first 4 characters followed by `****`.
- **Exit Code Conventions**:
  - `0`: Allow / Clean / Pass / Fixed.
  - `1`: Gate failed / finding present / warning.
  - `2`: Blocked / High or Critical risk hit / security violation.
  - `3`: Tool error / exception.
- **Fail-Closed on Supply Chain Risk**:
  - If a package has a known malicious advisory on OSV, the package gate immediately issues exit code `2`.

## 3. Deliberate Simplifications (`ponytail:` Tagging)
Any intentional shortcut or simplification with a known ceiling must be annotated with a `ponytail:` comment describing the ceiling and future upgrade path:
```python
# ponytail: Simple Levenshtein distance check; upgrade to SymSpell if dictionary exceeds 50k entries.
```
