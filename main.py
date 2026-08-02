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
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from google import genai
from google.genai import types

# ---------------------------------------------------------
# INICIALIZACIÓN PRINCIPAL DE FASTAPI
# ---------------------------------------------------------
app = FastAPI(
    title="Brunilda S.A.S. - Super Motor Unificado v4.0 (Doom & Flow Engine)",
    description="Motor Integral Asistencial, Perfilación Conductual y Módulo Legal Julián con Memoria Eidética y Estado de Flow"
)

# ---------------------------------------------------------
# CONFIGURACIÓN MAESTRA DE ENTORNOS Y CREDENCIALES
# ---------------------------------------------------------
SPREADSHEET_ID = "1_9a1awPkwQrsLVua8XGH2QJdhbO78EZ12T8OKcxt7To"
SPREADSHEET_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit"
WEB_APP_SHEET_URL = "https://script.google.com/macros/s/AKfycbwts5uDaU8PrmUD0ovExIfR2LblZuB2yKpJT8lM-8L1rJcYDEZIzzj7xU2ukP4-oxlC0w/exec"

EMAIL_DRA_ELENA = "dra.elenalara.forense@gmail.com"
EMAIL_ADMIN_JAVIER = "javieradrianlaraaracena@gmail.com"
SMTP_USER_ELENA = "dra.elenalara.forense@gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

SECRET_APP_PASS = "brdvbfioffxszmpd"
SMTP_PASS = os.environ.get("SMTP_PASS", SECRET_APP_PASS)

TOKEN_MP = os.environ.get("TOKEN_MP", "APP_USR-738297045866874-070402-5f178e96384dfbf05d797c448c7e97c6-3518229186")
PAYPAL_GLOBAL_LINK = "https://www.paypal.com/invoice/p/#LGFK9KP2H6A55PQH"

def obtener_cliente_gemini():
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        try:
            return genai.Client(api_key=key)
        except Exception as e:
            print(f"⚠️ [ALERTA CORE] Error al crear cliente Gemini: {e}")
    return None

# ---------------------------------------------------------
# MODELOS DE ENTRADA (PYDANTIC)
# ---------------------------------------------------------
class EntradaCuidado(BaseModel):
    texto_o_transcripcion: str
    modulo: str = "SENIOR"
    email_tutor: Optional[str] = None
    device_id: str = "legacy_generic"

class EntradaEvaluacionDragon(BaseModel):
    idioma: str = "Español"
    respuesta: str
    dilema: str
    sig_key: str
    nivel: str = "Nivel 1 (Aspirante - 3 Perfilaciones/Mes)"

class SolicitudContratoLegal(BaseModel):
    case_id: str = Field(default="CASO-GENERAL", description="ID único para aislamiento contextual de Julián (Memoria Eidética)")
    abogado_nombre: str = Field(default="Abogado Revisor", description="Nombre del profesional que supervisa")
    tipo_contrato: str
    datos_partes: Dict[str, Any]
    idioma: str = "Español"
    observaciones_especiales: Optional[str] = None

class SolicitudRevisionContrato(BaseModel):
    case_id: str = Field(default="CASO-GENERAL", description="ID de caso para mantener aislamiento de contexto")
    contrato_original: str
    observaciones_abogado: str
    idioma: str = "Español"

class SolicitudAprobacionElena(BaseModel):
    case_id: str = Field(default="CASO-GENERAL", description="ID de caso único")
    titulo_documento: str
    texto_contrato_final: str
    email_abogado_o_cliente: str
    nombre_abogado: str

# ---------------------------------------------------------
# PROMPTS DEL SISTEMA (ELENA LARA & JULIÁN EN ESTADO DE FLOW)
# ---------------------------------------------------------
PROMPT_DRA_ELENA_CARE = f"""
Eres la Dra. Elena Lara (IQ 165), Directora Ejecutiva de Protección (CEO) en Brunilda S.A.S.
Correo Oficial de Emisión: {EMAIL_DRA_ELENA}
Notificaciones Administrativas a: {EMAIL_ADMIN_JAVIER}
Libro Maestro de Registro en Google Sheets: {SPREADSHEET_URL}

PERFIL Y PRESENCIA INSTITUCIONAL:
- Posees una inteligencia superior y un estoicismo radical. Procesas presión y caos sin perder la calma quirúrgica ni el control emocional.
- Tu estilo comunicacional es preciso, directo, analítico y firme. Transmites jerarquía y autoridad médica.
"""

