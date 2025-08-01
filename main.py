from flask import Flask, request, Response
import requests

app = Flask(__name__)

@app.route('/')
def home():
    return 'API Consulta CPF BMG Online!'

@app.route('/consulta', methods=['GET'])
def consulta_cpf():
    cpf = request.args.get('cpf')
    if not cpf:
        return Response("Erro: CPF não informado", status=400)

    url = "https://ws1.bmgconsig.com.br/webservices/SaqueComplementar"
    headers = {
        "Content-Type": "text/xml;charset=UTF-8",
        "SOAPAction": "buscarCartoesDisponiveis"
    }

    body = f"""
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
        response = requests.post(url, data=body.strip().encode('utf-8'), headers=headers, timeout=30)
        return Response(response.text, status=response.status_code, mimetype='text/xml')
    except Exception as e:
        return Response(f"Erro interno: {str(e)}", status=500)

if __name__ == '__main__':
    app.run()
