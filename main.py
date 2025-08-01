from flask import Flask, request, send_file, jsonify
import pandas as pd
import requests
import xml.etree.ElementTree as ET
import iofrom flask import Flask, request, send_file, jsonify
import pandas as pd
import requests
import xml.etree.ElementTree as ET
import io
import re

app = Flask(__name__)

# Credenciais fixas
USUARIO = "robo.56780"
SENHA = "Miguel1@@@"
CODIGO_ENTIDADE = "1581"
URL = "https://webservice.econsig.bmg.com/cartao/consultaDisponibilidade"

@app.route("/")
def home():
    return "API BMG ConsultaCartoes Online"

def gerar_xml(cpf):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:web="http://webservice.econsig.bmg.com">
  <soapenv:Header/>
  <soapenv:Body>
    <web:buscarCartoesDisponiveis>
      <param>
        <login>{USUARIO}</login>
        <senha>{SENHA}</senha>
        <codigoEntidade>{CODIGO_ENTIDADE}</codigoEntidade>
        <cpf>{cpf}</cpf>
        <sequencialOrgao></sequencialOrgao>
      </param>
    </web:buscarCartoesDisponiveis>
  </soapenv:Body>
</soapenv:Envelope>"""

def consultar_bmg(cpf):
    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": ""
    }
    xml = gerar_xml(cpf)
    response = requests.post(URL, data=xml.encode("utf-8"), headers=headers, timeout=15)
    return response.text

def extrair_valores(xml_str):
    try:
        ns = {
            'soapenv': 'http://schemas.xmlsoap.org/soap/envelope/',
            'ns1': 'http://webservice.econsig.bmg.com',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'soapenc': 'http://schemas.xmlsoap.org/soap/encoding/'
        }
        root = ET.fromstring(xml_str)
        cartao = root.find(".//cartoesRetorno")
        if cartao is None:
            return {}

        def get(tag):
            el = cartao.find(f'{tag}')
            return el.text.strip() if el is not None and el.text else ''

        formas_envio = root.findall(".//formasEnvio/descricao")
        formas = ', '.join([f.text for f in formas_envio]) if formas_envio else ''

        msg = get('mensagemImpedimento') or ''
        saque = re.search(r'Limite disponivel para saque.*?: ([\d,.]+)', msg)
        total = re.search(r'Limite disponível de Total.*?: ([\d,.]+)', msg)
        credito = re.search(r'Limite de crédito.*?: ([\d,.]+)', msg)

        return {
            'cpfImpedidoComissionar': get('cpfImpedidoComissionar'),
            'entidade': get('entidade'),
            'liberado': get('liberado'),
            'matricula': get('matricula'),
            'mensagemImpedimento': msg,
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
        return {}

@app.route("/consulta-planilha", methods=["POST"])
def consulta_planilha():
    try:
        if "file" not in request.files:
            return jsonify({"erro": "Arquivo não enviado"}), 400

        file = request.files["file"]
        if not file.filename.endswith((".xlsx", ".xls")):
            return jsonify({"erro": "Tipo de arquivo inválido"}), 400

        df = pd.read_excel(file)
        if "cpf" not in df.columns:
            return jsonify({"erro": "Coluna 'cpf' não encontrada"}), 400

        resultados = []

        for cpf in df["cpf"].astype(str):
            try:
                xml = consultar_bmg(cpf)
                dados = extrair_valores(xml)
                resultados.append({
                    "cpf": cpf,
                    "status": "ok",
                    "mensagem": f"Consulta realizada com sucesso para CPF {cpf}",
                    **dados
                })
            except Exception:
                resultados.append({
                    "cpf": cpf,
                    "status": "erro",
                    "mensagem": f"Erro ao consultar CPF {cpf}"
                })

        df_saida = pd.DataFrame(resultados)
        output = io.BytesIO()
        df_saida.to_excel(output, index=False)
        output.seek(0)

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            download_name="retorno_bmg.xlsx",
            as_attachment=True
        )

    except Exception as e:
        return jsonify({"erro": f"Erro interno: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
import re
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

USUARIO = "robo.56780"
SENHA = "Miguel1@@@"
URL_TOKEN = "https://ws1.bmgconsig.com.br/auth"
URL_CONSULTA = "https://ws1.bmgconsig.com.br/cartao/consultaDisponibilidade"

@app.route('/')
def home():
    return 'API BMG Processor Online!'

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
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'soapenc': 'http://schemas.xmlsoap.org/soap/encoding/'
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

        msg = get('mensagemImpedimento') or ''
        saque = re.search(r'Limite disponivel para saque.*?: ([\d,.]+)', msg)
        total = re.search(r'Limite disponível de Total.*?: ([\d,.]+)', msg)
        credito = re.search(r'Limite de crédito.*?: ([\d,.]+)', msg)

        return {
            'cpfImpedidoComissionar': get('cpfImpedidoComissionar'),
            'entidade': get('entidade'),
            'liberado': get('liberado'),
            'matricula': get('matricula'),
            'mensagemImpedimento': msg,
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
        return {}

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
        token = obter_token()
        if not token:
            return jsonify({'erro': "Falha ao obter token"}), 500

        resultados = []
        for cpf in cpfs:
            try:
                xml = consultar_bmg(cpf, token)
                dados = extrair_valores(xml)
                resultados.append({
                    'cpf': cpf,
                    'status': 'ok',
                    'mensagem': f"Retorno simulado do BMG para CPF {cpf}",
                    **dados
                })
            except Exception:
                resultados.append({
                    'cpf': cpf,
                    'status': 'erro',
                    'mensagem': f"Erro ao consultar CPF {cpf}"
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
        logging.exception("Erro ao processar a planilha")
        return jsonify({'erro': str(e)}), 500

if __name__ == '__main__':
    app.run()
