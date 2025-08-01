from flask import Flask, request, send_file, jsonify
import pandas as pd
import requests
import xml.etree.ElementTree as ET
import io
import re
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Credenciais da API BMG
USUARIO = "robo.56780"
SENHA = "Miguel1@@@"
URL_TOKEN = "https://webservice.econsig.bmg.com/auth"
URL_CONSULTA = "https://webservice.econsig.bmg.com/cartao/consultaDisponibilidade"

def obter_token():
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {'usuario': USUARIO, 'senha': SENHA}
    response = requests.post(URL_TOKEN, headers=headers, data=data)
    if response.status_code == 200:
        return response.text.strip()
    return None

def consultar_bmg(cpf, token):
    headers = {'Authorization': f'Bearer {token}'}
    data = {'cpf': cpf}
    response = requests.post(URL_CONSULTA, headers=headers, data=data)
    return response.text

def extrair_valores(xml_str):
    try:
        ns = {
            'soapenv': 'http://schemas.xmlsoap.org/soap/envelope/',
            'ns1': 'http://webservice.econsig.bmg.com',
        }
        root = ET.fromstring(xml_str)
        cartao = root.find(".//ns1:cartoesRetorno", ns)
        if cartao is None:
            return {}

        def get(tag):
            el = cartao.find(f'ns1:{tag}', ns)
            return el.text if el is not None else ''

        formas_envio = root.findall(".//ns1:formasEnvio/ns1:descricao", ns)
        formas = ', '.join([f.text for f in formas_envio]) if formas_envio else ''

        msg = get('mensagemImpedimento')
        saque = re.search(r'Limite disponivel para saque.*?: ([\d,.]+)', msg or '')
        total = re.search(r'Limite disponível de Total.*?: ([\d,.]+)', msg or '')
        credito = re.search(r'Limite de crédito.*?: ([\d,.]+)', msg or '')

        return {
            'cpfImpedidoComissionar': get('cpfImpedidoComissionar'),
            'entidade': get('entidade'),
            'liberado': get('liberado'),
            'matricula': get('matricula'),
            'mensagemImpedimento': msg or '',
            'modalidadeSaque': get('modalidadeSaque'),
            'numeroAdesao': get('numeroAdesao'),
            'numeroCartao': get('numeroCartao'),
            'numeroContaInterna': get('numeroContaInterna'),
            'formasEnvio': formas,
            'limiteSaque': saque.group(1) if saque else '',
            'limiteTotal': total.group(1) if total else '',
            'limiteCredito': credito.group(1) if credito else ''
        }
    except Exception as e:
        logging.error(f"Erro ao extrair XML: {e}")
        return {}

@app.route('/')
def home():
    return 'API BMG Processor Online!'

@app.route('/consulta-planilha', methods=['POST'])
def consulta_planilha():
    try:
        if 'file' not in request.files:
            return jsonify({'erro': "Arquivo não enviado (campo 'file' obrigatório)"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'erro': "Nome do arquivo vazio"}), 400

        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({'erro': "Tipo de arquivo inválido. Envie um arquivo .xlsx ou .xls"}), 400

        df = pd.read_excel(file)
        if 'cpf' not in df.columns:
            return jsonify({'erro': "A planilha deve conter uma coluna chamada 'cpf'"}), 400

        token = obter_token()
        if not token:
            return jsonify({'erro': "Falha ao obter token do BMG"}), 500

        resultados = []
        for cpf in df['cpf'].astype(str):
            try:
                xml = consultar_bmg(cpf, token)
                dados = extrair_valores(xml)
                resultados.append({
                    'cpf': cpf,
                    'status': 'ok',
                    'mensagem': f"Retorno do BMG para CPF {cpf}",
                    **dados
                })
            except Exception as e:
                resultados.append({
                    'cpf': cpf,
                    'status': 'erro',
                    'mensagem': f"Erro ao consultar CPF {cpf}: {str(e)}"
                })

        df_saida = pd.DataFrame(resultados)
        caminho_saida = "/tmp/retorno_bmg.xlsx"
        df_saida.to_excel(caminho_saida, index=False)

        return send_file(
            caminho_saida,
            as_attachment=True,
            download_name="retorno_bmg.xlsx",
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        logging.exception("Erro geral na consulta da planilha")
        return jsonify({'erro': f"Erro interno: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
