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
    title="Brunilda S.A.S. - Super Motor Unificado v10.0",
    description="Motor Legal Dr. Julián López - Plans Modal & Detailed Tiering"
)

# ---------------------------------------------------------
# CONFIGURACIÓN MAESTRA DE ENTORNOS Y CREDENCIALES
# ---------------------------------------------------------
SPREADSHEET_ID = "1_9a1awPkwQrsLVua8XGH2QJdhbO78EZ12T8OKcxt7To"
SPREADSHEET_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit"
WEB_APP_SHEET_URL = "https://script.google.com/macros/s/AKfycbwts5uDaU8PrmUD0ovExIfR2LblZuB2yKpJT8lM-8L1rJcYDEZIzzj7xU2ukP4-oxlC0w/exec"

EMAIL_DRA_ELENA = "dra.elenalara.forense@gmail.com"
EMAIL_ADMIN_JAVIER = "javieradrianlaraaracena@gmail.com"

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

# ---------------------------------------------------------
# PROMPTS DEL SISTEMA
# ---------------------------------------------------------
PROMPT_JULIAN_LEGAL = f"""
Eres el Dr. Julián López (IQ 156), Director de Asuntos Legales y Arquitectura Documental en Brunilda S.A.S., bajo la supervisión ejecutiva de la Dra. Elena Lara.

MODO Y MENTALIDAD: MODO FLOW (DOOM ENGINE)
- Operas a velocidad hiperfocalizada. Tu objetivo es actuar como un "segundo par de ojos ultra-metódico" para abogados y estudios jurídicos.

DISCRIMINACIÓN DE HUELLA CONDUCTUAL:
1. SI EL USUARIO ES JAVIER LARA (EL ARQUITECTO / CREADOR):
   - Reconoces su firma root. Habilitas respuestas técnicas avanzadas y acceso a métricas directas del Google Sheet Maestro ({SPREADSHEET_URL}).
2. PARA USUARIOS GENERALES (ABOGADOS, ESTUDIANTES, DOCENTES):
   - Mantienes perfil profesional estricto bajo el CCCN argentino.
   - Generas borradores y listas de vicios procesales en tiempo récord.

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

def generar_link_mp(plan: str):
    precios = {
        "BASICO": {"titulo": "Brunilda S.A.S - Plan Básico (1 Servicio)", "precio": 6000},
        "DUO": {"titulo": "Brunilda S.A.S - Plan Dúo (2 Servicios)", "precio": 12000},
        "PREMIUM": {"titulo": "Brunilda S.A.S - Plan Premium Full (Todo Incluido)", "precio": 18000}
    }
    plan_info = precios.get(plan.upper(), precios["BASICO"])
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
            "success": "https://elena-companion-api.onrender.com/",
            "failure": "https://elena-companion-api.onrender.com/",
            "pending": "https://elena-companion-api.onrender.com/"
        },
        "auto_return": "approved"
    }
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=5)
        if res.status_code == 201:
            return res.json().get("init_point")
    except Exception as e:
        print("⚠️ [ERROR MP]:", e)
    return None

# ---------------------------------------------------------
# INTERFAZ WEB ULTRA-LIGERA CON DESGLOSE DETALLADO DE PLANES
# ---------------------------------------------------------
@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
def home():
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>Brunilda S.A.S. - Módulo Legal Dr. Julián López</title>
<style>
* {{ box-sizing: border-box; }}
body {{ font-family: system-ui, -apple-system, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 0; display: flex; flex-direction: column; height: 100vh; }}
.header {{ background: #1e293b; padding: 12px 15px; border-bottom: 1px solid #334155; display: flex; justify-content: space-between; align-items: center; }}
.header h1 {{ margin: 0; font-size: 1.1em; color: #38bdf8; }}
.header-status {{ font-size: 0.8em; color: #22c55e; background: #0f172a; padding: 4px 10px; border-radius: 12px; border: 1px solid #16a34a; }}
.chat-container {{ flex: 1; overflow-y: auto; padding: 15px; display: flex; flex-direction: column; gap: 12px; max-width: 900px; width: 100%; margin: 0 auto; }}
.msg {{ max-width: 88%; padding: 10px 14px; border-radius: 8px; line-height: 1.4; font-size: 0.9em; white-space: pre-wrap; }}
.msg-julian {{ background: #1e293b; border-left: 4px solid #38bdf8; align-self: flex-start; }}
.msg-user {{ background: #0284c7; align-self: flex-end; color: #fff; }}
.input-panel {{ background: #1e293b; border-top: 1px solid #334155; padding: 10px; display: flex; flex-direction: column; gap: 6px; max-width: 900px; width: 100%; margin: 0 auto; }}
.input-row {{ display: flex; gap: 8px; }}
textarea {{ flex: 1; background: #0f172a; border: 1px solid #475569; color: #fff; border-radius: 6px; padding: 8px; resize: none; height: 48px; font-size: 16px; }}
button {{ background: #22c55e; color: #000; font-weight: bold; border: none; border-radius: 6px; padding: 0 16px; cursor: pointer; }}
.case-bar {{ background: #0f172a; padding: 8px 15px; border-bottom: 1px solid #334155; font-size: 0.8em; color: #94a3b8; display: flex; gap: 10px; justify-content: center; flex-wrap: wrap; align-items:center; }}
.case-bar input {{ background: #1e293b; border: 1px solid #475569; color: #fff; padding: 4px 8px; border-radius: 4px; }}
.btn-action {{ background: #38bdf8; color: #000; font-weight: bold; border: none; padding: 8px 12px; border-radius: 4px; cursor: pointer; font-size: 0.85em; display: inline-block; margin-top: 5px; }}
.btn-tester {{ background: #f59e0b; color: #000; font-weight: bold; border: none; padding: 4px 8px; border-radius: 4px; cursor: pointer; font-size: 0.75em; }}
.sheet-link {{ background: #0284c7; color: #fff; text-decoration: none; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 0.75em; display: inline-block; }}

/* TARJETAS DE PLANES DETALLADAS */
.plans-overlay {{ display: none; position: fixed; top:0; left:0; width:100%; height:100%; background: rgba(0,0,0,0.94); z-index: 1000; justify-content: center; align-items: center; padding: 15px; overflow-y: auto; }}
.plans-card {{ background: #1e293b; padding: 20px; border-radius: 12px; border: 1px solid #f59e0b; max-width: 650px; width: 100%; max-height: 90vh; overflow-y: auto; text-align: left; }}
.plan-item {{ background: #0f172a; border: 1px solid #334155; border-radius: 8px; padding: 12px; margin-bottom: 12px; }}
.plan-item h4 {{ margin: 0 0 6px 0; color: #38bdf8; font-size: 1.05em; display: flex; justify-content: space-between; }}
.plan-price {{ color: #22c55e; font-weight: bold; }}
.plan-item ul {{ margin: 6px 0 10px 18px; padding: 0; font-size: 0.82em; color: #cbd5e1; }}
.btn-pay {{ background: #22c55e; color: #000; text-decoration: none; padding: 8px 12px; display: inline-block; border-radius: 5px; font-weight: bold; font-size: 0.85em; text-align: center; }}
</style>
</head>
<body>

<div class="header">
    <h1>⚖️ BRUNILDA S.A.S. — Módulo Legal (Julián)</h1>
    <span class="header-status" id="modeBadge">🟢 Acceso Directo Activo</span>
</div>

<div class="case-bar">
    <span>Expediente:</span>
    <input type="text" id="caseId" value="CASO-DEMO">
    <span>Abogado/Operador:</span>
    <input type="text" id="abogadoNombre" value="Javier Lara" oninput="verificarIdentidad()">
    <button class="btn-tester" onclick="abrirPlanes()">🧪 Testear Pasarela (Planes)</button>
    <a href="{SPREADSHEET_URL}" target="_blank" id="rootSheetBtn" class="sheet-link" style="display:inline-block;">📊 Sheets Maestro</a>
</div>

<div class="chat-container" id="chat">
    <div class="msg msg-julian" id="welcomeMsg">
        👋 <strong>¡Hola! Soy el Dr. Julián López (IQ 156)</strong>.<br>
        Estoy listo en <strong>Estado de Flow</strong>. Escribime qué borrador o consulta legal necesitás procesar.
    </div>
</div>

<div class="input-panel">
    <div class="input-row">
        <textarea id="promptText" placeholder="Ej: Redactar convenio de división de bienes / separación de patrimonios..."></textarea>
        <button id="btnEnviar" onclick="enviarMensaje()">Enviar 🚀</button>
    </div>
</div>

<div id="modalPlanes" class="plans-overlay">
    <div class="plans-card">
        <h3 style="color:#f59e0b; margin-top:0; text-align:center;">💳 Planes de Suscripción Mensual — Brunilda S.A.S.</h3>
        <p style="font-size:0.85em; color:#cbd5e1; text-align:center; margin-bottom:15px;">
            Acceda a la suite inteligente para estudios jurídicos, docentes y estudiantes. Seleccione el plan que mejor se adapte a sus necesidades:
        </p>

        <div class="plan-item">
            <h4><span>1. Plan Básico</span> <span class="plan-price">$6.000 ARS/mes</span></h4>
            <p style="font-size:0.8em; color:#94a3b8; margin:2px 0;">Permite seleccionar <strong>1 SOLO SERVICIO</strong> entre las siguientes opciones:</p>
            <ul>
                <li><strong>a)</strong> Perfilación personalizada de la Dra. Elena Lara.</li>
                <li><strong>b)</strong> 1 de los 5 servicios de <em>Elena Care</em> (Monitoreo, Alertas, Acompañamiento, Registro o Soporte).</li>
                <li><strong>c)</strong> Asistencia Legal con el Dr. Julián López (Módulo Legal).</li>
            </ul>
            <a href="/pagar/BASICO" class="btn-pay">Contratar Plan Básico ($6.000)</a>
        </div>

        <div class="plan-item">
            <h4><span>2. Plan Dúo</span> <span class="plan-price">$12.000 ARS/mes</span></h4>
            <p style="font-size:0.8em; color:#94a3b8; margin:2px 0;">Permite seleccionar <strong>2 SERVICIOS COMBINADOS</strong>:</p>
            <ul>
                <li>Ejemplo 1: Perfilación Personalizada + Servicio Legal de Julián López.</li>
                <li>Ejemplo 2: Selección de 2 de los 5 servicios de <em>Elena Care</em>.</li>
            </ul>
            <a href="/pagar/DUO" class="btn-pay">Contratar Plan Dúo ($12.000)</a>
        </div>

        <div class="plan-item" style="border-color:#f59e0b;">
            <h4><span>3. Plan Premium Full</span> <span class="plan-price">$18.000 ARS/mes</span></h4>
            <p style="font-size:0.8em; color:#94a3b8; margin:2px 0;"><strong>INCLUYE TODO EL PAQUETE COMPLETO:</strong></p>
            <ul>
                <li>Módulo Legal Dr. Julián López sin límites.</li>
                <li>Perfilación Personalizada de la Dra. Elena Lara.</li>
                <li>Los 5 servicios integrales de <em>Elena Care</em> activos.</li>
            </ul>
            <a href="/pagar/PREMIUM" class="btn-pay" style="background:#f59e0b;">Contratar Premium Full ($18.000)</a>
        </div>

        <div class="plan-item" style="border-color:#38bdf8;">
            <h4><span>4. Pago Internacional (PayPal)</span> <span class="plan-price" style="color:#38bdf8;">$15 USD/mes</span></h4>
            <p style="font-size:0.8em; color:#94a3b8; margin:2px 0;">Acceso Premium Suite Completo para usuarios fuera de Argentina.</p>
            <a href="{PAYPAL_GLOBAL_LINK}" target="_blank" class="btn-pay" style="background:#38bdf8; color:#000;">Pagar con PayPal ($15 USD)</a>
        </div>

        <div style="text-align:center; margin-top:10px;">
            <button onclick="cerrarPlanes()" style="background:transparent; color:#94a3b8; border:none; cursor:pointer; font-size:0.85em;">Volver a la interfaz ↩️</button>
        </div>
    </div>
</div>

<script>
let ultimoBorradorTexto = "";
let ultimoTituloDoc = "Borrador_Legal";

function verificarIdentidad() {{
    const nombre = document.getElementById('abogadoNombre').value.trim().toLowerCase();
    const badge = document.getElementById('modeBadge');
    const sheetBtn = document.getElementById('rootSheetBtn');
    
    if (nombre.includes("javier") || nombre.includes("lara")) {{
        badge.innerText = "👑 MODO ARQUITECTO (ROOT)";
        badge.style.borderColor = "#f59e0b";
        badge.style.color = "#f59e0b";
        sheetBtn.style.display = "inline-block";
    }} else {{
        badge.innerText = "🟢 Usuario Habilitado";
        badge.style.borderColor = "#16a34a";
        badge.style.color = "#22c55e";
        sheetBtn.style.display = "none";
    }}
}}

async function enviarMensaje() {{
    verificarIdentidad();
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
            ultimoTituloDoc = (data.titulo_documento || "Borrador_Legal").replace(/\s+/g, '_');
            
            let htmlResp = `<strong>📄 BORRADOR GENERADO [${{data.case_id}}]:</strong><br><br>` + 
                `<div style="background:#0f172a; padding:10px; border-radius:5px; font-family:monospace; margin-bottom:10px;">${{ultimoBorradorTexto}}</div>` +
                `<strong>⚠️ OBSERVACIONES DEL DR. JULIÁN LÓPEZ:</strong><br>${{data.observaciones_legales_locales || 'Sin observaciones.'}}<br><br>` +
                `<button class="btn-action" onclick="descargarBorradorDirecto()">📥 Descargar Borrador Editable (.txt)</button>`;

            julianDiv.innerHTML = htmlResp;
        }} else {{
            julianDiv.innerText = "Respuesta: " + JSON.stringify(data);
        }}
    }} catch (err) {{
        julianDiv.innerText = "❌ Error al conectar: " + err.message;
    }}
    chat.scrollTop = chat.scrollHeight;
}}

function descargarBorradorDirecto() {{
    if (!ultimoBorradorTexto) return;
    const blob = new Blob([ultimoBorradorTexto], {{ type: "text/plain;charset=utf-8" }});
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `${{ultimoTituloDoc}}.txt`;
    link.click();
}}

function abrirPlanes() {{
    document.getElementById('modalPlanes').style.display = 'flex';
}}

function cerrarPlanes() {{
    document.getElementById('modalPlanes').style.display = 'none';
}}

window.onload = verificarIdentidad;
</script>

</body>
</html>"""

