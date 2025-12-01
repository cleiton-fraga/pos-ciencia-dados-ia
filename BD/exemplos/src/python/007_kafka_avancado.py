from kafka import KafkaProducer, KafkaConsumer, TopicPartition
from kafka.admin import KafkaAdminClient, NewTopic
import json
import time
import threading

BROKER = "localhost:9092"
TOPICS = ["topico1", "topico2"]

# ---------- ADMINISTRAÇÃO (CRIAÇÃO/LIMPEZA DE TÓPICOS) ----------

def setup_topics():
    admin_client = KafkaAdminClient(bootstrap_servers=BROKER, client_id='admin')

    # Remove tópicos antigos
    try:
        admin_client.delete_topics(TOPICS, timeout_ms=5000)
        print("Tópicos antigos removidos...")
        time.sleep(2)
    except Exception:
        print("Nenhum tópico para remover ou já inexistentes.")

    # Cria tópicos novos
    topic_list = [
        NewTopic(name=topic, num_partitions=3, replication_factor=1)
        for topic in TOPICS
    ]
    try:
        admin_client.create_topics(new_topics=topic_list, validate_only=False)
        print("Tópicos criados com sucesso:", TOPICS)
    except Exception as e:
        print("Erro ao criar tópicos:", e)

# ---------- PRODUTOR AVANÇADO (ASSÍNCRONO) ----------

def produce_messages(topic):
    producer = KafkaProducer(
        bootstrap_servers=BROKER,
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        key_serializer=lambda k: k.encode('utf-8')
    )

    for i in range(10):
        key = f"user-{i%3}"
        value = {"msg": f"mensagem-{i}", "topico": topic}
        producer.send(topic, key=key, value=value).add_callback(
            lambda metadata: print(f"[Prod-{topic}] Enviado {value} para partição {metadata.partition}, offset {metadata.offset}")
        ).add_errback(
            lambda exc: print(f"[Prod-{topic}] Erro: {exc}")
        )
        time.sleep(0.3)

    producer.flush()
    producer.close()

# ---------- CONSUMIDOR AVANÇADO (COMMIT MANUAL) ----------

def consume_messages(topic, group_id):
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=BROKER,
        auto_offset_reset='earliest',
        enable_auto_commit=False,  # commit manual
        group_id=group_id,
        value_deserializer=lambda v: json.loads(v.decode('utf-8')),
        key_deserializer=lambda k: k.decode('utf-8') if k else None
    )

    print(f"[Cons-{topic}] Consumidor iniciado...")
    for message in consumer:
        print(f"[Cons-{topic}] key={message.key}, value={message.value}, partição={message.partition}, offset={message.offset}")

        # Simula processamento
        time.sleep(0.5)

        # Faz commit manual do offset
        consumer.commit()
        print(f"[Cons-{topic}] Offset confirmado até {message.offset}")

# ---------- EXECUÇÃO PRINCIPAL ----------

if __name__ == "__main__":
    # 1. Configura tópicos
    setup_topics()

    # 2. Inicia consumidores em threads
    consumer_threads = []
    for topic in TOPICS:
        t = threading.Thread(target=consume_messages, args=(topic, "grupo-final"))
        t.start()
        consumer_threads.append(t)

    # 3. Dá tempo pros consumidores se registrarem
    time.sleep(3)

    # 4. Inicia produtores em threads
    producer_threads = []
    for topic in TOPICS:
        t = threading.Thread(target=produce_messages, args=(topic,))
        t.start()
        producer_threads.append(t)

    # Espera todos produtores finalizarem
    for t in producer_threads:
        t.join()

    print("Produção finalizada. Consumidores continuam ativos (Ctrl+C para parar).")