# ---------------------------------------------------------
# LANDING PAGE OFICIAL CONECTADA A GOOGLE COLAB CORE
# ---------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def home():
    # Link directo al cerebro oficial en Google Colab
    URL_COLAB = "https://colab.research.google.com/drive/1YM9beGs02ggBU-aLHuAX3IszPgkL9_bG" 
    
    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Brunilda S.A.S. - Dra. Elena Lara v0.5</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }}
            .container {{ max-width: 850px; margin: 0 auto; background: #1e293b; padding: 30px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }}
            h1 {{ color: #38bdf8; text-align: center; font-size: 2em; margin-bottom: 5px; }}
            .subtitle {{ text-align: center; color: #94a3b8; font-size: 1.1em; margin-bottom: 25px; }}
            .terms-box {{ background: #334155; border-left: 5px solid #f59e0b; padding: 15px; border-radius: 6px; margin-bottom: 25px; font-size: 0.9em; line-height: 1.5; }}
            .download-btn {{ display: block; width: 100%; text-align: center; background: #22c55e; color: white; padding: 15px 0; font-size: 1.2em; font-weight: bold; border-radius: 8px; text-decoration: none; margin-bottom: 30px; transition: 0.3s; }}
            .download-btn:hover {{ background: #16a34a; }}
            .plans {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 15px; }}
            .plan-card {{ background: #0f172a; border: 1px solid #475569; border-radius: 8px; padding: 20px; text-align: center; display: flex; flex-direction: column; justify-content: space-between; }}
            .plan-price {{ font-size: 1.5em; color: #38bdf8; font-weight: bold; margin: 10px 0; }}
            .services-list {{ text-align: left; font-size: 0.85em; color: #cbd5e1; margin: 10px 0; padding-left: 18px; line-height: 1.4; }}
            .pay-btn {{ display: inline-block; background: #0284c7; color: white; padding: 8px 15px; border-radius: 5px; text-decoration: none; font-size: 0.9em; margin-top: 10px; font-weight: bold; }}
            .pay-btn:hover {{ background: #0369a1; }}
            .footer {{ text-align: center; margin-top: 30px; font-size: 0.8em; color: #64748b; }}
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

        <a href="{URL_COLAB}" target="_blank" class="download-btn">🧠 ACCEDER AL MOTOR CEREBRAL COLAB (v0.5)</a>

        <h2>Planes & Módulos Disponibles</h2>
        <div class="plans">
            <div class="plan-card">
                <h3>Elena Único</h3>
                <p style="font-size: 0.9em; color: #94a3b8;">1 Módulo a elección</p>
                <ul class="services-list">
                    <li>Elegí 1 de los 5 módulos de la Dra. Elena Lara.</li>
                </ul>
                <div class="plan-price">$6.000 ARS</div>
                <a href="https://elena-companion-api.onrender.com/crear-preferencia-pago?plan=UNICO" target="_blank" class="pay-btn">Suscribirme</a>
            </div>
            <div class="plan-card">
                <h3>Elena Dúo</h3>
                <p style="font-size: 0.9em; color: #94a3b8;">2 Módulos a elección</p>
                <ul class="services-list">
                    <li>Combiná 2 módulos (ej: Senior + Baby).</li>
                </ul>
                <div class="plan-price">$12.000 ARS</div>
                <a href="https://elena-companion-api.onrender.com/crear-preferencia-pago?plan=DUO" target="_btn" class="pay-btn">Suscribirme</a>
            </div>
            <div class="plan-card" style="border-color: #f59e0b;">
                <h3>Elena Premium Suite</h3>
                <p style="font-size: 0.9em; color: #f59e0b; font-weight: bold;">Acceso Total (5 Módulos)</p>
                <ul class="services-list">
                    <li>👵 <strong>Elena Senior:</strong> Adulto mayor y finanzas</li>
                    <li>👶 <strong>Elena Baby:</strong> Lactancia y pediatría</li>
                    <li>♿ <strong>Elena Care:</strong> Discapacidad y rutinas</li>
                    <li>🏥 <strong>Elena Recovery:</strong> Fármacos y rehabilitación</li>
                    <li>🧠 <strong>Elena Memory:</strong> Refuerzo cognitivo</li>
                </ul>
                <div class="plan-price">$63.000 ARS</div>
                <a href="https://elena-companion-api.onrender.com/crear-preferencia-pago?plan=SUITE" target="_blank" class="pay-btn">Suscribirme</a>
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
