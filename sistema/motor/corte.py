"""Tira os respiros da fala e aplica o tratamento de cor e de voz. Gera base.mp4 e palavras.json com os tempos novos."""
from __future__ import annotations

import subprocess
from pathlib import Path

from .comum import audio, config, duracao, eh_hdr, gravar_json, ler_json, preto, tem_video


def silencios(video: Path, respiro: float, cauda: float | None, pausa: float | None) -> tuple[list, object, float]:
    """Corta só onde o áudio está em silêncio de verdade. A borda de palavra da transcrição engana:
    ela pode esticar uma palavra por 1 s sobre o silêncio, ou cortar o começo da seguinte."""
    import numpy as np
    y = audio(video)
    h = 160  # 10 ms
    db = 20 * np.log10(np.sqrt(np.convolve(y ** 2, np.ones(h) / h, "same"))[::h] + 1e-7)
    piso, fala = np.percentile(db, 10), np.percentile(db, 90)
    limiar = piso + (fala - piso) * 0.30
    fundo = float(np.percentile(db, 3)) + 6  # abaixo disso, a voz já sumiu
    folga = 0.04
    lista, i, n = [], 0, len(db)
    while i < n:
        if db[i] < limiar:
            j = i
            while j + 1 < n and db[j + 1] < limiar:
                j += 1
            # O fim das palavras soa baixo: anda até o fundo antes de aceitar o corte.
            k, m = i, j
            while k <= j and db[k] > fundo:
                k += 1
            while m >= k and db[m] > fundo:
                m -= 1
            # Sala com eco: a cauda até o fundo passa de meio segundo. "cauda" limita o que fica depois da voz,
            # contado do fim de verdade da palavra (o último som acima do fundo + 6 dB nos primeiros 0,35 s da pausa),
            # para não comer o fim de palavra com consoante muda no meio ("posta").
            if cauda is not None:
                janela = db[i:min(j, i + 35) + 1]
                acima = np.nonzero(janela > fundo + 6)[0]
                e = i + (int(acima[-1]) + 1 if len(acima) else 0)
                k, m = min(k, e + int(cauda / 0.01)), max(m, j - 6)
            if (m - k + 1) * 0.01 >= respiro:
                lista.append((k * 0.01, (m + 1) * 0.01))
            i = j + 1
        else:
            i += 1
    if pausa is not None:
        # Teto do silêncio entre frases. O fim da frase se arrasta 10 a 15 dB abaixo da fala e fica acima do limiar:
        # aqui conta como pausa o que está abaixo da metade entre o fundo e a fala.
        meio = piso + (fala - piso) * 0.50
        i = 0
        while i < n:
            if db[i] < meio:
                j = i
                while j + 1 < n and db[j + 1] < meio:
                    j += 1
                if (j - i + 1) * 0.01 > pausa:
                    # O começo da próxima palavra pode ser baixo: do lado dela, o corte só vai até o último
                    # instante de silêncio de verdade.
                    quietos = np.nonzero(db[i:j + 1] < limiar)[0]
                    if len(quietos):
                        k = i + max(0, int(round((pausa - 0.06 - 2 * folga) / 0.01)))
                        m = min(j - 6, i + int(quietos[-1]) - 2)
                        if (m - k + 1) * 0.01 >= 0.04:
                            lista.append((k * 0.01, (m + 1) * 0.01))
                i = j + 1
            else:
                i += 1
        lista.sort()
        juntos = []
        for x0, x1 in lista:
            if juntos and x0 <= juntos[-1][1]:
                juntos[-1] = (min(juntos[-1][0], x0), max(juntos[-1][1], x1))
            else:
                juntos.append((x0, x1))
        lista = juntos
    return lista, db, limiar


