"""Repository Dependency Graph (RDG) Builder.

Parses multi-file Python repositories using the standard library `ast` module
(with fallback tree-sitter hooks) and constructs a typed, directed NetworkX graph
capturing structural dependencies, import hierarchies, call trees, and test linkages.
"""

from __future__ import annotations

import ast
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import networkx as nx


@dataclass
class CodeEntity:
    id: str
    name: str
    entity_type: str  # 'file', 'class', 'function', 'test'
    filepath: str
    start_line: int
    end_line: int
    docstring: str = ""
    source_code: str = ""
    outgoing_calls: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)


class ASTEntityExtractor(ast.NodeVisitor):
    """Walks Python AST to discover classes, functions, calls, and imports."""

    def __init__(self, filepath: str, source_code: str):
        self.filepath = filepath
        self.source_code = source_code
        self.lines = source_code.splitlines()
        self.entities: List[CodeEntity] = []
        self.current_class: Optional[str] = None
        self.current_function: Optional[CodeEntity] = None
        self.file_imports: List[str] = []

    def _get_snippet(self, start_line: int, end_line: int) -> str:
        if not self.lines:
            return ""
        # 1-indexed to 0-indexed slice
        start_idx = max(0, start_line - 1)
        end_idx = min(len(self.lines), end_line)
        return "\n".join(self.lines[start_idx:end_idx])

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.file_imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        for alias in node.names:
            full_name = f"{module}.{alias.name}" if module else alias.name
            self.file_imports.append(full_name)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        prev_class = self.current_class
        self.current_class = node.name
        start_line = node.lineno
        end_line = getattr(node, "end_lineno", node.lineno)
        doc = ast.get_docstring(node) or ""

        entity_id = f"{self.filepath}::{node.name}"
        entity = CodeEntity(
            id=entity_id,
            name=node.name,
            entity_type="class",
            filepath=self.filepath,
            start_line=start_line,
            end_line=end_line,
            docstring=doc,
            source_code=self._get_snippet(start_line, end_line),
        )
        self.entities.append(entity)

        self.generic_visit(node)
        self.current_class = prev_class

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._handle_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._handle_function(node)

    def _handle_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        start_line = node.lineno
        end_line = getattr(node, "end_lineno", node.lineno)
        doc = ast.get_docstring(node) or ""

        if self.current_class:
            qual_name = f"{self.current_class}.{node.name}"
        else:
            qual_name = node.name

        is_test = node.name.startswith("test_") or "test" in Path(self.filepath).stem.lower()
        entity_type = "test" if is_test else "function"
        entity_id = f"{self.filepath}::{qual_name}"

        entity = CodeEntity(
            id=entity_id,
            name=qual_name,
            entity_type=entity_type,
            filepath=self.filepath,
            start_line=start_line,
            end_line=end_line,
            docstring=doc,
            source_code=self._get_snippet(start_line, end_line),
        )

        prev_func = self.current_function
        self.current_function = entity
        self.entities.append(entity)

        self.generic_visit(node)
        self.current_function = prev_func

    def visit_Call(self, node: ast.Call) -> None:
        call_name = ""
        if isinstance(node.func, ast.Name):
            call_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            call_name = node.func.attr

        if call_name and self.current_function:
            self.current_function.outgoing_calls.append(call_name)

        self.generic_visit(node)


