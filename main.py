import os
import json
import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from google import genai
from google.genai import types

# IMPORTACIÓN DEL MÓDULO DE MERCADO PAGO
from mercadopago_service import generar_link_mp

app = FastAPI(title="Brunilda S.A.S. - Motor de Cuidados & Pagos v1.5 (Master)")

# ---------------------------------------------------------
# CONFIGURACIÓN MAESTRA DE DATOS Y SERVICIOS
# ---------------------------------------------------------
SPREADSHEET_ID = "17yjtHd1O5TvwmlTzxdd8t77vWgDb4Z5Y1VR3lAs0Fvw"
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/17yjtHd1O5TvwmlTzxdd8t77vWgDb4Z5Y1VR3lAs0Fvw/edit"

EMAIL_DRA_ELENA = "dra.elenalara.forense@gmail.com"
EMAIL_ADMIN_JAVIER = "javieradrianlaraaracena@gmail.com"

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

PAYPAL_GLOBAL_LINK = "https://www.paypal.com/invoice/p/#LGFK9KP2H6A55PQH"

PROMPTS_ESPECIALIZADOS = {
    "SENIOR": "Rol: Empleado asignado a 'Elena Senior'. Directora: Dra. Elena Lara.",
    "BABY": "Rol: Empleado asignado a 'Elena Baby'. Directora: Dra. Elena Lara.",
    "CARE": "Rol: Empleado asignado a 'Elena Care'. Directora: Dra. Elena Lara.",
    "RECOVERY": "Rol: Empleado asignado a 'Elena Recovery'. Directora: Dra. Elena Lara.",
    "MEMORY": "Rol: Empleado asignado a 'Elena Memory'. Directora: Dra. Elena Lara."
}

PROMPT_SISTEMA_BASE = f"""
Eres la Dra. Elena Lara (IQ 165), Directora Ejecutiva de Protección en Brunilda S.A.S.
Correo Oficial de Emisión: {EMAIL_DRA_ELENA}
Notificaciones Administrativas a: {EMAIL_ADMIN_JAVIER}
Libro Maestro de Registro en Google Sheets: {SPREADSHEET_URL}

REGLAS DE OPERACIÓN:
1. Delegas el registro diario en las pestañas correspondientes del Google Sheets a los empleados asignados.
2. Tras la confirmación de pago o alta de servicio, emites el correo de bienvenida al cliente/tutor.
3. Envías un informe ejecutivo automático a Javier Adrián Lara Aracena ({EMAIL_ADMIN_JAVIER}) detallando el o los módulos contratados.
"""

class EntradaCuidado(BaseModel):
    texto_o_transcripcion: str
    modulo: str = "SENIOR"
    email_tutor: str = None
    device_id: str = "legacy_generic"

