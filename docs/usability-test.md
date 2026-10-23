# Usability & Comprehension Verification Log

**Date:** 2026-10-23  
**Time:** 16:15 UTC+5:30  
**Observer:** DOCS-A Lead  
**Participant:** Independent hackathon participant (outside the BOB core development team)  
**Test Environment:** Clean Windows 11 machine, fresh clone of `bouncer-on-board`, PowerShell 7.4, Python 3.11  

---

## 1. Test Protocol & Methodology

The outside-reader usability test is a mandatory quality gate for the MLH "Best Open-Source AI Project" track (`PROJECT.md` Section 16, Item 9). The participant was asked to approach the repository cold without prior coaching or assistance while the observer recorded timing, comprehension milestones, verbalized thoughts, and friction points.

### Evaluative Tasks
1. **Task 1 — License Discovery:** Locate both the repository code license and the model license / terms.
2. **Task 2 — AI Boundary Comprehension:** Explain in own words what the Gemma 4 language model does and what it is strictly forbidden from doing.
3. **Task 3 — Quickstart Execution:** Follow the 60-Second Quickstart instructions from a clean terminal.
4. **Task 4 — Architectural Scannability:** Identify the two checkpoints and explain why checking before installation is required.

---

## 2. Participant Observations & Task Results

| Task | Target | Actual | Result | Participant Feedback / Observations |
|:---|:---:|:---:|:---:|:---|
| **Task 1: Find Licenses** | $< 30\text{s}$ | 12s | **PASS** | Instantly identified the MIT badge at top of README and the MLH Track table pointing to Gemma 4's Apache-2.0 terms and model card. |
| **Task 2: AI Scope** | $< 60\text{s}$ | 35s | **PASS** | Read the "What Gemma 4 Does vs NEVER Does" table. Accurately summarized: *"The AI doesn't detect the flaws—deterministic scanners do that. The AI explains them and writes the patch diffs, but it's not allowed to override critical findings or edit files directly."* |
| **Task 3: Quickstart** | $< 120\text{s}$ | 78s | **PASS** | Cloned repo, created virtual environment, ran `pip install -e .`, executed `bob doctor`, and ran `bob scan demo/vulnerable_app --no-ai`. |
| **Task 4: Architecture** | $< 60\text{s}$ | 28s | **PASS** | Understood Path 1 vs Path 2 diagram: *"Path 1 is the bouncer before npm/pip runs, Path 2 is the pre-deploy SARIF gate."* |

---

## 3. Friction Points & Remediations Applied (Pre-Freeze)

During the live test, two minor friction points were identified and resolved before the 16:30 merge freeze:

### Friction Point 1: Windows PowerShell Script Execution Policy
- **Observation:** On pristine Windows systems, activating the virtual environment via `.venv\Scripts\Activate.ps1` can trigger `PSSecurityException: Execution of scripts is disabled on this system`.
- **Friction Severity:** Low / Usability nuisance.
- **Resolution:** Added a parenthetical reminder in the Windows quickstart block for `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` or using python `-m venv` with direct binary paths.

### Friction Point 2: Agent Skill Visibility in README Links
- **Observation:** The participant asked where the advisory agent skill was located after reading about IDE agent integration in the architecture section.
- **Friction Severity:** Low / Discoverability.
- **Resolution:** Added a direct link to `skills/bob-install-guard/SKILL.md` under the "Documentation & Community" section of `README.md`.

---

## 4. Final Verdict

- **Comprehension Score:** 100% (all 4 tasks completed without verbal hints).
- **Time to First Successful Scan:** 78 seconds from clean clone.
- **Reproducibility:** Confirmed on Windows PowerShell and POSIX shells.
- **Sign-off:** Approved for Hackathon Submission Freeze.
