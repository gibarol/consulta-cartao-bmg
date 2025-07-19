from flask import Flask, request, jsonify
from zeep import Client
from zeep.transports import Transport
import requests

app = Flask(__name__)

# Dados fixos
LOGIN = "robo.56780"
SENHA = "Sucesso1@@@"
COD_ENTIDADE = "1581"  # INSS
WSDL = "https://ws1.bmgconsig.com.br/webservices/SaqueComplementar?wsdl"

# Transport SOAP
session = requests.Session()
transport = Transport(session=session)
client = Client(wsdl=WSDL, transport=transport)

@app.route("/")
def home():
    return "🟢 API SOAP BMG ativa e rodando via IP fixo Render"

@app.route("/consulta", methods=["POST"])
def consulta():
    cpf = request.json.get("cpf")
    if not cpf:
        return jsonify({"erro": "CPF não informado"}), 400

    try:
        result = client.service.buscarCartoesDisponiveis({
            "login": LOGIN,
            "senha": SENHA,
            "codigoEntidade": COD_ENTIDADE,
            "cpf": cpf,
            "sequencialOrgao": ""
        })
        return jsonify({"resultado": str(result)})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