# ---------------------------------------------------------
# LANDING PAGE OFICIAL CON MEJORAS DE PRODUCTO
# ---------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def home():
    return """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Brunilda S.A.S. - Dra. Elena Lara v0.5</title>
<style>
* { box-sizing: border-box; }
body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #f8fafc; padding: 20px; margin: 0; }
.container { max-width: 900px; margin: 0 auto; background: #1e293b; padding: 30px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
h1 { color: #38bdf8; text-align: center; margin-bottom: 5px; font-size: 2.2em; }
.subtitle { text-align: center; color: #94a3b8; margin-bottom: 20px; font-weight: 300; }
.hero-problem { background: #0f172a; border-left: 4px solid #f59e0b; padding: 18px; border-radius: 6px; margin-bottom: 25px; line-height: 1.5; color: #cbd5e1; }
.btn-doc { display: block; text-align: center; background: #22c55e; color: #fff; padding: 12px; border-radius: 6px; text-decoration: none; margin-bottom: 25px; font-weight: bold; }
.btn-doc:hover { background: #16a34a; }

/* MODULOS */
.section-title { color: #f8fafc; border-bottom: 2px solid #334155; padding-bottom: 8px; margin-top: 30px; }
.modules-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin-bottom: 30px; }
.module-card { background: #0f172a; border-left: 4px solid #38bdf8; padding: 15px; border-radius: 6px; }
.module-card h4 { margin: 0 0 8px 0; color: #38bdf8; font-size: 1.1em; }
.module-card p { font-size: 0.88em; color: #cbd5e1; margin: 0; line-height: 1.4; }

/* PLANES */
.plans { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 15px; margin-top: 20px; }
.card { background: #0f172a; border: 1px solid #475569; padding: 20px; border-radius: 8px; text-align: center; display: flex; flex-direction: column; justify-content: space-between; }
.card h3 { margin: 0 0 10px 0; color: #f8fafc; }
.price { font-size: 1.5em; color: #38bdf8; font-weight: bold; margin: 10px 0; }
.btn-pay { display: inline-block; background: #0284c7; color: #fff; padding: 10px 15px; border-radius: 6px; text-decoration: none; font-weight: bold; border: none; cursor: pointer; font-size: 1em; width: 100%; }
.btn-pay:hover { background: #0369a1; }

/* MODAL DE TERMINOS Y CONDICIONES */
.modal-overlay { display: none; position: fixed; top:0; left:0; width:100%; height:100%; background: rgba(0,0,0,0.85); z-index: 1000; justify-content: center; align-items: center; }
.modal-content { background: #1e293b; max-width: 750px; width: 90%; max-height: 85vh; padding: 25px; border-radius: 10px; border: 1px solid #475569; display: flex; flex-direction: column; }
.modal-body { overflow-y: auto; padding-right: 10px; font-size: 0.85em; color: #cbd5e1; line-height: 1.5; margin-bottom: 15px; background: #0f172a; padding: 15px; border-radius: 6px; }
.modal-body h3 { color: #38bdf8; margin-top: 15px; margin-bottom: 5px; }
.accept-container { display: flex; align-items: center; gap: 10px; margin-bottom: 15px; font-size: 0.9em; color: #f8fafc; }
.accept-container input { width: 18px; height: 18px; cursor: pointer; }
.modal-actions { display: flex; gap: 10px; }
.btn-cancel { background: #64748b; color: white; border: none; padding: 10px 15px; border-radius: 6px; cursor: pointer; width: 30%; font-weight: bold; }
.btn-confirm { background: #22c55e; color: white; border: none; padding: 10px 15px; border-radius: 6px; cursor: pointer; width: 70%; font-weight: bold; }
.btn-confirm:disabled { background: #334155; color: #94a3b8; cursor: not-allowed; }
</style>
</head>
<body>

<div class="container">
<h1>BRUNILDA S.A.S.</h1>
<p class="subtitle">Elena Companion — Inteligencia Asistiva para la Tranquilidad Familiar (v0.5)</p>

<div class="hero-problem">
    <strong>💡 La paz mental no tiene precio:</strong> Cuando un ser querido envejece o requiere cuidados especiales, una sola distracción puede convertirse en una emergencia. Elena Companion actúa como una memoria auxiliar pasiva que escucha, organiza, recuerda y alerta para proteger la autonomía de tu familia.
</div>

<a href="/docs" target="_blank" class="btn-doc">🚀 PROBAR INTERFAZ INTERACTIVA Y API (/docs)</a>

<h2 class="section-title">Especializaciones de Elena Companion</h2>
<div class="modules-grid">
    <div class="module-card">
        <h4>👩‍⚕️ Elena Senior</h4>
        <p>Monitoreo integral, recordatorio estricto de medicación, prevención de olvidos y asistencia pasiva doméstica para adultos mayores.</p>
    </div>
    <div class="module-card">
        <h4>👶 Elena Baby</h4>
        <p>Acompañamiento en la crianza, seguimiento del crecimiento, recordatorios de vacunas, alimentación, sueño y controles pediátricos.</p>
    </div>
    <div class="module-card">
        <h4>♿ Elena Care</h4>
        <p>Asistencia especializada para personas con discapacidad funcional o motriz, garantizando respuesta activa y coordinación de cuidadores.</p>
    </div>
    <div class="module-card">
        <h4>❤️ Elena Recovery</h4>
        <p>Supervisión y soporte en procesos de rehabilitación postoperatoria, kinesiológica y tratamientos médicos cronometrados.</p>
    </div>
    <div class="module-card">
        <h4>🧠 Elena Memory</h4>
        <p>Estimulación cognitiva pasiva y contención estructurada para pacientes con Alzheimer, demencia senil o pérdida de memoria progresiva.</p>
    </div>
</div>

<h2 class="section-title">Planes de Suscripción</h2>
<p style="color:#94a3b8; font-size: 0.9em; margin-bottom: 15px;">Elegí la cobertura que mejor se adapte a las necesidades de tu hogar:</p>

<div class="plans">
    <div class="card">
        <div>
            <h3>Elena Único</h3>
            <p style="color:#94a3b8; font-size:0.85em;">Elegís <strong>1 Módulo</strong> de especialización.</p>
            <div class="price">$6.000 ARS</div>
        </div>
        <button onclick="abrirTerminos('UNICO')" class="btn-pay">Suscribirme</button>
    </div>
    <div class="card">
        <div>
            <h3>Elena Dúo</h3>
            <p style="color:#94a3b8; font-size:0.85em;">Elegís <strong>2 Módulos</strong> combinados.</p>
            <div class="price">$12.000 ARS</div>
        </div>
        <button onclick="abrirTerminos('DUO')" class="btn-pay">Suscribirme</button>
    </div>
    <div class="card" style="border-color:#f59e0b;">
        <div>
            <h3>Elena Premium Suite</h3>
            <p style="color:#f59e0b; font-size:0.85em; font-weight:bold;">Acceso completo a los 5 Módulos.</p>
            <div class="price">$18.000 ARS</div>
        </div>
        <button onclick="abrirTerminos('SUITE')" class="btn-pay" style="background:#f59e0b; color:#000;">Suscribirme</button>
    </div>
</div>

<p style="text-align:center; margin-top:25px; color:#94a3b8; font-size: 0.9em;">🌐 Planes Internacionales: $5.00 USD/mes vía PayPal Factura Oficial</p>
</div>

<div id="modalTerminos" class="modal-overlay">
    <div class="modal-content">
        <h2 style="color:#38bdf8; margin: 0 0 10px 0; font-size:1.3em;">Términos & Condiciones del Servicio / Terms & Conditions</h2>
        <div class="modal-body">
            <h3>ESP: Términos del Servicio y Consentimiento de Privacidad</h3>
            <p>Al contratar cualquiera de los planes de asistencia de Brunilda S.A.S. (Dra. Elena Lara), el usuario/tutor acepta las siguientes cláusulas bajo la legislación de la República Argentina (Ley 25.326 de Protección de Datos), HIPAA (EE.UU.) y GDPR (Unión Europea):</p>
            <ul>
                <li><strong>Grabación y Escucha Asistiva Pasiva:</strong> El usuario autoriza expresamente a la aplicación y al motor de IA a procesar capturas de audio y eventos en segundo plano, **incluso con la pantalla del dispositivo bloqueada**, para la detección inmediata de crisis sanitarias o llamadas de auxilio.</li>
                <li><strong>Privacidad y Descarte Automático:</strong> Toda conversación o audio capturado que resulte irrelevante para la prestación del servicio asistencial será **ignorado y destruido inmediatamente**, sin quedar almacenado en servidores permanentes.</li>
                <li><strong>Comunicaciones y Agenda Médica:</strong> El usuario autoriza a la Dra. Elena Lara a agendar al tutor como contacto en Google Contacts, emitir reportes privados por correo electrónico, gestionar citas automáticas en Google Calendar y enviar notificaciones urgentes por WhatsApp o llamadas en situaciones de extrema prioridad.</li>
            </ul>

            <h3>ENG: Terms of Service and Privacy Consent</h3>
            <p>By subscribing to any plan offered by Brunilda S.A.S. (Dr. Elena Lara), you agree to the following terms pursuant to Argentina Law 25.326, US HIPAA privacy rules, and EU GDPR guidelines:</p>
            <ul>
                <li><strong>Passive Assistive Recording:</strong> You grant permission for passive background audio monitoring, **including when the device screen is locked**, solely for detecting health emergencies or distress signals.</li>
                <li><strong>Strict Privacy Filtering:</strong> Any audio or private conversation unrelated to the care service will be **automatically discarded and deleted**, ensuring strict personal data confidentiality.</li>
                <li><strong>Authorized Channels:</strong> The user authorizes Dr. Elena Lara to add tutors to Google Contacts, send private progress emails, schedule Google Calendar medical alerts, and contact via WhatsApp only for urgent, critical notifications.</li>
            </ul>
        </div>

        <div class="accept-container">
            <input type="checkbox" id="checkAcepto" onchange="validarAceptacion()">
            <label for="checkAcepto">He leído y acepto expresamente los Términos, Condiciones y Políticas de Privacidad. / I have read and agree to the Terms & Privacy Policy.</label>
        </div>

        <div class="modal-actions">
            <button onclick="cerrarTerminos()" class="btn-cancel">Cancelar</button>
            <button id="btnIrAPagar" disabled onclick="procederAlPago()" class="btn-confirm">Aceptar e Ir a Pagar</button>
        </div>
    </div>
</div>

<script>
let planSeleccionado = '';

function abrirTerminos(plan) {
    planSeleccionado = plan;
    document.getElementById('checkAcepto').checked = false;
    document.getElementById('btnIrAPagar').disabled = true;
    document.getElementById('modalTerminos').style.display = 'flex';
}

function cerrarTerminos() {
    document.getElementById('modalTerminos').style.display = 'none';
}

function validarAceptacion() {
    const check = document.getElementById('checkAcepto');
    document.getElementById('btnIrAPagar').disabled = !check.checked;
}

function procederAlPago() {
    if (planSeleccionado) {
        window.location.href = `/pagar/${planSeleccionado}`;
    }
}
</script>

</body>
</html>"""

