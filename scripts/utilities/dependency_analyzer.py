#!/usr/bin/env python3
"""
Module Dependency Analyzer for StockHistory project
Analyzes import dependencies between modules to detect cycles and violations
"""
import ast
import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict
import networkx as nx


class DependencyAnalyzer:
    def __init__(self, root_path: str = "src"):
        self.root = Path(root_path)
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_graph: Dict[str, Set[str]] = defaultdict(set)
        self.all_modules: Set[str] = set()
        self.cycles: List[List[str]] = []
        self.layer_violations: List[Tuple[str, str]] = []
        
        # Define allowed layer hierarchy (lower number = higher level)
        self.module_layers = {
            'Controller': 1,
            'View': 1,
            'Model': 2,
            'BackTestService': 3,
            'FilterService': 3,
            'ExternalService': 3,
            'UpdateStockService': 3,
            'ScheduleService': 3,
            'Common': 4,
        }

    def extract_imports(self, file_path: Path) -> List[str]:
        """Extract all imports from a Python file"""
        imports = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=file_path)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        imports.append(name.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
        except Exception as e:
            print(f"Warning: Could not parse {file_path}: {e}", file=sys.stderr)
        
        return imports

    def get_module_name(self, file_path: Path) -> str:
        """Convert file path to module name"""
        relative = file_path.relative_to(self.root.parent)
        return str(relative).replace('/', '.').replace('\\', '.').replace('.py', '')

    def is_project_module(self, module_name: str) -> bool:
        """Check if import is from the project"""
        return module_name.startswith('src.')

    def analyze(self) -> None:
        """Analyze all Python files in the project"""
        print(f"Analyzing dependencies in {self.root}...\n")
        
        # Collect all modules and their dependencies
        for py_file in self.root.rglob("*.py"):
            if py_file.name.startswith('_'):
                continue
                
            module_name = self.get_module_name(py_file)
            self.all_modules.add(module_name)
            
            imports = self.extract_imports(py_file)
            for imp in imports:
                if self.is_project_module(imp):
                    self.dependency_graph[module_name].add(imp)
                    self.reverse_graph[imp].add(module_name)
        
        # Build graph for cycle detection
        G = nx.DiGraph()
        for module, deps in self.dependency_graph.items():
            G.add_node(module)
            for dep in deps:
                G.add_edge(module, dep)
        
        # Find cycles
        self.cycles = list(nx.simple_cycles(G))
        
        # Check layer violations
        self._check_layer_violations()

    def _check_layer_violations(self) -> None:
        """Check if higher layers are importing lower layers incorrectly"""
        for module, deps in self.dependency_graph.items():
            module_layer = self._get_module_layer(module)
            for dep in deps:
                dep_layer = self._get_module_layer(dep)
                if module_layer < dep_layer:
                    self.layer_violations.append((module, dep))

    def _get_module_layer(self, module_name: str) -> int:
        """Get the layer number for a module"""
        for name, layer in self.module_layers.items():
            if name in module_name:
                return layer
        return 0  # Unknown layer, allow everything

    def generate_report(self) -> str:
        """Generate human readable report"""
        report = []
        report.append("=" * 80)
        report.append("STOCKHISTORY DEPENDENCY ANALYSIS REPORT")
        report.append("=" * 80)
        
        report.append(f"\n✅ Total modules analyzed: {len(self.all_modules)}")
        report.append(f"\n🔄 Cyclic Dependencies Found: {len(self.cycles)}")
        
        if self.cycles:
            report.append("\nDetected cycles:")
            for i, cycle in enumerate(self.cycles, 1):
                report.append(f"  {i}. {' → '.join(cycle)}")
        
        report.append(f"\n⚠️  Layer Violations Found: {len(self.layer_violations)}")
        
        if self.layer_violations:
            report.append("\nDetected layer violations (higher layer importing lower layer):")
            for module, dep in self.layer_violations:
                report.append(f"  ❌ {module} → {dep}")
        
        report.append("\n" + "=" * 80)
        return "\n".join(report)

    def save_report(self, output_path: str = "dependency_report.txt") -> None:
        """Save report to file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(self.generate_report())
        print(f"Report saved to {output_path}")


if __name__ == "__main__":
    analyzer = DependencyAnalyzer()
    analyzer.analyze()
    print(analyzer.generate_report())
    analyzer.save_report()