
from flask import Flask, request, jsonify, send_file, render_template_string
import requests
import datetime
import pandas as pd
import os

app = Flask(__name__)

UPLOAD_FOLDER = '/mnt/data/uploads'
RESULT_FILE = '/mnt/data/retorno_bmg.xlsx'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

HTML_FORM = '''
<!doctype html>
<title>Consulta Cartão BMG</title>
<h2>Enviar planilha com CPF</h2>
<form method=post enctype=multipart/form-data action="/consulta">
  <input type=file name=file>
  <input type=submit value=Enviar>
</form>
{% if download %}
  <a href="/download">Baixar resultado</a>
{% endif %}
'''

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_FORM, download=False)

@app.route("/consulta", methods=["POST"])
def consulta():
    file = request.files.get("file")
    if not file:
        return "Nenhum arquivo enviado", 400

    file_path = os.path.join(UPLOAD_FOLDER, "entrada.xlsx")
    file.save(file_path)

    df = pd.read_excel(file_path)
    resultados = []

    login = 'robo.56780'
    senha = 'Miguel1@@@'
    codigo_entidade = '1581'
    url = 'https://ws1.bmgconsig.com.br/webservices/SaqueComplementar'

    headers = {
        'Content-Type': 'text/xml;charset=UTF-8',
        'SOAPAction': ''
    }

    for cpf in df['CPF']:
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

        try:
            response = requests.post(url, data=xml_envio.encode('utf-8'), headers=headers)
            resultado = {
                "CPF": cpf,
                "Status": response.status_code,
                "Resposta": response.text
            }
        except Exception as e:
            resultado = {
                "CPF": cpf,
                "Status": "Erro",
                "Resposta": str(e)
            }

        resultados.append(resultado)

    df_resultado = pd.DataFrame(resultados)
    df_resultado.to_excel(RESULT_FILE, index=False)

    return render_template_string(HTML_FORM, download=True)

@app.route("/download", methods=["GET"])
def download():
    return send_file(RESULT_FILE, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