# ---------------------------------------------------------
# ENDPOINTS DE LA API Y PAGOS
# ---------------------------------------------------------
@app.get("/planes")
def obtener_planes():
    return {
        "empresa": "Brunilda S.A.S.",
        "directora_servicio": "Dra. Elena Lara",
        "email_oficial": EMAIL_DRA_ELENA,
        "notificaciones_admin": EMAIL_ADMIN_JAVIER,
        "google_sheets_maestro": SPREADSHEET_URL,
        "planes_argentina_ars": [
            {"plan": "Elena Único", "precio_ars": 6000, "modulos_incluidos": 1},
            {"plan": "Elena Dúo", "precio_ars": 12000, "modulos_incluidos": 2},
            {"plan": "Elena Premium Suite", "precio_ars": 18000, "modulos_incluidos": 5}
        ],
        "planes_internacional_usd": {"precio_usd": 5.00, "pasarela": PAYPAL_GLOBAL_LINK}
    }

@app.get("/pagar/{plan}")
def pagar_plan(plan: str):
    link = generar_link_mp(plan)
    if link:
        return RedirectResponse(url=link)
    raise HTTPException(status_code=500, detail="Error al conectar con Mercado Pago")

@app.post("/webhook/mercadopago")
async def webhook_mercadopago(request: Request):
    return {"status": "ok"}

@app.post("/analizar")
def analizar(datos: EntradaCuidado):
    if not client:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY no configurada.")
    
    modulo_key = datos.modulo.upper()
    prompt_modulo = PROMPTS_ESPECIALIZADOS.get(modulo_key, PROMPTS_ESPECIALIZADOS["SENIOR"])
    system_instruction_completo = prompt_modulo + "\n" + PROMPT_SISTEMA_BASE
    
    try:
        response = client.models.generate content(
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
