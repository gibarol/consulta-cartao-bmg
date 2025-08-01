from flask import Flask, request, jsonify
import httpx

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
        return jsonify({
            "cpf": cpf,
            "status_code": response.status_code,
            "erro": f"Erro HTTP {response.status_code}" if response.status_code != 200 else "",
            "resposta": response.text
        }), response.status_code
    except Exception as e:
        return jsonify({"cpf": cpf, "erro": str(e)}), 500

# Isso garante que funcione localmente também
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
