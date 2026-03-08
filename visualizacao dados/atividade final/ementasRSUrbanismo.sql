---------- Consulta para extrair dados de emendas parlamentares relacionadas a urbanismo no estado do Rio Grande do Sul (RS) --------

SELECT * FROM `basedosdados.br_cgu_emendas_parlamentares.microdados`
where sigla_uf_gasto = 'RS'
and nome_funcao like '%Urbanismo%'
and nome_subfuncao like '%infra-estrutura urbana%'
and id_municipio_gasto = '4314902' -- Código do município de Porto Alegre, RS (na estacoes é o id do municipio)
LIMIT 1000