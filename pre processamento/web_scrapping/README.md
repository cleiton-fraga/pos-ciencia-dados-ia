# Mercado Livre Service

Servico Python para scraping de busca do Mercado Livre, com enriquecimento de dados por pagina de detalhe.

## Como executar

```bash
python3 -m pip install -r requirements.txt
python3 main_mercado_livre.py --query "tablet" --pages 2 --max-items 30 --output-dir output
```

## Arquivos

- `main_mercado_livre.py`: ponto de entrada do servico para Mercado Livre.
- `resources/mercado_livre.py`: recursos de scraping, parse e enriquecimento.
