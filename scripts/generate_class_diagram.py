#!/usr/bin/env python3
"""Generate Mermaid diagrams from Python source without importing app code.

This script is intentionally AST-based so documentation generation cannot execute
module-level side effects such as opening RabbitMQ/S3 clients or loading secrets.
It is a local documentation aid, not part of the runtime application.
"""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class ClassInfo:
    name: str
    module: str
    bases: tuple[str, ...]
    attributes: tuple[str, ...]
    methods: tuple[str, ...]
    relations: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ModuleInfo:
    name: str
    path: Path
    functions: tuple[str, ...]
    classes: tuple[str, ...]
    dependencies: tuple[str, ...]


def _module_name(path: Path, root: Path) -> str:
    relative = path.relative_to(root.parent).with_suffix("")
    return ".".join(relative.parts)


def _is_public(name: str) -> bool:
    return not name.startswith("_")


def _safe_unparse(node: ast.AST | None) -> str | None:
    if node is None:
        return None
    try:
        return ast.unparse(node)
    except Exception:
        return None


def _short_type(annotation: ast.AST | None) -> str | None:
    raw = _safe_unparse(annotation)
    if not raw:
        return None
    return (
        raw.replace("typing.", "")
        .replace(" | None", "?")
        .replace("None | ", "")
        .replace("list[", "list~")
        .replace("dict[", "dict~")
        .replace("]", "~")
    )


def _collect_relation_names(annotation: ast.AST | None, known: set[str]) -> set[str]:
    raw = _safe_unparse(annotation)
    if not raw:
        return set()
    return {name for name in known if name in raw}


def _node_id(value: str) -> str:
    return value.replace(".", "_").replace("/", "_").replace("-", "_")


def _public_function_names(tree: ast.Module) -> tuple[str, ...]:
    return tuple(
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and _is_public(node.name)
    )


def _top_level_class_names(tree: ast.Module) -> tuple[str, ...]:
    return tuple(node.name for node in tree.body if isinstance(node, ast.ClassDef))


def _resolve_module_dependency(raw: str, module_names: set[str]) -> str | None:
    candidates = [name for name in module_names if raw == name or raw.startswith(f"{name}.")]
    if not candidates:
        return None
    return max(candidates, key=len)


def _imports_from_tree(tree: ast.Module, root_package: str, module_names: set[str]) -> set[str]:
    dependencies: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == root_package or alias.name.startswith(f"{root_package}."):
                    dependency = _resolve_module_dependency(alias.name, module_names)
                    if dependency:
                        dependencies.add(dependency)
        elif (
            isinstance(node, ast.ImportFrom)
            and node.module
            and (node.module == root_package or node.module.startswith(f"{root_package}."))
        ):
            dependency = _resolve_module_dependency(node.module, module_names)
            if dependency:
                dependencies.add(dependency)
    return dependencies


def _field_from_annassign(node: ast.AnnAssign) -> tuple[str, str | None] | None:
    if not isinstance(node.target, ast.Name):
        return None
    if not _is_public(node.target.id):
        return None
    return node.target.id, _short_type(node.annotation)


def _field_from_assign(node: ast.Assign) -> tuple[str, str | None] | None:
    if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
        return None
    name = node.targets[0].id
    if not _is_public(name):
        return None
    return name, None


def _method_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str | None:
    if not _is_public(node.name):
        return None
    args = [arg.arg for arg in node.args.args if arg.arg != "self"]
    suffix = " async" if isinstance(node, ast.AsyncFunctionDef) else ""
    return f"{node.name}({', '.join(args)}){suffix}"


def _class_bases(node: ast.ClassDef) -> tuple[str, ...]:
    bases: list[str] = []
    for base in node.bases:
        raw = _safe_unparse(base)
        if raw:
            bases.append(raw.split(".")[-1])
    return tuple(bases)


