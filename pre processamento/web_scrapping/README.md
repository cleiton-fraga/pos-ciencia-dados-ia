# Mercado Livre Service

Servico Python para scraping de busca do Mercado Livre, com enriquecimento de dados por pagina de detalhe.

## Como executar

```bash
python3 -m pip install -r requirements.txt
python3 main_mercado_livre.py --query "tablet" --pages 2 --max-items 30 --output-dir output
python3 main_kabum.py --query "tv" --pages 2 --delay 1.0 --output-dir output --no-headless --selenium-wait 8 --selenium-scrolls 12
# opcional: desabilitar fallback selenium
python3 main_kabum.py --query "tv" --no-selenium-fallback
# modo assertivo com relatorio e artefatos de debug
python3 main_kabum.py --query "tv" --pages 2 --min-items-per-page 5 --debug-dir output/debug_kabum --report-path output/kabum_report.json
```

## Arquivos

- `main_mercado_livre.py`: ponto de entrada do servico para Mercado Livre.
- `main_kabum.py`: ponto de entrada do servico para Kabum.
- `resources/mercado_livre.py`: recursos de scraping, parse e enriquecimento.
- `resources/kabum.py`: recurso de web scraping da Kabum (estrategia em camadas, validacao e debug artifacts).
