@app.route("/meuip")
def meu_ip():
    try:
        r = requests.get("https://api.ipify.org?format=json", timeout=10)
        return f"🧪 IP de saída do Render: {r.json()['ip']}"
    except Exception as e:
        return f"❌ Erro ao consultar IP: {e}"
