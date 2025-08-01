
from flask import Flask, request, jsonify, send_file
import requests
import pandas as pd
import os
from io import BytesIO

app = Flask(__name__)

@app.route("/consulta-planilha", methods=["POST"])
def consulta_planilha():
    if "file" not in request.files:
        return jsonify({"erro": "Nenhum arquivo enviado"}), 400

    file = request.files["file"]
    try:
        df = pd.read_excel(file)
    except Exception as e:
        return jsonify({"erro": f"Erro ao ler a planilha: {str(e)}"}), 400

    resultados = []

    for index, row in df.iterrows():
        cpf = str(row.get("cpf", "")).strip()
        if not cpf:
            resultados.append({"cpf": "", "erro": "CPF vazio"})
            continue

        url = "https://ws1.bmgconsig.com.br/webservices/SaqueComplementar"

        headers = {
            "Content-Type": "text/xml;charset=UTF-8",
            "SOAPAction": "buscarCartoesDisponiveis"
        }

        xml_body = f"""
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
        """.strip()

        try:
            response = requests.post(url, data=xml_body.encode("utf-8"), headers=headers, timeout=60)
            resultados.append({
                "cpf": cpf,
                "status_code": response.status_code,
                "erro": "" if response.status_code == 200 else f"Erro HTTP {response.status_code}",
                "resposta": response.text[:3000]  # limitando resposta
            })
        except Exception as e:
            resultados.append({"cpf": cpf, "erro": str(e), "resposta": "", "status_code": 0})

    df_resultado = pd.DataFrame(resultados)
    output = BytesIO()
    df_resultado.to_excel(output, index=False)
    output.seek(0)

    return send_file(output, download_name="resultado_bmg_logs.xlsx", as_attachment=True)


@app.route("/")
def home():
    return "API BMG pronta"

if __name__ == "__main__":
    app.run()
