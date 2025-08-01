from flask import Flask, request, send_file, jsonify
import pandas as pd
import os
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route('/')
def home():
    return 'API BMG Processor Online!'

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
            resultados.append({
                'cpf': cpf,
                'status': 'ok',
                'mensagem': f"Retorno simulado do BMG para CPF {cpf}"
            })

        df_saida = pd.DataFrame(resultados)
        caminho_saida = "/tmp/retorno_bmg.xlsx"
        df_saida.to_excel(caminho_saida, index=False)

        return send_file(
            caminho_saida,
            as_attachment=True,
            download_name="retorno_bmg.xlsx",
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        logging.exception("Erro ao processar a planilha")
        return jsonify({'erro': str(e)}), 500

if __name__ == '__main__':
    app.run()
