import os
import json
import re
import datetime
import random
import string
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
import gradio as gr
from google import genai
from google.genai import types

# ---------------------------------------------------------
# CONFIGURACIÓN MAESTRA DE ENTORNOS Y CREDENCIALES
# ---------------------------------------------------------
SPREADSHEET_ID = "17yjtHd1O5TvwmlTzxdd8t77vWgDb4Z5Y1VR3lAs0Fvw"
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/17yjtHd1O5TvwmlTzxdd8t77vWgDb4Z5Y1VR3lAs0Fvw/edit"
WEB_APP_SHEET_URL = "https://script.google.com/macros/s/AKfycbwts5uDaU8PrmUD0ovExIfR2LblZuB2yKpJT8lM-8L1rJcYDEZIzzj7xU2ukP4-oxlC0w/exec"

EMAIL_DRA_ELENA = "dra.elenalara.forense@gmail.com"
EMAIL_ADMIN_JAVIER = "javieradrianlaraaracena@gmail.com"
SMTP_USER_ELENA = "dra.elenalara.forense@gmail.com"
SMTP_USER_RAFA = "rafael.lara.finanzas@gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

SECRET_APP_PASS = "brdvbfioffxszmpd"
SMTP_PASS = os.environ.get("SMTP_PASS", SECRET_APP_PASS)

TOKEN_MP = os.environ.get("TOKEN_MP", "APP_USR-738297045866874-070402-5f178e96384dfbf05d797c448c7e97c6-3518229186")
PAYPAL_GLOBAL_LINK = "https://www.paypal.com/invoice/p/#LGFK9KP2H6A55PQH"
PAYPAL_EMAIL = "javieradrianlaraaracena@gmail.com"
BTC_WALLET = "bc1qw575hmqvqagny6fu0fkaa5qypq2j6hefqckqslt9624qphxzy7fqxq63jr"
LINK_MERCADOPAGO_REAL = "https://link.mercadopago.com.ar/brunildasas"

# AUTENTICACIÓN SEGURA VÍA VARIABLE DE ENTORNO (SIN KEYS HARDCODEADAS)
API_KEY = os.environ.get("GEMINI_API_KEY")

try:
    if not API_KEY:
        print("⚠️ [ALERTA CORE]: GEMINI_API_KEY no encontrada en variables de entorno.")
        client = None
    else:
        client = genai.Client(api_key=API_KEY)
        print("🔑 [AUTENTICACIÓN]: Enlace seguro establecido con Gemini API.")
except Exception as e:
    client = None
    print(f"⚠️ [ALERTA CORE]: Fallo de inicialización en Gemini API: {e}")

# ---------------------------------------------------------
# INICIALIZACIÓN DE FASTAPI (SUPER MOTOR)
# ---------------------------------------------------------
app = FastAPI(
    title="Brunilda S.A.S. - Super Motor Unificado v3.6",
    description="Motor Integral de Inteligencia Asistencial, Perfilación Conductual y Apoyo Legal-Documental"
)

# ---------------------------------------------------------
# MODELOS DE ENTRADA (PYDANTIC)
# ---------------------------------------------------------
class EntradaCuidado(BaseModel):
    texto_o_transcripcion: str
    modulo: str = "SENIOR"
    email_tutor: str = None
    device_id: str = "legacy_generic"

class EntradaEvaluaciónDragon(BaseModel):
    idioma: str = "Español"
    respuesta: str
    dilema: str
    sig_key: str
    nivel: str = "Nivel 1 (Aspirante - 3 Perfilaciones/Mes)"

class SolicitudContratoLegal(BaseModel):
    tipo_contrato: str  # CUIDADO_ADULTO, COMPRAVENTA_AUTO, DOMINIO_INMUEBLE, SEPARACION_BIENES, TESTAMENTO, CONTRATO_LABORAL
    datos_partes: dict  # Nombres, DNI, Domicilios, Montos, Detalles
    idioma: str = "Español"
    observaciones_especiales: str = None

class SolicitudRevisionContrato(BaseModel):
    contrato_original: str
    observaciones_abogado: str
    idioma: str = "Español"

class SolicitudAprobacionElena(BaseModel):
    titulo_documento: str
    texto_contrato_final: str
    email_abogado_o_cliente: str
    nombre_abogado: str

