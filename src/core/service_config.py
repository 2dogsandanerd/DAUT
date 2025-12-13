from pydantic import BaseModel
from typing import Optional
import json
import os

class ServiceConfig(BaseModel):
    ollama_host: str = "http://localhost:11434"
    chroma_host: str = "localhost"
    chroma_port: int = 8000
    ollama_timeout: int = 120
    chroma_timeout: int = 30
    
    def save_to_file(self, file_path: str):
        """Speichert die Konfiguration in eine Datei"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.dict(), f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load_from_file(cls, file_path: str):
        """Lädt die Konfiguration aus einer Datei"""
        if not os.path.exists(file_path):
            # Erstelle Standardkonfiguration, wenn Datei nicht existiert
            config = cls()
            config.save_to_file(file_path)
            return config
            
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls(**data)