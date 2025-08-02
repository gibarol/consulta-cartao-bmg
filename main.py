
import os
import tempfile
import pandas as pd
import httpx
from flask import Flask, request, send_file

app = Flask(__name__)

@app.route("/consulta-planilha", methods=["POST"])
def consulta_planilha():
    if "file" not in request.files:
        return {"erro": "Arquivo não enviado"}, 400

    file = request.files["file"]
    if not file.filename.endswith((".xlsx", ".xls")):
        return {"erro": "Formato de arquivo inválido. Envie um .xlsx ou .xls"}, 400

    with tempfile.TemporaryDirectory() as tmpdirname:
        input_path = os.path.join(tmpdirname, "entrada.xlsx")
        file.save(input_path)

        df = pd.read_excel(input_path)
        if "cpf" not in df.columns:
            return {"erro": "A planilha deve conter uma coluna chamada 'cpf'"}, 400

        resultados = []

        for cpf in df["cpf"]:
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

            headers = {
                "Content-Type": "text/xml; charset=utf-8",
                "SOAPAction": "",
                "User-Agent": "Python httpx"
            }

            try:
                response = httpx.post(
                    "https://ws1.bmgconsig.com.br/webservices/SaqueComplementar?wsdl",
                    data=payload,
                    headers=headers,
                    timeout=30.0
                )

                if response.status_code != 200:
                    resultados.append({
                        "cpf": cpf,
                        "status_code": response.status_code,
                        "erro": f"Erro HTTP {response.status_code}",
                        "motivo": "",
                        "liberado": "",
                        "limite_saque": "",
                        "limite_total": "",
                        "limite_credito": "",
                        "numero_adesao": "",
                        "numero_cartao": ""
                    })
                    continue

                content = response.text

                def extrair(tag):
                    inicio = content.find(f"<{tag}>")
                    fim = content.find(f"</{tag}>")
                    if inicio != -1 and fim != -1:
                        return content[inicio + len(tag) + 2:fim].strip()
                    return ""

                resultados.append({
                    "cpf": cpf,
                    "status_code": 200,
                    "erro": "",
                    "motivo": extrair("mensagemImpedimento"),
                    "liberado": extrair("liberado"),
                    "limite_saque": extrair("limite disponivel para saque...:"),
                    "limite_total": extrair("limite disponível de Total.....:"),
                    "limite_credito": extrair("limite de crédito..............:"),
                    "numero_adesao": extrair("numeroAdesao"),
                    "numero_cartao": extrair("numeroCartao")
                })

            except Exception as e:
                resultados.append({
                    "cpf": cpf,
                    "status_code": 500,
                    "erro": str(e),
                    "motivo": "",
                    "liberado": "",
                    "limite_saque": "",
                    "limite_total": "",
                    "limite_credito": "",
                    "numero_adesao": "",
                    "numero_cartao": ""
                })

        df_saida = pd.DataFrame(resultados)
        output_path = os.path.join(tmpdirname, "resultado_bmg.xlsx")
        df_saida.to_excel(output_path, index=False, engine='openpyxl')

        return send_file(
            output_path,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name="resposta_bmg.xlsx"
        )
