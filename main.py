from flask import Flask, request, jsonify
import requests
import datetime
import os
import pandas as pd

app = Flask(__name__)

@app.route('/consulta', methods=['POST'])
def consultar_bmg_planilha():
    if 'file' not in request.files:
        return jsonify({'erro': 'Nenhum arquivo enviado'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'erro': 'Nome de arquivo inválido'}), 400

    try:
        df = pd.read_excel(file)
        resultados = []

        for index, row in df.iterrows():
            cpf = str(row['CPF']).strip()

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
                resultados.append({
                    'CPF': cpf,
                    'Status Code': response.status_code,
                    'Resposta': response.text
                })
            except Exception as e:
                resultados.append({
                    'CPF': cpf,
                    'Status Code': 'Erro',
                    'Resposta': str(e)
                })

        df_resultado = pd.DataFrame(resultados)
        df_resultado.to_excel('retorno_bmg.xlsx', index=False)
        return jsonify({'mensagem': 'Consulta finalizada com sucesso. Arquivo retorno_bmg.xlsx gerado.'})

    except Exception as e:
        return jsonify({'erro': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
