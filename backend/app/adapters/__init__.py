"""Adapters implementing the orchestrator ports.

``fixtures`` = offline, deterministic implementations (tests + local CLI). Azure adapters
(Document Intelligence, Foundry IQ, Azure OpenAI) land here later, each satisfying the same
port contract so the orchestrator is unchanged (Liskov / Dependency Inversion).
"""
