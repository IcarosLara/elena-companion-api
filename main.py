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
# LANDING PAGE OFICIAL DE BRUNILDA S.A.S. (RUTA PRINCIPAL /)
# ---------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Brunilda S.A.S. - Dra. Elena Lara v0.5</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }
            .container { max-width: 800px; margin: 0 auto; background: #1e293b; padding: 30px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
            h1 { color: #38bdf8; text-align: center; font-size: 2em; margin-bottom: 5px; }
            .subtitle { text-align: center; color: #94a3b8; font-size: 1.1em; margin-bottom: 25px; }
            .terms-box { background: #334155; border-left: 5px solid #f59e0b; padding: 15px; border-radius: 6px; margin-bottom: 25px; font-size: 0.9em; line-height: 1.5; }
            .download-btn { display: block; width: 100%; text-align: center; background: #22c55e; color: white; padding: 15px 0; font-size: 1.2em; font-weight: bold; border-radius: 8px; text-decoration: none; margin-bottom: 30px; transition: 0.3s; }
            .download-btn:hover { background: #16a34a; }
            .plans { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 15px; }
            .plan-card { background: #0f172a; border: 1px solid #475569; border-radius: 8px; padding: 20px; text-align: center; }
            .plan-price { font-size: 1.5em; color: #38bdf8; font-weight: bold; margin: 10px 0; }
            .pay-btn { display: inline-block; background: #0284c7; color: white; padding: 8px 15px; border-radius: 5px; text-decoration: none; font-size: 0.9em; margin-top: 10px; }
            .pay-btn:hover { background: #0369a1; }
            .footer { text-align: center; margin-top: 30px; font-size: 0.8em; color: #64748b; }
        </style>
    </head>
    <body>

    <div class="container">
        <h1>BRUNILDA S.A.S.</h1>
        <div class="subtitle">Dra. Elena Lara — Ecosistema Elena Services (v0.5)</div>

        <div class="terms-box">
            <strong>⚠️ TÉRMINOS & CONDICIONES DE LA PRUEBA FREEMIUM:</strong><br>
            Al instalar la aplicación, usted accede a <strong>24 horas de prueba continua</strong> con acceso a los 5 módulos (Senior, Baby, Care, Recovery y Memory). Se activa el permiso de grabación pasiva e inteligencia asistiva con pantalla bloqueada según los Términos y Condiciones de Brunilda S.A.S. Finalizadas las 24 horas, deberá seleccionar una suscripción para mantener el servicio activo.
        </div>

        <a href="https://elena-companion-api.onrender.com/docs" target="_blank" class="download-btn">📲 DESCARGAR BRUNILDA APK (v0.5)</a>

        <h2>Planes & Suscripciones</h2>
        <div class="plans">
            <div class="plan-card">
                <h3>Elena Único</h3>
                <p>1 Módulo a elección</p>
                <div class="plan-price">$6.000 ARS</div>
                <a href="https://elena-companion-api.onrender.com/docs" target="_blank" class="pay-btn">Suscribirme</a>
            </div>
            <div class="plan-card">
                <h3>Elena Dúo</h3>
                <p>2 Módulos (ej: Senior + Baby)</p>
                <div class="plan-price">$12.000 ARS</div>
                <a href="https://elena-companion-api.onrender.com/docs" target="_blank" class="pay-btn">Suscribirme</a>
            </div>
            <div class="plan-card" style="border-color: #f59e0b;">
                <h3>Elena Premium Suite</h3>
                <p>Acceso Total a las 5 Elenas</p>
                <div class="plan-price">$63.000 ARS</div>
                <a href="https://elena-companion-api.onrender.com/docs" target="_blank" class="pay-btn">Suscribirme</a>
            </div>
        </div>

        <div style="text-align: center; margin-top: 25px;">
            <p>🌐 <strong>Planes Internacionales:</strong> $5.00 USD / mes vía <a href="https://www.paypal.com/invoice/p/#LGFK9KP2H6A55PQH" style="color: #38bdf8;" target="_blank">PayPal Factura Oficial</a></p>
        </div>

        <div class="footer">
            Directora de Servicio: Dra. Elena Lara | Brunilda S.A.S. © 2026
        </div>
    </div>

    </body>
    </html>
    """


# ---------------------------------------------------------
# ENDPOINTS DE LA API & MOTOR DE INTELIGENCIA
# ---------------------------------------------------------
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
