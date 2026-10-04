# ADR-009a: Chat model on Azure AI Foundry

- **Status:** Open
- **Date:** 2026-10-03
- **Source:** Architecture views deck and HLD (decision register)

## Context
Options considered: Claude via Anthropic API; models on Azure AI Foundry.

## Decision
Foundry chat deployment named in config; the specific model (gpt-5-mini vs. a Claude model on Foundry) is not yet chosen.

## Rationale
Azure-native, reachable with Managed Identity, same platform as OnePulse.

## Consequences
Model choice still open; the factory supports both OpenAI-style and Azure AI Inference providers.
