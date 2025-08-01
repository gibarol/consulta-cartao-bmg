from flask import Flask, request, jsonify, send_file
import requests
import datetime
import pandas as pd
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = '/tmp/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Configuração de autenticação
LOGIN = 'robo.56780'
SENHA = 'Miguel1@@@'
CODIGO_ENTIDADE = '1581'
URL_BMG = 'https://ws1.bmgconsig.com.br/webservices/SaqueComplementar'

@app.route('/')
def status():
    return 'Servidor BMG online!'

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files.get('file')
    if not file:
        return jsonify({'erro': 'Nenhum arquivo enviado.'}), 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    df = pd.read_excel(file_path)
    resultados = []

    for _, row in df.iterrows():
        cpf = str(row.get('cpf')).strip()
        if not cpf or cpf == 'nan':
            continue

        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:web="http://webservice.econsig.bmg.com">
  <soapenv:Header/>
  <soapenv:Body>
    <web:buscarCartoesDisponiveis>
      <param>
        <login>{LOGIN}</login>
        <senha>{SENHA}</senha>
        <codigoEntidade>{CODIGO_ENTIDADE}</codigoEntidade>
        <cpf>{cpf}</cpf>
        <sequencialOrgao></sequencialOrgao>
      </param>
    </web:buscarCartoesDisponiveis>
  </soapenv:Body>
</soapenv:Envelope>"""

        try:
            headers = {'Content-Type': 'text/xml;charset=UTF-8', 'SOAPAction': ''}
            response = requests.post(URL_BMG, data=xml.encode('utf-8'), headers=headers, timeout=30)
            status = response.status_code
            conteudo = response.text

        except Exception as e:
            status = 'erro'
            conteudo = str(e)

        resultados.append({
            'cpf': cpf,
            'status_code': status,
            'resposta': conteudo
        })

    retorno_path = os.path.join(UPLOAD_FOLDER, f'resposta_bmg_{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.xlsx')
    df_resultado = pd.DataFrame(resultados)
    df_resultado.to_excel(retorno_path, index=False)

    return jsonify({'mensagem': 'Processado com sucesso.', 'download': f'/download/{os.path.basename(retorno_path)}'})

@app.route('/download/<nome_arquivo>')
def download(nome_arquivo):
    caminho = os.path.join(UPLOAD_FOLDER, nome_arquivo)
    if not os.path.exists(caminho):
        return jsonify({'erro': 'Arquivo não encontrado'}), 404
    return send_file(caminho, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