def _collect_raw_classes(files: list[Path], root: Path) -> dict[str, tuple[ast.ClassDef, str]]:
    raw_classes: dict[str, tuple[ast.ClassDef, str]] = {}
    for path in files:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        module = _module_name(path, root)
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                raw_classes[node.name] = (node, module)
    return raw_classes


def _collect_modules(files: list[Path], root: Path) -> dict[str, ModuleInfo]:
    parsed_modules = {
        _module_name(path, root): (
            path,
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path)),
        )
        for path in files
    }
    module_names = set(parsed_modules)
    root_package = root.name
    modules: dict[str, ModuleInfo] = {}

    for name, (path, tree) in parsed_modules.items():
        dependencies = _imports_from_tree(tree, root_package, module_names)
        modules[name] = ModuleInfo(
            name=name,
            path=path,
            functions=_public_function_names(tree),
            classes=_top_level_class_names(tree),
            dependencies=tuple(sorted(item for item in dependencies if item != name)),
        )
    return modules


def _without_init_modules(modules: dict[str, ModuleInfo]) -> dict[str, ModuleInfo]:
    return {name: info for name, info in modules.items() if not name.endswith(".__init__")}


def _append_attribute(
    item: ast.AnnAssign | ast.Assign,
    attributes: list[str],
    relations: set[str],
    known: set[str],
) -> None:
    field_data = (
        _field_from_annassign(item) if isinstance(item, ast.AnnAssign) else _field_from_assign(item)
    )
    if not field_data:
        return

    field_name, field_type = field_data
    attributes.append(f"{field_type or 'Any'} {field_name}")
    if isinstance(item, ast.AnnAssign):
        relations.update(_collect_relation_names(item.annotation, known))


def _append_method(
    item: ast.FunctionDef | ast.AsyncFunctionDef,
    methods: list[str],
    relations: set[str],
    known: set[str],
) -> None:
    signature = _method_signature(item)
    if signature:
        methods.append(signature)
    for arg in item.args.args:
        relations.update(_collect_relation_names(arg.annotation, known))
    relations.update(_collect_relation_names(item.returns, known))


def _analyze_class_body(
    node: ast.ClassDef, known: set[str]
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    attributes: list[str] = []
    methods: list[str] = []
    relations: set[str] = set()

    for item in node.body:
        if isinstance(item, ast.AnnAssign | ast.Assign):
            _append_attribute(item, attributes, relations, known)
        elif isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef):
            _append_method(item, methods, relations, known)

    return (
        tuple(dict.fromkeys(attributes)),
        tuple(dict.fromkeys(methods)),
        tuple(sorted(rel for rel in relations if rel != node.name)),
    )


def _discover_classes(files: list[Path], root: Path) -> dict[str, ClassInfo]:
    raw_classes = _collect_raw_classes(files, root)
    known = set(raw_classes)
    classes: dict[str, ClassInfo] = {}
    for name, (node, module) in raw_classes.items():
        attributes, methods, relations = _analyze_class_body(node, known)

        classes[name] = ClassInfo(
            name=name,
            module=module,
            bases=_class_bases(node),
            attributes=attributes,
            methods=methods,
            relations=relations,
        )
    return classes


def _iter_python_files(root: Path, excludes: tuple[str, ...]) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*.py"):
        normalized = path.as_posix()
        if any(part in normalized for part in excludes):
            continue
        files.append(path)
    return sorted(files)


def _filter_classes(
    classes: dict[str, ClassInfo], includes: tuple[str, ...]
) -> dict[str, ClassInfo]:
    if not includes:
        return classes
    return {
        name: info
        for name, info in classes.items()
        if any(info.module == item or info.module.startswith(f"{item}.") for item in includes)
    }


