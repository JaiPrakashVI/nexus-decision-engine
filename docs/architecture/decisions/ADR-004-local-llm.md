# ADR-004: Local Agentic AI & Isolation of LLM from Infrastructure Actuation

## Context
NEXUS incorporates generative AI for incident explanation, risk analysis, and candidate intervention review. Cyber-physical infrastructure (water systems, power distribution) requires strict safety guarantees against hallucinations, unintended commands, and external cloud dependencies.

## Alternatives Considered
1. **Cloud LLM (OpenAI / Anthropic)**: Requires external API keys, incurs external network latency, leaks infrastructure metadata, and fails in air-gapped critical infrastructure environments.
2. **Direct LLM Tool Execution**: Giving the LLM direct access to invoke infrastructure commands or actuate valves.
3. **Local LLM with Sandboxed Deterministic Decision Engine**: Running a local model (Ollama) as an advisory component within a strict constraint-solving and simulation pipeline.

## Decision
We adopted **Local LLM integration via Ollama, strictly isolated from direct infrastructure control**:
1. The LLM runs locally on-premises (or falls back to a deterministic research agent if Ollama is not active).
2. The Deterministic Decision Engine formulates candidate actions using standard operating procedures (SOPs) and enforces hard physical constraints.
3. The LLM ensemble (State Analyst, Risk Analyst, Recovery Planner, Adversarial Critic, Evaluator) produces structured JSON assessments.
4. All candidate actions must be validated inside an isolated digital twin simulation sandbox before recommendation to human operators.

## Rationale
- Zero air-gap violations; data never leaves the local machine.
- Absolute safety: Even if the LLM produces a hallucinated response or invalid syntax, the system rejects it and falls back to deterministic decision logic.
