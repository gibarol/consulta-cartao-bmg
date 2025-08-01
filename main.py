from flask import Flask, request, jsonify, send_file
import requests, os, datetime
import pandas as pd
import re

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

    df = pd.read_excel(arquivo)
    resultados = []

    for _, row in df.iterrows():
        cpf = str(row['cpf'])
        resultado = consultar_bmg(cpf)
        resultados.append(resultado)

    df_saida = pd.DataFrame(resultados)
    caminho_saida = "/mnt/data/retorno_bmg_completo.xlsx"
    df_saida.to_excel(caminho_saida, index=False)
    return send_file(caminho_saida, as_attachment=True)

def extrair_limites(mensagem):
    saque = total = credito = None
    if isinstance(mensagem, str):
        saque_match = re.search(r"Limite disponivel para saque.*?:\s*([\d.,]+)", mensagem)
        total_match = re.search(r"Limite disponível de Total.*?:\s*([\d.,]+)", mensagem)
        credito_match = re.search(r"Limite de crédito.*?:\s*([\d.,]+)", mensagem)

        saque = float(saque_match.group(1).replace(",", ".")) if saque_match else None
        total = float(total_match.group(1).replace(",", ".")) if total_match else None
        credito = float(credito_match.group(1).replace(",", ".")) if credito_match else None

    return saque, total, credito

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
        conteudo = response.text

        # Extração dos dados SOAP via regex
        dados = {
            "cpf": cpf,
            "mensagem": re.search(r"<mensagemImpedimento.*?>(.*?)</mensagemImpedimento>", conteudo, re.DOTALL),
            "entidade": re.search(r"<entidade.*?>(.*?)</entidade>", conteudo),
            "matricula": re.search(r"<matricula.*?>(.*?)</matricula>", conteudo),
            "numeroAdesao": re.search(r"<numeroAdesao.*?>(.*?)</numeroAdesao>", conteudo),
            "numeroCartao": re.search(r"<numeroCartao.*?>(.*?)</numeroCartao>", conteudo),
            "modalidadeSaque": re.search(r"<modalidadeSaque.*?>(.*?)</modalidadeSaque>", conteudo),
            "numeroContaInterna": re.search(r"<numeroContaInterna.*?>(.*?)</numeroContaInterna>", conteudo),
            "liberado": re.search(r"<liberado.*?>(.*?)</liberado>", conteudo),
            "cpfImpedidoComissionar": re.search(r"<cpfImpedidoComissionar.*?>(.*?)</cpfImpedidoComissionar>", conteudo),
            "formasEnvio": ", ".join(re.findall(r"<descricao.*?>(.*?)</descricao>", conteudo))
        }

        dados = {k: (v.group(1).strip() if v else None) for k, v in dados.items()}
        saque, total, credito = extrair_limites(dados.get("mensagem"))
        dados["limiteSaque"] = saque
        dados["limiteTotal"] = total
        dados["limiteCredito"] = credito
        dados["status"] = "ok"
        return dados
    except Exception as e:
        return {"cpf": cpf, "status": "erro", "mensagem": str(e)}

if __name__ == "__main__":
    app.run(debug=True)
