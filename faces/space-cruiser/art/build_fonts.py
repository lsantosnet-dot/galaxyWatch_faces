#!/usr/bin/env python3
"""Gera as fontes do mostrador a partir da Inter variável (art/fonts/Inter-VF.ttf, licença OFL).

O Watch Face Format não suporta fonte variável nem converter texto para maiúsculas, então:
  inter_regular.ttf -> peso 400, óptica "display" (hora grande)
  inter_medium.ttf  -> peso 500 (valores das complicações)
  inter_caps.ttf    -> peso 500, minúsculas desenhadas como MAIÚSCULAS e o ponto "."
                       vazio. Assim [DAY_OF_WEEK_S] "qui." aparece "QUI" e "nov." aparece "NOV".
Todas são reduzidas aos caracteres latinos para ficarem pequenas.

Uso:   python faces/space-cruiser/art/build_fonts.py      (requer: pip install fonttools)
Saída: faces/space-cruiser/src/main/res/font/*.ttf
"""
import os

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import Glyph
from fontTools.varLib import instancer

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "fonts", "Inter-VF.ttf")
OUT = os.path.join(HERE, "..", "src", "main", "res", "font")
os.makedirs(OUT, exist_ok=True)

# Latim básico + Latim-1 (acentos do português) + • e alguns símbolos
UNICODES = list(range(0x20, 0x7F)) + list(range(0xA0, 0x100)) + [0x2022, 0x2013, 0x2014, 0x2026, 0x2212]


def rename(font, family):
    for rec in font["name"].names:
        if rec.nameID in (1, 4, 16):
            rec.string = family
        elif rec.nameID == 6:
            rec.string = family.replace(" ", "")


def build(name, family, wght, opsz, caps=False):
    font = instancer.instantiateVariableFont(TTFont(SRC), {"wght": wght, "opsz": opsz})
    opts = subset.Options()
    opts.layout_features = ["kern", "tnum", "case"]
    opts.name_IDs = ["*"]
    sub = subset.Subsetter(opts)
    sub.populate(unicodes=UNICODES)
    sub.subset(font)
    if caps:
        # glifo vazio e sem largura para o "."
        order = font.getGlyphOrder() + ["dotnull"]
        font.setGlyphOrder(order)
        font["glyf"].glyphOrder = order
        font["glyf"].glyphs["dotnull"] = Glyph()
        font["hmtx"].metrics["dotnull"] = (0, 0)
        for table in font["cmap"].tables:
            cmap = table.cmap
            for cp in list(cmap):
                ch = chr(cp)
                up = ch.upper()
                if ch != up and len(up) == 1 and ord(up) in cmap:
                    cmap[cp] = cmap[ord(up)]          # minúscula usa o desenho da maiúscula
            if 0x2E in cmap:
                cmap[0x2E] = "dotnull"                # "." some (qui. -> QUI)
    rename(font, family)
    path = os.path.join(OUT, name)
    font.save(path)
    print("gerado", name, os.path.getsize(path) // 1024, "KB")


if __name__ == "__main__":
    build("inter_regular.ttf", "Inter WF Regular", 400, 32)
    build("inter_medium.ttf", "Inter WF Medium", 500, 14)
    build("inter_caps.ttf", "Inter WF Caps", 500, 14, caps=True)
