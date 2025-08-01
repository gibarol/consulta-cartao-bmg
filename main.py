from flask import Flask, request, send_file, jsonify
import pandas as pd
import requests
import xml.etree.ElementTree as ET
import io

app = Flask(__name__)

@app.route('/')
def home():
    return 'API BMG Online'

@app.route('/consulta-planilha', methods=['POST'])
def consulta_planilha():
    try:
        if 'file' not in request.files:
            return jsonify({'erro': "Arquivo não enviado (campo 'file' obrigatório)"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'erro': "Nome do arquivo vazio"}), 400

        df = pd.read_excel(file)
        if 'cpf' not in df.columns:
            return jsonify({'erro': "A planilha deve conter uma coluna chamada 'cpf'"}), 400

        cpfs = df['cpf'].astype(str).tolist()
        resultados = []

        for cpf in cpfs:
            # Montar XML SOAP para o BMG
            envelope = f"""<?xml version="1.0" encoding="UTF-8"?>
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
</soapenv:Envelope>""".strip()

            headers = {
                "Content-Type": "text/xml;charset=UTF-8",
                "SOAPAction": ""
            }

            try:
                response = requests.post("https://webservice.econsig.bmg.com/servico/BmgServices", data=envelope, headers=headers, timeout=30)
                tree = ET.fromstring(response.text)
                ns = {"ns1": "http://webservice.econsig.bmg.com"}

                cartao = tree.find(".//ns1:cartoesRetorno", ns)
                dados = {}
                if cartao is not None:
                    for tag in ["cpfImpedidoComissionar", "entidade", "liberado", "matricula", "mensagemImpedimento",
                                "modalidadeSaque", "numeroAdesao", "numeroCartao", "numeroContaInterna"]:
                        el = cartao.find(f"ns1:{tag}", ns)
                        dados[tag] = el.text if el is not None else ""

                    formas = tree.findall(".//ns1:formasEnvio/ns1:descricao", ns)
                    dados["formasEnvio"] = ', '.join([f.text for f in formas if f is not None])

                    msg = dados.get("mensagemImpedimento", "")
                    import re
                    saque = re.search(r"Limite disponivel para saque.*?: ([\d\.,]+)", msg)
                    total = re.search(r"Limite disponível de Total.*?: ([\d\.,]+)", msg)
                    credito = re.search(r"Limite de crédito.*?: ([\d\.,]+)", msg)
                    dados["limiteSaque"] = saque.group(1) if saque else ""
                    dados["limiteTotal"] = total.group(1) if total else ""
                    dados["limiteCredito"] = credito.group(1) if credito else ""

                resultados.append({"cpf": cpf, "status": "ok", **dados})
            except Exception as e:
                resultados.append({"cpf": cpf, "status": "erro", "mensagem": str(e)})

        df_saida = pd.DataFrame(resultados)
        output_path = "/tmp/retorno_bmg.xlsx"
        df_saida.to_excel(output_path, index=False)

        return send_file(output_path, as_attachment=True, download_name="retorno_bmg.xlsx",
                         mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        return jsonify({'erro': f"Erro interno: {str(e)}"}), 500

if __name__ == '__main__':
    app.run()
