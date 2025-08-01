from flask import Flask, request, Response
import requests

app = Flask(__name__)

@app.route('/consulta', methods=['GET'])
def consulta():
    cpf = request.args.get('cpf')

    if not cpf:
        return {"erro": "CPF não informado"}, 400

    soap_body = f"""
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:web="http://webservice.econsig.bmg.com">
      <soapenv:Header/>
      <soapenv:Body>
        <web:buscarCartoesDisponiveis>
          <param>
            <login>robo.56780</login>
            <senha>Miguel1@@@</senha>
            <codigoEntidade>1581</codigoEntidade>
            <cpf>{cpf}</cpf>
            <sequencialOrgao></sequencialOrgao>
          </param>
        </web:buscarCartoesDisponiveis>
      </soapenv:Body>
    </soapenv:Envelope>
    """

    headers = {
        'Content-Type': 'text/xml; charset=utf-8',
        'SOAPAction': ''
    }

    url = "https://ws1.bmgconsig.com.br/webservices/SaqueComplementar?wsdl"

    try:
        response = requests.post(url, data=soap_body.encode('utf-8'), headers=headers)

        if response.status_code == 200:
            return Response(response.content, mimetype='application/xml')
        else:
            return {
                "cpf": cpf,
                "status_code": response.status_code,
                "erro": f"Erro HTTP {response.status_code}",
                "resposta": response.text
            }, response.status_code

    except Exception as e:
        return {"cpf": cpf, "erro": str(e)}, 500
