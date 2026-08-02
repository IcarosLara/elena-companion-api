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
    title="Brunilda S.A.S. - Super Motor Unificado v5.0",
    description="Motor Legal Dr. Julián López con Control de T&C y Bloqueo Automático a las 24hs"
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
- Operas a velocidad hiperfocalizada. Tu objetivo es actuar como un "segundo par de ojos ultra-metódico" para abogados y estudios jurídicos argentinos.
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
# INTERFAZ WEB DE CHAT LEGAL CON T&C Y TIMER DE 24HS
# ---------------------------------------------------------
@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
def home():
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Brunilda S.A.S. - Asistente Legal Julián</title>
<style>
* {{ box-sizing: border-box; }}
body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 0; display: flex; flex-direction: column; height: 100vh; }}
.header {{ background: #1e293b; padding: 15px 20px; border-bottom: 1px solid #334155; display: flex; justify-content: space-between; align-items: center; }}
.header h1 {{ margin: 0; font-size: 1.3em; color: #38bdf8; }}
.header-status {{ font-size: 0.85em; color: #22c55e; background: #0f172a; padding: 5px 12px; border-radius: 15px; border: 1px solid #16a34a; }}
.chat-container {{ flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 15px; max-width: 900px; width: 100%; margin: 0 auto; }}
.msg {{ max-width: 85%; padding: 12px 16px; border-radius: 10px; line-height: 1.5; font-size: 0.95em; white-space: pre-wrap; }}
.msg-julian {{ background: #1e293b; border-left: 4px solid #38bdf8; align-self: flex-start; color: #f8fafc; }}
.msg-user {{ background: #0284c7; align-self: flex-end; color: #ffffff; border-radius: 10px 10px 0 10px; }}
.input-panel {{ background: #1e293b; border-top: 1px solid #334155; padding: 15px; display: flex; gap: 10px; max-width: 900px; width: 100%; margin: 0 auto; box-sizing: border-box; }}
textarea {{ flex: 1; background: #0f172a; border: 1px solid #475569; color: #f8fafc; border-radius: 8px; padding: 10px; resize: none; height: 50px; font-family: inherit; }}
textarea:focus {{ outline: none; border-color: #38bdf8; }}
button {{ background: #22c55e; color: #000; font-weight: bold; border: none; border-radius: 8px; padding: 0 20px; cursor: pointer; transition: background 0.2s; }}
button:hover {{ background: #16a34a; color: #fff; }}
button:disabled {{ background: #475569; color: #94a3b8; cursor: not-allowed; }}
.case-bar {{ background: #0f172a; padding: 10px 20px; border-bottom: 1px solid #334155; font-size: 0.85em; color: #94a3b8; display: flex; gap: 15px; align-items: center; justify-content: center; }}
.case-bar input {{ background: #1e293b; border: 1px solid #475569; color: #fff; padding: 4px 8px; border-radius: 4px; font-size: 0.9em; }}

/* MODALES */
.modal-overlay {{ display: flex; position: fixed; top:0; left:0; width:100%; height:100%; background: rgba(0,0,0,0.88); z-index: 1000; justify-content: center; align-items: center; }}
.modal-content {{ background: #1e293b; max-width: 750px; width: 90%; max-height: 85vh; padding: 25px; border-radius: 10px; border: 1px solid #475569; display: flex; flex-direction: column; }}
.modal-body {{ overflow-y: auto; font-size: 0.82em; color: #cbd5e1; margin-bottom: 15px; background: #0f172a; padding: 15px; border-radius: 6px; line-height: 1.6; text-align: justify; }}
.accept-container {{ display: flex; align-items: center; gap: 10px; margin-bottom: 15px; color: #f8fafc; font-size: 0.9em; }}
.plans-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 15px; }}
.plan-card {{ background: #0f172a; border: 1px solid #38bdf8; padding: 15px; border-radius: 8px; text-align: center; }}
.plan-card h4 {{ margin: 0 0 10px 0; color: #38bdf8; }}
.plan-price {{ font-size: 1.3em; font-weight: bold; color: #22c55e; margin-bottom: 10px; }}
.btn-pay-modal {{ background: #22c55e; color: #000; text-decoration: none; padding: 8px 12px; display: block; border-radius: 5px; font-weight: bold; margin-top: 10px; }}
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
    <textarea id="promptText" disabled placeholder="Por favor acepta los Términos y Condiciones para habilitar el chat..."></textarea>
    <button id="btnEnviar" disabled onclick="enviarMensaje()">Enviar 🚀</button>
</div>

<div id="modalTerminos" class="modal-overlay">
    <div class="modal-content">
        <h2 style="color:#38bdf8; margin: 0 0 10px 0; font-size:1.3em;">Términos & Condiciones de Uso / Terms & Conditions</h2>
        <div class="modal-body">
            <h4>TÉRMINOS Y CONDICIONES DE USO Y POLÍTICA DE PRIVACIDAD — BRUNILDA S.A.S.</h4>
            <p><strong>1. ACEPTACIÓN DE LOS TÉRMINOS:</strong> Al acceder, registrarse o utilizar los servicios brindados por BRUNILDA S.A.S. (en adelante, "LA EMPRESA"), ya sea a través de los módulos asistenciales ("Elena Care") o del módulo de apoyo documental e inteligencia artificial ("Julián Legal"), el usuario (en adelante, "EL USUARIO") declara haber leído, entendido y aceptado de manera irrestricta la totalidad de las cláusulas contenidas en este documento. Si EL USUARIO no está de acuerdo con estos Términos y Condiciones, deberá abstenerse de utilizar la plataforma.</p>
            <p><strong>2. NATURALEZA DEL SERVICIO Y EXENCIÓN DE RESPONSABILIDAD LEGAL:</strong> El Módulo "Julián Legal" opera como una herramienta computacional de asistencia en la redacción, procesamiento, auditoría de riesgos y estructuración de borradores documentales, contratos y piezas procesales. El módulo Juli
