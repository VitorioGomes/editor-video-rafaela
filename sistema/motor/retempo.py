"""Acerta o tempo das palavras de um trecho pelo som: número, ano, valor e lista rápida.

A transcrição põe o número escrito em algarismos ("2026", "R$ 19,90") com tempo estimado, e o texto que entra na
palavra entra fora da fala (no teste do Estilo Títulos Desenhados, o calendário entraria 1,5 s depois do "2026").
Aqui o trecho é transcrito de novo, o alinhador acha cada palavra no som (o número por extenso: "dois mil e vinte e
seis") e o palavras.json é corrigido, com uma cópia do original. A energia do áudio sai junto, para conferir de olho.
"""
from __future__ import annotations

import difflib
import shutil
from pathlib import Path

from .comum import audio, config, gravar_json, ler_json, normal

TAXA = 16000
PASSO = 0.04  # a energia é mostrada em fatias de 40 ms


def _energia(y, de: float, ate: float):
    import numpy as np
    linhas = []
    t = de
    while t < ate:
        pedaco = y[int(t * TAXA):int((t + PASSO) * TAXA)]
        db = 20 * np.log10(float(np.sqrt((pedaco ** 2).mean())) + 1e-9) if len(pedaco) else -90.0
        linhas.append((round(t, 2), db))
        t += PASSO
    return linhas


def retempo(video: Path, arquivo: Path, de: float, ate: float, gravar: bool = True) -> None:
    from . import alinhamento
    from .transcricao import _segmentos, ouvir
    y = audio(video)
    total = len(y) / TAXA
    a, b = max(0.0, de - 0.4), min(total, ate + 0.4)
    idioma = config().get("idioma") or "pt"
    segmentos = _segmentos(ouvir(y[int(a * TAXA):int(b * TAXA)], None, condition_on_previous_text=False), a)
    if alinhamento.disponivel(idioma):
        alinhamento.alinhar(y, segmentos, idioma)
    else:
        print("Aviso: sem o alinhador (torch e transformers), o tempo fica o do Whisper.")
    novas = [p for s in segmentos for p in s["palavras"] if p["fim"] > de - 0.05 and p["inicio"] < ate + 0.05]

    lista = ler_json(arquivo)
    dentro = [i for i, p in enumerate(lista) if p["fim"] > de and p["inicio"] < ate]
    if not dentro:
        raise SystemExit(f"Nenhuma palavra do {arquivo.name} entre {de} e {ate} s.")
    velhas = [normal(lista[i]["texto"]) for i in dentro]
    casadas = difflib.SequenceMatcher(None, velhas, [normal(p["texto"]) for p in novas], autojunk=False)
    mudou = []
    for bloco in casadas.get_matching_blocks():
        for k in range(bloco.size):
            i, p = dentro[bloco.a + k], novas[bloco.b + k]
            antes = (lista[i]["inicio"], lista[i]["fim"])
            if abs(antes[0] - p["inicio"]) > 0.02 or abs(antes[1] - p["fim"]) > 0.02:
                mudou.append((i, lista[i]["texto"], antes, (p["inicio"], p["fim"])))
                lista[i]["inicio"], lista[i]["fim"] = p["inicio"], p["fim"]
    # Uma palavra não começa antes de a anterior terminar.
    for i in range(1, len(lista)):
        if lista[i]["inicio"] < lista[i - 1]["fim"]:
            lista[i - 1]["fim"] = round(max(lista[i - 1]["inicio"] + 0.03, lista[i]["inicio"]), 3)

    print(f"Trecho {de:.2f} a {ate:.2f} s, ouvido de novo: " + " ".join(p["texto"] for p in novas))
    nao = [lista[dentro[i]]["texto"] for i in range(len(dentro))
           if not any(blk.a <= i < blk.a + blk.size for blk in casadas.get_matching_blocks())]
    if nao:
        print(f"Sem par na transcrição nova (o tempo ficou o de antes): {', '.join(nao)}")
    print(f"\n{'n':>4}  {'palavra':16s} {'antes':>15}   {'agora':>15}")
    for i, texto, antes, agora in mudou:
        print(f"{i:4d}  {texto[:16]:16s} {antes[0]:6.2f}-{antes[1]:6.2f}   {agora[0]:6.2f}-{agora[1]:6.2f}"
              f"   ({agora[0] - antes[0]:+.2f} s)")
    if not mudou:
        print("Nenhum tempo mudou mais de 0,02 s.")

    # A energia, com o começo de cada palavra marcado: a fala está onde a barra é alta.
    inicios = {round(lista[i]["inicio"] / PASSO) * PASSO: lista[i]["texto"] for i in dentro}
    print(f"\nEnergia do áudio (cada linha {PASSO * 1000:.0f} ms; # = voz):")
    for t, db in _energia(y, de, ate):
        marca = next((txt for ti, txt in inicios.items() if abs(ti - t) < PASSO / 2), "")
        print(f"{t:7.2f} {db:6.1f} {'#' * int(max(0, db + 60) / 2):<30} {('<- ' + marca) if marca else ''}")

    if gravar and mudou:
        copia = arquivo.with_name(arquivo.stem + ".antes-do-retempo.json")
        if not copia.exists():
            shutil.copy(arquivo, copia)
        gravar_json(arquivo, lista)
        print(f"\n{len(mudou)} palavras corrigidas em {arquivo} (o original está em {copia.name}).")
    elif mudou:
        print("\nNada gravado (--so-mostrar).")