def cortar(video: Path, arquivo: Path, saida: Path, respiro: float = 0.16, trocas: Path | None = None,
           manter_ate: float = 0.0, cauda: float | None = 0.12, pausa: float | None = 0.22,
           manter: str | None = None, sem_tratamento: bool = False) -> None:
    import numpy as np
    saida.mkdir(parents=True, exist_ok=True)
    palavras = ler_json(arquivo)
    if trocas:
        for numero, texto in ler_json(trocas).items():
            palavras[int(numero)]["texto"] = texto
        # "" apaga a palavra (palavra a mais, ou duas que viraram uma): o tempo dela passa para a anterior.
        for i in range(len(palavras) - 1, -1, -1):
            if not palavras[i]["texto"].strip():
                if i:
                    palavras[i - 1]["fim"] = max(palavras[i - 1]["fim"], palavras[i]["fim"])
                del palavras[i]
    total = duracao(video)
    cortes, db, limiar = silencios(video, respiro, cauda, pausa)
    folga = 0.04
    if manter:
        # Trechos sem fala que ficam inteiros, como um gesto que é o gancho visual: "a-b,c-d", em segundos.
        for x0, x1 in [tuple(float(x) for x in r.split("-")) for r in manter.split(",") if r]:
            novos = []
            for a, b in cortes:
                if b <= x0 or a >= x1:
                    novos.append((a, b))
                    continue
                if a < x0 and x0 - a >= 0.04:
                    novos.append((a, x0))
                if b > x1 and b - x1 >= 0.04:
                    novos.append((x1, b))
            cortes = novos
    # Antes da fala pode haver gesto sem som (a mão saindo da câmera): "manter_ate" guarda esses segundos.
    # A transcrição erra o começo da primeira palavra quando há silêncio antes: vale o som.
    ativos = np.nonzero(db[int(manter_ate / 0.01):] >= limiar)[0]
    voz = manter_ate + (ativos[0] * 0.01 if len(ativos) else 0.0)
    if palavras[0]["inicio"] < voz:
        palavras[0]["inicio"] = voz
        palavras[0]["fim"] = max(palavras[0]["fim"], voz + 0.15)
    trechos, cursor = [], 0.0 if manter_ate else max(0.0, palavras[0]["inicio"] - folga)
    for a, b in cortes:
        if b <= cursor or (manter_ate and a < manter_ate):
            continue
        # Depois da última palavra nada é cortado: a voz termina de cair sozinha.
        if b >= total - 0.01 or a >= palavras[-1]["fim"] - 0.2:
            break
        fim = a + folga
        if fim > cursor:
            trechos.append([cursor, fim])
        cursor = max(cursor, b - folga)
    if total > cursor:
        trechos.append([cursor, total])

    cfg = config()["tratamento"]
    com_video = tem_video(video)
    hdr = ("zscale=t=linear:npl=203,tonemap=hable:desat=0,zscale=p=bt709:t=bt709:m=bt709:r=tv,format=gbrp,"
           if com_video and eh_hdr(video) else "")
    # sem isto, o vídeo convertido do HDR saía marcado como HDR (bt2020) e o render virava 10 bits
    bt709 = ",setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709" if hdr else ""
    cor = "" if sem_tratamento or not cfg.get("cor") else f"format=gbrp,{cfg['cor']},"
    voz_f = "" if sem_tratamento or not cfg.get("voz") else f",{cfg['voz']}"
    ent, fil = [], []
    for i, (a, b) in enumerate(trechos):
        ent += ["-ss", f"{a:.3f}", "-to", f"{b:.3f}", "-i", str(video)]
        # Fade de milissegundos nas pontas: sem ele, a junção estala.
        fil.append((f"[{i}:v:0]setpts=PTS-STARTPTS[v{i}];" if com_video else "") +
                   f"[{i}:a:0]aresample=48000,asetpts=PTS-STARTPTS,"
                   f"afade=t=in:d=0.006,afade=t=out:st={max(b - a - 0.008, 0):.3f}:d=0.008[a{i}]")
    n = len(trechos)
    if com_video:
        fil.append("".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[vc][ac];"
                   f"[vc]fps=30,{hdr}{cor}format=yuv420p,scale=1080:1920:force_original_aspect_ratio=increase,"
                   f"crop=1080:1920,setsar=1{bt709}[v];[ac]anull{voz_f}[a]")
        mapa = ["-map", "[v]", "-map", "[a]"]
    else:
        fil.append("".join(f"[a{i}]" for i in range(n)) + f"concat=n={n}:v=0:a=1[ac];[ac]anull{voz_f}[a]")
        ent += preto(sum(b - a for a, b in trechos))
        mapa = ["-map", f"{n}:v", "-map", "[a]"]
    base = saida / "base.mp4"
    # Quadro-chave frequente: o HyperFrames trava em vídeo com quadros-chave distantes.
    subprocess.run(["ffmpeg", "-v", "error", "-y", *ent, "-filter_complex", ";".join(fil), *mapa,
                    "-c:v", "libx264", "-crf", "17", "-preset", "fast", "-g", "30", "-pix_fmt", "yuv420p",
                    "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                    "-c:a", "aac", "-b:a", "256k", str(base)], check=True)

    def novo_tempo(t: float) -> float:
        acumulado = 0.0
        for a, b in trechos:
            if t < a:
                return acumulado
            if t <= b:
                return acumulado + t - a
            acumulado += b - a
        return acumulado

    # o que vier a mais em cada palavra ("quem" e "fala", nas falas gravadas) passa junto
    gravar_json(saida / "palavras.json", [{**p, "inicio": round(novo_tempo(p["inicio"]), 3),
                                           "fim": round(novo_tempo(p["fim"]), 3)} for p in palavras])
    if not com_video:
        # voz gravada sem vídeo (estilos sem rosto): o voz.wav é o que o Curta 3D e as falas gravadas leem
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(base), "-map", "0:a:0", "-ar", "48000", "-ac", "1",
                        str(saida / "voz.wav")], check=True)
    print(f"{len(trechos) - 1} cortes; de {total:.2f} s para {duracao(base):.2f} s. Saída em {saida}")
