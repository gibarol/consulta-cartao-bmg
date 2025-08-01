from flask import Flask, request, jsonify, send_file
import pandas as pd
from io import BytesIO
import tempfile
import os

app = Flask(__name__)

@app.route('/')
def home():
    return 'API BMG Planilha OK ✅'

@app.route('/consulta-planilha', methods=['POST'])
def processar_planilha():
    if 'file' not in request.files:
        return jsonify({'erro': 'Nenhum arquivo enviado.'}), 400

    arquivo = request.files['file']
    extensao = os.path.splitext(arquivo.filename)[1].lower()

    if extensao not in ['.xlsx', '.xls']:
        return jsonify({'erro': 'Formato inválido. Envie um .xlsx ou .xls'}), 400

    try:
        # Lê o conteúdo da planilha direto da memória
        df = pd.read_excel(BytesIO(arquivo.read()))

        # Verifica se a coluna "cpf" existe
        if 'cpf' not in df.columns:
            return jsonify({'erro': 'A planilha deve conter uma coluna chamada "cpf".'}), 400

        resultados = []

        for cpf in df['cpf']:
            # Aqui você faria a chamada real da API do BMG
            # Vamos simular uma resposta rica com todos os dados
            resposta_simulada = {
                'cpf': cpf,
                'status': 'ok',
                'mensagem': f'Retorno simulado do BMG para CPF {cpf}',
                'cpfImpedidoComissionar': False,
                'entidade': '1581',
                'liberado': False,
                'matricula': '5369143931',
                'mensagemImpedimento': 'Saque não liberado pelo motivo: Conta/Cartão com Bloqueio CRELI',
                'modalidadeSaque': 'Parcelado',
                'numeroAdesao': '38156227',
                'numeroCartao': '5259xxxxxxxx8117',
                'numeroContaInterna': '3431398',
                'formasEnvio': 'Digital, Digital Token, Físico',
                'limiteSaque': 344.86,
                'limiteTotal': 344.86,
                'limiteCredito': 2047.00
            }

            resultados.append(resposta_simulada)

        df_saida = pd.DataFrame(resultados)

        # Cria um arquivo temporário para salvar a planilha
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            caminho_saida = tmp.name
            df_saida.to_excel(caminho_saida, index=False)

        return send_file(
            caminho_saida,
            as_attachment=True,
            download_name='resultado-bmg.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        return jsonify({'erro': f'Erro ao processar a planilha: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)
