import json
import logging
from threading import Thread, Lock
from flask import Flask, jsonify, Response
from flask_cors import CORS
from kafka import KafkaConsumer

# Configuração básica de log
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
# Habilita o CORS para permitir que o frontend em outra porta (ou mesmo URL file:///)
# acesse os endpoints da API.
CORS(app) 

# Variáveis de estado e lock para garantir segurança de thread
data_lock = Lock()          
dados_veiculos = []         
MAX_VEICULOS = 10          

try:
    consumer = KafkaConsumer(
        'veiculosv2',
        bootstrap_servers='localhost:9092',
        # Começa a ler as últimas mensagens se não houver offset salvo
        auto_offset_reset='latest',
        enable_auto_commit=True,
        # Desserializa a mensagem de bytes para um objeto JSON (dicionário Python)
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )
    logging.info("Consumidor Kafka inicializado com sucesso.")
except Exception as e:
    logging.error(f"Erro ao inicializar o consumidor Kafka: {e}. Verifique o broker Kafka.")
    consumer = None

@app.route('/')
@app.route('/index.html')
def serve_html():
    """
    Serve o arquivo HTML para o navegador.
    """
    try:
        # Tenta ler o arquivo HTML
        with open('index.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        return Response(html_content, mimetype='text/html')
    except FileNotFoundError:
        logging.error("Arquivo index.html não encontrado.")
        return "Arquivo index.html não encontrado. Certifique-se de que está na mesma pasta que app.py.", 404


@app.route('/dados_veiculos', methods=['GET'])
def get_dados_veiculos():
    """
    ROTA DA API: Retorna todos os dados de veículos atualmente em cache.
    Este endpoint é chamado pelo JavaScript do frontend.
    """
    with data_lock:
        # Retorna a lista de dicionários armazenados como JSON
        return jsonify(dados_veiculos)

def consume_data():
    """
    Função principal que roda em uma thread separada e consome mensagens do Kafka.
    """
    if not consumer:
        logging.error("Não é possível consumir dados: Consumidor Kafka não está disponível.")
        return

    logging.info("Thread de consumo de dados do Kafka iniciada.")
    for mensagem in consumer:
        try:
            dados = mensagem.value 
            
            with data_lock:
                # Adiciona o novo dado à lista de veículos
                dados_veiculos.append(dados)
                
                # Mantém o tamanho do cache limitado (MAX_VEICULOS)
                if len(dados_veiculos) > MAX_VEICULOS:  
                    # Remove o item mais antigo (primeiro da lista)
                    dados_veiculos.pop(0) 

                if len(dados_veiculos) % 10 == 0:
                    logging.info(f"Total de veículos em cache: {len(dados_veiculos)}. Processando dados...")
            
        except Exception as e:
            logging.error(f"Erro ao processar mensagem do Kafka: {e}")

if __name__ == '__main__':
    # Inicia a thread de consumo do Kafka (daemon=True garante que a thread feche com o programa principal)
    Thread_de_consumo = Thread(target=consume_data, daemon=True)
    Thread_de_consumo.start()
    
    logging.info("Iniciando servidor Flask...")
    # ATENÇÃO: Configuração para rodar na porta 5001 e escutar em todas as interfaces (host='0.0.0.0')
    # Isso é crucial para resolver o erro 403/acessibilidade em ambientes docker/local.
    app.run(debug=True, port=5001, host='0.0.0.0', use_reloader=False)
