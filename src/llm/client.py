from typing import Dict, Any, Optional
import requests
import json
import time

class OllamaClient:
    def __init__(self, host: str = "http://localhost:11434", timeout: int = 120):
        self.base_url = host
        self.timeout = timeout
        self.session = requests.Session()
        # Setze Standard-Header
        self.session.headers.update({'Content-Type': 'application/json'})
        
    def health_check(self) -> bool:
        """Prüft, ob der Ollama-Server erreichbar ist"""
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=self.timeout)
            return response.status_code == 200
        except (requests.exceptions.RequestException, requests.exceptions.Timeout):
            return False
    
    def generate(self, model: str, prompt: str, options: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Generiert Text mit dem angegebenen Modell und Prompt"""
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": options or {}
            }
            
            response = self.session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                print(f"Ollama API Fehler: {response.status_code} - {response.text}")
                return None
        except (requests.exceptions.RequestException, requests.exceptions.Timeout) as e:
            print(f"Ollama Verbindungsfehler: {e}")
            return None
    
    def list_models(self) -> Optional[list]:
        """Listet verfügbare Modelle auf"""
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=self.timeout)
            if response.status_code == 200:
                result = response.json()
                return result.get("models", [])
            return []
        except (requests.exceptions.RequestException, requests.exceptions.Timeout):
            return []
    
    def check_model_exists(self, model_name: str) -> bool:
        """Prüft, ob ein bestimmtes Modell verfügbar ist"""
        models = self.list_models()
        if models:
            for model in models:
                if isinstance(model, dict):
                    # Falls die API ein Objekt mit Name zurückgibt
                    if model.get('name') == model_name or model.get('model') == model_name:
                        return True
                elif isinstance(model, str) and model == model_name:
                    # Falls die API eine einfache String-Liste zurückgibt
                    return True
        return False