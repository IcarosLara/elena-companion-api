@app.post("/crear-preferencia-pago")
def crear_pago_mercadopago(plan: str = "UNICO"):
    # Pegá tu clave APP_USR-... directo entre las comillas
    TOKEN_DIRECTO = "APP_USR-738297045866874-070402-5f178e96384dfbf05d797c448c7e97c6-3518229186" 
    
    precios = {
        "UNICO": {"titulo": "Brunilda S.A.S - Elena Unico", "precio": 6000},
        "DUO": {"titulo": "Brunilda S.A.S - Elena Duo", "precio": 12000},
        "SUITE": {"titulo": "Brunilda S.A.S - Elena Premium Suite", "precio": 63000}
    }
    plan_info = precios.get(plan.upper(), precios["UNICO"])
    
    url = "https://api.mercadopago.com/checkout/preferences"
    headers = {"Authorization": f"Bearer {TOKEN_DIRECTO}", "Content-Type": "application/json"}
    payload = {
        "items": [{"title": plan_info["titulo"], "quantity": 1, "unit_price": plan_info["precio"], "currency_id": "ARS"}],
        "notification_url": "https://elena-companion-api.onrender.com/webhook/mercadopago",
        "auto_return": "approved"
    }
    
    res = requests.post(url, headers=headers, json=payload)
    if res.status_code == 201:
        data = res.json()
        return {
            "status": "ok", 
            "plan": plan_info["titulo"], 
            "mercadopago_link_real": data.get("init_point"), 
            "mercadopago_link_prueba": data.get("sandbox_init_point")
        }
    else:
        raise HTTPException(status_code=500, detail=f"Error en Mercado Pago: {res.text}")
