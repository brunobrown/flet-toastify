---
icon: lucide/git-fork
---

# Diagrams

!!! info "Manual and generated diagrams"
    This page contains curated diagrams maintained manually to explain package intent and runtime behavior.
    The Mermaid `.mmd` files are the source of truth, and SVG files are generated with `beautiful-mermaid`.
    Code-generated diagrams live under **Architecture -> Generated diagrams** and are regenerated with `uv run task docs-diagrams`.

## Component view

Manual diagram. It explains how the global `toast` facade, the observable state and the
declarative components collaborate, and how a user app interacts with the package.

Source of truth: [`component-view.mmd`](../assets/diagrams/manual/component-view.mmd)
Generated artifact: [`component-view.svg`](../assets/diagrams/manual/component-view.svg)

<img class="beautiful-mermaid-static" src="../assets/diagrams/manual/component-view.svg" alt="Component view" />

## Toast lifecycle

Manual diagram. It documents the toast state machine
(`ENTERING → VISIBLE → LEAVING → removed`) and which events trigger each transition.

Source of truth: [`toast-lifecycle.mmd`](../assets/diagrams/manual/toast-lifecycle.mmd)
Generated artifact: [`toast-lifecycle.svg`](../assets/diagrams/manual/toast-lifecycle.svg)

<img class="beautiful-mermaid-static" src="../assets/diagrams/manual/toast-lifecycle.svg" alt="Toast lifecycle" />
