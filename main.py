
from flask import Flask, request
import requests
from zeep import Client
from zeep.transports import Transport

app = Flask(__name__)

@app.route("/")
def index():
    return "🟢 API BMG Online via Render – SOAP liberado"

@app.route("/meuip")
def meu_ip():
    ip_response = requests.get("https://httpbin.org/ip")
    return f"🧪 IP de saída usado pelo Render: {ip_response.text}"

@app.route("/consulta")
def consulta():
    cpf = request.args.get("cpf", "")
    if not cpf:
        return "❌ CPF não informado", 400

    try:
        # Captura o IP atual usado
        ip_response = requests.get("https://httpbin.org/ip")
        ip_info = ip_response.json()

        # URL do WSDL
        wsdl_url = "https://ws1.bmgconsig.com.br/webservices/SaqueComplementar?wsdl"
        transport = Transport(timeout=10)
        client = Client(wsdl=wsdl_url, transport=transport)

        # Parâmetros de autenticação (substituir se necessário)
        parametros = {
            "login": "97781",
            "senha": "kvdfyeau6nvzjk1bkhx3",
            "loginConsig": "97781",
            "codigoEntidade": "4277",
            "cpf": cpf,
            "senhaConsig": "kvdfyeau6nvzjk1bkhx3",
            "sequencialOrgao": 1
        }

        resposta = client.service.buscarCartoesDisponiveis(parametros)

        return (
            f"<p>✅ Consulta realizada com sucesso!</p>"
            f"<p>🔎 IP de saída: {ip_info['origin']}</p>"
            f"<p>📄 Resposta bruta da API BMG:</p>"
            f"<pre>{resposta}</pre>"
        )
    except Exception as e:
        return (
            f"<p>❌ Erro na consulta:</p><pre>{str(e)}</pre>"
            f"<p>🔎 IP usado: {ip_info.get('origin', 'Não identificado')}</p>"
        ), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
