"""
Coverage Checker - Verifiziert Code-zu-Docs Coverage
"""
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass


@dataclass
class CoverageReport:
    """Coverage-Bericht"""
    total_classes: int
    documented_classes: int
    missing_classes: List[str]
    total_functions: int
    documented_functions: int
    missing_functions: List[str]
    coverage_percentage: float

    def is_complete(self) -> bool:
        """Prüft ob 100% Coverage erreicht ist"""
        return len(self.missing_classes) == 0 and len(self.missing_functions) == 0


class CoverageChecker:
    """
    Prüft Coverage zwischen Code und Dokumentation
    """

    def __init__(self, project_path: str, docs_path: str = None):
        self.project_path = Path(project_path)
        self.docs_path = Path(docs_path) if docs_path else self.project_path / "auto_docs"

    def check_coverage(self) -> CoverageReport:
        """
        Führt vollständigen Coverage-Check durch

        Returns:
            CoverageReport mit allen Metriken
        """
        # 1. Scanne Code
        code_classes, code_functions = self._scan_code()

        # 2. Scanne Docs
        documented_classes, documented_functions = self._scan_docs()

        # 3. Berechne Delta (Case-Insensitive)
        code_classes_lower = {c.lower(): c for c in code_classes}
        docs_classes_lower = {d.lower() for d in documented_classes}

        missing_classes_lower = set(code_classes_lower.keys()) - docs_classes_lower
        missing_classes = sorted([code_classes_lower[m] for m in missing_classes_lower])

        # Funktionen (vereinfacht - könnte verbessert werden)
        missing_functions = sorted(list(code_functions - documented_functions))

        # 4. Berechne Coverage
        total_elements = len(code_classes) + len(code_functions)
        documented_elements = len(documented_classes) + len(documented_functions)

        if total_elements > 0:
            coverage = (documented_elements / total_elements) * 100
        else:
            coverage = 100.0

        return CoverageReport(
            total_classes=len(code_classes),
            documented_classes=len(documented_classes),
            missing_classes=missing_classes,
            total_functions=len(code_functions),
            documented_functions=len(documented_functions),
            missing_functions=missing_functions[:20],  # Limit für UI
            coverage_percentage=coverage
        )

    def _scan_code(self) -> Tuple[Set[str], Set[str]]:
        """
        Scannt Code-Verzeichnis nach Klassen und Funktionen

        Returns:
            (set of class names, set of function names)
        """
        classes = set()
        functions = set()

        # Scanne services/ingest/src (Hauptfokus für Soulkitchen)
        code_dirs = [
            self.project_path / "services" / "ingest" / "src",
            self.project_path / "services" / "agent" / "src",
            self.project_path / "services" / "knowledge" / "src",
            self.project_path / "services" / "graph" / "src",
        ]

        for code_dir in code_dirs:
            if not code_dir.exists():
                continue

            for py_file in code_dir.rglob('*.py'):
                try:
                    content = py_file.read_text()

                    # Finde Klassen
                    found_classes = re.findall(r'^class (\w+)', content, re.MULTILINE)
                    classes.update(found_classes)

                    # Finde Top-Level Funktionen
                    found_functions = re.findall(r'^def (\w+)', content, re.MULTILINE)
                    functions.update(found_functions)

                except Exception:
                    pass

        return classes, functions

    def _scan_docs(self) -> Tuple[Set[str], Set[str]]:
        """
        Scannt Docs-Verzeichnis nach dokumentierten Elementen

        Returns:
            (set of documented class names, set of documented function names)
        """
        classes = set()
        functions = set()

        if not self.docs_path.exists():
            return classes, functions

        for doc_file in self.docs_path.glob('*.md'):
            name = doc_file.stem

            # Klassen-Docs
            if '.class' in name:
                clean_name = name.replace('.class', '')
                classes.add(clean_name)
            # API-Docs (könnte auch Funktionen sein)
            elif '.api' in name:
                clean_name = name.replace('.api', '')
                functions.add(clean_name)
            else:
                # Generische Docs (Funktionen)
                functions.add(name)

        return classes, functions

    def print_report(self, report: CoverageReport) -> None:
        """
        Gibt Coverage-Report schön formatiert aus
        """
        print("=" * 70)
        print("📊 CODE COVERAGE REPORT")
        print("=" * 70)
        print()

        print(f"🔧 KLASSEN:")
        print(f"   Im Code:        {report.total_classes}")
        print(f"   Dokumentiert:   {report.documented_classes}")
        print(f"   ❌ FEHLEND:     {len(report.missing_classes)}")

        if report.missing_classes:
            print(f"\n   Fehlende Klassen:")
            for cls in report.missing_classes[:20]:
                print(f"      - {cls}")
            if len(report.missing_classes) > 20:
                print(f"      ... und {len(report.missing_classes) - 20} weitere")

        print(f"\n⚙️  FUNKTIONEN:")
        print(f"   Im Code:        {report.total_functions}")
        print(f"   Dokumentiert:   {report.documented_functions}")
        print(f"   ❌ FEHLEND:     {len(report.missing_functions)}")

        print()
        print("=" * 70)
        print(f"📈 GESAMT COVERAGE: {report.coverage_percentage:.1f}%")

        if report.is_complete():
            print("✅ 100% COVERAGE ERREICHT!")
        else:
            total_missing = len(report.missing_classes) + len(report.missing_functions)
            print(f"⚠️  Noch {total_missing} Elemente fehlen")

        print("=" * 70)
