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
