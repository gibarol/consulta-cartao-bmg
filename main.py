
from flask import Flask, request, send_file, jsonify
import pandas as pd
import os
import requests
import xml.etree.ElementTree as ET
import logging
from datetime import datetime

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route('/')
def home():
    return 'API BMG SOAP Online com Planilha!'

@app.route('/consulta-planilha', methods=['POST'])
def consulta_planilha():
    try:
        if 'file' not in request.files:
            return jsonify({'erro': "Arquivo não enviado (campo 'file' obrigatório)"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'erro': "Nome do arquivo vazio"}), 400

        df = pd.read_excel(file)
        if 'cpf' not in df.columns:
            return jsonify({'erro': "A planilha deve conter uma coluna chamada 'cpf'"}), 400

        cpfs = df['cpf'].astype(str).tolist()
        resultados = []

        for cpf in cpfs:
            try:
                dados = consultar_bmg(cpf)
                resultados.append(dados)
            except Exception as e:
                resultados.append({
                    'cpf': cpf,
                    'erro': str(e)
                })

        df_saida = pd.DataFrame(resultados)
        nome_saida = f"/tmp/retorno_bmg_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
        df_saida.to_excel(nome_saida, index=False)

        return send_file(
            nome_saida,
            as_attachment=True,
            download_name="retorno_bmg.xlsx",
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        logging.exception("Erro ao processar planilha")
        return jsonify({'erro': str(e)}), 500


def consultar_bmg(cpf):
    url = "https://ws1.bmgconsig.com.br/webservices/SaqueComplementar"
    headers = {
        "Content-Type": "text/xml;charset=UTF-8",
        "SOAPAction": "buscarCartoesDisponiveis"
    }

    body = f"""
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                      xmlns:tem="http://tempuri.org/">
       <soapenv:Header/>
       <soapenv:Body>
          <tem:buscarCartoesDisponiveis>
             <tem:cpf>{cpf}</tem:cpf>
             <tem:login>robo.56780</tem:login>
             <tem:senha>Miguel1@@@</tem:senha>
             <tem:codigoEntidade>1581</tem:codigoEntidade>
          </tem:buscarCartoesDisponiveis>
       </soapenv:Body>
    </soapenv:Envelope>
    """.strip()

    response = requests.post(url, data=body.encode('utf-8'), headers=headers, timeout=30)
    if response.status_code != 200:
        raise Exception(f"Erro HTTP {response.status_code}")

    root = ET.fromstring(response.content)
    namespaces = {'soap': 'http://schemas.xmlsoap.org/soap/envelope/'}
    body = root.find('soap:Body', namespaces)
    if body is None:
        raise Exception("Resposta SOAP inválida")

    dados = {
        'cpf': cpf,
        'status': 'ok',
        'mensagem': f"Consulta realizada com sucesso",
        'limiteSaque': extrair_valor_tag(response.text, 'limiteDisponivelSaque'),
        'limiteTotal': extrair_valor_tag(response.text, 'limiteDisponivelTotal'),
        'limiteCredito': extrair_valor_tag(response.text, 'limiteCredito')
    }

    return dados


def extrair_valor_tag(xml, tag):
    try:
        start = xml.find(f"<{tag}>") + len(tag) + 2
        end = xml.find(f"</{tag}>")
        return xml[start:end].strip()
    except:
        return ""

if __name__ == '__main__':
    app.run()
