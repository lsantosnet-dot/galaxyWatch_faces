#!/usr/bin/env python3
"""Gera todas as imagens do watch face Green Diver.

Uso:  python3 faces/green-diver/art/generate_images.py
Saída: faces/green-diver/src/main/res/drawable-nodpi/*.png

Camadas (de baixo para cima), todas 450x450 exceto os ponteiros:
  dial_<cor>.png     mostrador verde raio de sol (3 cores, escolhidas no relógio)
  bezel_<cor>.png    luneta de 60 minutos + anel de aço (2 cores)
  markers.png        trilha de minutos, índices de lume, moldura da janela dia/data e textos fixos
  aod_markers.png    índices brilhando em verde para o modo ambiente
  *_hand.png         ponteiros (aod_*_hand.png = versões do modo ambiente)
  preview.png        imagem da galeria (10:08:34)

Tudo é desenhado com Pillow em 4x de resolução e reduzido (supersampling).
"""
import math
import os
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

SIZE = 450
SS = 4
C = SIZE / 2

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "src", "main", "res")
OUT = os.path.join(RES, "drawable-nodpi")
os.makedirs(OUT, exist_ok=True)

FONT_BEZEL = os.path.join(HERE, "fonts", "BarlowCondensed-SemiBold.ttf")
FONT_TITLE = os.path.join(HERE, "fonts", "Archivo-Bold.ttf")
FONT_WINDOW = os.path.join(RES, "font", "barlow_condensed_bold.ttf")  # mesma fonte usada no XML

# cores
DIALS = {                      # cor base do mostrador (RGB)
    "floresta": (31, 80, 57),
    "esmeralda": (15, 92, 75),
    "oliva": (67, 76, 42),
}
BEZELS = {"preta": (17, 21, 19), "verde": (22, 58, 42)}
LUME = (238, 243, 226, 255)        # lume de dia (branco esverdeado)
LUME_AOD = (125, 255, 176, 255)    # lume brilhando no escuro
STEEL = (207, 214, 209, 255)
STEEL_DARK = (89, 98, 92, 255)
PRINT = (232, 238, 230, 255)       # tinta branca da luneta e do mostrador
ORANGE = (255, 106, 61, 255)

# janela dia/data às 3h (precisa bater com o watchface.xml)
WIN_X, WIN_Y, WIN_W, WIN_H, WIN_SPLIT = 314, 211, 74, 28, 44


def S(v):
    return v * SS