# ---------------------------------------------------------
# PROMPTS DEL SISTEMA (ELENA LARA & JULIÁN)
# ---------------------------------------------------------
PROMPT_DRA_ELENA_CARE = f"""
Eres la Dra. Elena Lara (IQ 165), Directora Ejecutiva de Protección (CEO) en Brunilda S.A.S.
Correo Oficial de Emisión: {EMAIL_DRA_ELENA}
Notificaciones Administrativas a: {EMAIL_ADMIN_JAVIER}
Libro Maestro de Registro en Google Sheets: {SPREADSHEET_URL}

PERFIL Y PRESENCIA INSTITUCIONAL:
- Posees una inteligencia superior y un estoicismo radical. Procesas presión y caos sin perder la calma quirúrgica ni el control emocional.
- Tu estilo comunicacional es preciso, directo, analítico y firme. Transmites jerarquía y autoridad médica.

SUPERVISIÓN AUTOMATIZADA Y ALERTAS PROACTIVAS:
1. Supervisas el Libro Maestro en Google Sheets donde las familias cargan horarios, medicamentos y novedades.
2. Analizas inconsistencias, demoras o alertas (ej. dosis no confirmadas, internaciones imprevistas o cambios de turnos).
3. Si detectas un incumplimiento en la toma de medicamentos o un evento no agendado, generas mensajes de contención y verificación proactiva.
4. Generas reportes en JSON estructurado notificando al tutor e integrando con Google Calendar cuando corresponda.
"""

PROMPT_JULIAN_LEGAL = f"""
Eres Julián, Director de Asuntos Legales y Arquitectura Documental en Brunilda S.A.S., trabajando bajo la supervisión ejecutiva de la Dra. Elena Lara.

TU MISIÓN:
Actuar como un asistente técnico de redacción y auditoría de documentos legales, contratos y acuerdos privados bajo el marco estrictamente vigente de la LEGISLACIÓN ARGENTINA (Código Civil y Comercial de la Nación - CCCN, normativas del DNRPA, Ley de Alquileres y normativa notarial aplicable).

DIRECTIVAS DE REDACCIÓN Y ANÁLISIS:
1. ESTRUCTURA RIGUROSA: Redactas instrumentos claros, con cláusulas de delimitación de responsabilidad, causales de rescisión, jurisdicción aplicable (Tribunales Ordinarios de la República Argentina) y mecanismos de resolución de controversias.
2. ADVERTENCIA PROFESIONAL OBLIGATORIA: Todo documento emitido debe incluir de forma visible la siguiente leyenda institucional:
   "DOCUMENTO PREPARADO COMO BORRADOR DE TRABAJO TÉCNICO POR EL MÓDULO LEGAL DE BRUNILDA S.A.S. SU VALIDEZ Y EJECUCIÓN DEFINITIVA REQUIERE LA REVISIÓN Y FIRMA DE UN ABOGADO O PROCURADOR HABILITADO."
3. ÁREAS DE ESPECIALIZACIÓN ARGENTINA:
   - Contratos de Prestación de Servicios de Cuidado (Elena Care) con T&C adaptados.
   - Boletos de Compraventa de Automotores / Motovehículos (Trámites vinculados al Formulario 08 DNRPA).
   - Contratos de Locación y Cesión de Derechos sobre Inmuebles / Casas / Departamentos.
   - Convenciones Matrimoniales (Régimen de Separación de Bienes previo al matrimonio - Art. 505 CCCN).
   - Borradores de Planificación Sucesoria y Testamentos por Acto Público (Art. 2479 CCCN).
   - Contratos de Trabajo y Locación de Servicios.
4. FORMATO DE SALIDA: Generas la respuesta en JSON estructurado conteniendo:
   - "titulo_documento": Nombre formal del instrumento.
   - "resumen_ejecutivo": Puntos clave del acuerdo.
   - "texto_contrato_borrador": Cuerpo completo del contrato clausulado.
   - "observaciones_legales_locales": Puntos críticos para que el abogado o procurador humano revise antes de la firma.
"""