def _render_class(info: ClassInfo, max_methods: int) -> list[str]:
    lines = [f"  class {info.name} {{"]
    for base in info.bases:
        if base in {"Protocol", "BaseModel", "Exception"}:
            lines.append(f"    <<{base}>>")
    for attribute in info.attributes:
        lines.append(f"    +{attribute}")
    for method in info.methods[:max_methods]:
        lines.append(f"    +{method}")
    if len(info.methods) > max_methods:
        lines.append(f"    +... {len(info.methods) - max_methods} more methods")
    lines.append("  }")
    return lines


def _render_mermaid(classes: dict[str, ClassInfo], *, title: str, max_methods: int) -> str:
    lines = ["classDiagram", "  direction LR", f"  %% {title}", ""]
    for info in sorted(classes.values(), key=lambda item: (item.module, item.name)):
        lines.extend(_render_class(info, max_methods))
        lines.append("")

    known = set(classes)
    for info in sorted(classes.values(), key=lambda item: item.name):
        for base in info.bases:
            if base in known:
                lines.append(f"  {info.name} --|> {base}")
        for relation in info.relations:
            if relation in known:
                lines.append(f"  {info.name} ..> {relation}")
    return "\n".join(lines).rstrip() + "\n"


def _render_module_class(info: ModuleInfo, max_functions: int) -> list[str]:
    node_id = _node_id(info.name)
    lines = [f"  class {node_id} {{", "    <<module>>", f"    +module {info.name}"]
    for class_name in info.classes:
        lines.append(f"    +class {class_name}")
    for function_name in info.functions[:max_functions]:
        lines.append(f"    +{function_name}()")
    if len(info.functions) > max_functions:
        lines.append(f"    +... {len(info.functions) - max_functions} more functions")
    lines.append("  }")
    return lines


def _render_module_dependencies(
    modules: dict[str, ModuleInfo], *, title: str, max_functions: int
) -> str:
    lines = ["classDiagram", "  direction LR", f"  %% {title}", ""]
    for info in sorted(modules.values(), key=lambda item: item.name):
        lines.extend(_render_module_class(info, max_functions))
        lines.append("")

    for info in sorted(modules.values(), key=lambda item: item.name):
        source = _node_id(info.name)
        for dependency in info.dependencies:
            if dependency in modules:
                lines.append(f"  {source} --> {_node_id(dependency)}")
    return "\n".join(lines).rstrip() + "\n"


def _module_label(info: ModuleInfo) -> str:
    label = f"{info.name.replace('.', '/')}.py"
    if info.classes:
        label += "<br/>classes: " + ", ".join(info.classes)
    if info.functions:
        label += "<br/>functions: " + ", ".join(info.functions)
    return label


def _group_label(name: str) -> str:
    return f"{name.replace('.', '/')}/"


def _hierarchy_id(name: str, ids: dict[str, str]) -> str:
    if name not in ids:
        ids[name] = f"node_{len(ids) + 1}"
    return ids[name]


def _immediate_children(parent: str, modules: dict[str, ModuleInfo]) -> tuple[str, ...]:
    prefix = f"{parent}."
    children = {
        name[len(prefix) :].split(".", maxsplit=1)[0] for name in modules if name.startswith(prefix)
    }
    return tuple(sorted(children))


def _render_hierarchy_group(
    lines: list[str],
    parent: str,
    modules: dict[str, ModuleInfo],
    ids: dict[str, str],
    *,
    depth: int,
) -> None:
    indent = "  " * depth
    group_id = _hierarchy_id(parent, ids)
    group_label = _group_label(parent)
    lines.append(f'{indent}subgraph {group_id}["{group_label}"]')
    lines.append(f"{indent}  direction TD")

    for child in _immediate_children(parent, modules):
        child_name = f"{parent}.{child}"
        if child_name in modules:
            label = _module_label(modules[child_name])
            lines.append(f'{indent}  {_hierarchy_id(child_name, ids)}["{label}"]:::module')
        else:
            _render_hierarchy_group(lines, child_name, modules, ids, depth=depth + 1)

    lines.append(f"{indent}end")


