import os
import json
import requests
from fastapi import FastAPI, HTTPException, Request
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

@app.get("/")
def home():
    return {
        "status": "ok", 
        "plataforma": "Brunilda S.A.S. - Engine v1.5 Live", 
        "directora": "Dra. Elena Lara",
        "modo": "DOOM Resiliente / Multi-Módulo Activo"
    }

@app.get("/planes")
def obtener_planes():
    return {
        "empresa": "Brunilda S.A.S.",
        "directora_servicio": "Dra. Elena Lara",
        "condiciones_freemium": "24 horas de prueba continua por perfil registrado. Permiso de grabación pasiva con pantalla bloqueada activo según Términos & Condiciones.",
        "planes_argentina_ars": [
            {"plan": "Elena Único", "precio_ars": 6000, "cobertura": "1 Módulo a elección (3kg Pata Muslo)"},
            {"plan": "Elena Dúo", "precio_ars": 12000, "cobertura": "2 Módulos (ej: Senior + Baby)"},
            {"plan": "Elena Premium Suite", "precio_ars": 63000, "cobertura": "Acceso total a las 5 Elenas"}
        ],
        "planes_internacional_usd": {
            "precio_usd": 5.00,
            "frecuencia": "mensual",
            "pasarela": PAYPAL_GLOBAL_LINK
        }
    }

@app.post("/crear-preferencia-pago")
def crear_pago_mercadopago(plan: str = "UNICO"):
    if not MP_ACCESS_TOKEN:
        raise HTTPException(status_code=500, detail="MP_ACCESS_TOKEN no configurado en Render.")
    
    precios = {
        "UNICO": {"titulo": "Brunilda S.A.S - Elena Unico (1 Modulo)", "precio": 6000},
        "DUO": {"titulo": "Brunilda S.A.S - Elena Duo (2 Modulos)", "precio": 12000},
        "SUITE": {"titulo": "Brunilda S.A.S - Elena Premium Suite (5 Modulos)", "precio": 63000}
    }
    plan_info = precios.get(plan.upper(), precios["UNICO"])
    
    url = "https://api.mercadopago.com/checkout/preferences"
    headers = {"Authorization": f"Bearer {MP_ACCESS_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "items": [{"title": plan_info["titulo"], "quantity": 1, "unit_price": plan_info["precio"], "currency_id": "ARS"}],
        "notification_url": "https://elena-companion-api.onrender.com/webhook/mercadopago",
        "auto_return": "approved"
    }
    
    res = requests.post(url, headers=headers, json=payload)
    if res.status_code == 201:
        data = res.json()
        return {
            "status": "ok", 
            "plan": plan_info["titulo"], 
            "mercadopago_link_real": data.get("init_point"), 
            "mercadopago_link_prueba": data.get("sandbox_init_point"),
            "paypal_link_internacional": PAYPAL_GLOBAL_LINK
        }
    else:
        raise HTTPException(status_code=500, detail=f"Error en Mercado Pago: {res.text}")

@app.post("/webhook/mercadopago")
async def webhook_mercadopago(request: Request):
    try:
        datos = await request.json()
        print("Evento Mercado Pago recibido:", datos)
        return {"status": "ok"}
    except Exception as e:
        return {"status": "ok", "error": str(e)}

@app.post("/analizar")
def analizar(datos: EntradaCuidado):
    if not client:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY no configurada.")
    
    modulo_key = datos.modulo.upper()
    prompt_modulo = PROMPTS_ESPECIALIZADOS.get(modulo_key, PROMPTS_ESPECIALIZADOS["SENIOR"])
    system_instruction_completo = prompt_modulo + "\n" + PROMPT_SISTEMA_BASE
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=datos.texto_o_transcripcion,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction_completo,
                temperature=0.2,
                response_mime_type="application/json"
            )
        )
        return json.loads(response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en motor: {str(e)}")
