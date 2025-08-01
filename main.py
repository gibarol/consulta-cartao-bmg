import requests

def consultar_bmg(cpf):
    url = "https://ws1.bmgconsig.com.br/webservices/SaqueComplementar?wsdl"
    headers = {
        "Content-Type": "text/xml;charset=UTF-8",
        "SOAPAction": "",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/115.0.0.0 Safari/537.36",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Referer": "https://bmgconsig.com.br",
        "Host": "ws1.bmgconsig.com.br"
    }

    body = f"""<?xml version="1.0" encoding="UTF-8"?>
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
        response = requests.post(url, data=body, headers=headers, timeout=20)
        return {
            "status_code": response.status_code,
            "content": response.text
        }
    except requests.exceptions.RequestException as e:
        return {"erro": str(e)}
