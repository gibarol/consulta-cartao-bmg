from flask import Flask, request, Response
import requests

app = Flask(__name__)

@app.route('/consulta', methods=['GET'])
def consulta():
    cpf = request.args.get('cpf')
    
    if not cpf:
        return 'CPF não informado', 400

    url = "https://ws1.bmgconsig.com.br/webservices/SaqueComplementar?wsdl"
    headers = {'Content-Type': 'text/xml; charset=utf-8'}
    xml_body = f"""
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

    try:
        response = requests.post(url, data=xml_body.encode('utf-8'), headers=headers, timeout=30)
        return Response(response.content, content_type='text/xml')
    except Exception as e:
        return {'erro': str(e)}, 500