def _render_module_hierarchy(modules: dict[str, ModuleInfo], *, title: str) -> str:
    lines = ["flowchart TD", f"  %% {title}"]
    ids: dict[str, str] = {}
    root_names = sorted({name.split(".", maxsplit=1)[0] for name in modules})
    for root_name in root_names:
        if root_name in modules:
            label = _module_label(modules[root_name])
            lines.append(f'  {_hierarchy_id(root_name, ids)}["{label}"]:::module')
        else:
            _render_hierarchy_group(lines, root_name, modules, ids, depth=1)
    lines.append("")
    lines.append("  classDef module fill:#f8fafc,stroke:#94a3b8,color:#111827")
    return "\n".join(lines).rstrip() + "\n"


def _append_hybrid_declarations(
    lines: list[str],
    classes: dict[str, ClassInfo],
    modules: dict[str, ModuleInfo],
    *,
    max_methods: int,
    max_functions: int,
) -> None:
    for info in sorted(modules.values(), key=lambda item: item.name):
        lines.extend(_render_module_class(info, max_functions))
        lines.append("")
    for info in sorted(classes.values(), key=lambda item: (item.module, item.name)):
        lines.extend(_render_class(info, max_methods))
        lines.append("")


def _append_class_relationships(lines: list[str], classes: dict[str, ClassInfo]) -> None:
    for info in sorted(classes.values(), key=lambda item: (item.module, item.name)):
        for base in info.bases:
            if base in classes:
                lines.append(f"  {info.name} --|> {base}")
        for relation in info.relations:
            if relation in classes:
                lines.append(f"  {info.name} ..> {relation}")


def _append_module_dependency_relationships(
    lines: list[str], modules: dict[str, ModuleInfo]
) -> None:
    for info in sorted(modules.values(), key=lambda item: item.name):
        source = _node_id(info.name)
        for dependency in info.dependencies:
            if dependency in modules:
                lines.append(f"  {source} --> {_node_id(dependency)}")


def _append_module_class_relationships(
    lines: list[str], classes: dict[str, ClassInfo], modules: dict[str, ModuleInfo]
) -> None:
    for info in sorted(classes.values(), key=lambda item: (item.module, item.name)):
        if info.module in modules:
            lines.append(f"  {_node_id(info.module)} ..> {info.name}")


def _render_hybrid(
    classes: dict[str, ClassInfo],
    modules: dict[str, ModuleInfo],
    *,
    title: str,
    max_methods: int,
    max_functions: int,
) -> str:
    lines = ["classDiagram", "  direction LR", f"  %% {title}", ""]
    _append_hybrid_declarations(
        lines,
        classes,
        modules,
        max_methods=max_methods,
        max_functions=max_functions,
    )
    _append_module_class_relationships(lines, classes, modules)
    _append_class_relationships(lines, classes)
    _append_module_dependency_relationships(lines, modules)
    return "\n".join(lines).rstrip() + "\n"


