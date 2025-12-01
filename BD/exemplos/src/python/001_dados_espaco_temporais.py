import geopandas as gpd
import matplotlib.pyplot as plt
import zipfile
import os
import shutil

# 1. Definindo o caminho para o arquivo ZIP e o diretório de destino
# O os.path.join() é a melhor prática para criar caminhos, pois funciona em todos os sistemas operacionais
zip_file_path = os.path.join('src', 'modulo2', 'data', 'BR_bairros_CD2022.zip')

# O diretório de destino para extração
destination_directory = os.path.join('src', 'modulo2', 'data', 'BR_bairros_CD2022')

# 2. Descompactando o arquivo ZIP
try:
    # Verificando se o arquivo ZIP existe
    if not os.path.exists(zip_file_path):
        print(f"Erro: O arquivo ZIP '{zip_file_path}' não foi encontrado.")
    else:
        # Removendo o diretório de destino se ele já existir para evitar conflitos
        if os.path.exists(destination_directory):
            shutil.rmtree(destination_directory)
            print(f"Diretório '{destination_directory}' removido para uma nova extração.")
            
        # Criando o novo diretório de destino
        os.makedirs(destination_directory)
        
        # Abrindo o arquivo ZIP e extraindo o conteúdo
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            print(f'Descompactando "{zip_file_path}" para "{destination_directory}"...')
            zip_ref.extractall(destination_directory)
            print('Descompactação concluída!')

    # 3. Encontrando o arquivo .shp dentro dos arquivos extraídos
    # Neste caso, o nome do arquivo .shp é 'BR_Setores_Censitarios_2022.shp'
    # Você pode inspecionar o conteúdo do ZIP para confirmar o nome correto
    shp_file_name = 'BR_bairros_CD2022.shp'
    shapefile_path = os.path.join(destination_directory, shp_file_name)

    # 4. Carregando o shapefile com GeoPandas
    gdf = gpd.read_file(shapefile_path)

    # 5. Plotando o mapa dos bairros censitários
    print('\nVisualizando as primeiras linhas do GeoDataFrame:')
    print(gdf.head())
    
    print(gdf.columns)
    
    print('\nPlotando o mapa...')
    gdf.plot(figsize=(12, 12), edgecolor='black', linewidth=0.3)
    plt.title('Mapa dos Bairros Censitários do Brasil (2022)')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.show()
    
    # Supondo que a coluna com o nome do município seja 'NM_MUN' e a do estado seja 'SIGLA_UF'
    # Filtrando apenas os bairros de Aracaju, por exemplo
    bairros_maceio = gdf[gdf['NM_MUN'] == 'Maceió']

    # Plotando apenas os bairros da cidade selecionada
    bairros_maceio.plot(figsize=(10, 10), edgecolor='black', linewidth=0.5, cmap='Pastel2')
    plt.title('Bairros de Maceió (2022)')
    plt.show()
    
    
    # Filtrando apenas os bairros de Aracaju
    bairros_aracaju = gdf[gdf['NM_MUN'] == 'Aracaju'].copy()

    # Criando o plot
    fig, ax = plt.subplots(figsize=(12, 12))

    # Plotando os polígonos dos bairros
    bairros_aracaju.plot(ax=ax, edgecolor='black', linewidth=0.5, cmap='Pastel2')

    # Adicionando o nome de cada bairro
    # A coluna com o nome do bairro é 'NM_BAIRRO'
    for idx, row in bairros_aracaju.iterrows():
        # Obtém o centroide do polígono para a coordenada do texto
        centroid = row.geometry.centroid
        
        # Anota o nome do bairro no mapa
        ax.annotate(text=row['NM_BAIRRO'], 
                    xy=(centroid.x, centroid.y),
                    horizontalalignment='center', 
                    fontsize=8, 
                    fontweight='bold', 
                    color='dimgray')

    plt.title('Bairros de Aracaju com Nomes (2022)')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.show()

except zipfile.BadZipFile:
    print("O arquivo baixado não é um arquivo ZIP válido.")
except FileNotFoundError as e:
    print(f"Erro: O arquivo shapefile não foi encontrado. Verifique se o nome '{shp_file_name}' está correto ou se o caminho está certo: {e}")
except Exception as e:
    print(f"Ocorreu um erro inesperado: {e}")