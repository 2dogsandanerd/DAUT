from pydantic import BaseModel
from enum import Enum
from typing import List, Dict, Optional, Any

class ElementType(str, Enum):
    FUNCTION = "function"
    CLASS = "class"
    API_ENDPOINT = "api_endpoint"
    IMPORT = "import"
    CONFIGURATION = "configuration"
    DOC_HEADING = "doc_heading"
    DOC_CODE_BLOCK = "doc_code_block"
    DOCUMENTATION = "documentation"

class CodeElement(BaseModel):
    name: str
    type: ElementType
    signature: Optional[str] = None
    parameters: Optional[List[Dict]] = None
    return_type: Optional[str] = None
    docstring: Optional[str] = None
    api_info: Optional[Dict[str, str]] = None  # Für API-Endpunkte
    methods: Optional[List[Dict]] = None  # Für Klassen
    imports: Optional[List[str]] = None  # Für Importe
    import_from: Optional[str] = None  # Für Importe
    line_number: Optional[int] = None
    file_path: Optional[str] = None
    project_path: Optional[str] = None
    code_snippet: Optional[str] = None

class DocElement(BaseModel):
    name: str
    type: ElementType
    content: Optional[str] = None
    full_content: Optional[str] = None
    level: Optional[int] = None  # Für Überschriften
    language: Optional[str] = None  # Für Code-Blöcke
    line_number: Optional[int] = None
    file_path: Optional[str] = None
    project_path: Optional[str] = None
    references: Optional[List[str]] = None  # Verweise auf Code-Elemente
    format: Optional[str] = "md"  # Dateiformat (z.B. md, rst, txt)