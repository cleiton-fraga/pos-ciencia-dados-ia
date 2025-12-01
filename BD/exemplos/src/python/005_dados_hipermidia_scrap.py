import requests
from bs4 import BeautifulSoup

# ================================
# 1. Fazer a requisição HTTP
# ================================
url = "https://news.ycombinator.com/"  # Exemplo: Hacker News
response = requests.get(url)

# Verifica se a requisição foi bem-sucedida
if response.status_code != 200:
    print("Erro ao acessar a página:", response.status_code)
    exit()

# ================================
# 2. Criar objeto BeautifulSoup
# ================================
soup = BeautifulSoup(response.text, "html.parser")

# ================================
# 3. Pegar os títulos das notícias
# ================================
titulos = soup.find_all("span", class_="titleline")

for i, titleline in enumerate(titulos[:10], 1):  # pegar as 10 primeiras
    a_tag = titleline.find("a")
    if a_tag:
        print(f"{i}. {a_tag.text}")

print("------------------")

# ================================
# 4. Exemplo extra: pegar informações adicionais
# ================================
subtextos = soup.find_all("td", class_="subtext")
for i, sub in enumerate(subtextos[:10], 1):
    pontos = sub.find("span", class_="score")
    if pontos:
        print(f"Notícia {i} tem {pontos.text}")
