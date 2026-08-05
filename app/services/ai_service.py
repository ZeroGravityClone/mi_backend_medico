import json
from groq import Groq
from app.core.config import settings

class AIService:
    def __init__(self):
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
                model="openai/gpt-oss-20b",
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
                model="openai/gpt-oss-20b",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Texto extraído del documento físico:\n{document_text}"}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            response_content = completion.choices[0].message.content
            if response_content:
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
                model="openai/gpt-oss-20b",
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
        """Usa el nuevo modelo Llama 4 Scout de Groq para analizar visualmente e identificar firmas, sellos e información del papel."""
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
            completion = self.client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
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
        
    def auto_register_worker_vision(self, base64_images: list) -> dict:
        """
        Analiza visualmente la primera página de un expediente escaneado para
        extraer de forma autónoma la ficha de datos del trabajador y la clasificación del archivo.
        """
        import json

        system_prompt = (
            "Eres el registrador automático inteligente de Talento Humano del hospital.\n"
            "Tu tarea es analizar visualmente la imagen de la planilla proporcionada y extraer "
            "toda la información de forma exacta estructurándola en un JSON.\n\n"
            
            "REGLAS CRÍTICAS DE EXTRACCIÓN PARA LA PLANTILLA DEL HOSPITAL:\n"
            "1. NOMBRE COMPLETO: Busca la línea 'NOMBRE COMPLETO:'. Extrae el nombre de pila en 'first_name' "
            "y los apellidos en 'last_name'. Elimina títulos profesionales de cortesía como 'Dr.', 'Dra.', 'Lic.', 'Abog.'.\n"
            "   Ejemplo: 'Dr. Ricardo Morales Pinto' -> first_name: 'Ricardo', last_name: 'Morales Pinto'.\n"
            "2. CÉDULA DE IDENTIDAD: Busca la línea 'CÉDULA DE IDENTIDAD (C.I.):'. Extrae el valor alfanumérico exacto "
            "en el campo 'cedula' (ej: 'V-12456789').\n"
            "3. CARGO: Busca la palabra 'CARGO:' en la sección de DATOS LABORALES. Extrae TODO el texto literal "
            "que viene inmediatamente después de los dos puntos (ej: 'Médico Internista - Unidad de Cuidados Intensivos') "
            "en el campo 'cargo'. Es de vital importancia para el hospital que este campo NO sea null o vacío.\n"
            "4. FECHA DE INGRESO: Busca la línea 'ESTATUS: Activo (con fecha de ingreso: DD-MM-YYYY)'. Extrae la fecha de "
            "ingreso física (ej: '18-09-2008') y normalízala a formato estándar YYYY-MM-DD (ej: '2008-09-18') en el campo 'birth_date'.\n"
            "5. CORREO ELECTRÓNICO: Busca el campo 'CORREO ELECTRÓNICO:'. Extrae el correo real del documento (ej: 'ricardo.morales@salud.gob.ve') "
            "y guárdalo en el campo 'email'. Si no aparece, sugiere uno en base a su nombre.\n"
            "6. DIRECCIÓN: Si no aparece explícitamente en el cuerpo del documento, pon null en el campo 'address'.\n\n"
            
            "Debes responder ÚNICAMENTE con un objeto JSON válido con este formato exacto:\n"
            "{\n"
            "  \"first_name\": \"Nombres del trabajador extraídos\",\n"
            "  \"last_name\": \"Apellidos del trabajador extraídos\",\n"
            "  \"cedula\": \"Cédula de identidad (ej: V-12345678)\",\n"
            "  \"address\": \"Dirección de habitación o null\",\n"
            "  \"cargo\": \"Cargo o posición laboral extraída de la línea CARGO: (ej: Médico Internista - Unidad de Cuidados Intensivos)\",\n"
            "  \"birth_date\": \"Fecha de ingreso normalizada (YYYY-MM-DD)\",\n"
            "  \"phone\": \"Teléfono o null\",\n"
            "  \"email\": \"Correo electrónico real extraído del documento (ej: ricardo.morales@salud.gob.ve)\",\n"
            "  \"category\": \"Clasificar el documento: Cédula, Contrato, Constancia, Certificado, Título, Seguro Social u Otros\",\n"
            "  \"suggested_title\": \"Título descriptivo corto del documento\",\n"
            "  \"remarks\": \"Observaciones o notas sobre lo que falta por digitalizar en este expediente físico\"\n"
            "}\n\n"
            "No agregues explicaciones, código markdown ni comentarios. Solo devuelve el objeto JSON de forma cruda."
        )

        user_content = []
        user_content.append({"type": "text", "text": "Analiza la primera página de esta planilla del hospital y extrae la metadata estructurada:"})
        
        for img in base64_images:
            user_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{img}"
                }
            })

        try:
            completion = self.client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
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
            return {}
        except Exception as e:
            print(f"Error en auto-registro por visión: {e}")
            return {}