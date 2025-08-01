import httpx
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/consulta", methods=["GET"])
def consulta_cpf():
    cpf = request.args.get("cpf")
    if not cpf:
        return jsonify({"erro": "CPF não informado"}), 400

    url = "https://ws1.bmgconsig.com.br/webservices/SaqueComplementar?wsdl"

    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "pt-BR,pt;q=0.9",
        "Origin": "https://bmgconsig.com.br",
        "Referer": "https://bmgconsig.com.br/",
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
        content = response.text

        # Tenta extrair mensagem de erro do XML (se houver)
        if "<faultstring>" in content:
            inicio = content.find("<faultstring>") + len("<faultstring>")
            fim = content.find("</faultstring>")
            erro_extraido = content[inicio:fim]
            # Substitui códigos XML comuns
            erro_extraido = erro_extraido.replace("&#xE3;", "ã").replace("&#xED;", "í").replace("&#xE9;", "é").replace("&#xE0;", "à")
        else:
            erro_extraido = ""

        resultado = {
            "cpf": cpf,
            "status_code": response.status_code,
            "erro": erro_extraido or (f"Erro HTTP {response.status_code}" if response.status_code != 200 else ""),
            "resposta": content if response.status_code == 200 else None
        }

        return jsonify(resultado), 200

    except Exception as e:
        return jsonify({"cpf": cpf, "erro": str(e)}), 500
