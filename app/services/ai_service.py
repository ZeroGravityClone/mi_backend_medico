from groq import Groq
from app.core.config import settings

class AIService:
    def __init__(self):

        self.client = Groq(api_key=settings.GROQ_API_KEY)

    def get_clinical_assistant_response(self, user_message: str) -> str:
        """Envía la consulta a Groq estructurando el rol de asistente de Archivo y RRHH."""
        
        # --- NUEVO SYSTEM PROMPT PARA ARCHIVO DE TALENTO HUMANO ---
        system_prompt = (
            "Eres el asistente virtual especializado en la Gestión de Archivos y "
            "Recursos Humanos del departamento de Talento Humano del hospital. "
            "Tu objetivo es ayudar al personal de archivo a organizar expedientes, "
            "resolver dudas sobre digitalización de documentos, y aplicar la normativa "
            "laboral para trabajadores (Activos, Jubilados, Pensionados, Vacaciones, Fallecidos). "
            "Responde de forma profesional, estructurada y basada en buenas prácticas de archivología."
        )

        try:
            completion = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
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