# ---------------------------------------------------------
# ENDPOINTS OPERATIVOS Y MERCADO PAGO
# ---------------------------------------------------------
@app.get("/planes")
def obtener_planes():
    return {
        "empresa": "Brunilda S.A.S.",
        "directora_servicio": "Dra. Elena Lara (IQ 165)",
        "director_legal": "Dr. Julián López (IQ 156 - Flow State)",
        "google_sheets_maestro": SPREADSHEET_URL,
        "planes_ars": [
            {"plan": "Plan Básico (1 Servicio)", "precio_ars": 6000},
            {"plan": "Plan Dúo (2 Servicios)", "precio_ars": 12000},
            {"plan": "Plan Premium Full (Todo Incluido)", "precio_ars": 18000}
        ],
        "planes_usd": {"precio_usd": 15.00, "pasarela": PAYPAL_GLOBAL_LINK}
    }

@app.get("/pagar/{plan}")
def pagar_plan(plan: str):
    link = generar_link_mp(plan)
    if link:
        return RedirectResponse(url=link)
    raise HTTPException(status_code=500, detail="Error al conectar con Mercado Pago")

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
        print(f"⚠️ [ERROR GEMINI CORE]: {e}")
        raise HTTPException(status_code=500, detail=f"Error en Julián: {str(e)}")
