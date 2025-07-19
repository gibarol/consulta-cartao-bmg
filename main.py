from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route("/")
def home():
    return "🟢 API BMG Online via Render – SOAP liberado"

@app.route("/consulta", methods=["POST"])
def consulta_cartao():
    try:
        cpf = request.json.get("cpf")

        if not cpf:
            return jsonify({"erro": "CPF não informado"}), 400

        login = "robo.56780"
        senha = "Sucesso1@@@"
        entidade = "1581"

        # XML SOAP para buscar cartões
        xml_cartao = f"""
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:web="http://webservice.econsig.bmg.com">
          <soapenv:Header/>
          <soapenv:Body>
            <web:buscarCartoesDisponiveis>
              <param>
                <login>{login}</login>
                <senha>{senha}</senha>
                <codigoEntidade>{entidade}</codigoEntidade>
                <cpf>{cpf}</cpf>
              </param>
            </web:buscarCartoesDisponiveis>
          </soapenv:Body>
        </soapenv:Envelope>
        """

        headers = {
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": ""
        }

        url = "https://ws1.bmgconsig.com.br/webservices/SaqueComplementar?wsdl"

        r1 = requests.post(url, data=xml_cartao.strip(), headers=headers)
        resposta = r1.text

        return jsonify({
            "cpf": cpf,
            "status_code": r1.status_code,
            "resposta": resposta
        })

    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
