import json
import time
import random
from kafka import KafkaProducer

# --- CONFIGURAÇÃO DA SIMULAÇÃO ---

# Dicionário para manter o estado (posição e velocidade) de cada veículo entre os ciclos
VEHICLE_STATES = {}
NUM_VEICULOS = 10

# Área inicial de Simulação (São Paulo, Brasil)
INITIAL_LAT = -23.5505  # Latitude central
INITIAL_LNG = -46.6333  # Longitude central
MOVEMENT_RANGE = 0.0005 # Simula pequenos deslocamentos por segundo (movimento suave)

# Inicializa as posições dos veículos
for i in range(1, NUM_VEICULOS + 1):
    VEHICLE_STATES[i] = {
        'idveiculo': i,
        # Adiciona uma pequena variação para espalhar os veículos inicialmente
        'latitude': INITIAL_LAT + random.uniform(-0.01, 0.01),
        'longitude': INITIAL_LNG + random.uniform(-0.01, 0.01),
        'velocidade': random.randint(0, 80),
        'timestamp': time.time()
    }

# --- CONFIGURAÇÃO DO KAFKA ---
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    # Serializa os dados em JSON UTF-8
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def update_vehicle_position(vehicle_data):
    """Atualiza a posição do veículo com base em seu estado anterior."""
    
    # Gera um pequeno deslocamento aleatório
    lat_delta = random.uniform(-MOVEMENT_RANGE, MOVEMENT_RANGE)
    lng_delta = random.uniform(-MOVEMENT_RANGE, MOVEMENT_RANGE)
    
    # Aplica o movimento
    vehicle_data['latitude'] += lat_delta
    vehicle_data['longitude'] += lng_delta
    
    # Atualiza velocidade (com variação) e timestamp
    vehicle_data['velocidade'] = random.randint(30, 80)
    vehicle_data['timestamp'] = time.time()
    
    return vehicle_data

# --- LOOP PRINCIPAL DE ENVIO ---
try:
    print(f"Iniciando envio de dados para {NUM_VEICULOS} veículos...")
    while True:
        for vehicle_id in range(1, NUM_VEICULOS + 1):
            # Obtém e atualiza o estado atual do veículo
            current_state = VEHICLE_STATES[vehicle_id]
            updated_data = update_vehicle_position(current_state)
            
            producer.send('veiculosv2', updated_data)
            
            print(f"Dados enviados: ID={vehicle_id}, Lat={updated_data['latitude']:.5f}, Lng={updated_data['longitude']:.5f}, Speed={updated_data['velocidade']} km/h")
            
        # Espera 1 segundo após o ciclo completo de envio dos 10 veículos
        time.sleep(1)

except KeyboardInterrupt:
    print("\nColeta interrompida pelo usuário.")

producer.flush()
producer.close()
