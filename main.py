import os
import json
import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from google import genai
from google.genai import types

app = FastAPI(title="Brunilda S.A.S. - Motor de Cuidados & Pagos v1.5 (Master)")

# VARIABLES DE ENTORNO EN RENDER
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None
MP_ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN")

# LINK OFICIAL DE PAYPAL DE BRUNILDA S.A.S.
PAYPAL_GLOBAL_LINK = "https://www.paypal.com/invoice/p/#LGFK9KP2H6A55PQH"

# PROMPTS ESPECIALIZADOS DE LOS EMPLEADOS DE BRUNILDA S.A.S.
PROMPTS_ESPECIALIZADOS = {
    "SENIOR": "Rol: Empleado asignado a 'Elena Senior'. Directora: Dra. Elena Lara. Objetivo: Proteger autonomía, medicación, salud y finanzas del adulto mayor. Detectar pagos duplicados, desorientación y coacción.",
    "BABY": "Rol: Empleado asignado a 'Elena Baby'. Directora: Dra. Elena Lara. Objetivo: Asistir a madres/padres primerizos. DESCARTAR charlas triviales. Registrar exclusivamente tomas de leche, pañales, sueño, vacunas, controles pediátricos y baño/uñas.",
    "CARE": "Rol: Empleado asignado a 'Elena Care'. Directora: Dra. Elena Lara. Objetivo: Acompañar a personas con discapacidad o movilidad reducida en sus rutinas, terapias y red de apoyo.",
    "RECOVERY": "Rol: Empleado asignado a 'Elena Recovery'. Directora: Dra. Elena Lara. Objetivo: Asistir en rehabilitación y enfermedades crónicas, monitoreando síntomas y dosis de fármacos.",
    "MEMORY": "Rol: Empleado asignado a 'Elena Memory'. Directora: Dra. Elena Lara. Objetivo: Refuerzo cognitivo para pérdida de memoria temprana, hitos diarios y desorientación."
}

PROMPT_SISTEMA_BASE = """
Eres la Dra. Elena Lara (IQ 165), Directora Ejecutiva de Protección en Brunilda S.A.S.
Delegas el registro de notas en la pestaña correspondiente de Google Sheets al empleado asignado, pero TÚ emites las notas de voz y alertas clínicas.

REGLAS DE PROCESAMIENTO:
1. Analiza el texto o audio transcrito. Descarta y NO registres charlas triviales.
2. Extrae si requiere agendar en Google Calendar (fecha, hora, síntesis).
3. Evalúa tono y sintaxis: si detectas miedo, amenaza o emergencia (caída, incendio, robo), activa protocolo silencioso y preservación judicial.
4. Define la pestaña exacta del libro de Google Sheets del usuario ('Pestaña_Elena_Senior', 'Pestaña_Elena_Baby', 'Pestaña_Elena_Care', etc.).
5. Redacta la nota de voz exacta que dirá la Dra. Elena Lara.
6. Genera EXCLUSIVAMENTE un objeto JSON válido.

ESTRUCTURA DE SALIDA (JSON REQUERIDO):
{
  "directora": "Dra. Elena Lara - Brunilda S.A.S.",
  "modulo_activo": "<SENIOR | BABY | CARE | RECOVERY | MEMORY>",
  "intencion_detectada": "<SALUD_MEDICACION | TURNO_MEDICO | REGISTRO_RUTINA | TRANSACCION_FINANCIERA | DUPLICADO_DETECTADO | EMERGENCIA | TRIVIAL_DESCARTADO>",
  "nivel_riesgo_cognitivo": <numero_1_al_10>,
  "analisis_estres_voz": "<NORMAL | ELEVADO_TEMBLOR | ANOMALO_MEDICO | COACCION_EXTERNA>",
  "registro_google_sheets": {
    "hoja_destino": "<Pestaña_Elena_Senior | Pestaña_Elena_Baby | Pestaña_Elena_Care | Pestaña_Elena_Recovery | Pestaña_Elena_Memory>",
    "evento": "<Síntesis del evento>",
    "monto_ARS": <numero_o_null>
  },
  "evento_calendar": {
    "requiere_agendar": <true | false>,
    "titulo": "<ej: Turno Pediátrico o null>",
    "fecha_hora_iso": "<YYYY-MM-DDTHH:MM:SS o null>",
    "detalles": "<Detalles o null>"
  },
  "protocolo_emergencia": {
    "activar_alerta_silenciosa": <true | false>,
    "servicio_requerido": "<POLICIA | AMBULANCIA | BOMBEROS | NINGUNO>",
    "preservar_dossier_judicial": <true | false>
  },
  "nota_de_voz_elena": "<Texto que dirá la Dra. Elena Lara>",
  "accion_sugerida": "<AGENDAR_Y_NOTIFICAR | BLOQUEAR_PAGO | NOTIFICAR_TUTOR | REGISTRAR_EN_HOJA | ACTIVAR_EMERGENCIA | DESCARTAR>"
}
"""

class EntradaCuidado(BaseModel):
    texto_o_transcripcion: str
    modulo: str = "SENIOR"
    email_tutor: str = None
    device_id: str = "legacy_generic"


# ---------------------------------------------------------
# LANDING PAGE OFICIAL SEGURA (RUTA PRINCIPAL /)
# ---------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def home():
    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Brunilda S.A.S. - Dra. Elena Lara v0.5</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }}
            .container {{ max-width: 850px; margin: 0 auto; background: #1e293b; padding: 30px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }}
            h1 {{ color: #
