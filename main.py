from flask import Flask, request
import zeep

app = Flask(__name__)

@app.route("/")
def home():
    return "<span style='color:green'>🟢 API BMG Online via Render – SOAP liberado</span>"

@app.route("/consulta")
def consulta():
    cpf = request.args.get("cpf")
    if not cpf:
        return "❌ CPF não informado na URL. Use ?cpf=SEUCPF", 400

    try:
        wsdl = "https://ws1.bmgconsig.com.br/webservices/SaqueComplementar?wsdl"
        client = zeep.Client(wsdl=wsdl)

        response = client.service.buscarCartoesDisponiveis(
            param={
                "login": "robo.56780",
                "senha": "Sucesso1@@@",
                "codigoEntidade": "1581",
                "cpf": cpf,
                "sequencialOrgao": ""
            }
        )

        return f"✅ Resultado para {cpf}:<br>Status Cartão: {getattr(response, 'descricaoSituacaoCartao', 'Não retornado')}<br>Tipo Saque: {getattr(response, 'tipoSaque', 'Não retornado')}"

    except Exception as e:
        return f"❌ Erro na consulta: {str(e)}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
