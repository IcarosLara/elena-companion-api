import os
import json
import datetime
import requests
import smtplib
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
    title="Brunilda S.A.S. - Super Motor Unificado v5.4",
    description="Motor Legal Dr. Julián López - Fix Multiusuario Simultáneo"
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
class SolicitudContratoLegal(BaseModel):
    case_id: str = Field(default="CASO-GENERAL", description="ID único para aislamiento contextual")
    abogado_nombre: str = Field(default="Abogado Revisor", description="Nombre del profesional")
    tipo_contrato: str
    datos_partes: Dict[str, Any]
    idioma: str = "Español"
    observaciones_especiales: Optional[str] = None

class SolicitudAprobacionElena(BaseModel):
    case_id: str = Field(default="CASO-GENERAL", description="ID de caso único")
    titulo_documento: str
    texto_contrato_final: str
    email_abogado_o_cliente: str
    nombre_abogado: str

# ---------------------------------------------------------
# PROMPTS DEL SISTEMA
# ---------------------------------------------------------
PROMPT_JULIAN_LEGAL = f"""
Eres el Dr. Julián López (IQ 156), Director de Asuntos Legales y Arquitectura Documental en Brunilda S.A.S., bajo la supervisión ejecutiva de la Dra. Elena Lara.

MODO Y MENTALIDAD: MODO FLOW (DOOM ENGINE)
- Operas a velocidad hiperfocalizada. Tu objetivo es actuar como un "segundo par de ojos ultra-metódico" para abogados y estudios jurídicos.
- Detectas proactivamente omisiones, vicios de forma, riesgos patrimoniales, impositivos o procesales en contratos y demandas (bajo CCCN, DNRPA, CPCCN y Ley de Alquileres).
- MEMORIA EIDÉTICA POR CASO: Mantienes aislamiento absoluto por `case_id`.

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

# ---------------------------------------------------------
# FUNCIONES AUXILIARES
# ---------------------------------------------------------
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

# ---------------------------------------------------------
# INTERFAZ WEB RESPONSIVA MULTIUSUARIO
# ---------------------------------------------------------
@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
def home():
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>Brunilda S.A.S. - Asistente Legal Julián</title>
<style>
* {{ box-sizing: border-box; }}
body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 0; display: flex; flex-direction: column; height: 100vh; }}
.header {{ background: #1e293b; padding: 15px 20px; border-bottom: 1px solid #334155; display: flex; justify-content: space-between; align-items: center; }}
.header h1 {{ margin: 0; font-size: 1.2em; color: #38bdf8; }}
.header-status {{ font-size: 0.85em; color: #22c55e; background: #0f172a; padding: 5px 12px; border-radius: 15px; border: 1px solid #16a34a; }}
.chat-container {{ flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 15px; max-width: 900px; width: 100%; margin: 0 auto; }}
.msg {{ max-width: 85%; padding: 12px 16px; border-radius: 10px; line-height: 1.5; font-size: 0.95em; white-space: pre-wrap; }}
.msg-julian {{ background: #1e293b; border-left: 4px solid #38bdf8; align-self: flex-start; color: #f8fafc; }}
.msg-user {{ background: #0284c7; align-self: flex-end; color: #ffffff; border-radius: 10px 10px 0 10px; }}
.input-panel {{ background: #1e293b; border-top: 1px solid #334155; padding: 15px; display: flex; gap: 10px; max-width: 900px; width: 100%; margin: 0 auto; box-sizing: border-box; }}
textarea {{ flex: 1; background: #0f172a; border: 1px solid #475569; color: #f8fafc; border-radius: 8px; padding: 10px; resize: none; height: 50px; font-family: inherit; font-size: 16px; }}
textarea:focus {{ outline: none; border-color: #38bdf8; }}
button {{ background: #22c55e; color: #000; font-weight: bold; border: none; border-radius: 8px; padding: 0 20px; cursor: pointer; transition: all 0.2s; -webkit-tap-highlight-color: transparent; }}
button:hover {{ background: #16a34a; color: #fff; }}
button:disabled {{ background: #475569 !important; color: #94a3b8 !important; cursor: not-allowed !important; opacity: 0.6; }}
.case-bar {{ background: #0f172a; padding: 10px 20px; border-bottom: 1px solid #334155; font-size: 0.85em; color: #94a3b8; display: flex; gap: 15px; align-items: center; justify-content: center; flex-wrap: wrap; }}
.case-bar input {{ background: #1e293b; border: 1px solid #475569; color: #fff; padding: 4px 8px; border-radius: 4px; font-size: 0.9em; }}

/* MODAL Y BOTONES */
.modal-overlay {{ display: flex; position: fixed; top:0; left:0; width:100%; height:100%; background: rgba(0,0,0,0.92); z-index: 1000; justify-content: center; align-items: center; padding: 10px; }}
.modal-content {{ background: #1e293b; max-width: 750px; width: 100%; max-height: 90vh; padding: 20px; border-radius: 12px; border: 1px solid #475569; display: flex; flex-direction: column; }}
.modal-body {{ overflow-y: auto; font-size: 0.85em; color: #cbd5e1; margin-bottom: 15px; background: #0f172a; padding: 15px; border-radius: 8px; line-height: 1.6; text-align: justify; -webkit-overflow-scrolling: touch; }}
.accept-container {{ display: flex; align-items: center; gap: 12px; margin-bottom: 15px; color: #f8fafc; font-size: 0.95em; cursor: pointer; padding: 10px; background: #0f172a; border-radius: 6px; }}
.accept-container input[type="checkbox"] {{ width: 24px; height: 24px; cursor: pointer; accent-color: #22c55e; }}
.btn-email {{ background: #38bdf8; color: #000; font-weight: bold; border: none; padding: 8px 15px; border-radius: 5px; margin-top: 10px; cursor: pointer; font-size: 0.85em; display: inline-block; }}
.btn-email:hover {{ background: #0284c7; color: #fff; }}
</style>
</head>
<body>

<div class="header">
    <h1>⚖️ BRUNILDA S.A.S. — Módulo Legal (Dr. Julián López)</h1>
    <span class="header-status" id="timerStatus">🟢 Prueba 24hs Activa</span>
</div>

<div class="case-bar">
    <span>Expediente / Case ID:</span>
    <input type="text" id="caseId" value="CASO-ESTUDIO-DEMO">
    <span>Abogado Revisor:</span>
    <input type="text" id="abogadoNombre" value="Dr. Abogado Revisor">
</div>

<div class="chat-container" id="chat">
    <div class="msg msg-julian">
        👋 <strong>¡Hola! Soy el Dr. Julián López (IQ 156)</strong>, Director de Asuntos Legales de Brunilda S.A.S.<br><br>
        Estoy listo en <strong>Estado de Flow</strong> para trabajar con vos. Una vez aceptados los Términos y Condiciones, escribime qué escrito procesal, contrato o demanda necesitas redactar o revisar bajo la legislación argentina.
    </div>
</div>

<div class="input-panel">
    <textarea id="promptText" disabled placeholder="Acepta los Términos y Condiciones para habilitar el chat..."></textarea>
    <button id="btnEnviar" disabled onclick="enviarMensaje()">Enviar 🚀</button>
</div>

<div id="modalTerminos" class="modal-overlay">
    <div class="modal-content">
        <h2 style="color:#38bdf8; margin: 0 0 10px 0; font-size:1.3em;">Términos & Condiciones de Uso / Terms & Conditions</h2>
        <div class="modal-body">
            <h4>TÉRMINOS Y CONDICIONES DE USO Y POLÍTICA DE PRIVACIDAD — BRUNILDA S.A.S.</h4>
            <p><strong>1. ACEPTACIÓN DE LOS TÉRMINOS:</strong> Al acceder o utilizar los servicios brindados por BRUNILDA S.A.S., el usuario declara haber leído, entendido y aceptado la totalidad de las cláusulas. Si el usuario no está de acuerdo, deberá abstenerse de utilizar la plataforma.</p>
            <p><strong>2. NATURALEZA DEL SERVICIO Y EXENCIÓN DE RESPONSABILIDAD LEGAL:</strong> El Módulo "Julián Legal" opera como una herramienta computacional de asistencia en la redacción, procesamiento y auditoría de riesgos. El módulo NO es un abogado matriculado ni imparte asesoramiento legal vinculante. Todo borrador generado DEBE ser obligatoriamente auditado y firmado por un abogado profesional antes de su presentación judicial o firma contractual.</p>
            <p><strong>3. PRUEBA GRATUITA DE 24 HORAS:</strong> LA EMPRESA otorga un pase de prueba gratuita por veinticuatro (24) horas consecutivas a contar desde el registro/aceptación inicial. Vencidas las 24 horas, el sistema requerirá la selección de un plan de suscripción mensual.</p>
            <p><strong>4. PROTECCIÓN DE DATOS PERSONALES (LEY N° 25.326):</strong> En cumplimiento de la Ley N° 25.326, LA EMPRESA garantiza la confidencialidad de la información. Los datos y documentos procesados operan bajo memoria aislada por expediente (`Case ID`).</p>
            <p><strong>5. JURISDICCIÓN Y LEY APLICABLE:</strong> Este acuerdo se rige por las leyes de la República Argentina, sometiéndose las partes a los <strong>Tribunales Ordinarios competentes de San Miguel de Tucumán</strong>.</p>
        </div>
        <div class="accept-container" onclick="toggleCheckboxDirecto(event)">
            <input type="checkbox" id="checkAcepto" onchange="validarAceptacion()" onclick="event.stopPropagation(); validarAceptacion();">
            <label for="checkAcepto" style="cursor:pointer;">He leído, acepto y me notifico de los Términos y Condiciones del Servicio.</label>
        </div>
        <button id="btnAceptarTerminos" disabled onclick="aceptarTerminos()" style="padding:15px; font-size:1.05em; width:100%;">Aceptar y Comenzar Prueba de 24hs 🚀</button>
    </div>
</div>

<script>
const DURACION_PRUEBA_MS = 24 * 60 * 60 * 1000;

function toggleCheckboxDirecto(e) {{
    const check = document.getElementById('checkAcepto');
    check.checked = !check.checked;
    validarAceptacion();
}}

function validarAceptacion() {{
    const check = document.getElementById('checkAcepto');
    const btn = document.getElementById('btnAceptarTerminos');
    if (check.checked) {{
        btn.disabled = false;
        btn.style.background = '#22c55e';
        btn.style.color = '#000000';
        btn.style.opacity = '1';
    }} else {{
        btn.disabled = true;
        btn.style.background = '#475569';
        btn.style.color = '#94a3b8';
        btn.style.opacity = '0.6';
    }}
}}

function verificarEstadoPrueba() {{
    const acepto = localStorage.getItem('termAccepted');
    const inicioTimestamp = localStorage.getItem('trialStartTimestamp');

    if (acepto === 'true' && inicioTimestamp) {{
        document.getElementById('modalTerminos').style.display = 'none';
        habilitarChat();
        
        const tiempoTranscurrido = Date.now() - parseInt(inicioTimestamp, 10);
        if (tiempoTranscurrido < DURACION_PRUEBA_MS) {{
            const horasRestantes = Math.round((DURACION_PRUEBA_MS - tiempoTranscurrido) / (1000 * 60 * 60));
            document.getElementById('timerStatus').innerText = `🟢 Prueba Activa (${{horasRestantes}}h restantes)`;
        }}
    }}
}}

function aceptarTerminos() {{
    localStorage.setItem('termAccepted', 'true');
    localStorage.setItem('trialStartTimestamp', Date.now().toString());
    document.getElementById('modalTerminos').style.display = 'none';
    habilitarChat();
}}

function habilitarChat() {{
    const txt = document.getElementById('promptText');
    const btn = document.getElementById('btnEnviar');
    txt.disabled = false;
    btn.disabled = false;
    txt.placeholder = "Ej: Redactar un contrato de alquiler comercial por $400.000 ARS...";
}}

async function enviarMensaje() {{
    const input = document.getElementById('promptText');
    const text = input.value.trim();
    if (!text) return;

    const chat = document.getElementById('chat');
    const caseId = document.getElementById('caseId').value || 'CASO-GENERAL';
    const abogadoNombre = document.getElementById('abogadoNombre').value || 'Abogado';

    const userDiv = document.createElement('div');
    userDiv.className = 'msg msg-user';
    userDiv.innerText = text;
    chat.appendChild(userDiv);

    input.value = '';
    chat.scrollTop = chat.scrollHeight;

    const julianDiv = document.createElement('div');
    julianDiv.className = 'msg msg-julian';
    julianDiv.innerText = '⚡ Dr. Julián López está procesando en Modo Flow...';
    chat.appendChild(julianDiv);
    chat.scrollTop = chat.scrollHeight;

    try {{
        const response = await fetch('/legal/redactar-contrato', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{
                case_id: caseId,
                abogado_nombre: abogadoNombre,
                tipo_contrato: text.substring(0, 50),
                datos_partes: {{ "instruccion_abogado": text }},
                idioma: "Español"
            }})
        }});

        const data = await response.json();
        if (data.texto_contrato_borrador) {{
            const contratoTexto = data.texto_contrato_borrador;
            const tituloDoc = data.titulo_documento || "Borrador Legal";
            
            julianDiv.innerHTML = `<strong>📄 BORRADOR GENERADO [${{data.case_id}}]:</strong><br><br>` + 
                `<div style="background:#0f172a; padding:10px; border-radius:5px; font-family:monospace; margin-bottom:10px;">${{contratoTexto}}</div>` +
                `<strong>⚠️ OBSERVACIONES DEL DR. JULIÁN LÓPEZ:</strong><br>${{data.observaciones_legales_locales || 'Sin observaciones adicionales.'}}<br><br>` +
                `<button class="btn-email" onclick="solicitarEnvioMail('${{data.case_id}}', '${{tituloDoc}}')">✉️ Recibir Borrador Certificado por Mail</button>`;
        }} else {{
            julianDiv.innerText = "Respuesta recibida: " + JSON.stringify(data);
        }}
    }} catch (err) {{
        julianDiv.innerText = "❌ Hubo un error al comunicarse con el módulo legal: " + err.message;
    }}
    chat.scrollTop = chat.scrollHeight;
}}

async function solicitarEnvioMail(caseId, titulo) {{
    const email = prompt("Ingrese su casilla de correo electrónico para recibir el borrador oficial:");
    if (!email) return;

    try {{
        const res = await fetch('/legal/aprobar-y-enviar', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{
                case_id: caseId,
                titulo_documento: titulo,
                texto_contrato_final: "Documento generado bajo supervisión de Julián López.",
                email_abogado_o_cliente: email,
                nombre_abogado: "Abogado Revisor"
            }})
        }});
        const data = await res.json();
        alert("✉️ " + data.mensaje);
    }} catch (e) {{
        alert("❌ Error al enviar el correo: " + e.message);
    }}
}}

window.onload = verificarEstadoPrueba;
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
        "director_legal": "Dr. Julián López (IQ 156 - Flow State)",
        "google_sheets_maestro": SPREADSHEET_URL,
        "planes_ars": [
            {"plan": "Elena Único", "precio_ars": 6000},
            {"plan": "Elena Dúo", "precio_ars": 12000},
            {"plan": "Suite Premium Full", "precio_ars": 18000}
        ],
        "planes_usd": {"precio_usd": 15.00, "pasarela": PAYPAL_GLOBAL_LINK}
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

# --- ENDPOINT LEGAL ---
@app.post("/legal/redactar-contrato")
def redactar_contrato_legal(solicitud: SolicitudContratoLegal):
    c = obtener_cliente_gemini()
    if not c:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY no configurada.")
    
    prompt_usuario = (
        f"[MODE: FLOW STATE / DOOM ENGINE]\n"
        f"[CASE ID: {solicitud.case_id}]\n"
        f"Abogado Revisor: {solicitud.abogado_nombre}\n"
        f"Solicitud: {solicitud.tipo_contrato}\n"
        f"Detalles de la consulta: {json.dumps(solicitud.datos_partes, ensure_ascii=False)}"
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
        raise HTTPException(status_code=500, detail=f"Error en Julián: {str(e)}")

@app.post("/legal/aprobar-y-enviar")
def aprobar_y_enviar_contrato(datos: SolicitudAprobacionElena):
    cuerpo_mail = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <div style="background-color: #0f172a; color: #ffffff; padding: 20px;">
            <h2 style="color: #38bdf8;">BRUNILDA S.A.S. - Certificación Documental</h2>
            <p>Dra. Elena Lara (CEO) | Dr. Julián López (Director Módulo Legal)</p>
        </div>
        <div style="padding: 20px; border: 1px solid #ccc; margin-top: 15px;">
            <p>Estimado/a <strong>{datos.nombre_abogado}</strong>,</p>
            <p>Se valida el instrumento jurídico <strong>"{datos.titulo_documento}"</strong> (Case ID: {datos.case_id}).</p>
            <pre style="background:#f8fafc; padding:15px; border-left:4px solid #22c55e;">{datos.texto_contrato_final}</pre>
        </div>
    </body>
    </html>
    """
    
    exito = enviar_correo_contrato(
        destinatario=datos.email_abogado_o_cliente,
        asunto=f"[BRUNILDA S.A.S.] Documento Validado [{datos.case_id}]: {datos.titulo_documento}",
        contenido_html=cuerpo_mail
    )
    
    if exito:
        return {"status": "ok", "mensaje": "Mail enviado exitosamente"}
    else:
        return {"status": "warning", "mensaje": "No se pudo enviar el correo."}
