import os
import json
import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from google import genai
from google.genai import types

# IMPORTACIÓN DEL NUEVO MÓDULO DE MERCADO PAGO
from mercadopago_service import generar_link_mp

app = FastAPI(title="Brunilda S.A.S. - Motor de Cuidados & Pagos v1.5 (Master)")

# ---------------------------------------------------------
# VARIABLES DE ENTORNO EN RENDER
# ---------------------------------------------------------
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

PROMPT_SISTEMA_BASE = "Eres la Dra. Elena Lara (IQ 165), Directora Ejecutiva de Protección en Brunilda S.A.S."

class EntradaCuidado(BaseModel):
    texto_o_transcripcion: str
    modulo: str = "SENIOR"
    email_tutor: str = None
    device_id: str = "legacy_generic"

# ---------------------------------------------------------
# LANDING PAGE OFICIAL
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
body { font-family: sans-serif; background: #0f172a; color: #f8fafc; padding: 20px; }
.container { max-width: 800px; margin: 0 auto; background: #1e293b; padding: 25px; border-radius: 10px; }
h1 { color: #38bdf8; text-align: center; }
.terms { background: #334155; border-left: 4px solid #f59e0b; padding: 12px; margin-bottom: 20px; }
.btn-doc { display: block; text-align: center; background: #22c55e; color: #fff; padding: 12px; border-radius: 6px; text-decoration: none; margin-bottom: 20px; font-weight: bold; }
.plans { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
.card { background: #0f172a; border: 1px solid #475569; padding: 15px; border-radius: 6px; text-align: center; }
.price { font-size: 1.4em; color: #38bdf8; font-weight: bold; margin: 10px 0; }
.btn-pay { display: inline-block; background: #0284c7; color: #fff; padding: 8px 12px; border-radius: 4px; text-decoration: none; font-weight: bold; }
</style>
</head>
<body>
<div class="container">
<h1>BRUNILDA S.A.S.</h1>
<p style="text-align:center; color:#94a3b8;">Dra. Elena Lara — Ecosistema Elena Services (v0.5)</p>

<div class="terms">
<strong>⚠️ PRUEBA FREEMIUM 24 HORAS:</strong> Al instalar la app se activan 24hs de prueba pasiva continua con pantalla bloqueada para los 5 módulos según Términos & Condiciones.
</div>

<a href="/docs" target="_blank" class="btn-doc">🚀 PROBAR INTERFAZ INTERACTIVA Y API (/docs)</a>

<h2>Planes Disponibles</h2>
<div class="plans">
<div class="card">
<h3>Elena Único</h3>
<p>1 Módulo</p>
<div class="price">$6.000 ARS</div>
<a href="/pagar/UNICO" class="btn-pay">Suscribirme</a>
</div>
<div class="card">
<h3>Elena Dúo</h3>
<p>2 Módulos</p>
<div class="price">$12.000 ARS</div>
<a href="/pagar/DUO" class="btn-pay">Suscribirme</a>
</div>
<div class="card" style="border-color:#f59e0b;">
<h3>Elena Premium Suite</h3>
<p>5 Módulos Totales</p>
<div class="price">$63.000 ARS</div>
<a href="/pagar/SUITE" class="btn-pay">Suscribirme</a>
</div>
</div>

<p style="text-align:center; margin-top:20px;">🌐 Planes Internacionales: $5.00 USD/mes vía PayPal Factura Oficial</p>
</div>
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
        "planes_argentina_ars": [
            {"plan": "Elena Único", "precio_ars": 6000},
            {"plan": "Elena Dúo", "precio_ars": 12000},
            {"plan": "Elena Premium Suite", "precio_ars": 63000}
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
