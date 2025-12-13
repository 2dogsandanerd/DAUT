import time
import os
import gc
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class PerformanceMetrics:
    """Datenklasse für Performance-Metriken"""
    start_time: float
    end_time: float
    duration: float
    cpu_percent: float  # Dies wird jetzt als geschätzter Wert berechnet
    memory_percent: float  # Dies wird jetzt als geschätzter Wert berechnet
    memory_used_mb: float
    files_processed: int
    file_sizes: List[int]
    directories_scanned: int
    avg_file_size: float
    largest_file: int
    smallest_file: int


class PerformanceAnalyzer:
    """Klasse zur Analyse der Scan-Performance"""

    def __init__(self):
        self.metrics: Optional[PerformanceMetrics] = None

    def start_timing(self) -> float:
        """Startet die Zeitmessung"""
        return time.time()

    def stop_timing(self, start_time: float, files_processed: int = 0,
                   file_sizes: List[int] = None, directories_scanned: int = 0) -> PerformanceMetrics:
        """Stoppt die Zeitmessung und sammelt Metriken"""
        end_time = time.time()
        duration = end_time - start_time

        # Schätzung der CPU-Auslastung basierend auf Dauer und Anzahl verarbeiteter Dateien
        if duration > 0:
            # Geschätzte CPU-Last - je mehr Dateien pro Zeit, desto höher die Last
            estimated_cpu = min(100.0, (files_processed / duration) * 0.1)  # Skalierungsfaktor
        else:
            estimated_cpu = 0.0

        # Speicherberechnung unter Verwendung der Python-interner gc-Statistik
        # und Schätzung des Dateigrößenverbrauchs
        import sys
        memory_allocated_estimate = sum(file_sizes) / (1024 * 1024) if file_sizes else 0  # in MB

        # Annahme: Basis-Speicherbedarf plus Dateiinhalte
        estimated_memory_mb = memory_allocated_estimate + 10  # Basisbedarf in MB
        estimated_memory_percent = min(100.0, (estimated_memory_mb / 1024) * 10)  # Schätzung (angenommen 8GB RAM)

        # Datei-Metriken
        if file_sizes:
            avg_file_size = sum(file_sizes) / len(file_sizes) if file_sizes else 0
            largest_file = max(file_sizes) if file_sizes else 0
            smallest_file = min(file_sizes) if file_sizes else 0
        else:
            avg_file_size = largest_file = smallest_file = 0

        self.metrics = PerformanceMetrics(
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            cpu_percent=estimated_cpu,
            memory_percent=estimated_memory_percent,
            memory_used_mb=estimated_memory_mb,
            files_processed=files_processed,
            file_sizes=file_sizes or [],
            directories_scanned=directories_scanned,
            avg_file_size=avg_file_size,
            largest_file=largest_file,
            smallest_file=smallest_file
        )

        return self.metrics
    
    def get_performance_report(self) -> Dict:
        """Gibt einen detaillierten Performance-Bericht zurück"""
        if not self.metrics:
            return {"error": "No performance metrics collected yet"}
        
        return {
            "timing": {
                "start_time": self.metrics.start_time,
                "end_time": self.metrics.end_time,
                "duration_seconds": self.metrics.duration,
                "duration_readable": f"{self.metrics.duration:.2f} seconds"
            },
            "system_resources": {
                "cpu_percent": self.metrics.cpu_percent,
                "memory_percent": self.metrics.memory_percent,
                "memory_used_mb": round(self.metrics.memory_used_mb, 2),
                "memory_used_gb": round(self.metrics.memory_used_mb / 1024, 2)
            },
            "file_processing": {
                "files_processed": self.metrics.files_processed,
                "directories_scanned": self.metrics.directories_scanned,
                "avg_file_size_bytes": round(self.metrics.avg_file_size, 2),
                "largest_file_bytes": self.metrics.largest_file,
                "smallest_file_bytes": self.metrics.smallest_file,
                "total_data_processed_mb": round(sum(self.metrics.file_sizes) / (1024 * 1024), 2) if self.metrics.file_sizes else 0
            },
            "performance_indicators": {
                "files_per_second": round(self.metrics.files_processed / self.metrics.duration, 2) if self.metrics.duration > 0 else 0,
                "efficiency_score": self._calculate_efficiency_score()
            }
        }
    
    def _calculate_efficiency_score(self) -> float:
        """Berechnet einen Effizienz-Score basierend auf verschiedenen Metriken"""
        if not self.metrics:
            return 0.0
        
        # Berechnung des Effizienz-Scores
        # Je niedriger der Speicher- und CPU-Verbrauch, desto höher der Score
        # Je höher die Verarbeitungsgeschwindigkeit, desto höher der Score
        
        # Normiere die Werte auf 0-100 Skala
        cpu_efficiency = max(0, 100 - self.metrics.cpu_percent)
        memory_efficiency = max(0, 100 - self.metrics.memory_percent)
        
        # Geschwindigkeitseffizienz - je höher desto besser
        speed_efficiency = min(100, (self.metrics.files_processed / self.metrics.duration) * 10) if self.metrics.duration > 0 else 0
        
        # Kombiniere die Effizienzen (kann nach Bedarf angepasst werden)
        efficiency_score = (cpu_efficiency * 0.3 + memory_efficiency * 0.3 + speed_efficiency * 0.4)
        
        return round(min(100, efficiency_score), 2)
    
    def print_performance_summary(self):
        """Gibt eine Zusammenfassung der Performance auf der Konsole aus"""
        if not self.metrics:
            print("No performance metrics collected yet")
            return
        
        report = self.get_performance_report()
        timing = report["timing"]
        resources = report["system_resources"]
        processing = report["file_processing"]
        indicators = report["performance_indicators"]
        
        print("\n=== Performance-Zusammenfassung ===")
        print(f"Dauer: {timing['duration_readable']}")
        print(f"CPU-Auslastung: {resources['cpu_percent']:.2f}%")
        print(f"Speichernutzung: {resources['memory_used_mb']:.2f} MB ({resources['memory_percent']:.2f}%)")
        print(f"Dateien verarbeitet: {processing['files_processed']}")
        print(f"Verzeichnisse gescannt: {processing['directories_scanned']}")
        print(f"Durchsatz: {indicators['files_per_second']} Dateien/Sekunde")
        print(f"Effizienz-Score: {indicators['efficiency_score']}/100")
    
    def save_performance_report(self, output_path: str):
        """Speichert den Performance-Bericht in einer Datei"""
        import json
        
        report = self.get_performance_report()
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)