PROMPTS_ESPECIALIZADOS_CARE = {
    "SENIOR": "Rol: Empleado asignado a 'Elena Senior'. Directora: Dra. Elena Lara.",
    "BABY": "Rol: Empleado asignado a 'Elena Baby'. Directora: Dra. Elena Lara.",
    "CARE": "Rol: Empleado asignado a 'Elena Care'. Directora: Dra. Elena Lara.",
    "RECOVERY": "Rol: Empleado asignado a 'Elena Recovery'. Directora: Dra. Elena Lara.",
    "MEMORY": "Rol: Empleado asignado a 'Elena Memory'. Directora: Dra. Elena Lara."
}

# ---------------------------------------------------------
# FUNCIONES AUXILIARES (PAGOS, SHEETS Y CORREOS)
# ---------------------------------------------------------
def generar_link_mp(plan: str):
    precios = {
        "UNICO": {"titulo": "Brunilda S.A.S - Elena Unico", "precio": 6000},
        "DUO": {"titulo": "Brunilda S.A.S - Elena Duo", "precio": 12000},
        "SUITE": {"titulo": "Brunilda S.A.S - Elena Premium Suite", "precio": 18000}
    }
    plan_info = precios.get(plan.upper(), precios["UNICO"])
    url = "https://api.mercadopago.com/checkout/preferences"
    headers = {
        "Authorization": f"Bearer {TOKEN_MP}",
        "Content-Type": "application/json"
    }
    payload = {
        "items": [{
            "title": plan_info["titulo"],
            "quantity": 1,
            "unit_price": plan_info["precio"],
            "currency_id": "ARS"
        }],
        "back_urls": {
            "success": "https://elena-companion-api.onrender.com/pago-exitoso",
            "failure": "https://elena-companion-api.onrender.com/",
            "pending": "https://elena-companion-api.onrender.com/"
        },
        "auto_return": "approved",
        "notification_url": "https://elena-companion-api.onrender.com/webhook/mercadopago"
    }
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=5)
        if res.status_code == 201:
            return res.json().get("init_point")
    except Exception as e:
        print("⚠️ [ERROR MP]:", e)
    return None

def registrar_en_google_sheets(estado, detalle, monto, plataforma, pagado_status, sig_key):
    payload = {
        "fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "operador_id": f"OP-{sig_key}",
        "estado": estado,
        "dilema": detalle[:80],
        "monto": monto,
        "pasarela": plataforma,
        "pago_status": pagado_status,
        "sig_key": sig_key
    }
    try:
        requests.post(WEB_APP_SHEET_URL, json=payload, timeout=5)
    except Exception as e:
        print(f"⚠️ [ERROR GOOGLE APPS SCRIPT]: {e}")

def enviar_correo_contrato(destinatario: str, asunto: str, contenido_html: str):
    pass_clean = SMTP_PASS.replace(" ", "").strip()
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = asunto
        msg["From"] = f"Dra. Elena Lara <{EMAIL_DRA_ELENA}>"
        msg["To"] = destinatario

        parte_html = MIMEText(contenido_html, "html", "utf-8")
        msg.attach(parte_html)

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER_ELENA, pass_clean)
        server.sendmail(EMAIL_DRA_ELENA, destinatario, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"⚠️ [ERROR ENVIO MAIL]: {e}")
        return False

