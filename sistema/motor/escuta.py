"""A "escuta" da IA: subtrai o render sem efeitos do render com efeitos e diz se cada efeito entrou, quando e quão alto.

Reprova efeito ausente, ou que começa a soar mais de 45 ms antes ou mais de 125 ms depois do previsto.
Efeito que começa enquanto o anterior ainda soa pode sair como FORA sem estar: ouça esse trecho antes de mexer. Não diz se ficou bom: isso é o ouvido de quem edita.
"""
from __future__ import annotations

import sys
from pathlib import Path

from .comum import audio, ler_json

TAXA = 48000
LIMITE_ALTO = 6.0  # dB de pico acima da fala típica a partir do qual o efeito chama mais atenção que a voz


def conferir(sem: Path, com: Path, arquivo: Path) -> None:
    import numpy as np
    a, b = audio(sem, TAXA), audio(com, TAXA)
    n = min(len(a), len(b))
    if not n:
        sys.exit("Um dos vídeos não tem áudio.")
    # Alinha, caso a compressão tenha deslocado o áudio de um render para o outro.
    trecho = min(n, 96000)
    corr = np.correlate(b[:trecho:4], a[:trecho:4], "full")
    desvio = (int(np.argmax(corr)) - (len(a[:trecho:4]) - 1)) * 4
    if desvio > 0:
        b = b[desvio:]
    elif desvio < 0:
        a = a[-desvio:]
    n = min(len(a), len(b))
    a, b = a[:n], b[:n]
    env = np.sqrt(np.convolve((b - a) ** 2, np.ones(240) / 240, "same"))  # 5 ms
    voz = np.sqrt(np.convolve(a ** 2, np.ones(4800) / 4800, "same"))  # 100 ms
    db, dbv = 20 * np.log10(env + 1e-9), 20 * np.log10(voz + 1e-9)
    deixas = sorted(ler_json(arquivo), key=lambda x: x["t"])
    # A voz de referência: o nível típico da fala no vídeo todo (não só no instante do efeito, que pode cair numa pausa).
    falando = dbv[dbv > float(np.percentile(dbv, 95)) - 20]
    voz_ref = float(np.median(falando)) if len(falando) else -25.0
    altos = []
    print(f"Resíduo fora dos efeitos: {np.median(db):.0f} dB. Desalinhamento: {desvio} amostras.")
    print(f"{'tempo':>7}  {'efeito':30s} {'situação':9s} {'erro':>7} {'pico':>7} {'voz':>7} {'pico-voz':>9}")
    falhas, difs = 0, []
    for d in deixas:
        # Compara com o instante em que o som começa a soar, não com o ponto de sincronia (que num whoosh vem depois).
        t = d.get("ataque", d["t"])
        i0, i1 = max(0, int((t - 0.06) * TAXA)), min(n, int((t + 0.25) * TAXA))
        if i1 <= i0:
            falhas += 1
            print(f"{t:6.2f}s  {d['som']:30s} FORA DO VÍDEO")
            continue
        pico = float(db[i0:i1].max())
        ataque = i0 + int(np.argmax(db[i0:i1] > pico - 12))
        erro = (ataque / TAXA - t) * 1000
        vz = float(dbv[min(int(t * TAXA), n - 1)])
        situacao = "AUSENTE" if pico < -50 else "FORA" if erro < -45 or erro > 125 else "ok"
        falhas += situacao != "ok"
        if situacao == "ok":
            difs.append(pico - vz)
            # O pico de um efeito curto soa mais forte que a mesma altura de voz: até 6 dB acima da fala típica fica junto dela.
            if pico - voz_ref > LIMITE_ALTO:
                altos.append((t, d["som"], pico - voz_ref - LIMITE_ALTO + 1))
        print(f"{t:6.2f}s  {d['som']:30s} {situacao:9s} {erro:+5.0f}ms {pico:5.1f}dB {vz:5.1f}dB {pico - vz:+7.1f}dB")
    print(f"{len(deixas) - falhas} de {len(deixas)} efeitos no lugar." + (f" Pico contra a voz, mediana {np.median(difs):+.1f} dB." if difs else ""))
    if altos:
        print()
        print(f"Efeitos acima da voz (fala típica em {voz_ref:.1f} dB):")
        for t, som, baixar in altos:
            print(f"  {t:6.2f}s  {som:30s} baixe uns {baixar:.0f} dB (\"ganho\": -{baixar:.0f} nesse som, ou desça o \"efeitos\": {{\"ganho\"}} do roteiro)")
    print("Falta o ouvido de quem edita: a voz fica clara, algum efeito chama mais atenção que a fala, algum soa barato.")
    if falhas:
        sys.exit(1)
