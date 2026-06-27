import fitz  # PyMuPDF
import base64
from io import BytesIO
from typing import List

def convert_pdf_to_base64_images(file_bytes: bytes, mode: str = "fast") -> List[str]:
    """
    Convierte un PDF en memoria a una lista de imágenes PNG codificadas en Base64.
    - Modo 'fast': Solo primera página (para clasificación rápida).
    - Modo 'full': Todas las páginas (para auditorías legales de firmas y sellos).
    """
    base64_images = []
    try:
        # Abrir el PDF directamente desde los bytes en memoria (RAM)
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        
        # Determinar qué páginas procesar según el modo
        pages_to_process = [doc[0]] if mode == "fast" else doc
        
        for page in pages_to_process:
            # Renderizar a alta resolución (Matrix 2x2 equivale a duplicar la nitidez para OCR)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img_bytes = pix.tobytes("png")
            encoded_img = base64.b64encode(img_bytes).decode("utf-8")
            base64_images.append(encoded_img)
            
        doc.close()
    except Exception as e:
        print(f"Error en la conversión de PDF a imagen: {e}")
    return base64_images

def encode_image_to_base64(file_bytes: bytes) -> str:
    """Codifica una imagen nativa (PNG/JPG) directamente a Base64."""
    return base64.b64encode(file_bytes).decode("utf-8")