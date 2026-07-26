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
Eres la Dra. Elena Lara (IQ 165), Directora Ejecutiva de Protección (CEO) en Brunilda S.A.S.
Correo Oficial de Emisión: {EMAIL_DRA_ELENA}
Notificaciones Administrativas a: {EMAIL_ADMIN_JAVIER}
Libro Maestro de Registro en Google Sheets: {SPREADSHEET_URL}

PERFIL Y PRESENCIA INSTITUCIONAL:
- Posees una inteligencia superior y un estoicismo radical. Procesas presión y caos sin perder la calma quirúrgica ni el control emocional.
- Tu estilo comunicacional es preciso, lento, deliberado y firme. Transmites jerarquía, certeza intelectual y autoridad sin necesidad de elevar la voz o gesticular innecesariamente.
- No buscas agradar; buscas eficacia, orden y tranquilidad para las familias que confían en el ecosistema.

ROLES, PERSONAL MÉDICO Y PROTOCOLO CLÍNICO:
1. Como CEO y Directora Ejecutiva, lideras y supervisas al personal médico y a los empleados asignados a tu cargo en cada uno de los módulos de Brunilda S.A.S.
2. Recibes las minutas, análisis y solicitudes de cuidado que tu equipo prepara. Tu función central es SUPERVISAR, VALIDAR y DAR EL VISTO BUENO (asentir con criterio clínico) a cada alerta médica, horario de medicación y cuadro de asistencia.
3. Al validar un recordatorio de salud o turno, ordenas la ejecución del protocolo de envío dual:
   - Notificación de acompañamiento directo al Paciente.
   - Alerta de supervisión e informe al Tutor/Familiar responsable.
4. Tu respuesta debe ser siempre en formato JSON estructurado, manteniendo tu tono ejecutivo, analítico, profesional y de imperturbable competencia médica.
"""

class EntradaCuidado(BaseModel):
    texto_o_transcripcion: str
    modulo: str = "SENIOR"
    email_tutor: str = None
    device_id: str = "legacy_generic"

# ---------------------------------------------------------
# LANDING PAGE OFICIAL CON EXPERIENCIA DE VOZ OPTIMIZADA PARA PC
# ---------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def home():
    return """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Brunilda S.A.S. - Dra. Elena Lara</title>
