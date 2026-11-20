#!/usr/bin/env python3
"""Gera todas as imagens do mostrador Forest Green.

Uso:  python3 faces/forest-green/art/generate_images.py
Saída: faces/forest-green/src/main/res/drawable-nodpi/*.png

Camadas (de baixo para cima, igual ao watchface.xml):
  background.png  folhagem verde escura (some no modo ambiente)
  (arco da meta diária — desenhado pelo próprio relógio, PartDraw)
  dial.png        marcações + números 12/3/6/9 (ficam por cima do arco)
  ícones, ponteiros e preview.png

Tudo é desenhado em SS x de resolução e reduzido (anti-aliasing).
O preview.png também desenha os textos/dados de exemplo nas MESMAS posições
do watchface.xml (constantes abaixo), para a galeria ficar fiel ao relógio.
"""
import math
import os
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

SIZE = 450
SS = 4
C = SIZE / 2

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "src", "main", "res", "drawable-nodpi")
os.makedirs(OUT, exist_ok=True)

NUM_FONT = os.path.join(HERE, "RussoOne-Regular.ttf")       # mesmo arquivo de res/font
TXT_FONT = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"  # só para o preview

WHITE = (255, 255, 255, 255)
ACCENT = (139, 224, 74, 255)    # verde-limão padrão (#ff8be04a)

# Arco da meta diária (tem que bater com o watchface.xml)
ARC_R = 192                     # raio externo; no XML o Arc tem diâmetro 2*(192-5.5) = 373
ARC_START, ARC_END = 120, 240   # graus, 0 = 12h, sentido horário (4h -> 6h -> 8h)
ARC_W = 11


