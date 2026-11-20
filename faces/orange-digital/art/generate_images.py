#!/usr/bin/env python3
"""Gera as imagens do mostrador Orange Digital (raio da bateria e preview).

Uso:   python faces/orange-digital/art/generate_images.py
Saída: faces/orange-digital/src/main/res/drawable-nodpi/*.png

O preview reproduz o layout do watchface.xml (mesmas coordenadas) com dados de exemplo.
"""
import math
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "src", "main", "res")
OUT = os.path.join(RES, "drawable-nodpi")
FONT = os.path.join(RES, "font", "bebas_neue.ttf")
os.makedirs(OUT, exist_ok=True)

SS = 4                                  # supersampling (bordas suaves)
WHITE = (255, 255, 255, 255)
ORANGE = (255, 140, 26, 255)
DIM = (255, 255, 255, 128)


def canvas(w, h):
    img = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def save(img, name):
    img = img.resize((img.width // SS, img.height // SS), Image.LANCZOS)
    img.save(os.path.join(OUT, name))
    print("gerado", name, img.size)
    return img


def s(*v):
    """Converte coordenadas lógicas para a escala de supersampling."""
    return [x * SS for x in v]


# ------------------------------------------------------------------ ícones
def sun_shape(d, cx, cy, r, color, rays=True):
    d.ellipse(s(cx - r, cy - r, cx + r, cy + r), fill=color)
    if rays:
        for i in range(8):
            a = math.radians(i * 45)
            p1 = (cx + (r + 3) * math.cos(a), cy + (r + 3) * math.sin(a))
            p2 = (cx + (r + 7) * math.cos(a), cy + (r + 7) * math.sin(a))
            d.line(s(*p1, *p2), fill=color, width=2 * SS)


def make_bolt():
    # branco: o watchface.xml pinta com a cor de destaque (tintColor)
    img, d = canvas(18, 30)
    pts = (11, 1, 2, 16, 9, 16, 7, 29, 16, 12, 9, 12)
    d.polygon(s(*pts), fill=WHITE)
    save(img, "icon_bolt.png")


# ------------------------------------------------------------------ preview
def make_preview():
    """Imagem da galeria. Coordenadas iguais às do watchface.xml."""
    S = 450
    img, d = canvas(S, S)
    d.ellipse(s(0, 0, S - 1, S - 1), fill=(0, 0, 0, 255))

    def text(x, y, w, size, txt, color, align="START"):
        # mesma regra do XML: topo das letras = y + 0.18 * size; baseline = topo + 0.7 * size
        f = ImageFont.truetype(FONT, size * SS)
        base = (y + 0.18 * size + 0.7 * size) * SS
        if align == "END":
            d.text(((x + w) * SS, base), txt, font=f, fill=color, anchor="rs")
        else:
            d.text((x * SS, base), txt, font=f, fill=color, anchor="ls")

    def paste(name, x, y, tint=None):
        icon = Image.open(os.path.join(OUT, name)).convert("RGBA")
        if tint:
            solid = Image.new("RGBA", icon.size, tint)
            solid.putalpha(icon.getchannel("A"))
            icon = solid
        icon = icon.resize((icon.width * SS, icon.height * SS), Image.LANCZOS)
        img.alpha_composite(icon, (x * SS, y * SS))

    text(96, 40, 240, 34, "AGOSTO 22", WHITE)
    text(88, 70, 240, 54, "TERÇA-FEIRA", ORANGE)
    sun_shape(d, 267, 58, 6, WHITE)                        # exemplo: ícone do clima
    text(286, 40, 86, 34, "31°", WHITE)
    paste("icon_bolt.png", 88, 141, ORANGE)
    text(110, 132, 84, 46, "82%", WHITE)
    text(8, 149, 200, 215, "16", WHITE, "END")
    text(230, 89, 216, 238, "02", ORANGE)
    d.rectangle(s(198, 141, 201, 173), fill=DIM)
    d.rectangle(s(214, 226, 224, 236), fill=WHITE)
    d.rectangle(s(214, 272, 224, 282), fill=WHITE)
    d.rectangle(s(227, 346, 230, 410), fill=DIM)

    # complicações de exemplo (passos e batimentos)
    text(100, 346, 122, 28, "STEPS", ORANGE)
    text(100, 372, 122, 46, "1734", WHITE)
    text(240, 306, 150, 28, "BPM", ORANGE)
    text(240, 332, 150, 46, "101", WHITE)

    save(img, "preview.png")


if __name__ == "__main__":
    make_bolt()
    make_preview()
