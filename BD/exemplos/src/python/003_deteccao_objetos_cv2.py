import cv2
import numpy as np

# Nomes das classes que o modelo consegue detectar
CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
	"bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
	"dog", "horse", "motorbike", "person", "pottedplant", "sheep",
	"sofa", "train", "tvmonitor"]

# Cores aleatórias para desenhar as caixas de cada classe
COLORS = np.random.uniform(0, 255, size=(len(CLASSES), 3))

# Caminhos para os arquivos do modelo
prototxt_path = "src/modulo2/data/MobileNetSSD_deploy.prototxt"
model_path = "src/modulo2/data/MobileNetSSD_deploy.caffemodel"

# Carregando o modelo pré-treinado da biblioteca dnn do OpenCV
print("Carregando o modelo...")
net = cv2.dnn.readNetFromCaffe(prototxt_path, model_path)
print("Modelo carregado com sucesso!")

# Inicializa a captura da webcam (0 para a câmera padrão)
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Erro: Não foi possível acessar a webcam. Verifique se ela está conectada e se as permissões estão corretas.")
else:
    print("Pressione 'q' para sair...")
    
    while True:
        # Lê um frame da webcam
        ret, frame = cap.read()
        if not ret:
            break

        # Redimensiona o frame e cria um 'blob' para a entrada da rede neural
        (h, w) = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 0.007843, (300, 300), 127.5)

        # Executa a detecção de objetos
        net.setInput(blob)
        detections = net.forward()

        # Itera sobre as detecções
        for i in np.arange(0, detections.shape[2]):
            # Extrai a confiança (probabilidade) da detecção
            confidence = detections[0, 0, i, 2]

            # Filtra detecções com confiança abaixo de 50%
            if confidence > 0.5:
                # Extrai o índice da classe e calcula a posição da caixa de delimitação
                idx = int(detections[0, 0, i, 1])
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (startX, startY, endX, endY) = box.astype("int")

                # Desenha a caixa de delimitação e o rótulo no frame
                label = f"{CLASSES[idx]}: {confidence:.2f}"
                cv2.rectangle(frame, (startX, startY), (endX, endY), COLORS[idx], 2)
                y = startY - 15 if startY - 15 > 15 else startY + 15
                cv2.putText(frame, label, (startX, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLORS[idx], 2)

        # Exibe o frame com as detecções
        cv2.imshow("Detecção de Objetos", frame)

        # Pressionar 'q' para sair do loop
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Libera a webcam e fecha as janelas
    cap.release()
    cv2.destroyAllWindows()