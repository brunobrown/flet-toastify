#!/usr/bin/env python3
"""Validate documentation coverage for the Python public API surface."""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Finding:
    """A missing documentation item detected by the AST checker."""

    path: Path
    line: int
    kind: str
    name: str


@dataclass(frozen=True)
class CoverageResult:
    """Aggregated docstring coverage result."""

    documented: int
    total: int
    findings: list[Finding]

    @property
    def percentage(self) -> float:
        """Return coverage as percentage."""
        if self.total == 0:
            return 100.0
        return (self.documented / self.total) * 100


def _try_rich() -> dict[str, Any] | None:
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
    except Exception:
        return None

    return {"Console": Console, "Panel": Panel, "Table": Table}


def _iter_python_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_file() and path.suffix == ".py":
            files.append(path)
            continue
        if path.is_dir():
            files.extend(
                file
                for file in path.rglob("*.py")
                if "__pycache__" not in file.parts and file.name != "__init__.py"
            )
    return sorted(files)


def _is_public_name(name: str) -> bool:
    return not name.startswith("_")


def _is_field_call(node: ast.AST) -> bool:
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id == "Field":
            return True
        if isinstance(node.func, ast.Attribute) and node.func.attr == "Field":
            return True
    return False


def _field_has_description(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    return any(
        keyword.arg == "description"
        and isinstance(keyword.value, ast.Constant)
        and keyword.value.value
        for keyword in node.keywords
    )


def _has_following_attribute_docstring(body: list[ast.stmt], index: int) -> bool:
    next_index = index + 1
    if next_index >= len(body):
        return False
    next_node = body[next_index]
    return (
        isinstance(next_node, ast.Expr)
        and isinstance(next_node.value, ast.Constant)
        and isinstance(next_node.value.value, str)
        and bool(next_node.value.value.strip())
    )


def _public_attribute_names(node: ast.Assign | ast.AnnAssign) -> list[str]:
    targets = [node.target] if isinstance(node, ast.AnnAssign) else list(node.targets)

    names: list[str] = []
    for target in targets:
        if isinstance(target, ast.Name) and _is_public_name(target.id) and not target.id.isupper():
            names.append(target.id)
    return names


def _attribute_is_documented(
    node: ast.Assign | ast.AnnAssign,
    *,
    body: list[ast.stmt],
    index: int,
) -> bool:
    value = node.value
    if _is_field_call(value) and _field_has_description(value):
        return True
    return _has_following_attribute_docstring(body, index)


def check_docstrings(paths: list[Path]) -> CoverageResult:
    """Check docstring coverage for a set of Python paths."""
    documented = 0
    total = 0
    findings: list[Finding] = []

    for path in _iter_python_files(paths):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        result = _check_file_with_tree(path, tree)
        documented += result.documented
        total += result.total
        findings.extend(result.findings)

    return CoverageResult(documented=documented, total=total, findings=findings)


def _count_docstring(
    *,
    path: Path,
    node: ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
    kind: str,
    name: str,
) -> CoverageResult:
    if ast.get_docstring(node):
        return CoverageResult(documented=1, total=1, findings=[])
    line = getattr(node, "lineno", 1)
    return CoverageResult(
        documented=0,
        total=1,
        findings=[Finding(path=path, line=line, kind=kind, name=name)],
    )


def _combine(results: list[CoverageResult]) -> CoverageResult:
    return CoverageResult(
        documented=sum(result.documented for result in results),
        total=sum(result.total for result in results),
        findings=[finding for result in results for finding in result.findings],
    )


def _check_attribute(
    *,
    path: Path,
    class_name: str,
    node: ast.Assign | ast.AnnAssign,
    body: list[ast.stmt],
    index: int,
) -> CoverageResult:
    results: list[CoverageResult] = []
    is_documented = _attribute_is_documented(node, body=body, index=index)
    for attribute_name in _public_attribute_names(node):
        if is_documented:
            results.append(CoverageResult(documented=1, total=1, findings=[]))
            continue
        results.append(
            CoverageResult(
                documented=0,
                total=1,
                findings=[
                    Finding(
                        path=path,
                        line=node.lineno,
                        kind="attribute",
                        name=f"{class_name}.{attribute_name}",
                    )
                ],
            )
        )
    return _combine(results)


def _check_class(path: Path, node: ast.ClassDef) -> CoverageResult:
    results = [_count_docstring(path=path, node=node, kind="class", name=node.name)]
    for index, child in enumerate(node.body):
        if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef) and _is_public_name(
            child.name
        ):
            results.append(_count_docstring(path=path, node=child, kind="method", name=child.name))
        elif isinstance(child, ast.Assign | ast.AnnAssign):
            results.append(
                _check_attribute(
                    path=path,
                    class_name=node.name,
                    node=child,
                    body=node.body,
                    index=index,
                )
            )
    return _combine(results)


def _check_file_with_tree(path: Path, tree: ast.Module) -> CoverageResult:
    results = [
        _count_docstring(path=path, node=tree, kind="module", name=path.as_posix()),
    ]
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and _is_public_name(node.name):
            results.append(_check_class(path, node))
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and _is_public_name(
            node.name
        ):
            results.append(_count_docstring(path=path, node=node, kind="function", name=node.name))
    return _combine(results)


def _print_result(result: CoverageResult, *, fail_under: float) -> None:
    summary = (
        f"Docstring coverage: {result.percentage:.2f}% "
        f"({result.documented}/{result.total}, required {fail_under:.2f}%)"
    )
    print(summary)

    rich = _try_rich()
    if rich:
        console = rich["Console"]()
        table = rich["Table"](title="Docstring coverage")
        table.add_column("Metric")
        table.add_column("Value", justify="right")
        table.add_row("Documented items", str(result.documented))
        table.add_row("Total items", str(result.total))
        table.add_row("Coverage", f"{result.percentage:.2f}%")
        table.add_row("Required", f"{fail_under:.2f}%")
        console.print(table)

        if result.findings:
            missing = rich["Table"](title="Missing documentation")
            missing.add_column("File")
            missing.add_column("Line", justify="right")
            missing.add_column("Kind")
            missing.add_column("Name")
            for finding in result.findings:
                missing.add_row(
                    finding.path.as_posix(),
                    str(finding.line),
                    finding.kind,
                    finding.name,
                )
            console.print(rich["Panel"](missing, border_style="red"))
        return

    for finding in result.findings:
        print(f"{finding.path}:{finding.line}: missing {finding.kind} docstring: {finding.name}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Python public API docstring coverage.")
    parser.add_argument("--paths", nargs="+", default=["src"], help="Files or directories to scan.")
    parser.add_argument("--fail-under", type=float, default=100.0, help="Minimum coverage percent.")
    args = parser.parse_args()

    paths = [Path(path) for path in args.paths]
    result = check_docstrings(paths)
    _print_result(result, fail_under=args.fail_under)

    if result.percentage < args.fail_under:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
