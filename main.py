
from flask import Flask, request, jsonify
import requests, os, pandas as pd

app = Flask(__name__)

@app.route("/")
def home():
    return "API BMG Processor Online!"

@app.route("/consulta-planilha", methods=["POST"])
def processar_planilha():
    if 'file' not in request.files:
        return jsonify({"erro": "Arquivo não enviado"}), 400

    arquivo = request.files['file']
    if not arquivo.filename.endswith('.xlsx'):
        return jsonify({"erro": "Formato inválido. Envie um .xlsx"}), 400

    try:
        df = pd.read_excel(arquivo)
    except Exception as e:
        return jsonify({"erro": f"Erro ao ler planilha: {str(e)}"}), 500

    colunas_possiveis = ['cpf', 'CPF', 'Cpf', 'cpf_cliente', 'cpf_cliente_']
    coluna_cpf = next((col for col in df.columns if col.strip() in colunas_possiveis), None)
    if not coluna_cpf:
        return jsonify({"erro": "Coluna de CPF não encontrada"}), 400

    resultados = []

    for _, row in df.iterrows():
        cpf = str(row.get(coluna_cpf)).strip()
        if not cpf or cpf.lower() == 'nan':
            continue

        resultado = consultar_bmg(cpf)
        resultados.append({"cpf": cpf, **resultado})

    df_saida = pd.DataFrame(resultados)
    caminho_saida = "/mnt/data/retorno_bmg.xlsx"
    df_saida.to_excel(caminho_saida, index=False)
    return jsonify({"mensagem": "Consulta finalizada", "arquivo": caminho_saida})

def consultar_bmg(cpf):
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

    headers = {'Content-Type': 'text/xml;charset=UTF-8', 'SOAPAction': ''}
    url = 'https://ws1.bmgconsig.com.br/webservices/SaqueComplementar'

    try:
        response = requests.post(url, data=xml_envio.encode('utf-8'), headers=headers)
        return {
            "status": response.status_code,
            "resposta": response.text.strip()
        }
    except Exception as e:
        return {"erro": str(e)}

if __name__ == "__main__":
    app.run(debug=True)
