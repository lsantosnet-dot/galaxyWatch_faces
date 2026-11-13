#!/usr/bin/env python3
"""Remove os textos da imagem de referência e recorta o círculo do mostrador.

Só precisa rodar de novo se trocar reference.png. Requer OpenCV:
    pip install opencv-python-headless

Uso:   python faces/space-cruiser/art/clean_background.py
Saída: faces/space-cruiser/art/background_clean.png (quadrado, só o círculo)

Para usar outra arte sem textos, basta salvar um PNG quadrado em background_clean.png
e rodar generate_images.py.
"""
import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
src = cv2.imread(os.path.join(HERE, "reference.png"))

# Regiões com texto na referência (x0, y0, x1, y1, modo):
#   'text' = apaga só os pixels claros (letras); 'box' = apaga o retângulo inteiro
REGIONS = [
    (170, 70, 500, 200, "text"),   # 10:08
    (250, 198, 420, 226, "text"),  # QUI • 14 NOV
    (62, 252, 114, 304, "box"),    # ícone de passos
    (40, 305, 135, 382, "text"),   # STEPS / 1,247 / passos
    (550, 255, 605, 300, "box"),   # ícone do clima
    (512, 303, 635, 380, "text"),  # PREVISÃO / 24°C / ENSOLARADO
    (290, 592, 385, 632, "text"),  # bateria
]
mask = np.zeros(src.shape[:2], np.uint8)
bright = src.max(axis=2)
for x0, y0, x1, y1, mode in REGIONS:
    if mode == "box":
        mask[y0:y1, x0:x1] = 255
    else:
        mask[y0:y1, x0:x1] |= ((bright[y0:y1, x0:x1] > 140) * 255).astype(np.uint8)
mask = cv2.dilate(mask, np.ones((7, 7), np.uint8))
clean = cv2.inpaint(src, mask, 9, cv2.INPAINT_TELEA)

# círculo do mostrador na referência: centro (333, 329); raio 314 corta a borda preta
CX, CY, R = 333, 329, 314
crop = clean[CY - R:CY + R, CX - R:CX + R]
cv2.imwrite(os.path.join(HERE, "background_clean.png"), crop)
print("gerado background_clean.png", crop.shape[1], "x", crop.shape[0])