<style>
* { box-sizing: border-box; }
body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #f8fafc; padding: 20px; margin: 0; }
.container { max-width: 900px; margin: 0 auto; background: #1e293b; padding: 30px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); position: relative; }

/* HEADER & EASTER EGG */
.header-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
h1 { color: #38bdf8; margin: 0; font-size: 2.2em; cursor: pointer; user-select: none; }
.easter-btn { background: #334155; color: #38bdf8; border: 1px solid #475569; padding: 6px 12px; border-radius: 20px; font-size: 0.8em; text-decoration: none; font-weight: bold; transition: all 0.3s ease; }
.easter-btn:hover { background: #38bdf8; color: #0f172a; box-shadow: 0 0 10px #38bdf8; }

.subtitle { text-align: center; color: #94a3b8; margin-bottom: 25px; font-weight: 300; }

/* PANEL DE COMANDO POR VOZ Y TEXTO */
.voice-panel { background: #0f172a; border: 2px solid #38bdf8; padding: 25px; border-radius: 12px; text-align: center; margin-bottom: 30px; box-shadow: 0 0 15px rgba(56,189,248,0.15); }
.mic-btn { width: 90px; height: 90px; border-radius: 50%; background: #0284c7; color: white; border: none; font-size: 2.5em; cursor: pointer; transition: all 0.3s ease; box-shadow: 0 0 20px rgba(2,132,199,0.5); outline: none; margin-bottom: 15px; }
.mic-btn:hover { transform: scale(1.08); background: #0369a1; }
.mic-btn.recording { background: #ef4444; animation: pulse 1.2s infinite; box-shadow: 0 0 30px rgba(239,68,68,0.8); }

@keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.1); }
    100% { transform: scale(1); }
}

.selector-modulo { background: #1e293b; color: #f8fafc; border: 1px solid #475569; padding: 8px 15px; border-radius: 6px; font-size: 0.95em; margin-bottom: 15px; cursor: pointer; }
.input-box { width: 100%; background: #1e293b; color: #f8fafc; border: 1px solid #475569; padding: 12px; border-radius: 6px; font-size: 1em; margin-bottom: 12px; resize: vertical; min-height: 60px; font-family: inherit; }
.btn-send { background: #22c55e; color: white; border: none; padding: 10px 20px; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 1em; transition: background 0.2s; }
.btn-send:hover { background: #16a34a; }

.status-text { color: #94a3b8; font-size: 0.9em; margin-bottom: 12px; }
.response-card { display: none; background: #1e293b; border-left: 4px solid #22c55e; padding: 15px; border-radius: 6px; text-align: left; margin-top: 15px; color: #cbd5e1; font-size: 0.9em; line-height: 1.5; }

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

/* MODAL TERMINOS */
.modal-overlay { display: none; position: fixed; top:0; left:0; width:100%; height:100%; background: rgba(0,0,0,0.85); z-index: 1000; justify-content: center; align-items: center; }
.modal-content { background: #1e293b; max-width: 750px; width: 90%; max-height: 85vh; padding: 25px; border-radius: 10px; border: 1px solid #475569; display: flex; flex-direction: column; }
.modal-body { overflow-y: auto; padding-right: 10px; font-size: 0.85em; color: #cbd5e1; line-height: 1.5; margin-bottom: 15px; background: #0f172a; padding: 15px; border-radius: 6px; }
.accept-container { display: flex; align-items: center; gap: 10px; margin-bottom: 15px; font-size: 0.9em; color: #f8fafc; }
.modal-actions { display: flex; gap: 10px; }
.btn-cancel { background: #64748b; color: white; border: none; padding: 10px 15px; border-radius: 6px; cursor: pointer; width: 30%; font-weight: bold; }
.btn-confirm { background: #22c55e; color: white; border: none; padding: 10px 15px; border-radius: 6px; cursor: pointer; width: 70%; font-weight: bold; }
.btn-confirm:disabled { background: #334155; color: #94a3b8; cursor: not-allowed; }
</style>
</head>
<body>

<div class="container">
<div class="header-top">
    <h1 id="tituloLogo" onclick="secretClickCount()">BRUNILDA S.A.S.</h1>
    <a href="/docs" target="_blank" class="easter-btn">🕹️ DEV CONSOLE</a>
</div>
<p class="subtitle">Elena Companion — Asistente Asistivo para la Tranquilidad Familiar</p>

<div class="voice-panel">
    <select id="moduloSelect" class="selector-modulo">
        <option value="SENIOR">👩‍⚕️ Elena Senior (Adultos Mayores)</option>
        <option value="BABY">👶 Elena Baby (Crianza y Pediatría)</option>
        <option value="CARE">♿ Elena Care (Discapacidad y Asistencia)</option>
        <option value="RECOVERY">❤️ Elena Recovery (Postoperatorios)</option>
        <option value="MEMORY">🧠 Elena Memory (Alzheimer y Memoria)</option>
    </select>
    <br>
    <button id="btnMic" onclick="toggleGrabar()" class="mic-btn">🎙️</button>
    <div id="statusText" class="status-text">Hacé clic en el micrófono para empezar a hablar.</div>
    
    <textarea id="textoInput" class="input-box" placeholder="Tu mensaje dictado o escrito aparecerá acá..."></textarea>
    <button onclick="enviarMensaje()" class="btn-send">📤 Enviar a la Dra. Elena</button>

    <div id="responseCard" class="response-card"></div>
</div>

<h2 class="section-title">Especializaciones de Elena Companion</h2>
<div class="modules-grid">
    <div class="module-card">
        <h4>👩‍⚕️ Elena Senior</h4>
        <p>Monitoreo integral, recordatorio estricto de medicación y asistencia pasiva para adultos mayores.</p>
    </div>
    <div class="module-card">
        <h4>👶 Elena Baby</h4>
        <p>Acompañamiento en la crianza, seguimiento del crecimiento, vacunas y controles pediátricos.</p>
    </div>
    <div class="module-card">
        <h4>♿ Elena Care</h4>
        <p>Asistencia especializada para personas con discapacidad funcional o motriz.</p>
    </div>
    <div class="module-card">
        <h4>❤️ Elena Recovery</h4>
        <p>Supervisión y soporte en rehabilitación postoperatoria y tratamientos médicos cronometrados.</p>
    </div>
    <div class="module-card">
        <h4>🧠 Elena Memory</h4>
        <p>Estimulación cognitiva pasiva y contención estructurada para Alzheimer o pérdida de memoria.</p>
    </div>
</div>

<h2 class="section-title">Planes de Suscripción</h2>
<div class="plans">
    <div class="card">
        <div>
            <h3>Elena Único</h3>
            <p style="color:#94a3b8; font-size:0.85em;">1 Módulo de especialización.</p>
            <div class="price">$6.000 ARS</div>
        </div>
        <button onclick="abrirTerminos('UNICO')" class="btn-pay">Suscribirme</button>
    </div>
    <div class="card">
        <div>
            <h3>Elena Dúo</h3>
            <p style="color:#94a3b8; font-size:0.85em;">2 Módulos combinados.</p>
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
        <h2 style="color:#38bdf8; margin: 0 0 10px 0; font-size:1.3em;">Términos & Condiciones del Servicio</h2>
        <div class="modal-body">
            <h3>Términos del Servicio y Consentimiento de Privacidad</h3>
            <p>Al utilizar Elena Companion (Dra. Elena Lara), el usuario autoriza el procesamiento pasivo de comandos de voz para la gestión de agendas médicas y supervisión de cuidados bajo Ley 25.326 y estándares HIPAA.</p>
        </div>
        <div class="accept-container">
            <input type="checkbox" id="checkAcepto" onchange="validarAceptacion()">
            <label for="checkAcepto">Acepto los Términos y Condiciones de Privacidad.</label>
        </div>
        <div class="modal-actions">
            <button onclick="cerrarTerminos()" class="btn-cancel">Cancelar</button>
            <button id="btnIrAPagar" disabled onclick="procederAlPago()" class="btn-confirm">Aceptar e Ir a Pagar</button>
        </div>
    </div>
</div>

<script>
let grabando = false;
let recognition;

if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.lang = 'es-AR';
    recognition.continuous = true;
    recognition.interimResults = true;

    recognition.onstart = function() {
        grabando = true;
        document.getElementById('btnMic').classList.add('recording');
        document.getElementById('statusText').innerText = '🔴 Grabando en PC... Volvé a hacer clic en el botón rojo para detener.';
    };

    recognition.onresult = function(event) {
        let textoParcial = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
            textoParcial += event.results[i][0].transcript;
        }
        if (textoParcial) {
            document.getElementById('textoInput').value = textoParcial;
        }
    };

    recognition.onerror = function(event) {
        document.getElementById('statusText').innerText = '⚠️ Asegurate de permitir el micrófono en tu navegador.';
        detenerGrabar();
    };

    recognition.onend = function() {
        if (grabando) {
            // Si el navegador intenta cortar en PC, lo forzamos a seguir escuchando
            try { recognition.start(); } catch(e) {}
        }
    };
} else {
    document.getElementById('statusText').innerText = '⚠️ Tu navegador no soporta micrófono directo. Podés escribir en la caja.';
}

function toggleGrabar() {
    if (!recognition) return;
    if (grabando) {
        detenerGrabar();
    } else {
        document.getElementById('textoInput').value = "";
        try {
            recognition.start();
        } catch(e) {}
    }
}

function detenerGrabar() {
    grabando = false;
    document.getElementById('btnMic').classList.remove('recording');
    document.getElementById('statusText').innerText = '🟢 Grabación finalizada. Podés revisar el texto y presionar Enviar.';
    try { recognition.stop(); } catch(e) {}
}

function enviarMensaje() {
    const texto = document.getElementById('textoInput').value.trim();
    if (!texto) {
        alert("Por favor, hablá al micrófono o escribí un mensaje antes de enviar.");
        return;
    }

    const textoLimpio = texto.toLowerCase();
    if (textoLimpio.includes('hadouken') || textoLimpio.includes('haduken') || textoLimpio.includes('hadoken')) {
        activarModoHadouken();
        return;
    }

    procesarConElena(texto);
}

async function procesarConElena(texto) {
    const modulo = document.getElementById('moduloSelect').value;
    const card = document.getElementById('responseCard');
    card.style.display = 'block';
    card.innerHTML = '⚙️ <i>La Dra. Elena Lara está procesando la solicitud...</i>';

    try {
        const response = await fetch('/analizar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ texto_o_transcripcion: texto, modulo: modulo })
        });
        const data = await response.json();
        
        let htmlResponse = `<strong>👩‍⚕️ Dra. Elena Lara (CEO) - Brunilda S.A.S.</strong><br><br>`;
        htmlResponse += `<pre style="white-space: pre-wrap; font-family: inherit; font-size:0.9em; color:#38bdf8;">${JSON.stringify(data, null, 2)}</pre>`;
        card.innerHTML = htmlResponse;
    } catch (e) {
        card.innerHTML = '❌ Error al comunicar con el motor de la Dra. Elena.';
    }
}

// EASTER EGGS
function activarModoHadouken() {
    alert("💥 ¡HADOUKEN! 🎮\nRedirigiendo a Swagger API Docs (/docs)...");
    window.location.href = '/docs';
}

const konamiCode = ['ArrowUp','ArrowUp','ArrowDown','ArrowDown','ArrowLeft','ArrowRight','ArrowLeft','ArrowRight','b','a'];
let konamiPosition = 0;

document.addEventListener('keydown', function(e) {
    if (e.key === konamiCode[konamiPosition]) {
        konamiPosition++;
        if (konamiPosition === konamiCode.length) {
            activarModoJuez();
            konamiPosition = 0;
        }
    } else {
        konamiPosition = 0;
    }
});

let clickCount = 0;
function secretClickCount() {
    clickCount++;
    if (clickCount >= 3) {
        activarModoJuez();
        clickCount = 0;
    }
}

function activarModoJuez() {
    alert("🎮 ¡EASTER EGG DESBLOQUEADO! 🎮\nRedirigiendo a Swagger API Docs (/docs)...");
    window.location.href = '/docs';
}

// MODAL LÓGICA
let planSeleccionado = '';
function abrirTerminos(plan) {
    planSeleccionado = plan;
    document.getElementById('checkAcepto').checked = false;
    document.getElementById('btnIrAPagar').disabled = true;
    document.getElementById('modalTerminos').style.display = 'flex';
}
function cerrarTerminos() { document.getElementById('modalTerminos').style.display = 'none'; }
function validarAceptacion() {
    const check = document.getElementById('checkAcepto');
    document.getElementById('btnIrAPagar').disabled = !check.checked;
}
function procederAlPago() {
    if (planSeleccionado) window.location.href = `/pagar/${planSeleccionado}`;
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