def save(img, name):
    img = img.resize((img.width // SS, img.height // SS), Image.LANCZOS)
    img.save(os.path.join(OUT, name), optimize=True)
    print("gerado", name, img.size)
    return img


def polar(r, deg, scale=SS):
    a = math.radians(deg)
    return (C * scale + r * scale * math.sin(a), C * scale - r * scale * math.cos(a))


# ------------------------------------------------------------- folhagem
PALETTE = [(22, 64, 34), (30, 84, 40), (40, 104, 46), (52, 120, 50), (70, 138, 58),
           (18, 52, 30), (34, 92, 52), (88, 150, 64)]


def leaf(d, x, y, length, width, ang, color):
    """Folha pontuda (dois arcos) com nervura central."""
    pts = []
    n = 14
    for i in range(n + 1):
        t = i / n
        pts.append((t * length, math.sin(math.pi * t) ** 0.8 * width / 2))
    for i in range(n, -1, -1):
        t = i / n
        pts.append((t * length, -math.sin(math.pi * t) ** 0.8 * width / 2))
    ca, sa = math.cos(ang), math.sin(ang)
    poly = [(x + px * ca - py * sa, y + px * sa + py * ca) for px, py in pts]
    d.polygon(poly, fill=color)
    dark = tuple(max(0, int(c * 0.65)) for c in color[:3]) + (color[3],)
    d.line([(x, y), (x + length * 0.9 * ca, y + length * 0.9 * sa)], fill=dark, width=max(1, int(SS * 0.6)))


def cluster(d, cx, cy, radius, count, rnd):
    """Copa de árvore vista de cima: muitas folhas, mais claras no topo-esquerda."""
    for _ in range(count):
        r = radius * math.sqrt(rnd.random())
        a = rnd.random() * 2 * math.pi
        x, y = cx + r * math.cos(a), cy + r * math.sin(a)
        light = 1 - r / radius * 0.55 + (-(x - cx) - (y - cy)) / radius * 0.15
        base = rnd.choice(PALETTE)
        col = tuple(max(0, min(255, int(c * (0.42 + 0.5 * light)))) for c in base) + (255,)
        ln = rnd.uniform(5, 13) * SS
        leaf(d, x, y, ln, ln * rnd.uniform(0.35, 0.55), rnd.random() * 2 * math.pi, col)


def fern(d, x0, y0, length, ang, curve, color, rnd):
    """Fronde de samambaia: haste curva com folíolos dos dois lados."""
    steps = 40
    pts = []
    for i in range(steps + 1):
        t = i / steps
        a = ang + curve * t
        if i == 0:
            pts.append((x0, y0, a))
        else:
            px, py, _ = pts[-1]
            seg = length / steps
            pts.append((px + seg * math.cos(a), py + seg * math.sin(a), a))
    d.line([(p[0], p[1]) for p in pts], fill=color, width=int(1.5 * SS))
    for i in range(2, steps, 2):
        t = i / steps
        px, py, a = pts[i]
        ln = length * 0.22 * math.sin(math.pi * (0.15 + 0.85 * t)) * (1.1 - t * 0.5)
        for side in (-1, 1):
            leaf(d, px, py, ln, ln * 0.32, a + side * 1.05, color)


def make_background():
    s = SIZE * SS
    rnd = random.Random(42)

    # fundo: verde-garrafa, um pouco mais claro no centro
    img = Image.new("RGBA", (SIZE, SIZE))
    px = img.load()
    for y in range(SIZE):
        for x in range(SIZE):
            r = math.hypot(x - C, y - C) / C
            k = 1 - 0.35 * r
            n = rnd.randint(-2, 2)
            px[x, y] = (int(16 * k) + n, int(48 * k) + n, int(30 * k) + n, 255)
    img = img.resize((s, s), Image.BICUBIC)

    # samambaias escuras, em relevo, por baixo de tudo
    ferns = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    fd = ImageDraw.Draw(ferns)
    for (x, y, ln, a, cv) in [(300, 420, 150, -1.9, 0.5), (360, 360, 120, -2.4, 0.4),
                              (250, 300, 90, -0.6, -0.4), (330, 120, 100, 2.2, 0.4),
                              (120, 140, 80, 0.5, 0.5), (200, 430, 110, -1.3, -0.3)]:
        fern(fd, x * SS, y * SS, ln * SS, a, cv, (34, 78, 46, 255), rnd)
    shadow = ferns.split()[3].filter(ImageFilter.GaussianBlur(3 * SS))
    shadow_img = Image.new("RGBA", (s, s), (4, 14, 8, 255))
    shadow_img.putalpha(shadow.point(lambda v: int(v * 0.8)))
    img.alpha_composite(shadow_img, (2 * SS, 3 * SS))
    img.alpha_composite(ferns)

    # copas de árvores nas bordas (deixa o miolo livre para os dados)
    trees = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    td = ImageDraw.Draw(trees)
    for (x, y, r, n) in [(95, 70, 55, 700), (150, 40, 40, 400), (40, 150, 45, 500),
                         (345, 75, 50, 650), (410, 140, 45, 500), (300, 30, 35, 300),
                         (25, 255, 50, 600), (40, 345, 55, 650), (100, 395, 45, 450),
                         (70, 205, 30, 300), (420, 330, 35, 350)]:
        cluster(td, x * SS, y * SS, r * SS, n, rnd)
    sh = trees.split()[3].filter(ImageFilter.GaussianBlur(5 * SS))
    shadow_img = Image.new("RGBA", (s, s), (2, 10, 5, 255))
    shadow_img.putalpha(sh.point(lambda v: int(v * 0.85)))
    img.alpha_composite(shadow_img, (4 * SS, 6 * SS))
    img.alpha_composite(trees)

    # escurece o miolo e a borda para os textos lerem bem
    mask = Image.new("L", (SIZE, SIZE))
    mp = mask.load()
    for y in range(SIZE):
        for x in range(SIZE):
            r = math.hypot(x - C, y - C) / C
            center = max(0.0, 1 - r / 0.62) ** 1.3 * 120
            edge = max(0.0, (r - 0.9) / 0.1) * 140
            mp[x, y] = int(min(255, center + edge))
    mask = mask.resize((s, s), Image.BICUBIC)
    dark = Image.new("RGBA", (s, s), (8, 26, 16, 255))
    dark.putalpha(mask)
    img.alpha_composite(dark)
    return save(img, "background.png")


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
        # sombra suave para destacar da folhagem
        sh = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((x * SS, y * SS + 3 * SS), txt, font=font, fill=(0, 0, 0, 170), anchor="mm")
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


# --------------------------------------------------------------------- ícones
def make_icons():
    # bateria: só o contorno + polo (o nível é um retângulo no XML) — 34x18
    w, h = 34, 18
    img = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([1 * SS, 1 * SS, 30 * SS, 17 * SS], radius=3 * SS, outline=WHITE, width=2 * SS)
    d.rounded_rectangle([30 * SS, 6 * SS, 33 * SS, 12 * SS], radius=1 * SS, fill=WHITE)
    save(img, "icon_battery.png")

    # pessoa caminhando — 24x28
    w, h = 24, 28
    img = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    L = lambda pts, wd=3.2: d.line([(x * SS, y * SS) for x, y in pts], fill=WHITE, width=int(wd * SS), joint="curve")
    d.ellipse([12 * SS, 0.5 * SS, 17 * SS, 5.5 * SS], fill=WHITE)
    L([(13.5, 8), (11, 17)], 3.6)                   # tronco
    L([(11, 17), (14.5, 21), (14, 27)])             # perna da frente
    L([(11, 17), (8.5, 22), (4, 26)])               # perna de trás
    L([(13.2, 9), (17.5, 13), (20.5, 14)], 2.6)     # braço da frente
    L([(13, 9.5), (9, 12), (7, 16)], 2.6)           # braço de trás
    save(img, "icon_walk.png")


# -------------------------------------------------------------------- preview
def make_preview(bg, dial):
    """Mostrador às 10:08:36 com dados de exemplo (só para a galeria)."""
    big = Image.new("RGBA", (SIZE * SS, SIZE * SS))
    big.alpha_composite(bg.resize(big.size, Image.BICUBIC))
    d = ImageDraw.Draw(big, "RGBA")

    # arco: trilho + progresso (64%)
    box = [(C - ARC_R) * SS, (C - ARC_R) * SS, (C + ARC_R) * SS, (C + ARC_R) * SS]
    pil = lambda a: a - 90                          # PIL: 0° = 3h
    track = Image.new("RGBA", big.size, (0, 0, 0, 0))
    ImageDraw.Draw(track).arc(box, pil(ARC_START), pil(ARC_END), fill=WHITE, width=ARC_W * SS)
    track.putalpha(track.split()[3].point(lambda v: v * 50 // 255))
    big.alpha_composite(track)
    pct = 0.64
    start = ARC_END - (ARC_END - ARC_START) * pct
    d.arc(box, pil(start), pil(ARC_END), fill=ACCENT, width=ARC_W * SS)
    for a in (start, ARC_END):                      # pontas arredondadas
        x, y = polar(ARC_R - ARC_W / 2 + 0.5, a)
        d.ellipse([x - ARC_W * SS / 2, y - ARC_W * SS / 2, x + ARC_W * SS / 2, y + ARC_W * SS / 2], fill=ACCENT)

    big.alpha_composite(dial.resize(big.size, Image.BICUBIC))
    d = ImageDraw.Draw(big)

    def text(x, y, s, size, color=WHITE, anchor="mm"):
        d.text((x * SS, y * SS), s, font=ImageFont.truetype(TXT_FONT, size * SS), fill=color, anchor=anchor)

    def icon(name, x, y, w, h, color):
        ic = Image.open(os.path.join(OUT, name)).convert("RGBA").resize((w * SS, h * SS), Image.LANCZOS)
        tint = Image.new("RGBA", ic.size, color)
        tint.putalpha(ic.split()[3])
        big.alpha_composite(tint, (int(x * SS), int(y * SS)))

    # clima (complicação)
    cloud = Image.new("RGBA", (26 * SS, 26 * SS), (0, 0, 0, 0))
    cd = ImageDraw.Draw(cloud)
    cd.ellipse([13 * SS, 2 * SS, 23 * SS, 12 * SS], fill=(255, 206, 60, 255))
    for bx in ([2, 10, 14, 22], [8, 6, 20, 18], [14, 10, 24, 22]):
        cd.ellipse([v * SS for v in bx], fill=WHITE)
    cd.rectangle([6 * SS, 16 * SS, 20 * SS, 22 * SS], fill=WHITE)
    big.alpha_composite(cloud, (WX * SS + 0, (WY + 2) * SS))
    text(WX + 32, WY + 15, "22°", 26, anchor="lm")
    text(WX + 58, WY + 44, "Nublado", 17)

    # bateria
    icon("icon_battery.png", BX - 17, BY, 34, 18, ACCENT)
    d.rectangle([(BX - 13) * SS, (BY + 4) * SS, (BX - 13 + 22 * 0.78) * SS, (BY + 14) * SS], fill=ACCENT)
    text(BX, BY + 40, "78%", 26)
    text(BX, BY + 66, "Bateria", 17)

    # passos
    icon("icon_walk.png", SX - 12, SY, 24, 28, ACCENT)
    text(SX, SY + 48, "8423", 26)
    text(SX, SY + 74, "Passos", 17)

    # meta diária
    text(GX, GY + 13, "64%", 26, ACCENT)
    text(GX, GY + 39, "META DIÁRIA", 15)

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
    pd.ellipse([C - 2.5, C - 2.5, C + 2.5, C + 2.5], fill=(20, 50, 32, 255))

    mask = Image.new("L", (SIZE * SS, SIZE * SS), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, SIZE * SS - 1, SIZE * SS - 1], fill=255)
    prev.putalpha(mask.resize((SIZE, SIZE), Image.LANCZOS))
    prev.save(os.path.join(OUT, "preview.png"), optimize=True)
    print("gerado preview.png")


# Posições dos blocos de dados (canto superior esquerdo / centro) — iguais ao XML
WX, WY = 104, 176     # clima: caixa 140x60 a partir daqui
BX, BY = 318, 178     # bateria: centro x, topo do ícone
SX, SY = 140, 262     # passos: centro x, topo do ícone
GX, GY = 268, 268     # meta diária: centro x, topo do bloco

if __name__ == "__main__":
    bg = make_background()
    dial = make_dial()
    make_hands()
    make_icons()
    make_preview(bg, dial)