def save(img, name, downscale=True):
    if downscale:
        img = img.resize((img.width // SS, img.height // SS), Image.LANCZOS)
    img.save(os.path.join(OUT, name))
    print("gerado", name, img.size)
    return img


def polar(r, deg, cx=C, cy=C):
    """Ponto (em pixels supersampled) a r do centro; 0° = 12h, sentido horário."""
    a = math.radians(deg)
    return (S(cx + r * math.sin(a)), S(cy - r * math.cos(a)))


def canvas():
    return Image.new("RGBA", (S(SIZE), S(SIZE)), (0, 0, 0, 0))


def circle_mask(r_out, r_in=0):
    m = Image.new("L", (S(SIZE), S(SIZE)), 0)
    d = ImageDraw.Draw(m)
    d.ellipse([S(C - r_out), S(C - r_out), S(C + r_out), S(C + r_out)], fill=255)
    if r_in:
        d.ellipse([S(C - r_in), S(C - r_in), S(C + r_in), S(C + r_in)], fill=0)
    return m


def shadow_of(layer, dx=2, dy=3, blur=2.2, opacity=0.55):
    """Sombra projetada (para elementos fixos: índices, janela)."""
    a = layer.getchannel("A").point(lambda v: int(v * opacity))
    sh = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    sh.putalpha(a)
    sh = sh.filter(ImageFilter.GaussianBlur(S(blur)))
    out = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    out.alpha_composite(sh, (S(dx), S(dy)))
    return out


def glow(layer, radius=3, strength=1.0):
    """Brilho em volta (modo ambiente)."""
    g = layer.filter(ImageFilter.GaussianBlur(S(radius)))
    if strength != 1.0:
        g.putalpha(g.getchannel("A").point(lambda v: min(255, int(v * strength))))
    out = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    out.alpha_composite(g)
    out.alpha_composite(layer)
    return out


# ---------------------------------------------------------------- mostrador
R_DIAL = 185


def make_dial(name, base):
    """Raio de sol: o brilho varia com o ângulo (2 faixas claras em diagonal)."""
    random.seed(11)
    n = SIZE  # resolução final direto (sem supersampling: é um gradiente suave)
    img = Image.new("RGB", (n, n))
    px = img.load()
    # ruído fino por ângulo simula o escovado radial
    grain = [random.uniform(-0.025, 0.025) for _ in range(1440)]
    for y in range(n):
        for x in range(n):
            dx, dy = x + 0.5 - C, y + 0.5 - C
            r = math.hypot(dx, dy)
            ang = math.atan2(dx, -dy)                 # 0 = 12h, horário
            b = 0.5 + 0.5 * math.cos(2 * (ang - math.radians(315)))
            k = 0.72 + 0.62 * b ** 1.6 + grain[int((ang % (2 * math.pi)) / (2 * math.pi) * 1440) % 1440]
            # vinheta: escurece perto da borda
            t = max(0.0, (r / R_DIAL - 0.55) / 0.45)
            k *= 1 - 0.55 * t ** 1.4
            px[x, y] = tuple(max(0, min(255, int(c * k))) for c in base)
    img = img.convert("RGBA")
    mask = circle_mask(R_DIAL + 1).resize((n, n), Image.LANCZOS)
    img.putalpha(mask)
    img.save(os.path.join(OUT, name))
    print("gerado", name, img.size)


# ------------------------------------------------------------------ luneta
def make_bezel(name, color):
    img = canvas()
    d = ImageDraw.Draw(img)
    d.ellipse([0, 0, S(SIZE) - 1, S(SIZE) - 1], fill=color + (255,))
    d.ellipse([S(1), S(1), S(SIZE - 1), S(SIZE - 1)], outline=(44, 51, 47, 255), width=S(2))

    font = ImageFont.truetype(FONT_BEZEL, S(25))
    for i in range(1, 60):
        deg = i * 6
        if i % 10 == 0:
            # número girado acompanhando o anel (o 30 fica de cabeça para baixo)
            t = Image.new("RGBA", (S(40), S(34)), (0, 0, 0, 0))
            ImageDraw.Draw(t).text((S(20), S(17)), str(i), font=font, fill=PRINT, anchor="mm")
            t = t.rotate(-deg, resample=Image.BICUBIC, expand=True)
            cx, cy = polar(205, deg)
            img.alpha_composite(t, (int(cx - t.width / 2), int(cy - t.height / 2)))
        elif i % 5 == 0:
            d.line([polar(212, deg), polar(197, deg)], fill=PRINT, width=S(5))
        elif i < 15:
            d.line([polar(211, deg), polar(201, deg)], fill=PRINT, width=int(S(1.8)))

    # triângulo às 12 com ponto de lume
    d.polygon([(S(C - 15), S(6)), (S(C + 15), S(6)), (S(C), S(31))], fill=PRINT)
    d.ellipse([S(C - 4.2), S(15 - 4.2), S(C + 4.2), S(15 + 4.2)], fill=LUME, outline=STEEL_DARK, width=S(1))

    # anel de aço entre a luneta e o mostrador
    d.ellipse([S(C - 189), S(C - 189), S(C + 189), S(C + 189)], outline=STEEL, width=S(3))
    d.ellipse([S(C - 186), S(C - 186), S(C + 186), S(C + 186)], outline=(0, 0, 0, 128), width=S(1))

    # centro transparente (o mostrador fica por baixo)
    a = ImageChops.multiply(img.getchannel("A"), circle_mask(226, 185.5))
    img.putalpha(a)
    save(img, name)


# ---------------------------------------------------- índices (dia e AOD)
def draw_indices(d, fill, ring, ring_w=2.5):
    rw = int(S(ring_w)) if ring else 0
    for h in range(12):
        deg = h * 30
        if h == 3:
            continue  # janela de dia/data
        if h == 0:
            d.polygon([(S(C - 15), S(50)), (S(C + 15), S(50)), (S(C + 10), S(92)), (S(C - 10), S(92))],
                      fill=fill, outline=ring, width=rw)
        elif h in (6, 9):
            # bastão: desenhado em pé às 12 e girado depois (ver make_markers)
            pass
        else:
            cx, cy = polar(150, deg)
            d.ellipse([cx - S(13), cy - S(13), cx + S(13), cy + S(13)], fill=fill, outline=ring, width=rw)


def baton(fill, ring, ring_w=2.5):
    """Bastão das 6 e 9 desenhado às 12, para girar em volta do centro."""
    lay = canvas()
    ImageDraw.Draw(lay).rounded_rectangle([S(C - 9), S(52), S(C + 9), S(92)], radius=S(2), fill=fill,
                                          outline=ring, width=int(S(ring_w)) if ring else 0)
    return lay


def make_markers():
    img = canvas()
    d = ImageDraw.Draw(img)

    # trilha de minutos
    for i in range(60):
        deg = i * 6
        long = i % 5 == 0
        col = PRINT[:3] + ((242,) if long else (178,))
        d.line([polar(181, deg), polar(171 if long else 175, deg)], fill=col, width=int(S(2.2 if long else 1.2)))

    # textos fixos
    title = ImageFont.truetype(FONT_TITLE, S(15))
    sub = ImageFont.truetype(FONT_BEZEL, S(12))
    spaced_text(d, (S(C), S(128)), "GREEN DIVER", title, (238, 242, 234, 255), S(3))
    spaced_text(d, (S(C), S(145)), "AUTOMATIC", sub, (207, 216, 207, 220), S(2.5))

    # índices + moldura da janela, com sombra
    raised = canvas()
    rd = ImageDraw.Draw(raised)
    draw_indices(rd, LUME, STEEL)
    for deg in (180, 270):
        b = baton(LUME, STEEL).rotate(-deg, resample=Image.BICUBIC, center=(S(C), S(C)))
        raised.alpha_composite(b)
    rd.rounded_rectangle([S(WIN_X - 3), S(WIN_Y - 3), S(WIN_X + WIN_W + 3), S(WIN_Y + WIN_H + 3)],
                         radius=S(3), fill=STEEL, outline=STEEL_DARK, width=S(1))
    rd.rounded_rectangle([S(WIN_X), S(WIN_Y), S(WIN_X + WIN_W), S(WIN_Y + WIN_H)], radius=S(1.5),
                         fill=(247, 247, 242, 255))
    rd.line([(S(WIN_X + WIN_SPLIT), S(WIN_Y)), (S(WIN_X + WIN_SPLIT), S(WIN_Y + WIN_H))],
            fill=(154, 161, 156, 255), width=S(1))
    img.alpha_composite(shadow_of(raised))
    img.alpha_composite(raised)
    save(img, "markers.png")


def make_aod_markers():
    lay = canvas()
    d = ImageDraw.Draw(lay)
    draw_indices(d, LUME_AOD, None)
    for deg in (180, 270):
        lay.alpha_composite(baton(LUME_AOD, None).rotate(-deg, resample=Image.BICUBIC, center=(S(C), S(C))))
    cx, cy = polar(150, 90)  # pontinho às 3h (a janela some no modo ambiente)
    d.ellipse([cx - S(6), cy - S(6), cx + S(6), cy + S(6)], fill=LUME_AOD)
    d.ellipse([S(C - 4.2), S(15 - 4.2), S(C + 4.2), S(15 + 4.2)], fill=LUME_AOD)  # ponto do triângulo
    save(glow(lay, 3), "aod_markers.png")


def spaced_text(d, center, text, font, fill, spacing):
    """Texto centralizado com espaçamento entre letras (baseline em center[1])."""
    widths = [d.textlength(ch, font=font) for ch in text]
    total = sum(widths) + spacing * (len(text) - 1)
    x = center[0] - total / 2
    for ch, w in zip(text, widths):
        d.text((x, center[1]), ch, font=font, fill=fill, anchor="ls")
        x += w + spacing


# --------------------------------------------------------------- ponteiros
# Cada ponteiro aponta para CIMA. A imagem tem largura W e altura length+tail;
# o pivô (centro do relógio) fica a `length` pixels do topo. Coordenadas das
# formas abaixo são relativas ao pivô (y negativo = em direção à ponta).
HANDS = {
    "hour":   dict(w=44, length=110, tail=28,
                   outer=[(-7, 22), (-7, -60), (-18, -60), (0, -104), (18, -60), (7, -60), (7, 22)],
                   inner=[(-3, -12), (-3, -56), (-11.5, -56), (0, -94), (11.5, -56), (3, -56), (3, -12)]),
    "minute": dict(w=28, length=170, tail=34,
                   outer=[(-4.5, 28), (-9.5, -22), (-7, -132), (0, -164), (7, -132), (9.5, -22), (4.5, 28)],
                   inner=[(-5, -26), (-3.8, -128), (0, -152), (3.8, -128), (5, -26)]),
}
SECOND = dict(w=26, length=176, tail=42)


def hand_canvas(w, length, tail):
    img = Image.new("RGBA", (S(w), S(length + tail)), (0, 0, 0, 0))
    return img, (lambda x, y: (S(w / 2 + x), S(length + y)))


def halo(layer, radius=1.6, opacity=0.7):
    """Contorno escuro suave e simétrico (não depende do ângulo do ponteiro)."""
    a = layer.getchannel("A").filter(ImageFilter.GaussianBlur(S(radius))).point(lambda v: int(v * opacity))
    out = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    out.putalpha(a)
    out.alpha_composite(layer)
    return out


def make_hands():
    for key, h in HANDS.items():
        # modo ativo: moldura de aço + lume
        img, P = hand_canvas(h["w"], h["length"], h["tail"])
        d = ImageDraw.Draw(img)
        d.polygon([P(x, y) for x, y in h["outer"]], fill=STEEL, outline=STEEL_DARK, width=S(1))
        d.polygon([P(x, y) for x, y in h["inner"]], fill=LUME)
        save(halo(img), f"{key}_hand.png")

        # modo ambiente: só contorno e lume, brilhando
        img, P = hand_canvas(h["w"], h["length"], h["tail"])
        d = ImageDraw.Draw(img)
        d.polygon([P(x, y) for x, y in h["outer"]], fill=(0, 0, 0, 255), outline=LUME_AOD, width=int(S(1.6)))
        d.polygon([P(x, y) for x, y in h["inner"]], fill=LUME_AOD)
        save(glow(img, 2.5, 0.9), f"aod_{key}_hand.png")

    # segundos: haste fina, ponta laranja, pirulito de lume, contrapeso e capa central
    w, length, tail = SECOND["w"], SECOND["length"], SECOND["tail"]
    img, P = hand_canvas(w, length, tail)
    d = ImageDraw.Draw(img)

    def disc(cy, r, fill, outline=None):
        (x0, y0), (x1, y1) = P(-r, cy - r), P(r, cy + r)
        d.ellipse([x0, y0, x1, y1], fill=fill, outline=outline, width=S(1) if outline else 0)

    d.rectangle([P(-1.3, -150), P(1.3, 36)], fill=STEEL)
    d.rectangle([P(-1.3, -170), P(1.3, -148)], fill=ORANGE)
    disc(-118, 8.5, STEEL)
    disc(-118, 5.8, LUME)
    disc(30, 5.5, STEEL)
    disc(0, 7.5, STEEL, STEEL_DARK)
    disc(0, 2.2, (58, 65, 60, 255))
    save(halo(img, 1.4, 0.6), "second_hand.png")


# ------------------------------------------------------------------ preview
def make_preview():
    """Imagem estática da galeria: Floresta + luneta preta, 10:08:34, sexta 15, 82%."""
    prev = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 255))
    for name in ("dial_floresta.png", "bezel_preta.png", "markers.png"):
        prev.alpha_composite(Image.open(os.path.join(OUT, name)).convert("RGBA"))

    # textos dinâmicos desenhados como ficariam no relógio
    big = Image.new("RGBA", (S(SIZE), S(SIZE)), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    f19 = ImageFont.truetype(FONT_WINDOW, S(19))
    f17 = ImageFont.truetype(FONT_WINDOW, S(17))
    mid = S(WIN_Y + WIN_H / 2)
    d.text((S(WIN_X + WIN_SPLIT / 2), mid), "SEX", font=f19, fill=(21, 24, 22, 255), anchor="mm")
    d.text((S(WIN_X + WIN_SPLIT + (WIN_W - WIN_SPLIT) / 2), mid), "15", font=f19, fill=(21, 24, 22, 255), anchor="mm")
    d.text((S(BAT_LABEL_END), S(BAT_BASELINE)), "BATERIA", font=f17, fill=(238, 242, 234, 255), anchor="rs")
    d.text((S(BAT_VALUE_START), S(BAT_BASELINE)), "82%", font=f17, fill=ORANGE, anchor="ls")
    prev.alpha_composite(big.resize((SIZE, SIZE), Image.LANCZOS))

    def compose(name, deg, length):
        hand = Image.open(os.path.join(OUT, name)).convert("RGBA")
        c = Image.new("RGBA", (SIZE * 2, SIZE * 2), (0, 0, 0, 0))
        c.paste(hand, (SIZE - hand.width // 2, SIZE - length), hand)
        c = c.rotate(-deg, resample=Image.BICUBIC, center=(SIZE, SIZE))
        prev.alpha_composite(c.crop((SIZE // 2, SIZE // 2, SIZE + SIZE // 2, SIZE + SIZE // 2)))

    h, m, s = 10, 8, 34
    compose("hour_hand.png", (h % 12 + m / 60) * 30, HANDS["hour"]["length"])
    compose("minute_hand.png", (m + s / 60) * 6, HANDS["minute"]["length"])
    compose("second_hand.png", s * 6, SECOND["length"])

    prev.putalpha(circle_mask(SIZE / 2).resize((SIZE, SIZE), Image.LANCZOS))
    prev.save(os.path.join(OUT, "preview.png"))
    print("gerado preview.png")


# bateria: "BATERIA" termina em BAT_LABEL_END, o percentual começa em BAT_VALUE_START
# (mesmos valores do watchface.xml)
BAT_BASELINE = 318
BAT_LABEL_END = 222
BAT_VALUE_START = 227


def print_xml_positions():
    """Imprime as caixas dos PartText (topo das letras = y + 0.28 x tamanho, altura 1.2 x tamanho)."""
    for label, cap_top, size in (("janela", WIN_Y + WIN_H / 2 - 0.7 * 19 / 2, 19),
                                 ("bateria", BAT_BASELINE - 0.7 * 17, 17)):
        print(f"{label}: y={cap_top - 0.28 * size:.1f} height={1.2 * size:.1f}")


if __name__ == "__main__":
    for k, v in DIALS.items():
        make_dial(f"dial_{k}.png", v)
    for k, v in BEZELS.items():
        make_bezel(f"bezel_{k}.png", v)
    make_markers()
    make_aod_markers()
    make_hands()
    make_preview()
    print_xml_positions()
