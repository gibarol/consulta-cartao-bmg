from flask import Flask, request
import requests
from zeep import Client

app = Flask(__name__)

# Endpoint de status
@app.route("/")
def status():
    return "🟢 API BMG Online via Render – SOAP liberado"

# Novo endpoint para verificar o IP de saída
@app.route("/meuip")
def meu_ip():
    try:
        r = requests.get("https://httpbin.org/ip", timeout=10)
        return f"🧪 IP de saída usado pelo Render: {r.text}"
    except Exception as e:
        return f"❌ Erro ao buscar IP: {e}"

# Endpoint de teste da consulta BMG com CPF
@app.route("/consulta")
def consulta():
    cpf = request.args.get("cpf", "99925125634")

    wsdl_url = "https://ws1.bmgconsig.com.br/webservices/SaqueComplementar?wsdl"
    login = "robo.56780"
    senha = "Sucesso1@@@"
    codigo_entidade = "1581"  # INSS

    try:
        client = Client(wsdl=wsdl_url)
        response = client.service.buscarCartoesDisponiveis({
            'login': login,
            'senha': senha,
            'codigoEntidade': codigo_entidade,
            'cpf': cpf,
            'sequencialOrgao': ''
        })
        return f"✅ Resultado da consulta: {response}"
    except Exception as e:
        return f"❌ Erro na consulta: {e}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
