from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Configurações fixas do BMG
WSDL_URL = "https://ws1.bmgconsig.com.br/webservices/SaqueComplementar?wsdl"
LOGIN = "robo.56780"
SENHA = "Miguel1@@@"
ENTIDADE = "1581"

def montar_soap_request(cpf):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:web="http://webservice.econsig.bmg.com">
  <soapenv:Header/>
  <soapenv:Body>
    <web:buscarCartoesDisponiveis>
      <param>
        <login>{LOGIN}</login>
        <senha>{SENHA}</senha>
        <codigoEntidade>{ENTIDADE}</codigoEntidade>
        <cpf>{cpf}</cpf>
        <sequencialOrgao></sequencialOrgao>
      </param>
    </web:buscarCartoesDisponiveis>
  </soapenv:Body>
</soapenv:Envelope>"""

@app.route("/consulta", methods=["GET"])
def consulta_cpf():
    cpf = request.args.get("cpf")
    if not cpf:
        return jsonify({"erro": "CPF não informado"}), 400

    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": ""
    }

    soap_body = montar_soap_request(cpf)

    try:
        response = requests.post(WSDL_URL, data=soap_body, headers=headers, timeout=30)

        if response.status_code == 200:
            return jsonify({
                "cpf": cpf,
                "status_code": response.status_code,
                "resposta": response.text
            })
        else:
            return jsonify({
                "cpf": cpf,
                "status_code": response.status_code,
                "erro": f"Erro HTTP {response.status_code}",
                "resposta": response.text
            })

    except Exception as e:
        return jsonify({
            "cpf": cpf,
            "erro": str(e)
        }), 500

if __name__ == "__main__":
    app.run(debug=True)
