
-- Quais tipos de desastre predominaram entre 2014 e 2021? 
SELECT cobrade, COUNT(*) as ocorrencias
FROM fato_desastre
WHERE status = 'Reconhecido'
GROUP BY cobrade
ORDER BY ocorrencias DESC
LIMIT 10;

-- Onde os desastres se concentraram geograficamente? 
SELECT cobrade, uf, municipio, COUNT(*) as ocorrencias
FROM fato_desastre
WHERE status = 'Reconhecido'
GROUP BY cobrade, uf, municipio
ORDER BY ocorrencias DESC;


-- Quais tipos de desastre geraram maior impacto humano entre 2014 e 2019 (excluindo covid)?
SELECT cobrade, uf, municipio, SUM(dh_mortos) as total_mortes 
FROM fato_desastre fd
WHERE status = 'Reconhecido'
and ano BETWEEN 2014 and 2019
GROUP BY cobrade, uf, municipio
ORDER BY total_mortes DESC;

-- Quais tipos de desastre geraram maior impacto humano entre 2014 e 2021 (juntando covid)?
SELECT cobrade, uf, municipio, SUM(dh_mortos) as total_mortes 
FROM fato_desastre fd
WHERE status = 'Reconhecido'
GROUP BY cobrade, uf, municipio
ORDER BY total_mortes DESC;





