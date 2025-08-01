from flask import Flask, request, send_file, jsonify
import pandas as pd
import tempfile
import os

app = Flask(__name__)

@app.route('/upload', methods=['POST'])
def upload_planilha():
    if 'file' not in request.files:
        return jsonify({"erro": "Arquivo não enviado"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"erro": "Nome do arquivo inválido"}), 400

    try:
        # Lê a planilha enviada
        df = pd.read_excel(file)
        if 'cpf' not in df.columns:
            return jsonify({"erro": "Coluna 'cpf' não encontrada"}), 400

        # Cria uma nova coluna simulando retorno
        df['mensagem'] = 'Consulta simulada com sucesso'  # Aqui você coloca o retorno real do BMG

        # Salva o arquivo temporariamente
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        df.to_excel(temp_file.name, index=False)

        return send_file(temp_file.name, as_attachment=True, download_name='resultado_consulta_bmg.xlsx')
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == '__main__':
    app.run()
