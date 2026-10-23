---
name: New Detection Rule
about: Propose a new prompt injection or heuristic package gate rule
title: '[RULE]: '
labels: ['detection-rule']
assignees: ''
---

## Rule Category
- [ ] Prompt Injection (`data/rules/injection.yaml`)
- [ ] Sensitive Path Guard (`data/rules/sensitive_paths.yaml`)
- [ ] Package Gate Heuristic (`src/bob/pkg/heuristics.py`)

## Proposed Rule ID & Severity
- **ID**: `INJ-XXX` or `GUARD-XXX`
- **Severity**: `critical` | `high` | `medium` | `low`

## Pattern / Regex Specification
```yaml
- id: INJ-XXX
  title: Short descriptive title
  severity: high
  regex: '(?i)...'
```

## Positive Test Case (Must Hit)
<!-- Example text that should be flagged. Keep inert! -->

## Negative Test Case (Must Pass Cleanly)
<!-- Legitimate developer text that should NOT be blocked. -->
