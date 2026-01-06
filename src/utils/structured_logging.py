"""
Modul für strukturiertes Logging in der DAUT-Anwendung
"""
import logging
import logging.config
import json
from pathlib import Path
from typing import Dict, Any, Optional
import sys
from datetime import datetime


class StructuredLogger:
    """Klasse für strukturiertes Logging mit verschiedenen Log-Levels und Formaten"""
    
    def __init__(self, name: str = "daut", config_path: Optional[str] = None):
        self.logger = logging.getLogger(name)
        self._setup_logger(name, config_path)
    
    def _setup_logger(self, name: str, config_path: Optional[str] = None):
        """Richtet den Logger mit Standard- oder benutzerdefinierter Konfiguration ein"""
        # Standardkonfiguration, falls keine Konfigurationsdatei angegeben ist
        if not config_path or not Path(config_path).exists():
            config = self._get_default_config()
        else:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        
        # Stelle sicher, dass das Log-Verzeichnis existiert
        log_dir = Path(config.get('log_dir', './logs'))
        log_dir.mkdir(exist_ok=True)
        
        # Aktualisiere die Konfiguration mit dem Log-Verzeichnis
        for handler_name, handler_config in config.get('handlers', {}).items():
            if 'filename' in handler_config:
                handler_config['filename'] = str(log_dir / handler_config['filename'])
        
        # Konfiguriere das Logging
        logging.config.dictConfig(config)
        self.logger = logging.getLogger(name)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Gibt die Standard-Logging-Konfiguration zurück"""
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "detailed": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
                },
                "structured": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(extra_data)s"
                },
                "simple": {
                    "format": "%(levelname)s - %(message)s"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "INFO",
                    "formatter": "simple",
                    "stream": sys.stdout
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "DEBUG",
                    "formatter": "detailed",
                    "filename": "daut.log",
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 5
                },
                "error_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "ERROR",
                    "formatter": "detailed",
                    "filename": "daut_errors.log",
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 5
                }
            },
            "loggers": {
                "daut": {
                    "level": "DEBUG",
                    "handlers": ["console", "file", "error_file"],
                    "propagate": False
                }
            },
            "root": {
                "level": "INFO",
                "handlers": ["console"]
            }
        }
    
    def debug(self, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """Loggt eine Debug-Nachricht"""
        self._log_with_extra(logging.DEBUG, message, extra_data)
    
    def info(self, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """Loggt eine Info-Nachricht"""
        self._log_with_extra(logging.INFO, message, extra_data)
    
    def warning(self, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """Loggt eine Warnung"""
        self._log_with_extra(logging.WARNING, message, extra_data)
    
    def error(self, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """Loggt eine Fehlermeldung"""
        self._log_with_extra(logging.ERROR, message, extra_data)
    
    def critical(self, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """Loggt eine kritische Nachricht"""
        self._log_with_extra(logging.CRITICAL, message, extra_data)
    
    def _log_with_extra(self, level: int, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """Hilfsmethode zum Loggen mit zusätzlichen Daten"""
        if extra_data:
            # Füge zusätzliche Daten als JSON-String hinzu
            extra_str = json.dumps(extra_data, ensure_ascii=False, default=str)
            formatted_message = f"{message} | Extra: {extra_str}"
        else:
            formatted_message = message
        
        self.logger.log(level, formatted_message)


# Globale Funktionen für einfache Verwendung
def get_logger(name: str = "daut", config_path: Optional[str] = None) -> StructuredLogger:
    """Gibt eine Instanz des strukturierten Loggers zurück"""
    return StructuredLogger(name, config_path)


# Beispiel für eine Konfigurationsdatei
DEFAULT_LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
        },
        "structured": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(extra_data)s"
        },
        "simple": {
            "format": "%(levelname)s - %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "simple",
            "stream": sys.stdout
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": "daut.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "detailed",
            "filename": "daut_errors.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5
        }
    },
    "loggers": {
        "daut": {
            "level": "DEBUG",
            "handlers": ["console", "file", "error_file"],
            "propagate": False
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"]
    },
    "log_dir": "./logs"
}