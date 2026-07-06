#!/usr/bin/env python3
"""Validate that public application modules are listed in the API Reference."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

MKDOCSTRINGS_BLOCK_RE = re.compile(r"^:::\s+([A-Za-z_][\w.]*)(?:\s|$)")


@dataclass(frozen=True)
class ApiReferenceCoverage:
    """Result of comparing Python modules with mkdocstrings blocks."""

    documented_modules: set[str]
    public_modules: set[str]
    stale_references: set[str]

    @property
    def missing_modules(self) -> set[str]:
        """Return public modules that are not exposed in the API Reference."""
        return self.public_modules - self.documented_modules

    @property
    def is_valid(self) -> bool:
        """Return whether the API Reference covers all known public modules."""
        return not self.missing_modules and not self.stale_references


def _try_rich() -> dict[str, Any] | None:
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
    except Exception:
        return None

    return {"Console": Console, "Panel": Panel, "Table": Table}


def _module_name_from_path(path: Path, *, root: Path) -> str:
    relative = path.relative_to(root.parent).with_suffix("")
    return ".".join(relative.parts)


def _iter_public_modules(root: Path, ignored_modules: set[str]) -> set[str]:
    modules: set[str] = set()
    for path in sorted(root.rglob("*.py")):
        if "__pycache__" in path.parts or path.name == "__init__.py":
            continue
        module_name = _module_name_from_path(path, root=root)
        if module_name not in ignored_modules:
            modules.add(module_name)
    return modules


def _iter_reference_modules(reference_path: Path, *, package: str) -> set[str]:
    modules: set[str] = set()
    for line in reference_path.read_text(encoding="utf-8").splitlines():
        match = MKDOCSTRINGS_BLOCK_RE.match(line.strip())
        if not match:
            continue
        identifier = match.group(1)
        if identifier == package or identifier.startswith(f"{package}."):
            modules.add(identifier)
    return modules


def check_api_reference(
    *,
    root: Path,
    reference_path: Path,
    package: str,
    ignored_modules: set[str],
) -> ApiReferenceCoverage:
    """Compare public Python modules with mkdocstrings entries."""
    public_modules = _iter_public_modules(root, ignored_modules)
    documented_modules = _iter_reference_modules(reference_path, package=package)
    stale_references = documented_modules - public_modules
    stale_references.discard(package)

    return ApiReferenceCoverage(
        documented_modules=documented_modules,
        public_modules=public_modules,
        stale_references=stale_references,
    )


def _summary_line(result: ApiReferenceCoverage) -> str:
    return (
        "API Reference coverage: "
        f"{len(result.documented_modules & result.public_modules)}/{len(result.public_modules)} "
        "public modules documented"
    )


def _print_plain(result: ApiReferenceCoverage) -> None:
    print(_summary_line(result))
    for module_name in sorted(result.missing_modules):
        print(f"missing API Reference module: {module_name}")
    for module_name in sorted(result.stale_references):
        print(f"stale API Reference module: {module_name}")


def _print_rich(result: ApiReferenceCoverage) -> None:
    rich = _try_rich()
    if not rich:
        _print_plain(result)
        return

    console = rich["Console"]()
    print(_summary_line(result))
    table = rich["Table"](title="API Reference coverage")
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    table.add_row("Public modules", str(len(result.public_modules)))
    table.add_row(
        "Documented public modules",
        str(len(result.documented_modules & result.public_modules)),
    )
    table.add_row("Missing modules", str(len(result.missing_modules)))
    table.add_row("Stale references", str(len(result.stale_references)))
    console.print(table)

    if result.is_valid:
        return

    missing = rich["Table"](title="API Reference drift")
    missing.add_column("Type")
    missing.add_column("Module")
    for module_name in sorted(result.missing_modules):
        missing.add_row("missing", module_name)
    for module_name in sorted(result.stale_references):
        missing.add_row("stale", module_name)
    console.print(rich["Panel"](missing, border_style="red"))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check that public src modules are exposed in docs/reference/api.md."
    )
    parser.add_argument("--root", default="src", help="Python package directory to scan.")
    parser.add_argument(
        "--reference",
        default="docs/reference/api.md",
        help="Markdown file containing mkdocstrings blocks.",
    )
    parser.add_argument("--package", default="src", help="Root Python package name.")
    parser.add_argument(
        "--ignore-module",
        action="append",
        default=[],
        help="Fully-qualified module intentionally excluded from the API Reference.",
    )
    args = parser.parse_args()

    result = check_api_reference(
        root=Path(args.root),
        reference_path=Path(args.reference),
        package=args.package,
        ignored_modules=set(args.ignore_module),
    )
    _print_rich(result)
    return 0 if result.is_valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
