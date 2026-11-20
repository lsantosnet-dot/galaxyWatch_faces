#!/usr/bin/env python3
"""Gera as imagens do mostrador Space Cruiser (fundo e preview).

Uso:   python faces/space-cruiser/art/generate_images.py     (requer Pillow)
Entrada: art/background_clean.png (arte sem textos; ver clean_background.py)
Saída:   src/main/res/drawable-nodpi/background.png e preview.png

O preview reproduz o layout do watchface.xml (mesmas coordenadas) com dados de exemplo.
"""
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "src", "main", "res")
OUT = os.path.join(RES, "drawable-nodpi")
FONTS = os.path.join(RES, "font")
os.makedirs(OUT, exist_ok=True)

S = 450
SS = 4  # supersampling do preview


def make_background():
    bg = Image.open(os.path.join(HERE, "background_clean.png")).convert("RGB")
    bg = bg.resize((S, S), Image.LANCZOS)
    bg.save(os.path.join(OUT, "background.png"), optimize=True)
    print("gerado background.png", os.path.getsize(os.path.join(OUT, "background.png")) // 1024, "KB")
    return bg


def make_preview(bg):
    img = bg.convert("RGBA").resize((S * SS, S * SS), Image.LANCZOS)
    d = ImageDraw.Draw(img)

    def text(x, y, w, size, txt, color, font, align="CENTER"):
        # mesma regra do XML: baseline = y + 0.96875 * size (ascendente da Inter)
        f = ImageFont.truetype(os.path.join(FONTS, font + ".ttf"), size * SS)
        base = (y + 0.96875 * size) * SS
        if align == "CENTER":
            d.text(((x + w / 2) * SS, base), txt, font=f, fill=color, anchor="ms")
        else:
            d.text((x * SS, base), txt, font=f, fill=color, anchor="ls")

    text(0, 36, 450, 104, "10:08", "#ffffff", "inter_regular")
    text(75, 145, 300, 21, "qui. • 14 nov.", "#e4e7f0", "inter_caps")

    # esquerda: passos
    ox, oy = 10, 164
    d.ellipse([(ox + 30) * SS, (oy + 2) * SS, (ox + 74) * SS, (oy + 46) * SS],
              fill=(28, 34, 48, 204), outline=(255, 255, 255, 64), width=SS)
    for fx, fy in ((46, 14), (56, 22)):                      # pegadas simples
        d.ellipse([(ox + fx) * SS, (oy + fy) * SS, (ox + fx + 6) * SS, (oy + fy + 11) * SS], fill="#a8dbff")
    text(ox, oy + 51, 104, 13, "passos", "#b4c8dc", "inter_caps")
    text(ox, oy + 65, 104, 30, "1.247", "#a8dbff", "inter_medium")

    # direita: clima (sol + nuvem simples)
    ox = 336
    d.ellipse([(ox + 38) * SS, (oy + 8) * SS, (ox + 58) * SS, (oy + 28) * SS], fill="#ffc53d")
    for cx, cy, r in ((52, 30, 9), (62, 26, 11), (72, 31, 8)):
        d.ellipse([(ox + cx - r) * SS, (oy + cy - r) * SS, (ox + cx + r) * SS, (oy + cy + r) * SS], fill="#f2f4f8")
    text(ox, oy + 51, 104, 13, "ensolarado", "#e6d6c0", "inter_caps")
    text(ox, oy + 65, 104, 30, "24°", "#ffc37a", "inter_medium")

    # embaixo: bateria
    ox, oy = 165, 366
    d.rounded_rectangle([(ox + 30) * SS, (oy + 7) * SS, (ox + 46) * SS, (oy + 16) * SS],
                        radius=2 * SS, outline="#7ee081", width=SS)
    d.rectangle([(ox + 32) * SS, (oy + 9) * SS, (ox + 42) * SS, (oy + 14) * SS], fill="#7ee081")
    text(ox + 52, oy, 68, 18, "78%", "#e4e7f0", "inter_medium", "START")
    text(ox, oy + 24, 120, 11, "bateria", "#b4bccc", "inter_caps")

    img = img.resize((S, S), Image.LANCZOS)
    mask = Image.new("L", (S * SS, S * SS), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, S * SS - 1, S * SS - 1], fill=255)
    img.putalpha(mask.resize((S, S), Image.LANCZOS))
    img.save(os.path.join(OUT, "preview.png"), optimize=True)
    print("gerado preview.png")


if __name__ == "__main__":
    make_preview(make_background())
