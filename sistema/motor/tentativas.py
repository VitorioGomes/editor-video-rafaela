"""Transforma um bruto com muitas repetições num corte só com as melhores tentativas.

O Whisper corrido engole as repetições. Por isso o áudio é cortado nos silêncios e cada pedaço é transcrito sozinho.
escolhas.json: {"bruto": "caminho", "trechos": [[início, fim, "motivo"], ...]}, em segundos do bruto.
No motivo, "exato" não mexe em nenhuma ponta (gesto sem som) e "início exato" só não mexe no começo.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from .comum import audio, eh_hdr, gravar_json, ler_json, niveis, rodar, preto, tem_video
from .transcricao import ouvir

TAXA = 16000


def separar(db, passo: float, min_pausa: float, min_fala: float, limiar: float) -> list[tuple[float, float]]:
    ativo, partes, i, n = db > limiar, [], 0, len(db)
    while i < n:
        if not ativo[i]:
            i += 1
            continue
        j = k = i
        silencio = 0
        while k < n and silencio * passo < min_pausa:
            if ativo[k]:
                silencio, j = 0, k
            else:
                silencio += 1
            k += 1
        if (j - i) * passo >= min_fala:
            partes.append((i * passo, j * passo))
        i = k
    return partes


def _audio(pasta: Path):
    return audio(pasta / "audio.wav", TAXA)


def _bruto(escolhas: Path, dados: dict) -> Path:
    """O caminho do bruto, e o audio.wav dele na pasta (o listar já cria; aqui só falta se a pasta veio de outro lugar)."""
    bruto = Path(dados["bruto"])
    if not bruto.is_absolute():
        bruto = (escolhas.parent / bruto).resolve()
    if not (escolhas.parent / "audio.wav").exists():
        rodar(["ffmpeg", "-v", "error", "-y", "-i", bruto, "-map", "0:a:0", "-ac", "1", "-ar", str(TAXA),
               escolhas.parent / "audio.wav"])
    return bruto


def _texto(y) -> str:
    import numpy as np
    mudo = np.zeros(int(0.3 * TAXA), dtype=np.float32)
    return " ".join(s.text.strip() for s in ouvir(np.concatenate([mudo, y, mudo]), palavras=False, rapido=True,
                                                   condition_on_previous_text=False)).strip()


def listar(bruto: Path, saida: Path, vocabulario: str = "") -> None:
    import numpy as np
    saida.mkdir(parents=True, exist_ok=True)
    rodar(["ffmpeg", "-v", "error", "-y", "-i", bruto, "-map", "0:a:0", "-ac", "1", "-ar", str(TAXA), saida / "audio.wav"])
    y = _audio(saida)
    db = niveis(y, TAXA, 0.02)
    piso, fala = np.percentile(db, 10), np.percentile(db, 90)
    blocos = separar(db, 0.02, 0.36, 0.25, piso + (fala - piso) * 0.30)
    res = []
    for a, b in blocos:
        a, b = max(0, a - 0.12), min(len(y) / TAXA, b + 0.15)
        w = [{"t": x.word.strip(), "i": round(a + x.start, 2), "p": round(x.probability, 2)}
             for s in ouvir(y[int(a * TAXA):int(b * TAXA)], vocabulario, rapido=True, condition_on_previous_text=False,
                            no_speech_threshold=0.9)
             for x in (s.words or [])]
        clareza = float(np.mean([x["p"] for x in w])) if w else 0
        if w and clareza >= 0.2:  # abaixo disso é ruído ou o vocabulário repetido no silêncio
            res.append({"n": len(res), "a": round(a, 2), "b": round(b, 2),
                        "clareza": round(float(np.mean([x["p"] for x in w])), 2), "palavras": w})
    gravar_json(saida / "tentativas.json", res)
    for r in res:
        print(f"{r['n']:3d} {r['a']:6.1f}-{r['b']:6.1f} c{r['clareza']:.2f} | " + " ".join(x["t"] for x in r["palavras"]))


def detalhar(pasta: Path, tempos: list[float]) -> None:
    """Reparte blocos em pausas curtas: mostra o gaguejo e a repetição que o Whisper esconde."""
    import numpy as np
    y = _audio(pasta)
    for a, b in zip(tempos[::2], tempos[1::2]):
        t = y[int(a * TAXA):int(b * TAXA)]
        db = niveis(t, TAXA, 0.01)
        print(f"== {a}-{b}")
        for pa, pb in separar(db, 0.01, 0.14, 0.08, np.percentile(db, 85) - 18):
            print(f"  {a + pa:7.2f}-{a + pb:7.2f} {_texto(t[max(0, int((pa - 0.08) * TAXA)):int((pb + 0.1) * TAXA)])}")


def faixas(dados: dict, pasta: Path) -> list[tuple[float, float]]:
    """Solta as pontas até a voz sumir de verdade: o fim das palavras ainda soa 0,2 s abaixo do volume da fala.
    Para no fundo, ou no vale antes de outra fala começar, para não trazer pedaço da tentativa vizinha."""
    import numpy as np
    db = niveis(_audio(pasta), TAXA, 0.01)
    fundo = float(np.percentile(db, 8)) + 5

    def andar(k: int, passo: int, maximo: int) -> int:
        vale, onde = db[k], k
        for _ in range(maximo):
            k += passo
            if k <= 0 or k >= len(db) - 3:
                return onde
            if db[k] < vale:
                vale, onde = db[k], k
            if db[k:k + 3].max() < fundo:
                return k
            if db[k] > vale + 10:  # outra fala começando
                return onde
        return onde

    trechos, res = dados["trechos"], []
    for i, tr in enumerate(trechos):
        a, b, motivo = tr[0], tr[1], tr[2] if len(tr) > 2 else ""
        if "exato" in motivo and "início exato" not in motivo:
            res.append((a, b))
            continue
        fim = andar(int(b / 0.01), 1, 70) * 0.01 + 0.04
        ini = a if "início exato" in motivo else andar(int(a / 0.01), -1, 18) * 0.01 - 0.02
        # Trechos vizinhos no bruto dividem o espaço entre eles.
        if i + 1 < len(trechos) and 0 < trechos[i + 1][0] - b < 0.7:
            fim = min(fim, (b + trechos[i + 1][0]) / 2)
        if i and 0 < a - trechos[i - 1][1] < 0.7:
            ini = max(ini, (a + trechos[i - 1][1]) / 2)
        res.append((round(max(ini, 0), 3), round(fim, 3)))
    return res


def conferir(escolhas: Path) -> None:
    """Transcreve cada trecho sozinho e mede as pontas: pega ponta com voz, repetição e falsa partida."""
    import numpy as np
    pasta = escolhas.parent
    dados = ler_json(escolhas)
    _bruto(escolhas, dados)
    y = _audio(pasta)
    db = niveis(y, TAXA, 0.01)
    piso = float(np.percentile(db, 8))
    for a, b in faixas(dados, pasta):
        fim, ini = db[int((b - 0.03) / 0.01):int(b / 0.01)].max(), db[int(a / 0.01):int((a + 0.03) / 0.01)].max()
        aviso = "  <<< PONTA COM VOZ" if fim > piso + 12 or ini > piso + 12 else ""
        print(f"{a:7.2f}-{b:7.2f} início {ini:4.0f} fim {fim:4.0f} (piso {piso:.0f}) | {_texto(y[int(a * TAXA):int(b * TAXA)])}{aviso}")
        # O Whisper esconde repetição ("E com IA, e com IA, uma página" sai como uma frase só).
        # Reparte em pausas curtas: dois pedaços seguidos que começam igual denunciam a repetição.
        pedaco = y[int(a * TAXA):int(b * TAXA)]
        dbp = niveis(pedaco, TAXA, 0.01)
        anterior = ""
        for pa, pb in separar(dbp, 0.01, 0.10, 0.08, float(np.percentile(dbp, 85)) - 18):
            txt = _texto(pedaco[max(0, int((pa - 0.06) * TAXA)):int((pb + 0.08) * TAXA)])
            inicio = " ".join(txt.lower().replace(",", " ").replace(".", " ").split()[:2])
            if inicio and inicio == anterior:
                print(f"    <<< REPETIÇÃO em {a + pa:.2f}-{a + pb:.2f}: {txt}")
            # A falsa partida pode vir irreconhecível: pedaço curto no começo do trecho é suspeito.
            if pa < 0.4 and pb - pa < 0.8 and b - a > 2.0:
                print(f"    <<< PEDAÇO CURTO NO COMEÇO em {a + pa:.2f}-{a + pb:.2f}: {txt}")
            anterior = inicio


def cortar(escolhas: Path, saida: Path) -> None:
    """Junta os trechos escolhidos num vídeo 1080x1920, 30 quadros, cor convertida do HDR se precisar.
    O tratamento de cor e de voz fica para o "cortar" do motor, que roda em todo vídeo."""
    dados = ler_json(escolhas)
    bruto = _bruto(escolhas, dados)
    com_video = tem_video(bruto)
    hdr = ("zscale=t=linear:npl=203,tonemap=hable:desat=0,zscale=p=bt709:t=bt709:m=bt709:r=tv,format=yuv420p,"
           "setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709,"
           if com_video and eh_hdr(bruto) else "")
    trechos, ent, fil = faixas(dados, escolhas.parent), [], []
    for i, (ini, fim) in enumerate(trechos):
        ent += ["-ss", f"{ini:.3f}", "-to", f"{fim:.3f}", "-i", str(bruto)]
        fil.append((f"[{i}:v:0]fps=30,{hdr}scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,"
                    f"setpts=PTS-STARTPTS[v{i}];" if com_video else "") +
                   f"[{i}:a:0]aresample=48000,asetpts=PTS-STARTPTS,afade=t=in:d=0.008,"
                   f"afade=t=out:st={max(fim - ini - 0.012, 0):.3f}:d=0.012[a{i}]")
    n = len(trechos)
    if com_video:
        fil.append("".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[v][a]")
        mapa = ["-map", "[v]", "-map", "[a]"]
    else:
        fil.append("".join(f"[a{i}]" for i in range(n)) + f"concat=n={n}:v=0:a=1[a]")
        ent += preto(sum(b - a for a, b in trechos))
        mapa = ["-map", f"{n}:v", "-map", "[a]"]
    subprocess.run(["ffmpeg", "-v", "error", "-y", *ent, "-filter_complex", ";".join(fil), *mapa,
                    "-c:v", "libx264", "-crf", "16", "-preset", "fast", "-g", "30", "-pix_fmt", "yuv420p",
                    "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                    "-c:a", "aac", "-b:a", "256k", str(saida)], check=True)
    print(f"{len(trechos)} trechos em {saida}" + (" (convertido do HDR)" if hdr else ""))
