# AHP Alternatives Analyzer

An interactive skill for evaluating and ranking alternatives with the Analytic Hierarchy Process (AHP), also known as the Saaty method.

The project turns a complex choice into a clear decision structure: goal, criteria, alternatives, pairwise comparisons, weights, final ranking, Pareto frontier, and trade-off explanation.

## Purpose

The skill helps a user choose the best alternative across several criteria, not just one metric. It guides the user step by step, collects expert judgments, checks their consistency, and explains why one option ranks above another.

## Key Ideas

### Decision Hierarchy

```text
Decision goal
-> criteria
-> criteria weights
-> alternatives
-> alternative scores for each criterion
-> final ranking
```

Criteria do not "win" by themselves. Criteria receive importance weights. Alternatives win.

### Pairwise Comparisons

AHP compares items in pairs:

```text
Which criterion is more important: A or B?
How much more important is it, from 1 to 9 on Saaty's scale?
```

This is often easier than assigning exact percentages to all criteria at once.

### Consistency

The skill calculates `CR`, the consistency ratio. If the judgments are contradictory, it identifies the most problematic comparison and suggests reviewing it.

Rule of thumb:

```text
CR <= 0.10 - judgments are consistent enough.
CR > 0.10 - contradictory comparisons should be reviewed.
```

### Pareto Frontier

The Pareto frontier shows alternatives that cannot be clearly discarded. An alternative stays on the frontier if no other alternative is at least as good on all key criteria and strictly better on at least one.

This separates:

```text
strong trade-off options
from options dominated by others.
```

### Trade-Offs and Strategic Bet

For alternatives on the Pareto frontier, the skill explains what the user gives up when choosing one option over another.

Example:

```text
Alternative A wins on speed and cost.
Alternative B wins on quality and reliability.
```

This makes the result more useful than a ranking alone: the user sees the meaning of the choice.

### Sensitivity Analysis

The skill checks how stable the result is: how much a key criterion weight would need to change for the leader to change. This shows whether the winning alternative is robust or depends on narrow weighting assumptions.

## Project Structure

```text
ahp-skill/
  SKILL.md                         # Skill instructions
  scripts/ahp_calculator.py        # Weights, CR, Pareto, and sensitivity calculations
  references/specification.md      # Detailed method specification
```

## Installation

Copy the `ahp-skill` directory into your Codex / ChatGPT skills directory:

```bash
cp -R ahp-skill ~/.codex/skills/
```

After installation, you can trigger the skill with prompts such as:

```text
Help me compare alternatives using AHP.
I need to choose the best option from several alternatives.
Run a Saaty method analysis for these alternatives.
```

## Running Calculations

The main workflow runs through the skill dialogue. The Python file in `scripts/ahp_calculator.py` is used as the helper calculation module.

To check the Python module syntax:

```bash
python3 -m py_compile ahp-skill/scripts/ahp_calculator.py
```

## Running with Antigravity Agent

The project includes an agent-tailored version of the skill in `ahp-skill-antigravity/` optimized for the **Antigravity AI agent**. 

Unlike standard chat-bots, the Antigravity agent can interact with your file system and run Python scripts to automate all calculations, manage state, and build dashboards.

### Project Structure (Antigravity version)
```text
ahp-skill-antigravity/
  SKILL.md                         # Skill instructions for Antigravity
  scripts/ahp_calculator.py        # Automated calculation and visualization engine
```

### How to Run

1. **Initiate the Skill**: Tell the Antigravity agent in the chat:
   > "Запусти/выполни скилл для оценки альтернатив AHP" (or in English: "Run/execute the AHP alternatives evaluation skill")
2. **Skill Execution**: 
   - Antigravity will automatically locate and load `ahp-skill-antigravity/SKILL.md` (reading it as a skill file).
   - The agent will guide you step-by-step to define your project goal, criteria (with directions and threshold logic), and alternatives.
3. **State Management**:
   - The agent automatically saves and updates the session state in `ahp_project.json` in the workspace root. If you pause or restart the agent, it can resume the analysis from this file.
4. **Automated Calculations**:
   - Instead of manual mental math, the agent runs the background computation command:
     ```bash
     python3 ahp-skill-antigravity/scripts/ahp_calculator.py ahp_project.json
     ```
5. **Interactive Dashboard**:
   - Once completed, the script generates a markdown report (`ahp_report.md`) and a premium glassmorphism interactive dashboard (`ahp_dashboard.html`).
   - The agent will provide clickable local links (e.g. `[ahp_dashboard.html](file:///...)`) to let you explore the results and run sensitivity analysis directly in your browser.

## Recommended Scope

For a first analysis, use:

```text
3-7 criteria
2-5 alternatives
```

The number of pairwise comparisons grows quickly:

```text
n x (n - 1) / 2
```

For example, 6 criteria require 15 criterion comparisons. If there are 4 alternatives and 6 criteria, the user will need 36 additional alternative comparisons.

## License

This project is distributed under the MIT License. You may use, copy, modify, publish, distribute, sublicense, and sell copies of the software under the license terms.
