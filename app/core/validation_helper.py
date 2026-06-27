import re
from datetime import datetime
from difflib import SequenceMatcher
from typing import Optional, Tuple

def normalize_date(raw_date_text: str) -> Optional[str]:
    """Toma cualquier formato de fecha de la IA y lo normaliza al estándar YYYY-MM-DD."""
    if not raw_date_text:
        return None
        
    cleaned = raw_date_text.strip()
    # Patrón común: DD/MM/YYYY o DD-MM-YYYY
    match = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", cleaned)
    if match:
        day, month, year = match.groups()
        return f"{year}-{int(month):02d}-{int(day):02d}"
        
    # Intentos de parseo nativos
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(cleaned, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None

def fuzzy_name_match(name_a: str, name_b: str) -> float:
    """Calcula la similitud de Jaro-Winkler entre dos nombres para evitar errores de tipeo."""
    return SequenceMatcher(None, name_a.lower(), name_b.lower()).ratio()

def verify_document_consistency(
    ocr_name: str, 
    ocr_cedula: str, 
    worker_first: str, 
    worker_last: str, 
    worker_cedula: str
) -> Tuple[bool, str]:
    """
    Capa de Validación: Compara lo que la IA leyó del papel contra los datos de la base de datos.
    Retorna (Consistente: bool, Observación: str).
    """
    # Limpiamos puntos o letras de las cédulas (V-123 -> 123)
    clean_ocr_c = re.sub(r"\D", "", ocr_cedula) if ocr_cedula else ""
    clean_db_c = re.sub(r"\D", "", worker_cedula) if worker_cedula else ""

    # 1. Alerta Crítica: Cédula cruzada (Guardar archivo de otro empleado)
    if clean_ocr_c and clean_db_c and clean_ocr_c != clean_db_c:
        return False, f"Alerta Crítica: El documento contiene la C.I. {ocr_cedula}, pero se intenta archivar en C.I. {worker_cedula}."

    # 2. Alerta de inconsistencia de nombres (Fuzzy matching < 65% de similitud)
    db_full_name = f"{worker_first} {worker_last}"
    if ocr_name:
        similarity = fuzzy_name_match(ocr_name, db_full_name)
        if similarity < 0.65:
            return False, f"Alerta de Inconsistencia: El nombre leído ('{ocr_name}') tiene baja coincidencia con el expediente ('{db_full_name}')."

    return True, "Verificación de consistencia aprobada."