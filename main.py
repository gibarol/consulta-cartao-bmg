import os
import tempfile
import pandas as pd
import httpx
from flask import Flask, request, send_file
import zipfile

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
                "User-Agent": "Python httpx"
            }

            try:
                response = httpx.post(
                    "https://ws1.bmgconsig.com.br/webservices/SaqueComplementar?wsdl",
                    data=payload,
                    headers=headers,
                    timeout=30.0
                )

                ip_origem = httpx.get("https://api.ipify.org").text
                content = response.text

                def extrair(tag):
                    inicio = content.find(f"<{tag}>")
                    fim = content.find(f"</{tag}>")
                    if inicio != -1 and fim != -1:
                        return content[inicio + len(tag) + 2:fim].strip()
                    return ""

                resultados.append({
                    "cpf": cpf,
                    "status_code": response.status_code,
                    "erro": "" if response.status_code == 200 else f"Erro HTTP {response.status_code}",
                    "motivo": extrair("mensagemImpedimento"),
                    "liberado": extrair("liberado"),
                    "limite_saque": extrair("limite disponivel para saque...:"),
                    "limite_total": extrair("limite disponível de Total.....:"),
                    "limite_credito": extrair("limite de crédito..............:"),
                    "numero_adesao": extrair("numeroAdesao"),
                    "numero_cartao": extrair("numeroCartao")
                })

                logs.append(f"\n----- CPF {cpf} -----\nIP de Origem: {ip_origem}\nStatus: {response.status_code}\nResposta:\n{content}\n")

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
                logs.append(f"\n----- CPF {cpf} -----\nErro ao consultar: {str(e)}\n")

        # Salva a planilha corretamente
        df_saida = pd.DataFrame(resultados)
        output_path = os.path.join(tmpdirname, "resultado_bmg.xlsx")
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df_saida.to_excel(writer, index=False)

        # Salva os logs em .txt
        log_path = os.path.join(tmpdirname, "log_requisicoes.txt")
        with open(log_path, "w", encoding="utf-8") as f:
            f.writelines(logs)

        # Compacta tudo
        zip_path = os.path.join(tmpdirname, "resposta_bmg.zip")
        with zipfile.ZipFile(zip_path, "w") as zipf:
            zipf.write(output_path, arcname="resultado_bmg.xlsx")
            zipf.write(log_path, arcname="log_requisicoes.txt")

        return send_file(zip_path, as_attachment=True, download_name="resposta_bmg.zip")
