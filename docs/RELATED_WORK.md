# Related work

Short survey of systems that **edit agent harnesses** (prompts, tools, control flow, skill libraries) rather than model weights.

## Darwin Gödel Machine (DGM, 2025)

[Zhang et al., arXiv:2505.22954](https://arxiv.org/abs/2505.22954) — Sakana / UBC / Vector.

The DGM maintains an **archive of coding agents** and iteratively **rewrites its own Python codebase**, evaluating each variant on SWE-bench and Polyglot. Open-ended exploration (Darwinian archive + foundation-model edits) drives large benchmark gains. Safety emphasis: sandboxing and human oversight.

**Contrast:** DGM mutates full agent code on **in-loop benchmarks**; **self-rewriting-harness** keeps a **git-versioned harness** (prompt + 50+ SKILL.md library + checks) and accepts edits only when **held-out tasks** (never used for proposals) improve or tie.

## ADAS / Meta Agent Search (2024–2025)

[Hu et al., arXiv:2408.08435](https://arxiv.org/abs/2408.08435) — Automated Design of Agentic Systems.

A **meta agent writes new agents in code**, evaluates on validation tasks, and archives successes to seed later designs. Shows transfer across domains and models.

**Contrast:** ADAS discovers **new agent programs**; we evolve an **explicit skill library + system prompt** with a **critic gate** and an **ungated ablation** to measure regression from uncontrolled self-edits.

## Voyager (2023)

[Wang et al., arXiv:2305.16291](https://arxiv.org/abs/2305.16291) — Minecraft lifelong agent.

**Skill library** of verified JavaScript skills, retrieved by embedding of descriptions; curriculum + iterative prompting with environment feedback.

**Contrast:** Voyager grows **executable skills in-environment** without a held-out acceptance test for harness changes; our harness edits are **versioned** and **gated on disjoint tasks**.

## Self-Harness (2026)

[Self-Harness: Harnesses That Improve Themselves](https://arxiv.org/html/2606.09498v1)

Three-stage loop: weakness mining from traces → harness proposals → **regression / held-out validation** before promotion. Terminal-Bench-2.0 instantiation across multiple base models.

**Closest neighbor.** We share trace-driven proposals and validation-before-merge. **self-rewriting-harness** open-sources a **seed library of 57 general skills**, git commits per accepted revision, and a **mock backend** so CI reproduces the full loop without API keys.

## RRSI (2026)

[Regularized Recursive Self-Improvement of Agent Harnesses](https://arxiv.org/abs/2609.24972)

Adds **regularization** (annealed edit budgets, critic + pruner) so harness RSI generalizes OOD instead of memorizing training benchmarks.

**Contrast:** RRSI is a research system with broad benchmark sweeps; v1 here is a **minimal reference implementation** with frozen vs gated vs ungated baselines on a small task suite.

## VERSE (2026)

[Verified Self-Evolving Optimizer](https://arxiv.org/html/2610.02616)

The **optimizer** evolves its own tools/prompts/skills while improving executor harnesses, with **execution-based verification** and disjoint train/val/test splits.

**Contrast:** VERSE co-evolves optimizer + executor; we focus on a **single harness tree** and **skill/prompt edits** with git audit trail.

## HarnessOpt-Bench (2026)

[Evaluating LLMs at Harness Optimization](https://arxiv.org/html/2608.06301)

Benchmarks **LLMs as harness optimizers** under expensive stochastic evaluation, with a **held-out test partition** locked during search.

**Contrast:** HarnessOpt-Bench measures optimizer capability; we provide a **runnable open loop** and seed skill library intended to **be** the object of optimization.

## Controlled harness self-improvement on ARC-AGI-3 (2026)

[Can LLMs Improve Their Own Harness?](https://arxiv.org/html/2610.30499)

Fixed protocol: build harness on development games, revise twice, evaluate on **20 held-out games**. Finds **development gains overstate held-out improvement** — motivation for explicit gates and ablations.

## Positioning summary

| System | What evolves | Acceptance test |
|--------|----------------|-----------------|
| DGM | Full agent code | Benchmark eval |
| ADAS | New agent programs | Validation archive |
| Voyager | Skill code (in world) | Environment verification |
| Self-Harness / VERSE / RRSI | Prompts, tools, skills | Held-out / regularized selection |
| **self-rewriting-harness (v1)** | **SYSTEM_PROMPT + 57 SKILL.md + checks** | **Held-out score gate (+ ungated ablation)** |
