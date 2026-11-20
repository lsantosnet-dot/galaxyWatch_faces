#!/usr/bin/env python3
"""Gera todas as imagens do mostrador Forest Green.

Uso:  python3 faces/forest-green/art/generate_images.py
Saída: faces/forest-green/src/main/res/drawable-nodpi/*.png

Camadas (de baixo para cima, igual ao watchface.xml):
  background.png  degradê verde-escuro com névoa (some no modo ambiente)
  (arco decorativo — desenhado pelo próprio relógio, PartDraw)
  dial.png        marcações + números 12/3/6/9 (ficam por cima do arco)
  4 complicações editáveis, ponteiros e preview.png

Tudo é desenhado em SS x de resolução e reduzido (anti-aliasing).
O preview.png desenha dados de exemplo nas MESMAS posições do watchface.xml
(constantes abaixo), para a galeria ficar fiel ao relógio.
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

SIZE = 450
SS = 4
C = SIZE / 2

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "src", "main", "res", "drawable-nodpi")
os.makedirs(OUT, exist_ok=True)

NUM_FONT = os.path.join(HERE, "RussoOne-Regular.ttf")            # números (ficam no dial.png)
TXT_FONT = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"  # só para o preview

WHITE = (255, 255, 255, 255)
ACCENT = (139, 224, 74, 255)    # verde-limão padrão (#ff8be04a)

# Arco decorativo fixo (tem que bater com o watchface.xml)
ARC_R = 192                     # raio externo; no XML o Arc tem diâmetro 2*(192-5.5) = 373
ARC_START, ARC_END = 110, 250   # graus, 0 = 12h, sentido horário; simétrico em volta do 6
ARC_W = 11

# 4 complicações: (centro x, topo). Caixa de 120x80 começando em (cx-60, topo).
SLOTS = {
    "TOP_LEFT": (155, 148),
    "TOP_RIGHT": (295, 148),
    "BOTTOM_LEFT": (155, 258),
    "BOTTOM_RIGHT": (295, 258),
}


def save(img, name):
    img = img.resize((img.width // SS, img.height // SS), Image.LANCZOS)
    img.save(os.path.join(OUT, name), optimize=True)
    print("gerado", name, img.size)
    return img


def polar(r, deg, scale=SS):
    a = math.radians(deg)
    return (C * scale + r * scale * math.sin(a), C * scale - r * scale * math.cos(a))


# ------------------------------------------------------------- fundo: névoa
def make_background():
    """Degradê radial verde-escuro + manchas de névoa verde bem desfocadas."""
    rnd = random.Random(7)
    img = Image.new("RGBA", (SIZE, SIZE))
    px = img.load()
    for y in range(SIZE):
        for x in range(SIZE):
            # centro de luz um pouco acima do meio, escurecendo para a borda
            r = min(1.0, math.hypot(x - C, (y - C * 0.85) * 1.1) / (C * 1.05))
            k = (1 - r) ** 1.6
            px[x, y] = (int(6 + 20 * k), int(22 + 52 * k), int(14 + 30 * k), 255)

    # névoa: nuvens grandes, translúcidas, desfocadas
    fog = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fog)
    for _ in range(34):
        cx, cy = rnd.uniform(30, 420), rnd.uniform(40, 420)
        rx, ry = rnd.uniform(50, 120), rnd.uniform(25, 60)
        g = rnd.randint(80, 150)
        fd.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(int(g * 0.45), g, int(g * 0.6), rnd.randint(30, 62)))
    fog = fog.filter(ImageFilter.GaussianBlur(28))
    img.alpha_composite(fog)

    # vinheta na borda + granulado leve (evita "degraus" no degradê)
    vig = Image.new("L", (SIZE, SIZE))
    vp = vig.load()
    for y in range(SIZE):
        for x in range(SIZE):
            r = math.hypot(x - C, y - C) / C
            vp[x, y] = int(max(0.0, min(1.0, (r - 0.72) / 0.28)) ** 1.5 * 200)
    dark = Image.new("RGBA", (SIZE, SIZE), (3, 12, 7, 255))
    dark.putalpha(vig)
    img.alpha_composite(dark)
    px = img.load()
    for y in range(SIZE):
        for x in range(SIZE):
            r, g, b, a = px[x, y]
            n = rnd.randint(-1, 1)
            px[x, y] = (max(0, r + n), max(0, g + n), max(0, b + n), a)

    img.save(os.path.join(OUT, "background.png"), optimize=True)
    print("gerado background.png", img.size)
    return img


# ------------------------------------------------------- marcações e números
NUMBERS = {  # número: (centro x, centro y, tamanho da fonte) na tela de 450
    "12": (225, 88, 92),
    "3": (380, 225, 92),
    "6": (225, 366, 92),
    "9": (70, 225, 92),
}


def make_dial():
    s = SIZE * SS
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i in range(60):
        deg = i * 6
        if i % 15 == 0:
            continue                                   # lugar dos números grandes
        if i % 5 == 0:
            d.line([polar(203, deg), polar(219, deg)], fill=WHITE, width=int(2.6 * SS))
        else:
            d.line([polar(213, deg), polar(219, deg)], fill=(255, 255, 255, 150), width=int(1.1 * SS))

    for txt, (x, y, size) in NUMBERS.items():
        font = ImageFont.truetype(NUM_FONT, size * SS)
        sh = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((x * SS, y * SS + 3 * SS), txt, font=font, fill=(0, 0, 0, 150), anchor="mm")
        img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(4 * SS)))
        d.text((x * SS, y * SS), txt, font=font, fill=WHITE, anchor="mm")
    return save(img, "dial.png")


# ------------------------------------------------------------------ ponteiros
def make_hand(name, w, length, tail, base_w, tip_w, color):
    """Ponteiro apontando para cima; pivô a `length` px do topo."""
    img = Image.new("RGBA", (w * SS, (length + tail) * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, py = w * SS / 2, length * SS
    d.polygon([(cx - tip_w * SS / 2, 0), (cx + tip_w * SS / 2, 0),
               (cx + base_w * SS / 2, py), (cx + base_w * SS / 2, py + tail * SS),
               (cx - base_w * SS / 2, py + tail * SS), (cx - base_w * SS / 2, py)], fill=color)
    return save(img, name)


def make_hands():
    make_hand("hour_hand.png", 12, 118, 16, 5, 3, WHITE)
    make_hand("minute_hand.png", 12, 188, 18, 4.4, 2.4, WHITE)
    make_hand("second_hand.png", 12, 205, 34, 2.2, 1.6, (235, 235, 235, 255))


# ------------------------------------- ícones de exemplo (só para o preview)
def sample_icon(kind):
    """No relógio o ícone vem do provedor da complicação; aqui é só ilustração."""
    w = 24 * SS
    img = Image.new("RGBA", (w, w), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    S = lambda *v: [x * SS for x in v]
    if kind == "weather":
        for b in ((1, 11, 11, 21), (6, 4, 17, 15), (13, 9, 23, 19)):
            d.ellipse(S(*b), fill=WHITE)
        d.rectangle(S(6, 14, 18, 21), fill=WHITE)
    elif kind == "battery":
        d.rounded_rectangle(S(1, 6, 21, 18), radius=2 * SS, outline=WHITE, width=2 * SS)
        d.rectangle(S(21, 10, 23, 14), fill=WHITE)
        d.rectangle(S(4, 9, 15, 15), fill=WHITE)
    elif kind == "steps":
        L = lambda pts, wd=3: d.line([(x * SS, y * SS) for x, y in pts], fill=WHITE, width=int(wd * SS), joint="curve")
        d.ellipse(S(12, 0, 16.5, 4.5), fill=WHITE)
        L([(13.5, 7), (11, 15)], 3.4)
        L([(11, 15), (14, 19), (13.5, 24)])
        L([(11, 15), (8.5, 19.5), (4.5, 23)])
        L([(13.2, 8), (17, 11.5), (19.5, 12.5)], 2.4)
        L([(13, 8.5), (9.5, 10.5), (7.5, 14)], 2.4)
    elif kind == "heart":
        d.ellipse(S(2, 3, 13, 14), fill=WHITE)
        d.ellipse(S(11, 3, 22, 14), fill=WHITE)
        d.polygon(S(2.6, 11, 21.4, 11, 12, 22), fill=WHITE)
    tint = Image.new("RGBA", img.size, ACCENT)
    tint.putalpha(img.split()[3])
    return tint


# -------------------------------------------------------------------- preview
PREVIEW_DATA = {  # slot: (ícone, valor, título) — os padrões do watchface.xml
    "TOP_LEFT": ("weather", "22°", "Nublado"),
    "TOP_RIGHT": ("battery", "78%", "Bateria"),
    "BOTTOM_LEFT": ("steps", "8423", "Passos"),
    "BOTTOM_RIGHT": ("heart", "72", "BPM"),
}


def make_preview(bg, dial):
    """Mostrador às 10:08:36 com dados de exemplo (só para a galeria)."""
    big = Image.new("RGBA", (SIZE * SS, SIZE * SS))
    big.alpha_composite(bg.resize(big.size, Image.BICUBIC))

    # arco decorativo fixo, pontas arredondadas
    arc = Image.new("RGBA", big.size, (0, 0, 0, 0))
    ad = ImageDraw.Draw(arc)
    box = [(C - ARC_R) * SS, (C - ARC_R) * SS, (C + ARC_R) * SS, (C + ARC_R) * SS]
    ad.arc(box, ARC_START - 90, ARC_END - 90, fill=ACCENT, width=ARC_W * SS)
    for a in (ARC_START, ARC_END):
        x, y = polar(ARC_R - ARC_W / 2 + 0.5, a)
        ad.ellipse([x - ARC_W * SS / 2, y - ARC_W * SS / 2, x + ARC_W * SS / 2, y + ARC_W * SS / 2], fill=ACCENT)
    big.alpha_composite(arc)

    big.alpha_composite(dial.resize(big.size, Image.BICUBIC))
    d = ImageDraw.Draw(big)

    def text(x, y, s, size, color=WHITE):
        d.text((x * SS, y * SS), s, font=ImageFont.truetype(TXT_FONT, size * SS), fill=color, anchor="mm")

    for slot, (cx, top) in SLOTS.items():
        kind, value, title = PREVIEW_DATA[slot]
        big.alpha_composite(sample_icon(kind), (int((cx - 12) * SS), int(top * SS)))
        text(cx, top + 42.5, value, 26)
        text(cx, top + 69.5, title, 17)

    prev = big.resize((SIZE, SIZE), Image.LANCZOS)

    def compose(name, deg, length):
        hand = Image.open(os.path.join(OUT, name)).convert("RGBA")
        canvas = Image.new("RGBA", (SIZE * 2, SIZE * 2), (0, 0, 0, 0))
        canvas.paste(hand, (SIZE - hand.width // 2, SIZE - length), hand)
        canvas = canvas.rotate(-deg, resample=Image.BICUBIC, center=(SIZE, SIZE))
        prev.alpha_composite(canvas.crop((SIZE // 2, SIZE // 2, SIZE + SIZE // 2, SIZE + SIZE // 2)))

    h, m, s = 10, 8, 36
    compose("hour_hand.png", (h % 12 + m / 60) * 30, 118)
    compose("minute_hand.png", (m + s / 60) * 6, 188)
    compose("second_hand.png", s * 6, 205)
    pd = ImageDraw.Draw(prev)
    pd.ellipse([C - 6, C - 6, C + 6, C + 6], fill=WHITE)
    pd.ellipse([C - 3, C - 3, C + 3, C + 3], fill=(20, 50, 32, 255))

    mask = Image.new("L", (SIZE * SS, SIZE * SS), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, SIZE * SS - 1, SIZE * SS - 1], fill=255)
    prev.putalpha(mask.resize((SIZE, SIZE), Image.LANCZOS))
    prev.save(os.path.join(OUT, "preview.png"), optimize=True)
    print("gerado preview.png")


if __name__ == "__main__":
    for old in ("icon_battery.png", "icon_walk.png"):   # não são mais usados
        p = os.path.join(OUT, old)
        if os.path.exists(p):
            os.remove(p)
    bg = make_background()
    dial = make_dial()
    make_hands()
    make_preview(bg, dial)
