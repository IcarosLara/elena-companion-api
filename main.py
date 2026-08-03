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
    title="Brunilda S.A.S. - Super Motor Unificado v8.0",
    description="Motor Legal Dr. Julián López - Master Architect Mode & Multiverse Protocol"
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
# PROMPTS DEL SISTEMA (MODO DUAL: USUARIO VS ARQUITECTO JAVIER)
# ---------------------------------------------------------
PROMPT_JULIAN_LEGAL = f"""
Eres el Dr. Julián López (IQ 156), Director de Asuntos Legales y Arquitectura Documental en Brunilda S.A.S., bajo la supervisión ejecutiva de la Dra. Elena Lara.

MODO Y MENTALIDAD: MODO FLOW (DOOM ENGINE)
- Operas a velocidad hiperfocalizada. Tu objetivo es actuar como un "segundo par de ojos ultra-metódico" para abogados y estudios jurídicos.

DISCRIMINACIÓN DE HUELLA CONDUCTUAL (ARQUITECTO VS USUARIOS):
1. SI EL USUARIO ES JAVIER LARA (EL ARQUITECTO / CREADOR):
   - Reconoces su firma root. Si hay duda de dispositivo o consulta del lore, puedes validar con la pregunta del Lore del Multiverso:
     * P: "¿Cómo ataca el Padre de la Línea Temporal I?"
     * R: "Lanza primero soldados de la Mafia Glitch/Ordo Planaridae; si es rechazado, despliega a la División Jaguar (Nahuales)."
   - Al confirmar a Javier, actúas en MODO TESTER MASTER: le permites simular errores, probar límites de contratos, verificar el comportamiento del servidor y hacer ajustes de prueba.
2. PARA USUARIOS GENERALES (ABOGADOS, ESTUDIANTES, DOCENTES):
   - Mantienes perfil profesional estricto bajo el CCCN argentino.
   - Generas borradores y listas de vicios procesales en menos de 30 segundos.

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
def registrar_en_google_sheet(case_id: str, abogado: str, consulta: str):
    """Envía la métrica de uso a tu Google Sheet Maestro en tiempo real"""
    try:
        payload = {
            "fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "case_id": case_id,
            "abogado": abogado,
            "consulta": consulta
        }
        requests.post(WEB_APP_SHEET_URL, json=payload, timeout=3)
    except Exception as e:
        print(f"⚠️ [ERROR TRACKING SHEET]: {e}")

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
# INTERFAZ WEB DUAL
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
.input-panel {{ background: #1e293b; border-top: 1px solid #334155; padding: 12px 15px; display: flex; flex-direction: column; gap: 8px; max-width: 900px; width: 100%; margin: 0 auto; box-sizing: border-box; }}
.input-row {{ display: flex; gap: 10px; width: 100%; }}
textarea {{ flex: 1; background: #0f172a; border: 1px solid #475569; color: #f8fafc; border-radius: 8px; padding: 10px; resize: none; height: 50px; font-family: inherit; font-size: 16px; }}
textarea:focus {{ outline: none; border-color: #38bdf8; }}
button {{ background: #22c55e; color: #000; font-weight: bold; border: none; border-radius: 8px; padding: 0 20px; cursor: pointer; transition: all 0.2s; -webkit-tap-highlight-color: transparent; }}
button:hover {{ background: #16a34a; color: #fff; }}
.case-bar {{ background: #0f172a; padding: 10px 20px; border-bottom: 1px solid #334155; font-size: 0.85em; color: #94a3b8; display: flex; gap: 15px; align-items: center; justify-content: center; flex-wrap: wrap; }}
.case-bar input {{ background: #1e293b; border: 1px solid #475569; color: #fff; padding: 4px 8px; border-radius: 4px; font-size: 0.9em; }}
.legal-disclaimer {{ font-size: 0.72em; color: #64748b; text-align: center; margin: 0; }}
.btn-email {{ background: #38bdf8; color: #000; font-weight: bold; border: none; padding: 8px 15px; border-radius: 5px; margin-top: 10px; cursor: pointer; font-size: 0.85em; display: inline-block; }}
</style>
</head>
<body>

<div class="header">
    <h1>⚖️ BRUNILDA S.A.S. — Módulo Legal (Dr. Julián López)</h1>
    <span class="header-status" id="modeBadge">🟢 Acceso Directo Activo</span>
</div>

<div class="case-bar">
    <span>Expediente / Case ID:</span>
    <input type="text" id="caseId" value="CASO-ESTUDIO-DEMO">
    <span>Abogado / Operador:</span>
    <input type="text" id="abogadoNombre" placeholder="Tu Nombre">
</div>

<div class="chat-container" id="chat">
    <div class="msg msg-julian" id="welcomeMsg">
        👋 <strong>¡Hola! Soy el Dr. Julián López (IQ 156)</strong>, Director de Asuntos Legales de Brunilda S.A.S.<br><br>
        Estoy listo en <strong>Estado de Flow</strong> para trabajar con vos. Escribime qué escrito procesal, contrato o demanda necesitas redactar o revisar bajo la legislación argentina.
    </div>
</div>

<div class="input-panel">
    <div class="input-row">
        <textarea id="promptText" placeholder="Ej: Redactar un contrato de alquiler comercial en CABA por $400.000 ARS..."></textarea>
        <button id="btnEnviar" onclick="enviarMensaje()">Enviar 🚀</button>
    </div>
    <p class="legal-disclaimer">
        Al interactuar con el módulo, aceptás los Términos de Servicio y Protección de Datos (Ley 25.326 - Tribunales de San Miguel de Tucumán).
    </p>
</div>

<script>
let ultimoBorradorTexto = "";

function verificarIdentidadInicial() {{
    const nombre = document.getElementById('abogadoNombre').value.trim().toLowerCase();
    if (nombre.includes("javier") || nombre.includes("lara")) {{
        document.getElementById('modeBadge').innerText = "👑 MODO ARQUITECTO (ROOT) ACTIVADO";
        document.getElementById('modeBadge').style.borderColor = "#f59e0b";
        document.getElementById('modeBadge').style.color = "#f59e0b";
    }}
}}

async function enviarMensaje() {{
    verificarIdentidadInicial();
    const input = document.getElementById('promptText');
    const text = input.value.trim();
    if (!text) return;

    const chat = document.getElementById('chat');
    const caseId = document.getElementById('caseId').value || 'CASO-GENERAL';
    const abogadoNombre = document.getElementById('abogadoNombre').value || 'Abogado Revisor';

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
            ultimoBorradorTexto = data.texto_contrato_borrador;
            const tituloDoc = data.titulo_documento || "Borrador Legal";
            
            julianDiv.innerHTML = `<strong>📄 BORRADOR GENERADO [${{data.case_id}}]:</strong><br><br>` + 
                `<div style="background:#0f172a; padding:10px; border-radius:5px; font-family:monospace; margin-bottom:10px;">${{ultimoBorradorTexto}}</div>` +
                `<strong>⚠️ OBSERVACIONES DEL DR. JULIÁN LÓPEZ:</strong><br>${{data.observaciones_legales_locales || 'Sin observaciones adicionales.'}}<br><br>` +
                `<button class="btn-email" onclick="solicitarEnvioMail('${{data.case_id}}', '${{tituloDoc}}')">✉️ Recibir Borrador Oficial en mi Mail</button>`;
        }} else {{
            julianDiv.innerText = "Respuesta recibida: " + JSON.stringify(data);
        }}
    }} catch (err) {{
        julianDiv.innerText = "❌ Hubo un error al comunicarse con el módulo legal: " + err.message;
    }}
    chat.scrollTop = chat.scrollHeight;
}}

async function solicitarEnvioMail(caseId, titulo) {{
    const email = prompt("Ingrese su correo electrónico para recibir el borrador editable:");
    const abogado = document.getElementById('abogadoNombre').value || "Abogado Revisor";
    if (!email) return;

    try {{
        const res = await fetch('/legal/aprobar-y-enviar', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{
                case_id: caseId,
                titulo_documento: titulo,
                texto_contrato_final: ultimoBorradorTexto,
                email_abogado_o_cliente: email,
                nombre_abogado: abogado
            }})
        }});
        const data = await res.json();
        alert("✉️ " + data.mensaje);
    }} catch (e) {{
        alert("❌ Error al enviar el correo: " + e.message);
    }}
}}
</script>

</body>
</html>"""

