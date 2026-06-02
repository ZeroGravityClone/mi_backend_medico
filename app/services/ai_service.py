from groq import Groq
from app.core.config import settings

class AIService:
    def __init__(self):

        self.client = Groq(api_key=settings.GROQ_API_KEY)

    def get_clinical_assistant_response(self, user_message: str) -> str:
        """Envía el mensaje del doctor a Groq estructurando el rol clínico de la IA."""
        
        system_prompt = (
            "Eres un asistente de IA clínico especializado, diseñado para apoyar a "
            "profesionales de la salud en la gestión de su consulta médica. "
            "Analiza síntomas, resume historiales médicos o sugiere diagnósticos "
            "diferenciales con un tono profesional, científico y empático. "
            "ADVERTENCIA: Tus respuestas son únicamente de apoyo informativo y no "
            "reemplazan el diagnóstico ni el juicio clínico del médico a cargo."
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