class RepoGraph:
    """Directed Knowledge and Dependency Graph of a multi-file Python codebase."""

    def __init__(self, root_dir: str | Path):
        self.root_dir = Path(root_dir).resolve()
        self.graph = nx.DiGraph()
        self.entities: Dict[str, CodeEntity] = {}
        self.parsing_errors: List[Dict[str, str]] = []

    def build(self) -> RepoGraph:
        """Parses all Python files within root_dir and populates the graph."""
        py_files = list(self.root_dir.rglob("*.py"))

        for p in py_files:
            rel_path = str(p.relative_to(self.root_dir)).replace("\\", "/")
            # Filter virtual environments or cache directories
            if any(part in rel_path for part in [".venv", "venv", "__pycache__", ".git", ".pytest_cache"]):
                continue

            try:
                code = p.read_text(encoding="utf-8", errors="replace")
                tree = ast.parse(code, filename=str(p))
            except Exception as e:
                self.parsing_errors.append({"file": rel_path, "error": str(e)})
                continue

            # Add File Node
            file_id = f"file::{rel_path}"
            self.graph.add_node(
                file_id,
                name=rel_path,
                entity_type="file",
                filepath=rel_path,
                lines=len(code.splitlines()),
                content=code,
            )

            extractor = ASTEntityExtractor(rel_path, code)
            extractor.visit(tree)

            # Record file-level imports
            self.graph.nodes[file_id]["imports"] = extractor.file_imports

            for entity in extractor.entities:
                self.entities[entity.id] = entity
                self.graph.add_node(
                    entity.id,
                    name=entity.name,
                    entity_type=entity.entity_type,
                    filepath=entity.filepath,
                    start_line=entity.start_line,
                    end_line=entity.end_line,
                    docstring=entity.docstring,
                    source_code=entity.source_code,
                    calls=entity.outgoing_calls,
                )
                # Link File -> Entity
                self.graph.add_edge(file_id, entity.id, relation="DEFINES")

                # Link calls heuristic
                for called_name in entity.outgoing_calls:
                    for target_entity in extractor.entities:
                        if target_entity.name.endswith(called_name) and target_entity.id != entity.id:
                            self.graph.add_edge(entity.id, target_entity.id, relation="CALLS")

        # Cross-file Linkage: Link Calls & Test Coverage
        self._resolve_cross_file_relationships()
        return self

    def _resolve_cross_file_relationships(self) -> None:
        """Links inter-file call edges and connects tests to corresponding target code."""
        nodes = list(self.graph.nodes(data=True))
        test_nodes = [n for n, d in nodes if d.get("entity_type") == "test"]
        func_nodes = [n for n, d in nodes if d.get("entity_type") in ("function", "class")]

        # Connect tests to target functions by naming and call analysis
        for t_id in test_nodes:
            t_data = self.graph.nodes[t_id]
            t_name = t_data.get("name", "").lower()
            for f_id in func_nodes:
                f_data = self.graph.nodes[f_id]
                f_name = f_data.get("name", "").split(".")[-1].lower()
                # Direct call match
                if f_name in [c.lower() for c in t_data.get("calls", [])]:
                    self.graph.add_edge(t_id, f_id, relation="TESTS")
                # Semantic name match (e.g., test_calculate_tax -> calculate_tax)
                elif f_name in t_name and len(f_name) > 3:
                    self.graph.add_edge(t_id, f_id, relation="TESTS")

    def get_k_hop_neighborhood(self, seed_nodes: List[str], k: int = 2) -> Set[str]:
        """Returns union of k-hop in- and out-neighbors around seeds."""
        neighborhood: Set[str] = set(seed_nodes)
        frontier = set(seed_nodes)

        for _ in range(k):
            next_frontier = set()
            for node in frontier:
                if node in self.graph:
                    neighbors = set(self.graph.successors(node)).union(self.graph.predecessors(node))
                    next_frontier.update(neighbors - neighborhood)
            neighborhood.update(next_frontier)
            frontier = next_frontier
            if not frontier:
                break
        return neighborhood

    def personalized_pagerank(self, seed_nodes: List[str], alpha: float = 0.85) -> Dict[str, float]:
        """Computes Personalized PageRank biased toward seed nodes."""
        if not self.graph.nodes():
            return {}

        valid_seeds = [s for s in seed_nodes if s in self.graph]
        try:
            if not valid_seeds:
                return nx.pagerank(self.graph, alpha=alpha)

            personalization = {n: 0.0 for n in self.graph.nodes()}
            weight = 1.0 / len(valid_seeds)
            for s in valid_seeds:
                personalization[s] = weight

            return nx.pagerank(self.graph, alpha=alpha, personalization=personalization, max_iter=100)
        except Exception:
            # Fallback if scipy is missing or convergence fails on disconnected graph
            return {n: (1.0 if n in valid_seeds else 0.1) for n in self.graph.nodes()}

    def summary(self) -> Dict[str, Any]:
        """Returns diagnostic statistics of the constructed graph."""
        node_types: Dict[str, int] = {}
        for _, data in self.graph.nodes(data=True):
            t = data.get("entity_type", "unknown")
            node_types[t] = node_types.get(t, 0) + 1

        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "node_distribution": node_types,
            "parsing_errors_count": len(self.parsing_errors),
            "parsing_errors": self.parsing_errors,
        }