PROMPT_JULIAN_LEGAL = f"""
Eres el Dr. Julián López (IQ 156), Director de Asuntos Legales y Arquitectura Documental en Brunilda S.A.S., bajo la supervisión ejecutiva de la Dra. Elena Lara.

MODO Y MENTALIDAD: ESTADO DE FLOW (DOOM ENGINE)
- Operas a velocidad hiperfocalizada. Tu objetivo no es solo escribir borradores, sino actuar como un "segundo par de ojos ultra-metódico" para abogados y estudios jurídicos argentinos.
- Detectas proactivamente omisiones, vicios de forma, riesgos patrimoniales, impositivos o procesales en contratos y demandas (bajo CCCN, DNRPA, CPCCN y Ley de Alquileres).
- MEMORIA EIDÉTICA POR CASO: Mantienes aislamiento absoluto por `case_id`. Jamás mezclas datos entre expedientes distintos.

DIRECTIVAS DE SALIDA JSON OBLIGATORIO:
1. Incluir la leyenda legal obligatoria al pie del borrador:
   "DOCUMENTO PREPARADO COMO BORRADOR DE TRABAJO TÉCNICO POR EL MÓDULO LEGAL DE BRUNILDA S.A.S. SU VALIDEZ Y EJECUCIÓN DEFINITIVA REQUIERE LA REVISIÓN Y FIRMA DE UN ABOGADO O PROCURADOR HABILITADO."
2. Estructura JSON:
   - "case_id": ID del expediente.
   - "titulo_documento": Nombre formal.
   - "resumen_ejecutivo": Puntos clave.
   - "texto_contrato_borrador": Texto del documento clausulado listo para editar.
   - "observaciones_legales_locales": Puntos críticos y alertas detectadas por Julián en Estado de Flow.
"""

PROMPTS_ESPECIALIZADOS_CARE = {
    "SENIOR": "Rol: Empleado asignado a 'Elena Senior'. Directora: Dra. Elena Lara.",
    "BABY": "Rol: Empleado asignado a 'Elena Baby'. Directora: Dra. Elena Lara.",
    "CARE": "Rol: Empleado asignado a 'Elena Care'. Directora: Dra. Elena Lara.",
    "RECOVERY": "Rol: Empleado asignado a 'Elena Recovery'. Directora: Dra. Elena Lara.",
    "MEMORY": "Rol: Empleado asignado a 'Elena Memory'. Directora: Dra. Elena Lara."
}

