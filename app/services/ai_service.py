import json
from groq import Groq
from app.core.config import settings

class AIService:
    def __init__(self):
        # Validación de seguridad: Evita errores de conexión si falta la API Key en el .env
        if not settings.GROQ_API_KEY or settings.GROQ_API_KEY == "":
            raise ValueError("La API Key de Groq no se pudo cargar. Verifica tu archivo .env")
            
        self.client = Groq(api_key=settings.GROQ_API_KEY)

    def get_clinical_assistant_response(self, user_message: str) -> str:
        """Envía el mensaje del doctor a Groq estructurando el rol clínico de la IA (Lógica del Chatbot)."""
        system_prompt = (
            "Eres un asistente de IA clínico especializado, diseñado para apoyar a "
            "profesionales de la salud en la gestión de su consulta médica. "
            "Analiza síntomas, sugiere diagnósticos diferenciales o resume historiales médicos "
            "con un tono profesional, científico y empático. "
            "ADVERTENCIA: Tus respuestas son únicamente de apoyo informativo y no "
            "reemplazan el diagnóstico ni el juicio clínico del médico a cargo."
        )

        try:
            completion = self.client.chat.completions.create(
                model="openai/gpt-oss-20b",  # <-- ACTUALIZADO: Migración al nuevo modelo de 1000 tps
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.3,
                max_tokens=1024,
            )
            
            ai_reply = completion.choices[0].message.content
            return ai_reply if ai_reply else "La IA no generó ninguna respuesta."
            
        except Exception as e:
            return f"Error al comunicarse con el servicio de IA: {str(e)}"

    def classify_document(self, document_text: str) -> dict:
        """Analiza el extracto de texto de un PDF y retorna la clasificación de metadatos en formato JSON."""
        system_prompt = (
            "Eres un clasificador automático de documentos para el departamento de Talento Humano del hospital.\n"
            "Tu tarea es analizar el extracto de texto proporcionado y clasificarlo estrictamente en una de las siguientes categorías:\n"
            "'Cédula', 'Contrato', 'Constancia', 'Certificado', 'Título', 'Seguro Social', 'Otros'.\n\n"
            "Debes responder ÚNICAMENTE con un objeto JSON válido con este formato:\n"
            "{\n"
            "  \"category\": \"Categoría Clasificada\",\n"
            "  \"suggested_title\": \"Título corto y descriptivo del documento\"\n"
            "}\n\n"
            "No incluyas saludos, explicaciones ni código markdown de bloques de código. Solo devuelve el objeto JSON de forma cruda."
        )

        try:
            completion = self.client.chat.completions.create(
                model="openai/gpt-oss-20b",  # <-- ACTUALIZADO: Migración al nuevo modelo de 1000 tps
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Texto extraído del documento físico:\n{document_text}"}
                ],
                temperature=0.1,  # Temperatura ultra-baja para garantizar precisión y evitar alucinaciones
                response_format={"type": "json_object"}  # Forzamos la salida en formato JSON estructurado
            )
            
            response_content = completion.choices[0].message.content
            if response_content:
                # Convertimos el string de la IA en un diccionario nativo de Python
                return json.loads(response_content)
                
            return {"category": "Otros", "suggested_title": "Documento Digitalizado"}
        except Exception as e:
            print(f"Error en la clasificación por IA: {e}")
            return {"category": "Otros", "suggested_title": "Documento Digitalizado"}
        
    def audit_expediente(self, estatus_laboral: str, documentos_existentes: list) -> dict:
        """Usa Groq para analizar la lista de documentos subidos de un trabajador y detectar faltantes."""
        import json

        system_prompt = (
            "Eres el Auditor de Control de Calidad de Archivo de Talento Humano del hospital.\n"
            "Tu tarea es analizar la lista de documentos que ya han sido digitalizados para un trabajador "
            "y determinar si su expediente físico está Completo, Pendiente o en estado Crítico.\n\n"
            "Reglas de Negocio del Hospital (Reglas de Auditoría):\n"
            "1. TODO trabajador (sin importar estatus) necesita obligatoriamente: 'Cédula' y 'Contrato'.\n"
            "2. Los trabajadores en estatus 'ACTIVO' o 'VACACIONES' necesitan además obligatoriamente: 'Seguro Social'.\n"
            "3. Los trabajadores en estatus 'EGRESADO' necesitan además obligatoriamente: 'Constancia' de egreso.\n"
            "4. Los 'JUBILADOS' o 'PENSIONADOS' necesitan además obligatoriamente: 'Certificado' de jubilación.\n\n"
            "Criterios de Evaluación:\n"
            "- 'COMPLETO': Si el expediente tiene TODOS los documentos requeridos según las reglas.\n"
            "- 'CRITICO': Si falta la 'Cédula' o el 'Contrato' (documentos de identidad y legalidad básicos).\n"
            "- 'PENDIENTE': Si tiene Cédula y Contrato, pero falta algún otro documento requerido según su estatus.\n\n"
            "Debes responder ÚNICAMENTE con un objeto JSON válido con este formato:\n"
            "{\n"
            "  \"document_status\": \"COMPLETO\" o \"PENDIENTE\" o \"CRITICO\",\n"
            "  \"remarks\": \"Texto descriptivo y corto de lo que falta. Ej: Falta copia de Cédula y Seguro Social.\"\n"
            "}\n\n"
            "No incluyas explicaciones. Solo el objeto JSON."
        )

        user_content = f"Estatus Laboral: {estatus_laboral}\nDocumentos ya digitalizados: {documentos_existentes}"

        try:
            completion = self.client.chat.completions.create(
                model="openai/gpt-oss-20b",  # <-- ACTUALIZADO: Migración al nuevo modelo de 1000 tps
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            response_content = completion.choices[0].message.content
            if response_content:
                return json.loads(response_content)
                
            return {"document_status": "PENDIENTE", "remarks": "No se pudo realizar la auditoría automática."}
        except Exception as e:
            print(f"Error en auditoría por IA: {e}")
            return {"document_status": "PENDIENTE", "remarks": "Error de comunicación con el motor de auditoría."}
        
    def classify_document_vision(self, base64_images: list, mode: str = "fast") -> dict:
        """Usa Llama 3.2 Vision de Groq para analizar visualmente e identificar firmas, sellos e información del papel."""
        import json

        system_prompt = (
            "Eres el clasificador de visión e integridad documental de Talento Humano del hospital.\n"
            "Tu tarea es analizar las imágenes del documento proporcionado (pueden ser una o varias páginas) "
            "y extraer de forma precisa y estructurada la información del papel.\n\n"
            "Debes clasificar el documento estrictamente en una de las siguientes categorías:\n"
            "'Cédula', 'Contrato', 'Constancia', 'Certificado', 'Título', 'Seguro Social', 'Otros'.\n\n"
            "Además, debes verificar visualmente si existen firmas autógrafas o sellos húmedos visibles "
            "en cualquiera de las páginas analizadas.\n\n"
            "Debes responder ÚNICAMENTE con un objeto JSON válido con este formato:\n"
            "{\n"
            "  \"category\": \"Categoría Clasificada\",\n"
            "  \"extracted_name\": \"Nombre del trabajador leído en el documento\",\n"
            "  \"extracted_cedula\": \"Cédula de identidad leída en el documento\",\n"
            "  \"extracted_date\": \"Fecha importante del documento en cualquier formato\",\n"
            "  \"has_signatures_and_stamps\": true o false,\n"
            "  \"suggested_title\": \"Título corto y descriptivo para el archivo\"\n"
            "}\n\n"
            "No agregues explicaciones, código markdown ni bloques de código. Solo devuelve el objeto JSON."
        )

        # Preparamos el contenido multimodal (Texto + Imágenes en Base64)
        user_content = []
        user_content.append({"type": "text", "text": f"Analiza las siguientes páginas en modo {mode} e indexa la información:"})
        
        for img in base64_images:
            user_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{img}"
                }
            })

        try:
            # Usamos Llama 3.2 Vision Preview para inferencia visual de alta velocidad
            completion = self.client.chat.completions.create(
                model="llama-3.2-11b-vision-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            response_content = completion.choices[0].message.content
            if response_content:
                return json.loads(response_content)
                
            return {"category": "Otros", "extracted_name": "", "extracted_cedula": "", "extracted_date": "", "has_signatures_and_stamps": False, "suggested_title": "Digitalización"}
        except Exception as e:
            print(f"Error en visión artificial de Groq: {e}")
            return {"category": "Otros", "extracted_name": "", "extracted_cedula": "", "extracted_date": "", "has_signatures_and_stamps": False, "suggested_title": "Digitalización"}