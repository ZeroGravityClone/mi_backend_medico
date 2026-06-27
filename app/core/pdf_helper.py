import pypdf
from io import BytesIO

def extract_text_from_pdf(file_bytes: bytes, max_chars: int = 1500) -> str:
    """Extrae de forma ultraligera los primeros caracteres de texto de un PDF en memoria."""
    try:
        # Convertimos los bytes del archivo en un objeto de flujo de bytes
        pdf_file = BytesIO(file_bytes)
        reader = pypdf.PdfReader(pdf_file)
        text = ""
        
        # Leemos únicamente las primeras 2 páginas para proteger la memoria RAM
        for page in reader.pages[:2]:
            page_text = page.extract_text()
            if page_text:
                text += page_text
                
        # Retornamos un extracto limitado de caracteres para no saturar el prompt de la IA
        return text[:max_chars]
    except Exception as e:
        print(f"Error al extraer texto del PDF: {e}")
        return ""