#!/usr/bin/env python3
"""Gera todas as imagens do watch face (mostrador, ponteiros, ícones e preview).

Uso:  python3 faces/classic/art/generate_images.py
Saída: faces/classic/src/main/res/drawable-nodpi/*.png

Tudo é desenhado com Pillow em 4x de resolução e reduzido (supersampling)
para ficar com bordas suaves (anti-aliasing).
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

SIZE = 450            # resolução lógica do watch face (WFF usa 450x450)
SS = 4                # fator de supersampling
C = SIZE / 2          # centro

OUT = os.path.join(os.path.dirname(__file__), "..", "src", "main", "res", "drawable-nodpi")
os.makedirs(OUT, exist_ok=True)

FONT_PATH = "/usr/share/fonts/opentype/inter/Inter-ExtraLight.otf"
INK = (52, 52, 56, 255)       # cinza escuro dos números/ticks
RED = (214, 40, 40, 255)      # vermelho dos números 12/3/6/9 e ponteiro dos segundos
BLACK = (18, 18, 20, 255)


def save(img, name):
    img = img.resize((img.width // SS, img.height // SS), Image.LANCZOS)
    img.save(os.path.join(OUT, name))
    print("gerado", name, img.size)


def polar(r, deg):
    """Ponto a r pixels do centro; 0° = 12h, sentido horário."""
    a = math.radians(deg)
    return (C * SS + r * SS * math.sin(a), C * SS - r * SS * math.cos(a))


# ---------------------------------------------------------------- mostrador
def make_dial():
    s = SIZE * SS
    # fundo: gradiente diagonal creme -> cinza-claro (simula o brilho do vidro)
    base = Image.new("RGBA", (SIZE, SIZE))
    px = base.load()
    random.seed(7)
    for y in range(SIZE):
        for x in range(SIZE):
            t = (x + y) / (2 * SIZE)                    # 0..1 na diagonal
            v = 228 - 22 * t                            # claro no canto sup. esquerdo
            n = random.randint(-3, 3)                   # leve granulado de papel
            px[x, y] = (int(v + n), int(v - 2 + n), int(v - 9 + n), 255)
    img = base.resize((s, s), Image.BICUBIC)
    d = ImageDraw.Draw(img)

    # marcações dos minutos (60) e das horas (12)
    for i in range(60):
        deg = i * 6
        if i % 5 == 0:
            p1, p2, w = polar(205, deg), polar(219, deg), 2.2
        else:
            p1, p2, w = polar(212, deg), polar(219, deg), 1.0
        d.line([p1, p2], fill=INK, width=int(w * SS))

    # números
    font = ImageFont.truetype(FONT_PATH, 50 * SS)
    for h in range(1, 13):
        deg = h * 30
        color = RED if h % 3 == 0 else INK
        cx, cy = polar(166, deg)
        d.text((cx, cy), str(h), font=font, fill=color, anchor="mm")

    save(img, "dial.png")


# ---------------------------------------------------------------- ponteiros
def hand_image(w, length, tail, shape, color, pivot_extra=0):
    """Ponteiro apontando para CIMA. A imagem tem altura length+tail; o pivô
    (centro do relógio) fica a `length` pixels do topo."""
    h = length + tail
    img = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = w * SS / 2
    py = length * SS
    d.polygon(shape(cx, py, w, length, tail), fill=color)
    return img


def tapered(base_w, tip_w):
    def shape(cx, py, w, length, tail):
        return [
            (cx - tip_w * SS / 2, 0), (cx + tip_w * SS / 2, 0),
            (cx + base_w * SS / 2, py - 10 * SS),
            (cx + base_w * SS / 3, py + tail * SS), (cx - base_w * SS / 3, py + tail * SS),
            (cx - base_w * SS / 2, py - 10 * SS),
        ]
    return shape


def make_hands():
    # hora: curto e largo, ponta afinada
    save(hand_image(24, 112, 22, tapered(18, 3), BLACK), "hour_hand.png")
    # minuto: longo e mais fino
    save(hand_image(20, 182, 26, tapered(14, 2), BLACK), "minute_hand.png")

    # segundos: haste vermelha fina + contrapeso + capa central
    length, tail, w = 205, 70, 20
    img = Image.new("RGBA", (w * SS, (length + tail) * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, py = w * SS / 2, length * SS
    d.rectangle([cx - 1.5 * SS, 0, cx + 1.5 * SS, py + tail * SS], fill=RED)
    d.ellipse([cx - 7 * SS, py - 7 * SS, cx + 7 * SS, py + 7 * SS], fill=RED)
    d.ellipse([cx - 2.5 * SS, py - 2.5 * SS, cx + 2.5 * SS, py + 2.5 * SS], fill=(255, 190, 190, 255))
    save(img, "second_hand.png")


# ------------------------------------------------------------------- ícones
def make_icons():
    # ícone nascer/pôr do sol: semicírculo + raios + horizonte
    w = h = 28
    img = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy = w * SS / 2, 18 * SS
    d.pieslice([cx - 7 * SS, cy - 7 * SS, cx + 7 * SS, cy + 7 * SS], 180, 360, fill=INK)
    for deg in (-60, -30, 0, 30, 60):
        a = math.radians(deg)
        p1 = (cx + 10 * SS * math.sin(a), cy - 10 * SS * math.cos(a))
        p2 = (cx + 14 * SS * math.sin(a), cy - 14 * SS * math.cos(a))
        d.line([p1, p2], fill=INK, width=2 * SS)
    d.line([(3 * SS, cy + 3 * SS), (25 * SS, cy + 3 * SS)], fill=INK, width=2 * SS)
    d.line([(8 * SS, cy + 8 * SS), (20 * SS, cy + 8 * SS)], fill=INK, width=2 * SS)
    save(img, "icon_sun.png")

    # raio da bateria
    w, h = 20, 28
    img = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pts = [(12, 1), (4, 15), (10, 15), (8, 27), (16, 11), (10, 11)]
    d.polygon([(x * SS, y * SS) for x, y in pts], fill=INK)
    save(img, "icon_bolt.png")


# ------------------------------------------------------------------ preview
def make_preview():
    """Imagem estática mostrada na galeria de watch faces (10:08:34)."""
    dial = Image.open(os.path.join(OUT, "dial.png")).convert("RGBA")
    prev = dial.copy()

    def paste_hand(name, deg, length):
        hand = Image.open(os.path.join(OUT, name)).convert("RGBA")
        canvas = Image.new("RGBA", (SIZE * 2, SIZE * 2), (0, 0, 0, 0))
        # coloca o pivô da mão no centro do canvas ampliado e gira em torno dele
        canvas.paste(hand, (SIZE - hand.width // 2, SIZE - length), hand)
        canvas = canvas.rotate(-deg, resample=Image.BICUBIC, center=(SIZE, SIZE))
        prev.alpha_composite(canvas, (-SIZE // 2, -SIZE // 2), (0, 0))

    # canvas é 2x maior que o dial; recorta a área central ao compor
    def compose(name, deg, length):
        hand = Image.open(os.path.join(OUT, name)).convert("RGBA")
        canvas = Image.new("RGBA", (SIZE * 2, SIZE * 2), (0, 0, 0, 0))
        canvas.paste(hand, (SIZE - hand.width // 2, SIZE - length), hand)
        canvas = canvas.rotate(-deg, resample=Image.BICUBIC, center=(SIZE, SIZE))
        crop = canvas.crop((SIZE - SIZE // 2, SIZE - SIZE // 2, SIZE + SIZE // 2, SIZE + SIZE // 2))
        prev.alpha_composite(crop)

    h, m, s = 10, 8, 34
    compose("hour_hand.png", (h % 12 + m / 60) * 30, 112)
    compose("minute_hand.png", (m + s / 60) * 6, 182)
    compose("second_hand.png", s * 6, 205)

    # recorte circular, como o relógio real
    mask = Image.new("L", (SIZE * SS, SIZE * SS), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, SIZE * SS - 1, SIZE * SS - 1], fill=255)
    mask = mask.resize((SIZE, SIZE), Image.LANCZOS)
    prev.putalpha(mask)
    prev.save(os.path.join(OUT, "preview.png"))
    print("gerado preview.png")


if __name__ == "__main__":
    make_dial()
    make_hands()
    make_icons()
    make_preview()
