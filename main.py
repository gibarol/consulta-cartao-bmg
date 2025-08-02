import os
import tempfile
import time
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
        logs = []

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
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            try:
                response = httpx.post(
                    "https://ws1.bmgconsig.com.br/webservices/SaqueComplementar?wsdl",
                    data=payload,
                    headers=headers,
                    timeout=30.0
                )

                status = response.status_code
                content = response.text

                def extrair(tag):
                    inicio = content.find(f"<{tag}>")
                    fim = content.find(f"</{tag}>")
                    if inicio != -1 and fim != -1:
                        return content[inicio + len(tag) + 2:fim].strip()
                    return ""

                if status == 200:
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
                else:
                    resultados.append({
                        "cpf": cpf,
                        "status_code": status,
                        "erro": f"Erro HTTP {status}",
                        "motivo": "",
                        "liberado": "",
                        "limite_saque": "",
                        "limite_total": "",
                        "limite_credito": "",
                        "numero_adesao": "",
                        "numero_cartao": ""
                    })

                logs.append(f"CPF: {cpf} | Status: {status}\n{content}\n{'='*60}\n")

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
                logs.append(f"CPF: {cpf} | EXCEPTION: {str(e)}\n{'='*60}\n")

            # Delay para evitar bloqueio por flood
            time.sleep(1)

        df_saida = pd.DataFrame(resultados)
        output_path = os.path.join(tmpdirname, "resultado.xlsx")
        df_saida.to_excel(output_path, index=False)

        log_path = os.path.join(tmpdirname, "log.txt")
        with open(log_path, "w", encoding="utf-8") as log_file:
            log_file.writelines(logs)

        # Cria arquivo zip com os dois arquivos
        zip_path = os.path.join(tmpdirname, "resposta.zip")
        from zipfile import ZipFile
        with ZipFile(zip_path, "w") as zipf:
            zipf.write(output_path, "resultado.xlsx")
            zipf.write(log_path, "log.txt")

        return send_file(zip_path, as_attachment=True, download_name="resposta_bmg.zip")
