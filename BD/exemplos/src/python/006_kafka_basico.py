# /usr/bin/python3 -m  pip uninstall kafka kafka-python confluent-kafka -y
# /usr/bin/python3 -m pip install --upgrade kafka-python

from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
import json
import time

TOPIC = "meu_topico"
BROKER = "localhost:9092"   # importante: usar o nome do serviço do docker-compose

# ---------- PRODUTOR ----------

def produce_messages():
    producer = KafkaProducer(
        bootstrap_servers=BROKER,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

    for i in range(10):
        message = {"numero": i}
        future = producer.send(TOPIC, message)

        try:
            record_metadata = future.get(timeout=10)
            print(f"Mensagem enviada: {message}, Partição: {record_metadata.partition}, Offset: {record_metadata.offset}")
        except KafkaError as e:
            print(f"Erro ao enviar mensagem: {e}")

    producer.flush()
    producer.close()

# ---------- CONSUMIDOR SIMPLES ----------

def consume_messages():
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=BROKER,
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='grupo1',
        value_deserializer=lambda v: json.loads(v.decode('utf-8'))
    )

    print("Consumindo mensagens (simples)...")
    try:
        for message in consumer:
            print(f"Mensagem recebida: {message.value}")
            break  # apenas para exemplo
    finally:
        consumer.close()

# ---------- CONSUMIDOR EM LOTE ----------

def consume_batch(batch_size=5):
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=BROKER,
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='grupo2',
        value_deserializer=lambda v: json.loads(v.decode('utf-8'))
    )

    batch = []
    print("Consumindo mensagens em lote...")
    try:
        for message in consumer:
            batch.append(message.value)
            if len(batch) >= batch_size:
                print(f"Lote recebido: {batch}")
                batch = []
                break  # apenas exemplo
    finally:
        consumer.close()

# ---------- EXECUÇÃO ----------

if __name__ == "__main__":
    print("Produzindo mensagens...")
    produce_messages()
    time.sleep(2)

    print("\nConsumidor simples:")
    consume_messages()

    print("\nConsumidor em lote:")
    consume_batch()