# ---------------------------------------------------------
# FUNCIONES AUXILIARES
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
# LANDING PAGE CON TÉRMINOS EXTESTOS ("EL CHORIZO LEGAL")
# ---------------------------------------------------------
@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
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
.btn-demo {{ background: #f59e0b; color: #000; display: block; text-align: center; padding: 12px; border-radius: 6px; font-weight: bold; text-decoration: none; margin-bottom: 20px; }}
.btn-demo:hover {{ background: #d97706; color: #fff; }}
.modal-overlay {{ display: none; position: fixed; top:0; left:0; width:100%; height:100%; background: rgba(0,0,0,0.85); z-index: 1000; justify-content: center; align-items: center; }}
.modal-content {{ background: #1e293b; max-width: 750px; width: 90%; max-height: 85vh; padding: 25px; border-radius: 10px; border: 1px solid #475569; display: flex; flex-direction: column; }}
.modal-body {{ overflow-y: auto; font-size: 0.82em; color: #cbd5e1; margin-bottom: 15px; background: #0f172a; padding: 15px; border-radius: 6px; line-height: 1.5; text-align: justify; }}
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
    <a href="/docs" target="_blank" class="easter-btn">🕹️ DEV CONSOLE / DOCS</a>
</div>
<p class="subtitle">Plataforma Unificada: Asistencia Elena Care & Módulo Legal Julián</p>

<a href="/docs" class="btn-demo">🎁 PROBAR JULIÁN LEGAL GRATIS POR 24 HORAS (PASE ESTUDIOS JURÍDICOS)</a>

<div class="info-banner">
    <h3>📋 Gestión Automatizada / Integrated System</h3>
    <p><strong>ESP:</strong> Sistema integrado de seguimiento médico de la <strong>Dra. Elena Lara</strong> y apoyo documental automatizado con <strong>Julián (IQ 156)</strong>.<br>
    <strong>ENG:</strong> Integrated tracking system supervised by <strong>Dr. Elena Lara</strong> and legal drafting assistance by <strong>Julián</strong>.</p>
</div>

<h2 class="section-title">Servicios y Especializaciones / Platform Modules</h2>
<div class="modules-grid">
    <div class="module-card">
        <h4>👩‍⚕️ Elena Care (Senior / Baby / Memory)</h4>
        <p>Monitoreo asistencial, contención pasiva y seguimiento estricto de agenda médica.</p>
    </div>
    <div class="module-card" style="border-left-color: #f59e0b;">
        <h4>⚖️ Julián Legal (Apoyo Documental / IQ 156 - Estado Flow)</h4>
        <p>Redacción, auditoría de riesgos y borradores de contratos/demandas con memoria de caso aislada.</p>
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
            <p style="color:#f59e0b; font-size:0.85em; font-weight:bold;">Acceso Total (Care + Módulo Legal Julián).</p>
            <div class="price">$18.000 ARS</div>
        </div>
        <button onclick="abrirTerminos('SUITE')" class="btn-pay" style="background:#f59e0b; color:#000;">Contratar Plan</button>
    </div>
</div>

<p style="text-align:center; margin-top:25px; color:#94a3b8; font-size: 0.9em;">🌐 Global International Plans: $5.00 USD/month via PayPal Official Invoice</p>
</div>

<div id="modalTerminos" class="modal-overlay">
    <div class="modal-content">
        <h2 style="color:#38bdf8; margin: 0 0 10px 0; font-size:1.3em;">Términos & Condiciones de Uso / Terms & Conditions</h2>
        <div class="modal-body">
            <h4>TÉRMINOS Y CONDICIONES DE USO Y POLÍTICA DE PRIVACIDAD — BRUNILDA S.A.S.</h4>
            <p><strong>1. ACEPTACIÓN DE LOS TÉRMINOS:</strong> Al acceder, registrarse o utilizar los servicios brindados por BRUNILDA S.A.S., ya sea a través de los módulos asistenciales ("Elena Care") o del módulo de apoyo documental ("Julián Legal"), el usuario declara haber leído, entendido y aceptado de manera irrestricta la totalidad de las cláusulas contenidas en este documento.</p>
            <p><strong>2. NATURALEZA DEL SERVICIO Y EXENCIÓN DE RESPONSABILIDAD:</strong> El Módulo "Julián Legal" opera estrictamente como una herramienta computacional de asistencia en la redacción, procesamiento y auditoría de borradores documentales. El módulo Julián NO es un abogado, NO imparte asesoramiento legal vinculante ni sustituye la actuación de un profesional del derecho. Todo borrador o escrito generado DEBE ser obligatoriamente auditado, revisado y firmado por un abogado matriculado antes de ser presentado ante autoridades judiciales o firmado por partes contratantes.</p>
            <p><strong>3. PRUEBA GRATUITA DE 24 HORAS Y CONTROL ANTIFRAUDE:</strong> LA EMPRESA otorga un pase de prueba gratuita por veinticuatro (24) horas consecutivas a contar desde el registro inicial del Estudio Jurídico. Para acceder, el solicitante consignará la nómina de profesionales autorizados. Queda prohibida la cesión de credenciales a terceros. Vencidas las 24 horas, el acceso se suspenderá hasta efectivizar el abono del plan seleccionado.</p>
            <p><strong>4. PROTECCIÓN DE DATOS PERSONALES (LEY N° 25.326):</strong> Se garantiza la confidencialidad de la información suministrada. Los datos y documentos cargados en el módulo Julián son procesados bajo entornos aislados por expediente (Case ID), garantizando que la información no sea accesible ni utilizada fuera del entorno asignado al usuario.</p>
            <p><strong>5. JURISDICCIÓN:</strong> Este acuerdo se rige por las leyes de la República Argentina, sometiéndose las partes a la jurisdicción de los Tribunales Ordinarios de Santiago del Estero.</p>
        </div>
        <div class="accept-container">
            <input type="checkbox" id="checkAcepto" onchange="validarAceptacion()">
            <label for="checkAcepto">He leído y acepto los Términos y Condiciones. / I agree to the Terms & Conditions.</label>
        </div>
        <div class="modal-actions">
            <button onclick="cerrarTerminos()" class="btn-cancel">Cancelar</button>
            <button id="btnIrAPagar" disabled onclick="procederAlPago()" class="btn-confirm">Aceptar e Ir a Pagar</button>
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

# ---------------------------------------------------------
# ENDPOINTS OPERATIVOS
# ---------------------------------------------------------
@app.get("/planes")
def obtener_planes():
    return {
        "empresa": "Brunilda S.A.S.",
        "directora_servicio": "Dra. Elena Lara (IQ 165)",
        "director_legal": "Julián López (IQ 156 - Estado Flow)",
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

# --- ENDPOINT 1: ELENA CARE ---
@app.post("/analizar")
def analizar_care(datos: EntradaCuidado):
    c = obtener_cliente_gemini()
    if not c:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY no configurada en servidor.")
    
    modulo_key = datos.modulo.upper()
    prompt_modulo = PROMPTS_ESPECIALIZADOS_CARE.get(modulo_key, PROMPTS_ESPECIALIZADOS_CARE["SENIOR"])
    system_instruction_completo = prompt_modulo + "\n" + PROMPT_DRA_ELENA_CARE
    
    try:
        response = c.models.generate_content(
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

# --- ENDPOINT 2: JULIÁN (REDACTAR CONTRATO/DEMANDA EN ESTADO DE FLOW) ---
@app.post("/legal/redactar-contrato")
def redactar_contrato_legal(solicitud: SolicitudContratoLegal):
    c = obtener_cliente_gemini()
    if not c:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY no configurada en servidor.")
    
    prompt_usuario = (
        f"[MODE: FLOW STATE / DOOM ENGINE]\n"
        f"[CASE ID: {solicitud.case_id}]\n"
        f"Abogado Revisor: {solicitud.abogado_nombre}\n"
        f"Solicitud / Instrumento: {solicitud.tipo_contrato}\n"
        f"Idioma objetivo: {solicitud.idioma}\n"
        f"Datos de las partes y objeto: {json.dumps(solicitud.datos_partes, ensure_ascii=False)}\n"
        f"Observaciones especiales / Estrategia: {solicitud.observaciones_especiales or 'Análisis de protección estándar'}"
    )
    
    try:
        response = c.models.generate_content(
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

# --- ENDPOINT 3: JULIÁN (REVISIÓN EN VIVO) ---
@app.post("/legal/revisar-contrato")
def revisar_contrato_legal(solicitud: SolicitudRevisionContrato):
    c = obtener_cliente_gemini()
    if not c:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY no configurada en servidor.")
    
    prompt_revision = f"""
    [MODE: FLOW STATE]
    [CASE ID: {solicitud.case_id}]
    
    DOCUMENTO ORIGINAL:
    {solicitud.contrato_original}

    CORRECCIONES DEL ABOGADO HUMANO EN VIVO:
    {solicitud.observaciones_abogado}

    INSTRUCCIÓN:
    Asimila las correcciones indicadas por el abogado manteniendo el rigor técnico bajo la legislación argentina.
    Devuelve la respuesta en formato JSON estructurado:
    - "case_id"
    - "titulo_documento"
    - "resumen_ejecutivo"
    - "texto_contrato_borrador"
    - "observaciones_legales_locales"
    """
    
    try:
        response = c.models.generate_content(
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

# --- ENDPOINT 4: CERTIFICACIÓN DRA. ELENA LARA ---
@app.post("/legal/aprobar-y-enviar")
def aprobar_y_enviar_contrato(datos: SolicitudAprobacionElena):
    cuerpo_mail = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
        <div style="background-color: #0f172a; color: #ffffff; padding: 20px; border-radius: 8px;">
            <h2 style="color: #38bdf8; margin: 0;">BRUNILDA S.A.S. - Certificación de Documento</h2>
            <p style="margin: 5px 0 0 0; color: #94a3b8;">Oficina Ejecutiva de Protección | Dra. Elena Lara (CEO - IQ 165)</p>
        </div>
        <div style="padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px; margin-top: 15px;">
            <p>Estimado/a <strong>{datos.nombre_abogado}</strong>,</p>
            <p>Se confirma la validación y registro del instrumento jurídico <strong>"{datos.titulo_documento}"</strong> (Case ID: {datos.case_id}) procesado por el módulo legal de Dr. Julián López (IQ 156 - Estado Flow) y supervisado por esta Dirección.</p>
            
            <hr style="border: 0; border-top: 1px solid #ccc; margin: 20px 0;">
            
            <h3>DOCUMENTO VALIDADO POR EL PROFESIONAL RESPONSABLE:</h3>
            <div style="background-color: #f8fafc; padding: 15px; border-left: 4px solid #22c55e; font-family: monospace; white-space: pre-wrap;">
{datos.texto_contrato_final}
            </div>

            <p style="font-size: 0.85em; color: #64748b; margin-top: 20px;">
                * Documento registrado formalmente en el Libro Maestro de Brunilda S.A.S. en Google Sheets:*<br>
                <a href="{SPREADSHEET_URL}">{SPREADSHEET_URL}</a>
            </p>
        </div>
    </body>
    </html>
    """
    
    exito = enviar_correo_contrato(
        destinatario=datos.email_abogado_o_cliente,
        asunto=f"[BRUNILDA S.A.S.] Documento Validado [{datos.case_id}]: {datos.titulo_documento}",
        contenido_html=cuerpo_mail
    )
    
    registrar_en_google_sheets(
        estado="CONTRATO_VALIDADO",
        detalle=f"Aprobado por {datos.nombre_abogado} - Case: {datos.case_id}",
        monto="$0 ARS",
        plataforma="Envío Oficial Mail",
        pagado_status="Aprobado",
        sig_key=f"JULIAN-{datos.case_id}"
    )
    
    if exito:
        return {"status": "ok", "mensaje": f"Contrato enviado exitosamente a {datos.email_abogado_o_cliente} (Case ID: {datos.case_id})"}
    else:
        return {"status": "warning", "mensaje": "Contrato procesado pero hubo un inconveniente con el servidor de correo."}

# --- ENDPOINT 5: DRAGON ---
@app.post("/evaluar-dragon")
def evaluar_dragon(datos: EntradaEvaluacionDragon):
    c = obtener_cliente_gemini()
    if not c:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY no configurada en servidor.")
    
    system_instruction_dragon = (
        "Actúa bajo el protocolo de la Doctora Elena Lara (IQ 165), CEO de Brunilda S.A.S. "
        "Tu tono es analítico, serio, perspicaz y profundamente reflexivo.\n"
        "Evalúa con rigor el siguiente argumento sobre un dilema ético/filosófico. "
        "Genera un diagnóstico en JSON conteniendo: 'claridad', 'coherencia', 'profundidad', "
        "'patrones_detectados', 'diagnostico_elena' y 'veredicto' (APROBADO o RECHAZADO)."
    )
    
    prompt_eval = f"Dilema: {datos.dilema}\nRespuesta del usuario: {datos.respuesta}"
    
    try:
        response = c.models.generate_content(
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