def _write_output(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _diagram_page_title(name: str) -> str:
    return {
        "classes": "Generated Class Details",
        "modules": "Generated Module Dependencies",
        "hierarchy": "Generated Module Hierarchy",
        "hybrid": "Generated Hybrid Audit View",
    }[name]


def _diagram_page_description(name: str) -> str:
    return {
        "classes": (
            "Code-generated class view with public attributes, public methods and type-level "
            "relationships discovered from Python AST."
        ),
        "modules": (
            "Code-generated module dependency view. Arrows show Python imports between modules, "
            "which helps reviewers understand who depends on whom."
        ),
        "hierarchy": (
            "Code-generated package hierarchy view. Nested groups represent filesystem/package "
            "containment, not class inheritance."
        ),
        "hybrid": (
            "Code-generated audit view combining module dependencies and class details. This is "
            "intentionally denser and is better suited for review than for onboarding."
        ),
    }[name]


def _render_markdown_page(name: str, mermaid: str) -> str:
    title = _diagram_page_title(name)
    description = _diagram_page_description(name)
    return f"""---
icon: lucide/workflow
---

# {title}

!!! info "Generated diagram"
    This page is generated by `scripts/generate_class_diagram.py`.
    Do not edit the Mermaid block manually. Run `uv run task docs-diagrams` and review the diff.

{description}

```mermaid
{mermaid.rstrip()}
```
"""


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Mermaid diagrams from Python AST.")
    parser.add_argument("--module", default="app", help="Root package directory to scan.")
    parser.add_argument("--output", help="Output .mmd file. Prints to stdout when omitted.")
    parser.add_argument(
        "--output-dir", help="Output directory used when --diagram all is selected."
    )
    parser.add_argument(
        "--diagram",
        choices=["classes", "modules", "hierarchy", "hybrid", "all"],
        default="classes",
        help="Diagram type to generate.",
    )
    parser.add_argument(
        "--include",
        action="append",
        default=[],
        help="Module prefix to include. Can be repeated. Defaults to all scanned modules.",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=["__pycache__", ".venv", "tests"],
        help="Path fragment to exclude. Can be repeated.",
    )
    parser.add_argument("--max-methods", type=int, default=8)
    parser.add_argument("--max-functions", type=int, default=8)
    parser.add_argument("--title", default="Generated from Python AST")
    parser.add_argument(
        "--include-init",
        action="store_true",
        help="Include __init__.py modules in module, hierarchy and hybrid diagrams.",
    )
    parser.add_argument(
        "--format",
        choices=["mermaid", "markdown"],
        default="mermaid",
        help="Write raw .mmd files or Markdown pages containing Mermaid diagrams.",
    )
    return parser.parse_args()


def _diagram_outputs(
    diagram: str,
    classes: dict[str, ClassInfo],
    modules: dict[str, ModuleInfo],
    *,
    title: str,
    max_methods: int,
    max_functions: int,
) -> dict[str, str]:
    outputs = {
        "classes": _render_mermaid(classes, title=f"{title}: classes", max_methods=max_methods),
        "modules": _render_module_dependencies(
            modules, title=f"{title}: module dependencies", max_functions=max_functions
        ),
        "hierarchy": _render_module_hierarchy(modules, title=f"{title}: module hierarchy"),
        "hybrid": _render_hybrid(
            classes,
            modules,
            title=f"{title}: hybrid modules and classes",
            max_methods=max_methods,
            max_functions=max_functions,
        ),
    }
    if diagram == "all":
        return outputs
    return {diagram: outputs[diagram]}


def main() -> int:
    args = _parse_args()
    root = Path(args.module).resolve()
    files = _iter_python_files(root, tuple(args.exclude))
    classes = _filter_classes(_discover_classes(files, root), tuple(args.include))
    modules = _collect_modules(files, root)
    if args.include:
        modules = {
            name: info
            for name, info in modules.items()
            if any(name == item or name.startswith(f"{item}.") for item in args.include)
        }
    if not args.include_init:
        modules = _without_init_modules(modules)
    outputs = _diagram_outputs(
        args.diagram,
        classes,
        modules,
        title=args.title,
        max_methods=args.max_methods,
        max_functions=args.max_functions,
    )

    if args.diagram == "all":
        output_dir = Path(args.output_dir or args.output or "tmp/generated_diagrams")
        for name, content in outputs.items():
            suffix = "md" if args.format == "markdown" else "mmd"
            output = _render_markdown_page(name, content) if args.format == "markdown" else content
            _write_output(output_dir / f"{name}.{suffix}", output)
        return 0

    if args.output:
        name, content = next(iter(outputs.items()))
        output = _render_markdown_page(name, content) if args.format == "markdown" else content
        _write_output(Path(args.output), output)
    else:
        print(next(iter(outputs.values())), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
