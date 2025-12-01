import json
from kafka import KafkaConsumer
import geopandas as gpd
import matplotlib.pyplot as plt

# Configura o consumidor Kafka
consumer = KafkaConsumer(
    'veiculos',
    bootstrap_servers='localhost:9092',
    auto_offset_reset='earliest',  # Começa do início do tópico
    enable_auto_commit=True,
    group_id='grupo_veiculos'
)

# Armazenando os dados recebidos
lista_dados = []

for mensagem in consumer:
    dados = json.loads(mensagem.value)
    lista_dados.append(dados)

    # Para visualização contínua, pode-se limitar o número de pontos
    if len(lista_dados) > 50:
        lista_dados.pop(0)

    # Transformando para GeoDataFrame
    gdf = gpd.GeoDataFrame(
        lista_dados,
        geometry=gpd.points_from_xy(
            [dado['longitude'] for dado in lista_dados],
            [dado['latitude'] for dado in lista_dados]
        )
    )

    # Plotando as localizações dos veículos
    gdf.plot(marker='o', color='red', markersize=50)
    plt.title('Monitoramento de Veículos em Tempo Real')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.pause(1)  # Pausa para atualizar o gráfico
    plt.clf()     # Limpa o gráfico anterior para atualizar
