import httpx
import xml.etree.ElementTree as ET
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
        xml = response.text
        status_code = response.status_code

        if status_code != 200:
            return jsonify({
                "cpf": cpf,
                "status_code": status_code,
                "erro": f"Erro HTTP {status_code}",
                "mensagem": "Falha na requisição ao BMG"
            }), status_code

        # Parse XML
        ns = {
            "soapenv": "http://schemas.xmlsoap.org/soap/envelope/",
            "ns1": "http://webservice.econsig.bmg.com",
            "soapenc": "http://schemas.xmlsoap.org/soap/encoding/",
            "xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xsd": "http://www.w3.org/2001/XMLSchema"
        }
        root = ET.fromstring(xml)

        cartao = root.find(".//cartoesRetorno", ns)
        if cartao is None:
            return jsonify({
                "cpf": cpf,
                "status_code": 204,
                "mensagem": "Nenhum cartão disponível ou CPF sem dados"
            }), 200

        dados = {
            "cpf": cpf,
            "liberado": cartao.findtext("liberado", default="", namespaces=ns) == "true",
            "motivo": cartao.findtext("mensagemImpedimento", default="", namespaces=ns).replace("\r", "").replace("\n", " "),
            "modalidade": cartao.findtext("modalidadeSaque", default="", namespaces=ns),
            "numero_adesao": cartao.findtext("numeroAdesao", default="", namespaces=ns),
            "numero_cartao": cartao.findtext("numeroCartao", default="", namespaces=ns),
        }

        # Extrair limites de dentro da mensagemImpedimento
        msg = dados["motivo"]
        for linha in msg.split(" "):
            if "saque...:" in linha:
                dados["limite_saque"] = linha.split(":")[-1].strip()
            elif "Total.....:" in linha:
                dados["limite_total"] = linha.split(":")[-1].strip()
            elif "crédito" in linha.lower():
                dados["limite_credito"] = linha.split(":")[-1].strip()

        # Formas de envio
        formas = root.findall(".//formasEnvio", ns)
        formas_envio = [f.findtext("descricao", default="", namespaces=ns) for f in formas]
        dados["formas_envio"] = formas_envio

        return jsonify(dados), 200

    except Exception as e:
        return jsonify({"cpf": cpf, "erro": str(e)}), 500
