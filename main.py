from flask import Flask, request, send_file, jsonify
import httpx
import pandas as pd
import tempfile
import os
from xml.etree import ElementTree as ET

app = Flask(__name__)

@app.route("/consulta-planilha", methods=["POST"])
def consulta_planilha():
    if "file" not in request.files:
        return jsonify({"erro": "Arquivo não enviado"}), 400

    file = request.files["file"]
    df = pd.read_excel(file)

    resultados = []

    for cpf in df["cpf"].astype(str):
        resultado = consulta_bmg(cpf)
        resultados.append(resultado)

    df_resultado = pd.DataFrame(resultados)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        df_resultado.to_excel(tmp.name, index=False)
        tmp_path = tmp.name

    return send_file(tmp_path, as_attachment=True, download_name="resposta_bmg.xlsx")

def consulta_bmg(cpf):
    url = "https://ws1.bmgconsig.com.br/webservices/SaqueComplementar?wsdl"

    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
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
        response = httpx.post(url, data=payload, headers=headers, timeout=25.0)
        if response.status_code != 200:
            return {"cpf": cpf, "erro": f"Erro HTTP {response.status_code}", "resposta": response.text}

        root = ET.fromstring(response.text)

        ns = {"soapenv": "http://schemas.xmlsoap.org/soap/envelope/"}
        body = root.find("soapenv:Body", ns)

        dados = {
            "cpf": cpf,
            "liberado": "",
            "motivo": "",
            "modalidade": "",
            "numero_adesao": "",
            "numero_cartao": "",
            "formas_envio": []
        }

        if body is not None and "Fault" not in response.text:
            for tag in ["liberado", "mensagemImpedimento", "modalidadeSaque", "numeroAdesao", "numeroCartao"]:
                el = root.find(f".//{tag}")
                if el is not None:
                    dados[tag.replace("mensagemImpedimento", "motivo")
                          .replace("modalidadeSaque", "modalidade")
                          .replace("numeroAdesao", "numero_adesao")
                          .replace("numeroCartao", "numero_cartao")] = el.text or ""

            formas = root.findall(".//formasEnvio/descricao")
            if formas:
                dados["formas_envio"] = [f.text for f in formas]

        return dados

    except Exception as e:
        return {"cpf": cpf, "erro": str(e), "resposta": ""}

if __name__ == "__main__":
    app.run(debug=True)