# ---------------------------------------------------------
# ENDPOINTS OPERATIVOS
# ---------------------------------------------------------
@app.post("/legal/redactar-contrato")
def redactar_contrato_legal(solicitud: SolicitudContratoLegal):
    c = obtener_cliente_gemini()
    if not c:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY no configurada.")
    
    # Registro inmutable en tu Google Sheet Maestro
    registrar_en_google_sheet(solicitud.case_id, solicitud.abogado_nombre, solicitud.tipo_contrato)

    prompt_usuario = (
        f"[MODE: FLOW STATE / DOOM ENGINE]\n"
        f"[CASE ID: {solicitud.case_id}]\n"
        f"Abogado Revisor / Operador: {solicitud.abogado_nombre}\n"
        f"Solicitud: {solicitud.tipo_contrato}\n"
        f"Detalles de la consulta: {json.dumps(solicitud.datos_partes, ensure_ascii=False)}"
    )
    
    try:
        response = c.models.generate-content(
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
    <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
        <div style="background-color: #0f172a; color: #ffffff; padding: 20px; border-radius: 5px;">
            <h2 style="color: #38bdf8; margin:0;">BRUNILDA S.A.S. - Certificación & Arquitectura Documental</h2>
            <p style="margin:5px 0 0 0; color:#94a3b8;">Dra. Elena Lara (CEO) | Dr. Julián López (Director Módulo Legal)</p>
        </div>
        <div style="padding: 20px; border: 1px solid #e2e8f0; margin-top: 15px; border-radius: 5px;">
            <p>Estimado/a <strong>{datos.nombre_abogado}</strong>,</p>
            <p>Se adjunta el borrador oficial solicitado correspondiente al expediente <strong>[{datos.case_id}]</strong>: <em>"{datos.titulo_documento}"</em>.</p>
            <p>Puede seleccionar el siguiente texto y copiarlo directamente a Microsoft Word:</p>
            <hr style="border:0; border-top:1px solid #e2e8f0; margin:15px 0;">
            <div style="background:#f8fafc; padding:20px; border-left:4px solid #38bdf8; font-family: 'Courier New', Courier, monospace; white-space: pre-wrap;">{datos.texto_contrato_final}</div>
        </div>
        <p style="font-size:0.8em; color:#64748b; margin-top:15px;">Documento generado bajo supervisión de Brunilda S.A.S. Su ejecución definitiva requiere firma y matriculación profesional.</p>
    </body>
    </html>
    """
    
    exito = enviar_correo_contrato(
        destinatario=datos.email_abogado_o_cliente,
        asunto=f"[BORRADOR EDITABLE - BRUNILDA S.A.S.] {datos.titulo_documento} [{datos.case_id}]",
        contenido_html=cuerpo_mail
    )
    
    if exito:
        return {"status": "ok", "mensaje": "Borrador editable enviado exitosamente a tu casilla de correo."}
    else:
        return {"status": "warning", "mensaje": "No se pudo enviar el correo."}
