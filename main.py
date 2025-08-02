import httpx
from flask import Flask, request, jsonify, send_file
import os
import tempfile
import pandas as pd
from openpyxl import Workbook
from xml.etree import ElementTree as ET
import re

app = Flask(__name__)

@app.route("/consulta", methods=["GET"])
def consulta_cpf():
    cpf = request.args.get("cpf")
    if not cpf:
        return jsonify({"erro": "CPF não informado"}), 400

    url = "https://ws1.bmgconsig.com.br/webservices/SaqueComplementar?wsdl"

    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "User-Agent": "Mozilla/5.0",
        "Accept": "*/*",
        "SOAPAction": ""
    }

    payload = f"""<?xml version="1.0" encoding="UTF-8"?>
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:web="http://webservice.econsig.bmg.com">
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
    </soapenv:Envelope>"""

    try:
        response = httpx.post(url, data=payload, headers=headers, timeout=20.0)
        if response.status_code != 200:
            return jsonify({
                "cpf": cpf,
                "status_code": response.status_code,
                "erro": f"Erro HTTP {response.status_code}",
                "resposta": response.text
            }), response.status_code

        root = ET.fromstring(response.text)
        texto = ET.tostring(root, encoding="unicode")

        # Extrair dados com regex
        info = {
            "cpf": cpf,
            "liberado": bool(re.search(r"<liberado[^>]*>(true|1)</liberado>", texto)),
            "motivo": extrair_texto(texto, "mensagemImpedimento"),
            "modalidade": extrair_texto(texto, "modalidadeSaque"),
            "numero_adesao": extrair_texto(texto, "numeroAdesao"),
            "numero_cartao": extrair_texto(texto, "numeroCartao"),
            "formas_envio": re.findall(r"<descricao[^>]*>(.*?)</descricao>", texto)
        }

        return jsonify(info)

    except Exception as e:
        return jsonify({"cpf": cpf, "erro": str(e)}), 500

def extrair_texto(xml, tag):
    match = re.search(fr"<{tag}[^>]*>(.*?)</{tag}>", xml)
    if match:
        return match.group(1)
    return ""

@app.route("/consulta-planilha", methods=["POST"])
def consulta_planilha():
    if "file" not in request.files:
        return jsonify({"erro": "Arquivo não enviado"}), 400

    file = request.files["file"]
    temp_dir = tempfile.mkdtemp()
    input_path = os.path.join(temp_dir, "entrada.xlsx")
    output_path = os.path.join(temp_dir, "resposta.xlsx")
    file.save(input_path)

    df = pd.read_excel(input_path)
    resultados = []

    for cpf in df["cpf"]:
        resultado = consultar_bmg_via_soap(str(cpf))
        resultados.append(resultado)

    df_saida = pd.DataFrame(resultados)
    df_saida.to_excel(output_path, index=False)

    return send_file(output_path, as_attachment=True, download_name="resposta_bmg.xlsx")

def consultar_bmg_via_soap(cpf):
    url = "https://ws1.bmgconsig.com.br/webservices/SaqueComplementar?wsdl"

    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "User-Agent": "Mozilla/5.0",
        "Accept": "*/*",
        "SOAPAction": ""
    }

    payload = f"""<?xml version="1.0" encoding="UTF-8"?>
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:web="http://webservice.econsig.bmg.com">
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
    </soapenv:Envelope>"""

    try:
        response = httpx.post(url, data=payload, headers=headers, timeout=20.0)
        if response.status_code != 200:
            return {
                "cpf": cpf,
                "erro": f"Erro HTTP {response.status_code}",
                "resposta": response.text,
                "status_code": response.status_code
            }

        root = ET.fromstring(response.text)
        texto = ET.tostring(root, encoding="unicode")

        return {
            "cpf": cpf,
            "liberado": bool(re.search(r"<liberado[^>]*>(true|1)</liberado>", texto)),
            "motivo": extrair_texto(texto, "mensagemImpedimento"),
            "modalidade": extrair_texto(texto, "modalidadeSaque"),
            "numero_adesao": extrair_texto(texto, "numeroAdesao"),
            "numero_cartao": extrair_texto(texto, "numeroCartao"),
            "formas_envio": ", ".join(re.findall(r"<descricao[^>]*>(.*?)</descricao>", texto))
        }

    except Exception as e:
        return {"cpf": cpf, "erro": str(e)}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
