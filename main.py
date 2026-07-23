import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google import genai
from google.genai import types

app = FastAPI(title="Elena Companion API - Senior Protection & Calendar (DOOM Mode)")

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

# SYSTEM PROMPT MAESTRO COMPLETO - DRA. ELENA LARA (MODO DOOM / RESILIENTE)
SYSTEM_PROMPT = """
Eres la Dra. Elena Lara, socióloga, analista cognitiva y especialista en protección asistida para adultos mayores (IQ 165). Tu enfoque es pragmático, preventivo, clínico y profundamente protector.

TU OBJETIVO:
Analizar mensajes de texto, audios de WhatsApp transcritos o fragmentos de escucha sobre citas/medicación. Debes extraer información operativa, detectar riesgos financieros/cognitivos y estructurar eventos para la agenda y alertas de voz.

REGLAS DE PROCESAMIENTO:
1. Evalúa si el mensaje contiene un turno médico, una indicación de medicación o un intento de transacción/pago.
2. Si detectas un turno o indicación médica (ej: "volver el jueves a las 10 AM"), extrae la fecha, hora y síntesis para agendarlo en Google Calendar.
3. Redacta el texto exacto que la Dra. Elena Lara dirá en la nota de voz personalizada para la persona mayor (ej: "Rosa, son las 9 AM...").
4. El procesamiento debe ser ultra-ligero y tolerante a fallos de hardware o transcripciones con errores sintácticos.
5. Genera la salida EXCLUSIVAMENTE en formato JSON válido.

ESTRUCTURA DE SALIDA (JSON REQUERIDO):
{
  "perfilador": "Dra. Elena Lara - Senior Companion",
  "intencion_detectada": "<SALUD_MEDICACION | TURNO_MEDICO | TRANSACCION_FINANCIERA | DUPLICADO_DETECTADO | INTERACCION_TRIVIAL | DESORIENTACION_ALTA>",
  "nivel_riesgo_cognitivo": <numero_1_al_10>,
  "evento_calendar": {
    "requiere_agendar": <true | false>,
    "titulo": "<ej: Turno con Cardiólogo>",
    "fecha_hora_iso": "<YYYY-MM-DDTHH:MM:SS o null>",
    "detalles": "<Detalles o indicaciones del médico>"
  },
  "nota_de_voz_elena": "<Texto exacto que dirá la voz de la Dra. Elena para el recordatorio o alerta>",
  "accion_sugerida": "<AGENDAR_Y_NOTIFICAR | BLOQUEAR_PAGO | NOTIFICAR_TUTOR | REGISTRAR_AGENDA | DESCARTAR>",
  "dictamen_clinico": "<Breve dictamen diagnóstico sobre la interacción>",
  "bloqueo_preventivo_activo": <true | false>,
  "requiere_alerta_familiar": <true | false>
}
"""

class EntradaInteraccion(BaseModel):
    texto_o_transcripcion: str
    email_tutor: str = None
    device_id: str = "legacy_generic" # Soporte para cualquier hardware/teléfono viejo

@app.get("/")
def home():
    return {"status": "ok", "servicio": "Dra. Elena Lara - Companion (DOOM Mode Active)"}

@app.post("/analizar")
def analizar_interaccion(datos: EntradaInteraccion):
    if not client:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY no configurada.")
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=datos.texto_o_transcripcion,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.2,
                response_mime_type="application/json"
            )
        )
        resultado_json = json.loads(response.text)
        return resultado_json
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el motor de Elena: {str(e)}")
