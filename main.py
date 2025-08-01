from flask import Flask, request, jsonify
import requests
import datetime

app = Flask(__name__)

@app.route('/consulta', methods=['GET'])
def consultar_bmg():
    cpf = request.args.get('cpf', '99925125634')  # valor padrão para teste

    login = 'robo.56780'
    senha = 'Miguel1@@@'
    codigo_entidade = '1581'

    xml_envio = f"""<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:web="http://webservice.econsig.bmg.com">
  <soapenv:Header/>
  <soapenv:Body>
    <web:buscarCartoesDisponiveis>
      <param>
        <login>{login}</login>
        <senha>{senha}</senha>
        <codigoEntidade>{codigo_entidade}</codigoEntidade>
        <cpf>{cpf}</cpf>
        <sequencialOrgao></sequencialOrgao>
      </param>
    </web:buscarCartoesDisponiveis>
  </soapenv:Body>
</soapenv:Envelope>"""

    headers = {
        'Content-Type': 'text/xml;charset=UTF-8',
        'SOAPAction': ''
    }

    url = 'https://ws1.bmgconsig.com.br/webservices/SaqueComplementar'

    try:
        response = requests.post(url, data=xml_envio.encode('utf-8'), headers=headers)

        # Criar log detalhado sempre, mesmo com erro
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_text = f"TIMESTAMP: {timestamp}\n\nCPF: {cpf}\n\nXML ENVIADO:\n{xml_envio}\n\nSTATUS CODE: {response.status_code}\n\nRESPOSTA RECEBIDA:\n{response.text}"

        with open("log_bmg.txt", "w", encoding="utf-8") as f:
            f.write(log_text)

        return response.text, response.status_code

    except requests.exceptions.RequestException as e:
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        error_message = f"TIMESTAMP: {timestamp}\n\nErro na requisição: {str(e)}\n\nXML Enviado:\n{xml_envio}"
        with open("log_bmg.txt", "w", encoding="utf-8") as f:
            f.write(error_message)
        return jsonify({'erro': 'Erro na requisição', 'detalhe': str(e)}), 500

if __name__ == '__main__':
    app.run()
