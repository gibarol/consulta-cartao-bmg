
from flask import Flask, request, send_file, jsonify
import pandas as pd
import requests
import xml.etree.ElementTree as ET
import io

app = Flask(__name__)

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
            xml = f"""
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:web="http://webservice.econsig.bmg.com">
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
                "Content-Type": "text/xml;charset=UTF-8",
                "SOAPAction": ""
            }

            try:
                response = requests.post(
                    url="https://ws1.bmgconsig.com.br/webservices/SaqueComplementar",
                    data=xml.encode('utf-8'),
                    headers=headers,
                    timeout=30
                )

                if response.status_code != 200:
                    resultados.append({'cpf': cpf, 'erro': f'Erro HTTP {response.status_code}'})
                    continue

                root = ET.fromstring(response.content)
                ns = {'ns1': 'http://webservice.econsig.bmg.com'}
                cartao = root.find(".//ns1:cartoesRetorno", ns)

                def get_text(tag):
                    el = cartao.find(f"ns1:{tag}", ns) if cartao is not None else None
                    return el.text.strip() if el is not None else ''

                msg = get_text('mensagemImpedimento')
                import re
                saque = re.search(r'saque.*?: ([\d.,]+)', msg)
                total = re.search(r'Total.*?: ([\d.,]+)', msg)
                credito = re.search(r'crédito.*?: ([\d.,]+)', msg)

                formas_envio = root.findall(".//ns1:formasEnvio/ns1:descricao", ns)
                formas = ', '.join([f.text for f in formas_envio]) if formas_envio else ''

                resultados.append({
                    'cpf': cpf,
                    'liberado': get_text('liberado'),
                    'mensagemImpedimento': msg,
                    'limiteSaque': saque.group(1) if saque else '',
                    'limiteTotal': total.group(1) if total else '',
                    'limiteCredito': credito.group(1) if credito else '',
                    'formasEnvio': formas
                })

            except Exception as e:
                resultados.append({'cpf': cpf, 'erro': str(e)})

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
        return jsonify({'erro': str(e)}), 500

@app.route('/')
def home():
    return 'API Consulta BMG Online'

if __name__ == '__main__':
    app.run()
