import cv2
import mediapipe as mp
import pygame

# -------------------------------------------------------------
# ÁUDIO
# -------------------------------------------------------------
pygame.mixer.init()

relat_path = "src/modulo2/data/wav/"

notes = {
    "Do": pygame.mixer.Sound(f"{relat_path}do.wav"),
    "Re": pygame.mixer.Sound(f"{relat_path}re.wav"),
    "Mi": pygame.mixer.Sound(f"{relat_path}mi.wav"),
    "Fa": pygame.mixer.Sound(f"{relat_path}fa.wav"),
    "Sol": pygame.mixer.Sound(f"{relat_path}sol.wav"),
    "La": pygame.mixer.Sound(f"{relat_path}la.wav"),
    "Si": pygame.mixer.Sound(f"{relat_path}si.wav"),
}

# Tabela de notas para cada dedo (polegar → mínimo)
finger_note_map = ["Do", "Re", "Mi", "Fa", "Sol", "La", "Si", "Do"]

# Não repetir nota continuamente
played_left = [False] * 8
played_right = [False] * 8

# -------------------------------------------------------------
# MEDIAPIPE – Duas mãos
# -------------------------------------------------------------
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

# -------------------------------------------------------------
# Função para detectar dedos levantados
# -------------------------------------------------------------
def detect_fingers(lm):
    fingers = []

    # Polegar → eixo X
    fingers.append(1 if lm[4].x < lm[3].x else 0)

    # Indicador, médio, anelar, mínimo → eixo Y
    for tip in [8, 12, 16, 20]:
        fingers.append(1 if lm[tip].y < lm[tip - 2].y else 0)

    # Usa 8 dedinhos como você pediu (repetindo 3 primeiros)
    return fingers + fingers[:3]


# -------------------------------------------------------------
# LOOP PRINCIPAL
# -------------------------------------------------------------
cap = cv2.VideoCapture(0)

while True:
    ok, img = cap.read()
    if not ok:
        break

    img = cv2.flip(img, 1)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)

    if results.multi_hand_landmarks and results.multi_handedness:
        
        for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
            handedness = results.multi_handedness[idx].classification[0].label  # "Left" / "Right"

            mp_draw.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            lm = hand_landmarks.landmark

            fingers_up = detect_fingers(lm)

            # CENTRO DA MÃO PARA EXIBIR TEXTO
            h, w, _ = img.shape
            cx = int(lm[9].x * w)
            cy = int(lm[9].y * h)

            # Escolhe array certo para evitar repetição
            played = played_left if handedness == "Left" else played_right

            # Varre os 8 dedos
            for i in range(8):
                note = finger_note_map[i]

                if fingers_up[i] == 1:
                    if not played[i]:
                        notes[note].play()
                        played[i] = True

                    # Mostra nome da nota perto da mão
                    cv2.putText(img, f"{handedness}: {note}",
                                (cx - 50, cy - 80 + i * 20),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.6, (0, 255, 0), 2)
                else:
                    played[i] = False

            # RÓTULOS FIXOS NOS DEDOS
            tip_positions = [4, 8, 12, 16, 20]
            for i, tip_id in enumerate(tip_positions):
                x = int(lm[tip_id].x * w)
                y = int(lm[tip_id].y * h)
                cv2.putText(img, finger_note_map[i], (x - 20, y - 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

    cv2.imshow("Piano com os Dedos - Duas Mãos", img)

    if cv2.waitKey(1) & 0xFF == 27:  # ESC para sair
        break

cap.release()
cv2.destroyAllWindows()
