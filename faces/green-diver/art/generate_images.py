#!/usr/bin/env python3
"""Gera todas as imagens do watch face Green Diver (v2, visual realista).

Uso:  python3 faces/green-diver/art/generate_images.py
Saída: faces/green-diver/src/main/res/drawable-nodpi/*.png
Requer: Pillow e numpy (pip install pillow numpy).

Coordenadas lógicas 450x450, as mesmas do watchface.xml. As imagens saem em 2x
(900 px) para ficarem nítidas em telas maiores; o XML continua usando 450.
A luz vem do canto superior esquerdo: chanfros, brilhos e sombras seguem essa direção.

Camadas (de baixo para cima):
  dial_<cor>.png              mostrador raio de sol (floresta, esmeralda, oliva)
  bezel_<cor>.png             luneta de 60 min + anel de aço (preta, verde)
  markers.png                 trilha de minutos, índices aplicados, janela dia/data, textos fixos
  *_hand_shadow.png           sombras dos ponteiros (giram deslocadas 4,5 px no XML)
  *_hand.png                  ponteiros de aço facetado com lume
  glass.png                   reflexo suave do vidro (por cima de tudo)
  aod_markers.png, aod_*_hand.png   modo ambiente
  preview.png                 imagem da galeria (10:08:34)
"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

K = 2            # escala de saída (450 -> 900)
SS = 2           # supersampling
U = K * SS       # pixels de trabalho por unidade lógica
SIZE = 450
C = SIZE / 2
N = SIZE * U     # lado do canvas de trabalho

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "src", "main", "res")
OUT = os.path.join(RES, "drawable-nodpi")
FONTS = os.path.join(HERE, "fonts")
FONT_WINDOW = os.path.join(RES, "font", "barlow_condensed_bold.ttf")   # mesma fonte do XML
FONT_BEZEL = os.path.join(FONTS, "BarlowCondensed-SemiBold.ttf")
FONT_TITLE = os.path.join(FONTS, "Archivo-Bold.ttf")
os.makedirs(OUT, exist_ok=True)

LX, LY = -0.70710678, -0.70710678       # direção de onde vem a luz (cima-esquerda)
RNG = np.random.default_rng(7)

DIALS = {"floresta": (0.115, 0.330, 0.225), "esmeralda": (0.055, 0.370, 0.300), "oliva": (0.270, 0.305, 0.160)}
BEZELS = {"preta": (0.070, 0.082, 0.076), "verde": (0.075, 0.215, 0.150)}
STEEL = np.array([0.80, 0.83, 0.81])
LUME = np.array([0.905, 0.925, 0.835])       # creme esverdeado (lume envelhecido)
PRINT = np.array([0.90, 0.93, 0.89])
ORANGE = np.array([1.0, 0.40, 0.20])
LUME_AOD = (125, 255, 176)


# ------------------------------------------------------------------ utilidades
def P(v):
    return v * U


def mask_new(w=N, h=N):
    return Image.new("L", (w, h), 0)


def arr(m):
    return np.asarray(m, dtype=np.float32) / 255.0


def blur(a, r):
    """Desfoque gaussiano de um array 0..1 (raio em unidades lógicas)."""
    im = Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8))
    return arr(im.filter(ImageFilter.GaussianBlur(r * U)))


def blur_f(a, r):
    """Desfoque com precisão (usa modo F)."""
    sigma = r * U
    rad = max(1, int(round(math.sqrt(12 * sigma * sigma / 3 + 1) / 2)))   # 3 caixas ~ gaussiana

    def box(x, axis):
        pad = [(0, 0)] * x.ndim
        pad[axis] = (rad + 1, rad)
        c = np.cumsum(np.pad(x, pad, mode="edge"), axis=axis, dtype=np.float64)
        hi = np.take(c, range(2 * rad + 1, c.shape[axis]), axis=axis)
        lo = np.take(c, range(0, c.shape[axis] - 2 * rad - 1), axis=axis)
        return ((hi - lo) / (2 * rad + 1)).astype(np.float32)

    out = a.astype(np.float32)
    for _ in range(3):
        out = box(box(out, 0), 1)
    return out


def bevel(mask, r):
    """Iluminação de um chanfro: >0 nas bordas viradas para a luz, <0 nas opostas."""
    h = blur_f(mask, r)
    gy, gx = np.gradient(h)
    s = -(gx * LX + gy * LY) * (r * U * 2.5)
    return np.clip(s, -1, 1)


def offset(a, dx, dy):
    out = np.zeros_like(a)
    dx, dy = int(round(P(dx))), int(round(P(dy)))
    h, w = a.shape[:2]
    out[max(dy, 0):h + min(dy, 0), max(dx, 0):w + min(dx, 0)] = a[max(-dy, 0):h - max(dy, 0), max(-dx, 0):w - max(dx, 0)]
    return out


def noise(shape, r, amp):
    n = RNG.standard_normal(shape).astype(np.float32)
    if r:
        n = blur_f(n, r)
        n /= (n.std() + 1e-6)
    return n * amp


class Layer:
    """Acumulador RGBA em float (composição 'over')."""

    def __init__(self, w=N, h=N):
        self.rgb = np.zeros((h, w, 3), np.float32)
        self.a = np.zeros((h, w), np.float32)

    def over(self, rgb, a):
        a = np.clip(a, 0, 1)
        rgb = np.broadcast_to(np.asarray(rgb, np.float32), self.rgb.shape)
        na = a + self.a * (1 - a)
        self.rgb = (rgb * a[..., None] + self.rgb * (self.a * (1 - a))[..., None]) / np.maximum(na, 1e-6)[..., None]
        self.a = na

    def image(self, out_scale=True):
        rgba = np.dstack([np.clip(self.rgb, 0, 1), np.clip(self.a, 0, 1)])
        im = Image.fromarray((rgba * 255 + 0.5).astype(np.uint8), "RGBA")
        if out_scale:
            im = im.resize((im.width // SS, im.height // SS), Image.LANCZOS)
        return im


def save(im, name):
    im.save(os.path.join(OUT, name))
    print("gerado", name, im.size)


def grid(w=N, h=N, cx=C, cy=C):
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    dx = (xs + 0.5) / U - cx
    dy = (ys + 0.5) / U - cy
    r = np.hypot(dx, dy)
    ang = np.arctan2(dx, -dy)          # 0 = 12h, horário
    return dx, dy, r, ang


DX, DY, R, ANG = grid()


def circle(cx, cy, r, w=N, h=N):
    m = mask_new(w, h)
    ImageDraw.Draw(m).ellipse([P(cx - r), P(cy - r), P(cx + r), P(cy + r)], fill=255)
    return arr(m)


def poly(pts, w=N, h=N):
    m = mask_new(w, h)
    ImageDraw.Draw(m).polygon([(P(x), P(y)) for x, y in pts], fill=255)
    return arr(m)


def rrect(x0, y0, x1, y1, rad, w=N, h=N):
    m = mask_new(w, h)
    ImageDraw.Draw(m).rounded_rectangle([P(x0), P(y0), P(x1), P(y1)], radius=P(rad), fill=255)
    return arr(m)


def polar(r, deg):
    a = math.radians(deg)
    return C + r * math.sin(a), C - r * math.cos(a)


def metal(mask, r=1.2, base=STEEL, env=None, spec=0.55):
    """Aço polido: chanfro + brilho especular + reflexo do ambiente."""
    s = bevel(mask, r)
    c = base[None, None, :] * (0.78 + 0.42 * s[..., None])
    c = c + spec * np.clip(s, 0, 1)[..., None] ** 3
    if env is not None:
        c = c + env[..., None]
    return np.clip(c, 0, 1)


def lume_fill(mask, color=LUME):
    """Lume rebaixado: borda de cima/esquerda na sombra, textura granulada."""
    s = bevel(mask, 0.9)
    tex = noise(mask.shape, 0.25, 0.010)
    k = 1.0 + 0.10 * (-s) * (s < 0) - 0.22 * np.clip(s, 0, 1) + tex
    return np.clip(color[None, None, :] * k[..., None], 0, 1)


def drop_shadow(layer, mask, dx=1.8, dy=2.6, r=1.8, op=0.55):
    sh = offset(blur(mask, r), dx, dy) * op
    layer.over((0, 0, 0), sh)


# ------------------------------------------------------------------ mostrador
R_DIAL = 185


def make_dial(name, base):
    base = np.array(base, np.float32)
    b = 0.5 + 0.5 * np.cos(2 * (ANG - math.radians(315)))
    bins = 7200
    streak = RNG.standard_normal(bins).astype(np.float32)
    streak = np.convolve(np.concatenate([streak[-3:], streak, streak[:3]]), np.ones(7) / 7, "same")[3:-3]
    idx = ((ANG % (2 * np.pi)) / (2 * np.pi) * bins).astype(int) % bins
    k = 0.60 + 0.85 * b ** 2.4
    k = k * (1 + streak[idx] * 0.07 * (0.35 + b)) + noise(ANG.shape, 0, 0.008)
    t = np.clip((R / R_DIAL - 0.50) / 0.50, 0, 1)
    k *= 1 - 0.50 * t ** 1.5
    # sombra que o anel de minutos projeta na borda do mostrador (luz de cima-esquerda)
    rim = np.clip(1 - (R_DIAL - R) / 7, 0, 1) ** 2
    lit = 0.5 + 0.5 * np.cos(ANG - math.radians(315))
    k *= 1 - rim * (0.25 + 0.35 * lit)
    rgb = base[None, None, :] * k[..., None]
    hi = np.clip(k - 1.0, 0, None)[..., None] * np.array([0.10, 0.12, 0.05])
    rgb = np.clip(rgb + hi, 0, 1)
    L = Layer()
    L.over(rgb, circle(C, C, R_DIAL + 0.5))
    save(L.image(), name)


# ------------------------------------------------------------------ luneta
def text_mask(text, font, cx, cy, deg=0, spacing=0, anchor="mm"):
    m = mask_new()
    d = ImageDraw.Draw(m)
    if spacing:
        widths = [d.textlength(ch, font=font) for ch in text]
        total = sum(widths) + P(spacing) * (len(text) - 1)
        x = P(cx) - total / 2
        for ch, w in zip(text, widths):
            d.text((x, P(cy)), ch, font=font, fill=255, anchor="ls")
            x += w + P(spacing)
    else:
        d.text((P(cx), P(cy)), text, font=font, fill=255, anchor=anchor)
    if deg:
        m = m.rotate(-deg, resample=Image.BICUBIC, center=(P(cx), P(cy)))
    return arr(m)


def make_bezel(name, base):
    base = np.array(base, np.float32)
    lit = 0.5 + 0.5 * np.cos(ANG - math.radians(315))
    conc = noise((1, 4000), 0, 1)[0]
    ridx = np.clip((R * 8).astype(int), 0, 3999)
    k = 0.80 + 0.55 * lit ** 3 + conc[ridx] * 0.025
    insert = base[None, None, :] * k[..., None] + (0.06 * lit ** 6)[..., None]
    ring_out = circle(C, C, 225)
    ring_in = circle(C, C, 190.5)
    L = Layer()
    L.over(np.clip(insert, 0, 1), ring_out - ring_in)

    # marcas e números (tinta levemente em relevo)
    marks = mask_new()
    d = ImageDraw.Draw(marks)
    for i in range(1, 60):
        deg = i * 6
        if i % 10 == 0:
            continue
        if i % 5 == 0:
            p1, p2 = polar(212, deg), polar(197, deg)
            d.line([(P(p1[0]), P(p1[1])), (P(p2[0]), P(p2[1]))], fill=255, width=P(5))
        elif i < 15:
            p1, p2 = polar(211, deg), polar(201, deg)
            d.line([(P(p1[0]), P(p1[1])), (P(p2[0]), P(p2[1]))], fill=255, width=int(P(1.8)))
    m = arr(marks)
    font = ImageFont.truetype(FONT_BEZEL, P(25))
    for i in range(10, 60, 10):
        x, y = polar(205, i * 6)
        m = np.maximum(m, text_mask(str(i), font, x, y, i * 6))
    tri = poly([(C - 15, 6), (C + 15, 6), (C, 31)])
    m = np.maximum(m, tri)
    s = bevel(m, 0.5)
    paint = PRINT[None, None, :] * (0.93 + 0.10 * s[..., None])
    L.over(paint, m)

    # ponto de lume no triângulo, com aro de metal
    pip_o, pip_i = circle(C, 15, 4.6), circle(C, 15, 3.4)
    L.over(metal(pip_o, 0.6), pip_o)
    L.over(lume_fill(pip_i), pip_i)

    # anel de aço polido entre a luneta e o mostrador
    steel_ring = circle(C, C, 190.5) - circle(C, C, 185.5)
    env = 0.22 * np.cos(ANG - math.radians(315)) - 0.05
    L.over(metal(steel_ring, 1.0, env=env, spec=0.35), steel_ring)
    # borda externa escura (encontro com a caixa)
    L.over((0, 0, 0), np.clip((R - 222.5) / 2.5, 0, 1) * ring_out * 0.8)
    save(L.image(), name)


# ------------------------------------------------- índices, trilha e janela
# janela de dia/data às 3h (os PartText do watchface.xml ficam dentro dela)
WIN_X, WIN_Y, WIN_W, WIN_H, WIN_SPLIT = 300, 208.5, 88, 33, 52


def index_shapes():
    """(máscara_metal, máscara_lume) de todos os índices aplicados."""
    metal_m = np.zeros((N, N), np.float32)
    lume_m = np.zeros((N, N), np.float32)
    for h in range(12):
        deg = h * 30
        if h == 3:
            continue
        if h == 0:
            o = poly([(C - 16.5, 48.5), (C + 16.5, 48.5), (C + 11, 93.5), (C - 11, 93.5)])
            i = poly([(C - 13, 51.5), (C + 13, 51.5), (C + 8.6, 90.5), (C - 8.6, 90.5)])
        elif h in (6, 9):
            o = rrect(C - 10.5, 50.5, C + 10.5, 93.5, 2.5)
            i = rrect(C - 7.5, 53.5, C + 7.5, 90.5, 1.5)
            o = arr(Image.fromarray((o * 255).astype(np.uint8)).rotate(-deg, Image.BICUBIC, center=(P(C), P(C))))
            i = arr(Image.fromarray((i * 255).astype(np.uint8)).rotate(-deg, Image.BICUBIC, center=(P(C), P(C))))
        else:
            x, y = polar(150, deg)
            o, i = circle(x, y, 14.2), circle(x, y, 11.0)
        metal_m = np.maximum(metal_m, o)
        lume_m = np.maximum(lume_m, i)
    return metal_m, lume_m


def make_markers():
    L = Layer()
    # trilha de minutos impressa
    tr = mask_new()
    d = ImageDraw.Draw(tr)
    for i in range(60):
        deg = i * 6
        lng = i % 5 == 0
        p1, p2 = polar(181.5, deg), polar(171 if lng else 175.5, deg)
        d.line([(P(p1[0]), P(p1[1])), (P(p2[0]), P(p2[1]))], fill=255 if lng else 190, width=int(P(2.2 if lng else 1.1)))
    L.over(PRINT, arr(tr) * 0.95)

    title = ImageFont.truetype(FONT_TITLE, P(15))
    sub = ImageFont.truetype(FONT_BEZEL, P(12))
    L.over(PRINT, text_mask("GREEN DIVER", title, C, 128, spacing=3))
    L.over(PRINT * 0.92, text_mask("AUTOMATIC", sub, C, 145, spacing=2.5) * 0.9)

    # índices aplicados: sombra, aro de aço chanfrado, lume rebaixado
    mm, lm = index_shapes()
    drop_shadow(L, mm)
    env = 0.10 * np.clip(-(DX * LX + DY * LY) / 200, -1, 1)
    L.over(metal(mm, 1.1, env=env), mm)
    L.over(lume_fill(lm), lm)

    # janela de dia/data: moldura de aço e papel rebaixado
    fo = rrect(WIN_X - 3.5, WIN_Y - 3.5, WIN_X + WIN_W + 3.5, WIN_Y + WIN_H + 3.5, 3.5)
    fi = rrect(WIN_X, WIN_Y, WIN_X + WIN_W, WIN_Y + WIN_H, 1.5)
    drop_shadow(L, fo, 1.2, 1.8, 1.4, 0.5)
    L.over(metal(fo, 1.0), fo)
    paper = np.full((N, N, 3), 0.965, np.float32)
    top = np.clip(1 - ((DY + C) - WIN_Y) / 5, 0, 1)      # sombra da moldura sobre o papel
    left = np.clip(1 - ((DX + C) - WIN_X) / 3, 0, 1)
    paper *= (1 - 0.28 * np.maximum(top, left * 0.7))[..., None]
    L.over(paper, fi)
    sep = rrect(WIN_X + WIN_SPLIT - 0.5, WIN_Y, WIN_X + WIN_SPLIT + 0.5, WIN_Y + WIN_H, 0)
    L.over((0.55, 0.58, 0.56), sep)
    save(L.image(), "markers.png")


def make_aod_markers():
    _, lm = index_shapes()
    x, y = polar(150, 90)
    lm = np.maximum(lm, circle(x, y, 5.5))
    lm = np.maximum(lm, circle(C, 15, 4))
    g = np.clip(blur(lm, 3.5) * 0.9 + lm, 0, 1)
    L = Layer()
    L.over(np.array(LUME_AOD) / 255.0, g)
    save(L.image(), "aod_markers.png")


def make_glass():
    """Reflexo do vidro: um crescente bem suave no alto à esquerda."""
    a = circle(C - 12, C - 12, 208) - circle(C + 30, C + 40, 205)
    a = np.clip(a, 0, 1)
    a = blur(a, 14) * 0.10 * circle(C, C, 224)
    L = Layer()
    L.over((1, 1, 1), a)
    save(L.image(), "glass.png")


# ------------------------------------------------------------------ ponteiros
HANDS = {
    "hour":   dict(w=44, length=110, tail=28,
                   outer=[(-7, 22), (-7, -60), (-18, -60), (0, -104), (18, -60), (7, -60), (7, 22)],
                   inner=[(-3.2, -12), (-3.2, -56.5), (-11.8, -56.5), (0, -95), (11.8, -56.5), (3.2, -56.5), (3.2, -12)]),
    "minute": dict(w=28, length=170, tail=34,
                   outer=[(-4.5, 28), (-9.5, -22), (-7, -132), (0, -164), (7, -132), (9.5, -22), (4.5, 28)],
                   inner=[(-5.3, -26), (-4.0, -128), (0, -153), (4.0, -128), (5.3, -26)]),
}
SECOND = dict(w=26, length=176, tail=42)


def hand_space(w, length, tail):
    W, H = w * U, (length + tail) * U

    def pts(lst):
        return [(w / 2 + x, length + y) for x, y in lst]
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    hx = (xs + 0.5) / U - w / 2           # x relativo ao eixo do ponteiro
    hy = (ys + 0.5) / U - length          # y relativo ao pivô
    return W, H, pts, hx, hy


def hand_layers(key, h):
    w, length, tail = h["w"], h["length"], h["tail"]
    W, H, pts, hx, hy = hand_space(w, length, tail)
    o = poly(pts(h["outer"]), W, H)
    i = poly(pts(h["inner"]), W, H)
    # duas faces: metade esquerda pega luz, metade direita fica na sombra
    facet = np.tanh(-hx / 0.6) * 0.5            # +0.5 esquerda, -0.5 direita
    s = bevel(o, 0.8)
    along = np.clip(-hy / length, 0, 1)
    c = STEEL[None, None, :] * (0.80 + 0.38 * facet + 0.25 * s - 0.06 * along)[..., None]
    c = c + 0.45 * np.clip(s, 0, 1)[..., None] ** 3
    c = c + 0.20 * np.exp(-((hx + 1.2) ** 2) / 0.5)[..., None] * 0.6      # filete de brilho
    L = Layer(W, H)
    L.over(np.clip(c, 0, 1), o)
    L.over(lume_fill(i), i)
    save(L.image(), f"{key}_hand.png")

    sh = Layer(W, H)
    sh.over((0, 0, 0), blur(o, 1.8) * 0.72)
    save(sh.image(), f"{key}_hand_shadow.png")

    a = Layer(W, H)
    edge = np.clip(o - poly(pts(shrink(h["outer"], 1.6)), W, H), 0, 1)
    a.over(np.array(LUME_AOD) / 255.0, np.clip(blur(o, 2.2) * 0.55, 0, 1))
    a.over((0, 0, 0), o)
    a.over(np.array(LUME_AOD) / 255.0, edge)
    a.over(np.array(LUME_AOD) / 255.0, i)
    save(a.image(), f"aod_{key}_hand.png")


def shrink(pts_, d):
    """Encolhe um polígono simétrico (aproximação simples para o contorno do AOD)."""
    cy = sum(y for _, y in pts_) / len(pts_)
    out = []
    for x, y in pts_:
        nx = x - math.copysign(d, x) if abs(x) > d else 0
        ny = y + (d if y < cy else -d)
        out.append((nx, ny))
    return out


def sphere(mask_cx, mask_cy, r, W, H, base=STEEL):
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    dx = ((xs + 0.5) / U - mask_cx) / r
    dy = ((ys + 0.5) / U - mask_cy) / r
    d2 = dx * dx + dy * dy
    nz = np.sqrt(np.clip(1 - d2, 0, 1))
    lam = np.clip(-(dx * LX + dy * LY) * 0.6 + nz * 0.6, 0, 1)
    spec = np.clip(-(dx * LX + dy * LY) * 0.7 + nz * 0.7, 0, 1) ** 18
    c = base[None, None, :] * (0.45 + 0.65 * lam)[..., None] + spec[..., None] * 0.8
    return np.clip(c, 0, 1)


def make_second():
    w, length, tail = SECOND["w"], SECOND["length"], SECOND["tail"]
    W, H, pts, hx, hy = hand_space(w, length, tail)
    L = Layer(W, H)
    bar = rrect(w / 2 - 1.3, length - 150, w / 2 + 1.3, length + 36, 0.6, W, H)
    tip = rrect(w / 2 - 1.3, length - 171, w / 2 + 1.3, length - 148, 0.6, W, H)
    lol_o, lol_i = circle(w / 2, length - 118, 8.6, W, H), circle(w / 2, length - 118, 5.9, W, H)
    cw = circle(w / 2, length + 30, 5.6, W, H)
    cap = circle(w / 2, length, 7.6, W, H)
    body = np.maximum.reduce([bar, lol_o, cw, cap])
    facet = np.tanh(-hx / 0.5) * 0.35
    c = STEEL[None, None, :] * (0.82 + facet + 0.25 * bevel(body, 0.6))[..., None]
    L.over(np.clip(c, 0, 1), np.maximum.reduce([bar, lol_o, cw]))
    o = ORANGE[None, None, :] * (0.92 + 0.25 * np.tanh(-hx / 0.5))[..., None]
    L.over(np.clip(o, 0, 1), tip)
    L.over(lume_fill(lol_i), lol_i)
    L.over(sphere(w / 2, length, 7.6, W, H), cap)
    L.over((0.20, 0.22, 0.21), circle(w / 2, length, 1.8, W, H))
    save(L.image(), "second_hand.png")
    sh = Layer(W, H)
    sh.over((0, 0, 0), blur(np.maximum.reduce([bar, tip, lol_o, cw, cap]), 1.4) * 0.55)
    save(sh.image(), "second_hand_shadow.png")


# ------------------------------------------------------------------ prévia
def compose_preview(dial="floresta", bezel="preta", hms=(10, 8, 34), day="SEX", date="15", bat="82%",
                    shadow=(4, 5), name="preview.png"):
    S = SIZE * K
    prev = Image.new("RGBA", (S, S), (0, 0, 0, 255))
    for n in (f"dial_{dial}.png", f"bezel_{bezel}.png", "markers.png"):
        prev.alpha_composite(Image.open(os.path.join(OUT, n)).convert("RGBA"))
    big = Image.new("RGBA", (S * 2, S * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    f19 = ImageFont.truetype(FONT_WINDOW, 23 * K * 2)
    f17 = ImageFont.truetype(FONT_WINDOW, 17 * K * 2)
    q = K * 2
    mid = (WIN_Y + WIN_H / 2) * q
    ink = (21, 24, 22, 255)
    d.text(((WIN_X + WIN_SPLIT / 2) * q, mid), day, font=f19, fill=(200, 38, 42, 255) if day == "DOM" else ink, anchor="mm")
    d.text(((WIN_X + WIN_SPLIT + (WIN_W - WIN_SPLIT) / 2) * q, mid), date, font=f19, fill=ink, anchor="mm")
    d.text((222 * q, 318 * q), "BATERIA", font=f17, fill=(238, 242, 234, 255), anchor="rs")
    d.text((227 * q, 318 * q), bat, font=f17, fill=(255, 106, 61, 255), anchor="ls")
    prev.alpha_composite(big.resize((S, S), Image.LANCZOS))

    def put(fname, deg, length, dx=0, dy=0):
        hand = Image.open(os.path.join(OUT, fname)).convert("RGBA")
        c = Image.new("RGBA", (S * 2, S * 2), (0, 0, 0, 0))
        c.paste(hand, (S - hand.width // 2, S - length * K), hand)
        c = c.rotate(-deg, resample=Image.BICUBIC, center=(S, S))
        prev.alpha_composite(c.crop((S // 2 - int(dx * K), S // 2 - int(dy * K),
                                     S // 2 - int(dx * K) + S, S // 2 - int(dy * K) + S)))

    h, m, s = hms
    angs = {"hour": (h % 12 + m / 60) * 30, "minute": (m + s / 60) * 6, "second": s * 6}
    lens = {"hour": HANDS["hour"]["length"], "minute": HANDS["minute"]["length"], "second": SECOND["length"]}
    for k_ in ("hour", "minute", "second"):
        put(f"{k_}_hand_shadow.png", angs[k_], lens[k_], *shadow)
        put(f"{k_}_hand.png", angs[k_], lens[k_])
    prev.alpha_composite(Image.open(os.path.join(OUT, "glass.png")).convert("RGBA"))
    mask = Image.new("L", (S * 2, S * 2), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, S * 2 - 1, S * 2 - 1], fill=255)
    prev.putalpha(mask.resize((S, S), Image.LANCZOS))
    prev.save(os.path.join(OUT, name))
    print("gerado", name)
    return prev


if __name__ == "__main__":
    for k_, v in DIALS.items():
        make_dial(f"dial_{k_}.png", v)
    for k_, v in BEZELS.items():
        make_bezel(f"bezel_{k_}.png", v)
    make_markers()
    make_aod_markers()
    make_glass()
    for k_, h in HANDS.items():
        hand_layers(k_, h)
    make_second()
    compose_preview()
