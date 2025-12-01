import json
import time
import random
from kafka import KafkaProducer

# Configura o produtor Kafka
producer = KafkaProducer(bootstrap_servers='localhost:9092')

while True:
    # Simulando dados de localização de um veículo
    dados = {
        'id_veiculo': random.randint(1, 10),
        'latitude': random.uniform(-23.500, -23.300),
        'longitude': random.uniform(-46.700, -46.600),
        'timestamp': time.time()
    }

    # Envia os dados para o tópico 'veiculos'
    producer.send('veiculos', json.dumps(dados).encode('utf-8'))

    # Aguardar 1 segundo antes de enviar a próxima mensagem
    time.sleep(1)
