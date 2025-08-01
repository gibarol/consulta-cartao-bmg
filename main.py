from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route('/consulta', methods=['GET'])
def consulta_bmg():
    cpf = request.args.get('cpf')

    if not cpf:
        return jsonify({"erro": "CPF não informado"}), 400

    url = "https://ws1.bmgconsig.com.br/webservices/SaqueComplementar"

    headers = {
        "Content-Type": "text/xml;charset=UTF-8",
        "SOAPAction": "buscarCartoesDisponiveis"
    }

    xml_body = f"""
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                      xmlns:tem="http://tempuri.org/">
       <soapenv:Header/>
       <soapenv:Body>
          <tem:buscarCartoesDisponiveis>
             <tem:cpf>{cpf}</tem:cpf>
             <tem:login>robo.56780</tem:login>
             <tem:senha>Miguel1@@@</tem:senha>
             <tem:codigoEntidade>56780</tem:codigoEntidade>
          </tem:buscarCartoesDisponiveis>
       </soapenv:Body>
    </soapenv:Envelope>
    """

    try:
        response = requests.post(url, data=xml_body.encode('utf-8'), headers=headers, timeout=30)
        return response.text, response.status_code, {'Content-Type': 'text/xml'}
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == '__main__':
    app.run()
