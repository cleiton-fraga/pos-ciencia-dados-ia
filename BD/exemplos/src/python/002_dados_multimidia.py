# /usr/bin/python3 -m pip install opencv-python

import cv2
# Carregando uma imagem
imagem = cv2.imread('src/modulo2/data/ferrari.avif')
# Convertendo para escala de cinza
imagem_cinza = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
# Exibindo a imagem original e a imagem em escala de cinza
cv2.imshow('Imagem Original', imagem)
cv2.imshow('Imagem em Escala de Cinza', imagem_cinza)
cv2.waitKey(0)
cv2.destroyAllWindows()