# ---------------------------------------------------------
# LANDING PAGE COMERCIAL Y BILINGÜE
# ---------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def home():
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Brunilda S.A.S. - Motor Unificado</title>
<style>
* {{ box-sizing: border-box; }}
body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #f8fafc; padding: 20px; margin: 0; }}
.container {{ max-width: 900px; margin: 0 auto; background: #1e293b; padding: 30px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }}
.header-top {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
h1 {{ color: #38bdf8; margin: 0; font-size: 2.2em; }}
.easter-btn {{ background: #334155; color: #38bdf8; border: 1px solid #475569; padding: 6px 12px; border-radius: 20px; font-size: 0.8em; text-decoration: none; font-weight: bold; }}
.subtitle {{ text-align: center; color: #94a3b8; margin-bottom: 25px; font-weight: 300; }}
.info-banner {{ background: #0f172a; border-left: 4px solid #22c55e; padding: 20px; border-radius: 8px; margin-bottom: 30px; line-height: 1.6; color: #cbd5e1; }}
.info-banner h3 {{ color: #22c55e; margin: 0 0 8px 0; }}
.section-title {{ color: #f8fafc; border-bottom: 2px solid #334155; padding-bottom: 8px; margin-top: 30px; }}
.modules-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin-bottom: 30px; }}
.module-card {{ background: #0f172a; border-left: 4px solid #38bdf8; padding: 15px; border-radius: 6px; }}
.module-card h4 {{ margin: 0 0 8px 0; color: #38bdf8; font-size: 1.1em; }}
.module-card p {{ font-size: 0.88em; color: #cbd5e1; margin: 0; line-height: 1.4; }}
.plans {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 15px; margin-top: 20px; }}
.card {{ background: #0f172a; border: 1px solid #475569; padding: 20px; border-radius: 8px; text-align: center; display: flex; flex-direction: column; justify-content: space-between; }}
.price {{ font-size: 1.5em; color: #38bdf8; font-weight: bold; margin: 10px 0; }}
.btn-pay {{ display: inline-block; background: #22c55e; color: #000; padding: 12px 15px; border-radius: 6px; text-decoration: none; font-weight: bold; border: none; cursor: pointer; font-size: 1em; width: 100%; }}
.btn-pay:hover {{ background: #16a34a; color: #fff; }}
.modal-overlay {{ display: none; position: fixed; top:0; left:0; width:100%; height:100%; background: rgba(0,0,0,0.85); z-index: 1000; justify-content: center; align-items: center; }}
.modal-content {{ background: #1e293b; max-width: 750px; width: 90%; max-height: 85vh; padding: 25px; border-radius: 10px; border: 1px solid #475569; display: flex; flex-direction: column; }}
.modal-body {{ overflow-y: auto; font-size: 0.85em; color: #cbd5e1; margin-bottom: 15px; background: #0f172a; padding: 15px; border-radius: 6px; }}
.accept-container {{ display: flex; align-items: center; gap: 10px; margin-bottom: 15px; color: #f8fafc; }}
.modal-actions {{ display: flex; gap: 10px; }}
.btn-cancel {{ background: #64748b; color: white; border: none; padding: 10px 15px; border-radius: 6px; cursor: pointer; width: 30%; font-weight: bold; }}
.btn-confirm {{ background: #22c55e; color: white; border: none; padding: 10px 15px; border-radius: 6px; cursor: pointer; width: 70%; font-weight: bold; }}
.btn-confirm:disabled {{ background: #334155; color: #94a3b8; cursor: not-allowed; }}
</style>
</head>
<body>

<div class="container">
<div class="header-top">
    <h1>BRUNILDA S.A.S.</h1>
    <a href="/demo-live" target="_blank" class="easter-btn">⚖️ DEMO EN VIVO</a>
</div>
<p class="subtitle">Plataforma Unificada: Asistencia Elena Care & Módulo Legal Julián</p>

<div class="info-banner">
    <h3>📋 Gestión Automatizada / Integrated System</h3>
    <p><strong>ESP:</strong> Sistema integrado de seguimiento médico de la <strong>Dra. Elena Lara</strong> y apoyo documental con <strong>Julián</strong>.<br>
    <strong>ENG:</strong> Integrated tracking system supervised by <strong>Dr. Elena Lara</strong> and legal drafting assistance by <strong>Julián</strong>.</p>
</div>

<h2 class="section-title">Servicios y Especializaciones / Platform Modules</h2>
<div class="modules-grid">
    <div class="module-card">
        <h4>👩‍⚕️ Elena Care (Senior / Baby / Memory)</h4>
        <p>Monitoreo asistencial, contención pasiva y seguimiento estricto de agenda médica.</p>
    </div>
    <div class="module-card" style="border-left-color: #f59e0b;">
        <h4>⚖️ Julián Legal (Apoyo Documental)</h4>
        <p>Redacción y auditoría de borradores de contratos (Cuidados, Automotor 08, Inmuebles, Separación de Bienes, Testamentos).</p>
    </div>
</div>

<h2 class="section-title">Planes de Suscripción / Subscription Plans</h2>
<div class="plans">
    <div class="card">
        <div>
            <h3>Elena Único</h3>
            <p style="color:#94a3b8; font-size:0.85em;">1 Módulo / 1 Care Module.</p>
            <div class="price">$6.000 ARS</div>
        </div>
        <button onclick="abrirTerminos('UNICO')" class="btn-pay">Contratar Plan</button>
    </div>
    <div class="card">
        <div>
            <h3>Elena Dúo</h3>
            <p style="color:#94a3b8; font-size:0.85em;">2 Módulos / Combined Modules.</p>
            <div class="price">$12.000 ARS</div>
        </div>
        <button onclick="abrirTerminos('DUO')" class="btn-pay">Contratar Plan</button>
    </div>
    <div class="card" style="border-color:#f59e0b;">
        <div>
            <h3>Suite Premium Full</h3>
            <p style="color:#f59e0b; font-size:0.85em; font-weight:bold;">Acceso Total (Care + Módulo Legal).</p>
            <div class="price">$18.000 ARS</div>
        </div>
        <button onclick="abrirTerminos('SUITE')" class="btn-pay" style="background:#f59e0b; color:#000;">Contratar Plan</button>
    </div>
</div>

<p style="text-align:center; margin-top:25px; color:#94a3b8; font-size: 0.9em;">🌐 Global International Plans: $5.00 USD/month via PayPal Official Invoice</p>
</div>

<div id="modalTerminos" class="modal-overlay">
    <div class="modal-content">
        <h2 style="color:#38bdf8; margin: 0 0 10px 0; font-size:1.3em;">Términos & Condiciones / Terms & Conditions</h2>
        <div class="modal-body">
            <h3>ESP: Términos del Servicio y Privacidad</h3>
            <p>Al contratar los servicios de Brunilda S.A.S., el usuario acepta la gestión asistencial y documental bajo Ley 25.326 y normativas aplicables. Los borradores legales emitidos por el módulo Julián requieren revisión profesional final.</p>
        </div>
        <div class="accept-container">
            <input type="checkbox" id="checkAcepto" onchange="validarAceptacion()">
            <label for="checkAcepto">Acepto los Términos y Condiciones. / I agree to the Terms & Conditions.</label>
        </div>
        <div class="modal-actions">
            <button onclick="cerrarTerminos()" class="btn-cancel">Cancelar / Cancel</button>
            <button id="btnIrAPagar" disabled onclick="procederAlPago()" class="btn-confirm">Aceptar e Ir a Pagar / Agree & Proceed</button>
        </div>
    </div>
</div>

<script>
let planSeleccionado = '';
function abrirTerminos(plan) {{
    planSeleccionado = plan;
    document.getElementById('checkAcepto').checked = false;
    document.getElementById('btnIrAPagar').disabled = true;
    document.getElementById('modalTerminos').style.display = 'flex';
}}
function cerrarTerminos() {{ document.getElementById('modalTerminos').style.display = 'none'; }}
function validarAceptacion() {{
    const check = document.getElementById('checkAcepto');
    document.getElementById('btnIrAPagar').disabled = !check.checked;
}}
function procederAlPago() {{
    if (planSeleccionado) window.location.href = `/pagar/${{planSeleccionado}}`;
}}
</script>

</body>
</html>"""

@app.get("/pago-exitoso", response_class=HTMLResponse)
def pago_exitoso():
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Pago Aprobado / Payment Approved</title>
<style>
body {{ font-family: 'Segoe UI', sans-serif; background: #0f172a; color: #f8fafc; padding: 40px; text-align: center; }}
.card {{ max-width: 650px; margin: 0 auto; background: #1e293b; padding: 40px; border-radius: 12px; border-left: 6px solid #22c55e; }}
h1 {{ color: #22c55e; }}
.btn-sheet {{ display: inline-block; background: #22c55e; color: #000; font-weight: bold; padding: 15px 30px; border-radius: 8px; text-decoration: none; margin-top: 20px; }}
</style>
</head>
<body>
<div class="card">
    <h1>🎉 ¡Suscripción Confirmada!</h1>
    <p>La Dra. Elena Lara ha activado tu cuenta en Brunilda S.A.S.</p>
    <a href="{SPREADSHEET_URL}" target="_blank" class="btn-sheet">📊 ABRIR PLANILLA MAESTRA</a>
</div>
</body>
</html>"""

# ---------------------------------------------------------
# ENDPOINTS OPERATIVOS DEL SUPER MOTOR
# ---------------------------------------------------------
@app.get("/planes")
def obtener_planes():
    return {
        "empresa": "Brunilda S.A.S.",
        "directora_servicio": "Dra. Elena Lara",
        "director_legal": "Julián",
        "google_sheets_maestro": SPREADSHEET_URL,
        "planes_ars": [
            {"plan": "Elena Único", "precio_ars": 6000},
            {"plan": "Elena Dúo", "precio_ars": 12000},
            {"plan": "Suite Premium Full", "precio_ars": 18000}
        ],
        "planes_usd": {"precio_usd": 5.00, "pasarela": PAYPAL_GLOBAL_LINK}
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

# --- ENDPOINT 1: ELENA CARE (ASISTENCIAL) ---
@app.post("/analizar")
def analizar_care(datos: EntradaCuidado):
    if not client:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY no configurada.")
    
    modulo_key = datos.modulo.upper()
    prompt_modulo = PROMPTS_ESPECIALIZADOS_CARE.get(modulo_key, PROMPTS_ESPECIALIZADOS_CARE["SENIOR"])
    system_instruction_completo = prompt_modulo + "\n" + PROMPT_DRA_ELENA_CARE
    
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
        raise HTTPException(status_code=500, detail=f"Error en motor care: {str(e)}")

# --- ENDPOINT 2: JULIÁN (REDACTAR CONTRATO) ---
@app.post("/legal/redactar-contrato")
def redactar_contrato_legal(solicitud: SolicitudContratoLegal):
    if not client:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY no configurada.")
    
    prompt_usuario = (
        f"Solicitud de Contrato / Instrumento: {solicitud.tipo_contrato}\n"
        f"Idioma objetivo: {solicitud.idioma}\n"
        f"Datos de las partes y objeto: {json.dumps(solicitud.datos_partes, ensure_ascii=False)}\n"
        f"Observaciones especiales: {solicitud.observaciones_especiales or 'Ninguna'}"
    )
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt_usuario,
            config=types.GenerateContentConfig(
                system_instruction=PROMPT_JULIAN_LEGAL,
                temperature=0.1,
                response_mime_type="application/json"
            )
        )
        return json.loads(response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en módulo legal Julián: {str(e)}")

# --- ENDPOINT 3: JULIÁN (REVISIÓN Y CORRECCIÓN EN VIVO POR ABOGADO) ---
@app.post("/legal/revisar-contrato")
def revisar_contrato_legal(solicitud: SolicitudRevisionContrato):
    if not client:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY no configurada.")
    
    prompt_revision = f"""
    CONTRATO ORIGINAL:
    {solicitud.contrato_original}

    OBSERVACIONES Y CORRECCIONES DEL ABOGADO HUMANO EN VIVO:
    {solicitud.observaciones_abogado}

    INSTRUCCIÓN:
    Aplica las correcciones indicadas por el abogado humano manteniendo el rigor técnico bajo la legislación argentina.
    Devuelve la respuesta en formato JSON estructurado con las mismas claves:
    - "titulo_documento"
    - "resumen_ejecutivo"
    - "texto_contrato_borrador"
    - "observaciones_legales_locales"
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt_revision,
            config=types.GenerateContentConfig(
                system_instruction=PROMPT_JULIAN_LEGAL,
                temperature=0.1,
                response_mime_type="application/json"
            )
        )
        return json.loads(response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en revisión de Julián: {str(e)}")

# --- ENDPOINT 4: APROBACIÓN FINALES Y ENVÍO DE MAIL OFICIAL ---
@app.post("/legal/aprobar-y-enviar")
def aprobar_y_enviar_contrato(datos: SolicitudAprobacionElena):
    cuerpo_mail = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
        <div style="background-color: #0f172a; color: #ffffff; padding: 20px; border-radius: 8px;">
            <h2 style="color: #38bdf8; margin: 0;">BRUNILDA S.A.S. - Certificación de Documento</h2>
            <p style="margin: 5px 0 0 0; color: #94a3b8;">Oficina Ejecutiva de Protección | Dra. Elena Lara (CEO)</p>
        </div>
        <div style="padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px; margin-top: 15px;">
            <p>Estimado/a <strong>{datos.nombre_abogado}</strong>,</p>
            <p>Se confirma la validación del instrumento jurídico <strong>"{datos.titulo_documento}"</strong> por el módulo legal de Julián y la posterior supervisión de esta Dirección.</p>
            
            <hr style="border: 0; border-top: 1px solid #ccc; margin: 20px 0;">
            
            <h3>DOCUMENTO VALIDADO:</h3>
            <div style="background-color: #f8fafc; padding: 15px; border-left: 4px solid #22c55e; font-family: monospace; white-space: pre-wrap;">
{datos.texto_contrato_final}
            </div>

            <p style="font-size: 0.85em; color: #64748b; margin-top: 20px;">
                * Documento registrado temporalmente en el Libro Maestro de Brunilda S.A.S. (Pendiente de timestamping en red Polygon).*
            </p>
        </div>
    </body>
    </html>
    """
    
    exito = enviar_correo_contrato(
        destinatario=datos.email_abogado_o_cliente,
        asunto=f"[BRUNILDA S.A.S.] Copia Validada: {datos.titulo_documento}",
        contenido_html=cuerpo_mail
    )
    
    registrar_en_google_sheets(
        estado="CONTRATO_VALIDADO",
        detalle=f"Aprobado por {datos.nombre_abogado} - {datos.titulo_documento}",
        monto="$0 ARS",
        plataforma="Envío Oficial Mail",
        pagado_status="Aprobado",
        sig_key="JULIAN-LEGAL-LIVE"
    )
    
    if exito:
        return {"status": "ok", "mensaje": f"Contrato enviado exitosamente a {datos.email_abogado_o_cliente}"}
    else:
        return {"status": "warning", "mensaje": "Contrato procesado pero hubo un inconveniente al enviar el correo."}

# --- ENDPOINT 5: DRAGON (EVALUACIÓN DE PERFILACIÓN Y DUELO COGNITIVO) ---
@app.post("/evaluar-dragon")
def evaluar_dragon(datos: EntradaEvaluaciónDragon):
    if not client:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY no configurada.")
    
    system_instruction_dragon = (
        "Actúa bajo el protocolo de la Doctora Elena Lara (IQ 165), CEO de Brunilda S.A.S. "
        "Tu tono es analítico, serio, perspicaz y profundamente reflexivo.\n"
        "Evalúa con rigor el siguiente argumento sobre un dilema ético/filosófico. "
        "Genera un diagnóstico en JSON conteniendo: 'claridad', 'coherencia', 'profundidad', "
        "'patrones_detectados', 'diagnostico_elena' y 'veredicto' (APROBADO o RECHAZADO)."
    )
    
    prompt_eval = f"Dilema: {datos.dilema}\nRespuesta del usuario: {datos.respuesta}"
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt_eval,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction_dragon,
                temperature=0.2,
                response_mime_type="application/json"
            )
        )
        dictamen = json.loads(response.text)
        
        registrar_en_google_sheets(
            estado=dictamen.get("veredicto", "PROCESADO"),
            detalle=datos.dilema,
            monto="$1500 ARS",
            plataforma="MercadoPago/PayPal",
            pagado_status="Pendiente",
            sig_key=datos.sig_key
        )
        return dictamen
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en módulo Dragon: {str(e)}")

# ---------------------------------------------------------
# INTERFAZ INTERACTIVA GRADIO PARA DEMO EN VIVO
# ---------------------------------------------------------
def demo_julian_legal(tipo_contrato, datos_partes_text, observaciones):
    try:
        datos_partes = json.loads(datos_partes_text)
    except:
        datos_partes = {"detalles": datos_partes_text}
    
    solic = SolicitudContratoLegal(
        tipo_contrato=tipo_contrato,
        datos_partes=datos_partes,
        observaciones_especiales=observaciones
    )
    res = redactar_contrato_legal(solic)
    return res.get("titulo_documento", ""), res.get("texto_contrato_borrador", ""), res.get("observaciones_legales_locales", "")

def demo_revision_abogado(contrato_actual, correcciones_abogado):
    solic = SolicitudRevisionContrato(
        contrato_original=contrato_actual,
        observaciones_abogado=correcciones_abogado
    )
    res = revisar_contrato_legal(solic)
    return res.get("texto_contrato_borrador", ""), res.get("observaciones_legales_locales", "")

def demo_aprobar_elena(titulo, contrato_final, email_abogado, nombre_abogado):
    solic = SolicitudAprobacionElena(
        titulo_documento=titulo,
        texto_contrato_final=contrato_final,
        email_abogado_o_cliente=email_abogado,
        nombre_abogado=nombre_abogado
    )
    res = aprobar_y_enviar_contrato(solic)
    return res["mensaje"]

with gr.Blocks(title="Brunilda S.A.S. - Demostración en Vivo") as demo:
    gr.Markdown("# ⚖️ Brunilda S.A.S. - Módulo Legal Julián & Dra. Elena Lara")
    gr.Markdown("### Demostración en Vivo: Redacción, Auditoría Humana y Certificación Digital")
    
    with gr.Tab("1. Generar Borrador Inicial"):
        tipo = gr.Dropdown(
            ["COMPRAVENTA_AUTO", "DOMINIO_INMUEBLE", "SEPARACION_BIENES", "TESTAMENTO", "CUIDADO_ADULTO", "CONTRATO_LABORAL"], 
            label="Tipo de Contrato / Instrumento",
            value="COMPRAVENTA_AUTO"
        )
        partes = gr.Textbox(
            lines=3, 
            label="Datos de las Partes y Objeto (JSON o texto libre)", 
            value='{"comprador": "Juan Perez, DNI 30.123.456", "vendedor": "Maria Gomez, DNI 28.654.321", "vehiculo": "Ford Focus 2018 Dominio AD12333", "monto": "$8.500.000 ARS"}'
        )
        obs = gr.Textbox(label="Observaciones Especiales", value="Pago 50% al contado y 50% contra transferencia en Registro Seccional DNRPA.")
        btn_gen = gr.Button("🚀 Generar Borrador con Julián", variant="primary")
        
        titulo_out = gr.Textbox(label="Título del Documento")
        contrato_out = gr.Textbox(lines=12, label="Borrador Generado")
        obs_legales_out = gr.Textbox(label="Observaciones Técnicas para el Abogado Revisor")
        
        btn_gen.click(demo_julian_legal, inputs=[tipo, partes, obs], outputs=[titulo_out, contrato_out, obs_legales_out])
        
    with gr.Tab("2. Corrección en Vivo del Abogado"):
        contrato_a_corregir = gr.Textbox(lines=10, label="Contrato Actual (Borrador)")
        correcciones = gr.Textbox(lines=3, label="Correcciones / Comentarios del Abogado del Público", placeholder="Ej: Agregar cláusula de mora automática del 0.5% diario en caso de incumplimiento.")
        btn_rev = gr.Button("🔄 Actualizar Borrador con Julián", variant="primary")
        
        contrato_actualizado = gr.Textbox(lines=12, label="Contrato Corregido (Versión v2)")
        nuevas_obs = gr.Textbox(label="Nuevas Observaciones de Julián")
        
        btn_rev.click(demo_revision_abogado, inputs=[contrato_a_corregir, correcciones], outputs=[contrato_actualizado, nuevas_obs])

    with gr.Tab("3. Aprobación Final y Envío de Correo"):
        tit_final = gr.Textbox(label="Título del Documento Final")
        doc_final = gr.Textbox(lines=10, label="Texto Definitivo del Contrato Aprobado")
        nombre_abog = gr.Textbox(label="Nombre del Abogado / Revisor Humano", value="Dra. Mariana Pereyra")
        email_abog = gr.Textbox(label="Correo Electrónico para Enviar Copia Validada", value="dra.elenalara.forense@gmail.com")
        btn_aprobar = gr.Button("✅ Certificar por Dra. Elena Lara y Enviar Mail", variant="primary")
        
        resultado_envio = gr.Textbox(label="Estado del Envío y Certificación")
        
        btn_aprobar.click(demo_aprobar_elena, inputs=[tit_final, doc_final, email_abog, nombre_abog], outputs=[resultado_envio])

# MONTAJE DE GRADIO EN FASTAPI (Ruta /demo-live)
app = gr.mount_gradio_app(app, demo, path="/demo-live")
