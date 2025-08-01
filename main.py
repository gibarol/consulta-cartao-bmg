from flask import Flask, request, jsonify
import pandas as pd
import os
import logging

app = Flask(__name__)

# Configura o log para aparecer no console da Render
logging.basicConfig(level=logging.INFO)

@app.route('/')
def home():
    return 'API BMG Processor Online!'

@app.route('/consulta-planilha', methods=['POST'])
def consulta_planilha():
    try:
        if 'file' not in request.files:
            logging.error("Nenhum arquivo enviado na chave 'file'.")
            return jsonify({'erro': "Arquivo não enviado (campo 'file' obrigatório)"}), 400

        file = request.files['file']

        if file.filename == '':
            logging.error("Nome do arquivo vazio.")
            return jsonify({'erro': "Nome do arquivo vazio"}), 400

        logging.info(f"Arquivo recebido: {file.filename}")

        # Tenta ler a planilha
        try:
            df = pd.read_excel(file)
            logging.info(f"Colunas encontradas: {list(df.columns)}")
        except Exception as e:
            logging.exception("Erro ao ler a planilha")
            return jsonify({'erro': f"Erro ao ler o arquivo Excel: {str(e)}"}), 400

        # Verifica se a coluna 'cpf' existe
        if 'cpf' not in df.columns:
            logging.error("Coluna 'cpf' não encontrada na planilha.")
            return jsonify({'erro': "A planilha deve conter uma coluna chamada 'cpf'"}), 400

        cpfs = df['cpf'].astype(str).tolist()

        # Simulação de processamento (pode substituir com chamada ao BMG)
        resultados = []
        for cpf in cpfs:
            logging.info(f"Processando CPF: {cpf}")
            resultados.append({
                'cpf': cpf,
                'status': 'ok',  # aqui pode ser "consultado", "erro", etc
                'mensagem': f"Simulação para CPF {cpf}"
            })

        return jsonify({'resultado': resultados}), 200

    except Exception as e:
        logging.exception("Erro interno ao processar a planilha")
        return jsonify({'erro': f"Erro interno: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
