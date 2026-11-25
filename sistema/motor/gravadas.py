"""Falas gravadas pela pessoa (o áudio do celular) no lugar da voz de IA, para os estilos com mais de uma voz
(Série Animada, Estilo Conversa) ou com o texto marcado por fala.

O texto é o mesmo da voz de IA: uma fala por linha, "[nome] fala" para um personagem, linha sem marcação para o
narrador e "[pausa 0.6]" para o silêncio depois da fala de cima. Os áudios podem vir de três jeitos:

  um áudio só, com todas as falas na ordem do texto (as duas vozes no mesmo arquivo): quem fala vem da ordem;
  um áudio por personagem, com o nome dele no arquivo (claude.m4a, eu.m4a, narrador.mp3): as falas dele, na ordem;
  um áudio por fala, na ordem do texto (tantos arquivos quanto falas).

Cada áudio é transcrito e cortado como qualquer gravação (sem as pausas, com o tratamento de voz). Depois, cada fala
do texto é achada no que foi ouvido, tirada do áudio dela e posta em ordem, com a pausa do texto entre uma e outra.
Sai o mesmo que a voz de IA grava: voz.wav, palavras.json (com "quem" e "fala"), falas.json e base.mp4.
O texto da tela é o do roteiro; o tempo de cada palavra é o da gravação. Palavra dita diferente do texto ("catorze
zero cinco" no lugar de "1405") fica com o tempo repartido entre as vizinhas.
"""
from __future__ import annotations

import difflib
import subprocess
from pathlib import Path

from .comum import EDITAR, audio, config, duracao, gravar_json, ler_json, niveis, normal, rel
from .voz import _limpa, ler_falas

ALVO_DB = -20.0  # nível da fala de todas as gravações, para uma voz não sair mais alta que a outra


def _distribuir(falas: list[dict], audios: list[Path]) -> dict[int, list[int]]:
    """Qual áudio tem quais falas (os números das falas, na ordem do texto)."""
    if len(audios) == 1:
        return {0: list(range(len(falas)))}
    quem = {f["quem"] for f in falas}
    nomes = [_limpa(a.stem) for a in audios]
    if quem <= set(nomes) and len(set(nomes)) == len(nomes):
        return {i: [n for n, f in enumerate(falas) if f["quem"] == nome] for i, nome in enumerate(nomes)}
    if len(audios) == len(falas):
        return {i: [i] for i in range(len(falas))}
    raise SystemExit(
        f"{len(audios)} áudios para {len(falas)} falas de {', '.join(sorted(quem))}. Use um destes jeitos:\n"
        "  um áudio só, com as falas na ordem do texto;\n"
        f"  um áudio por personagem, com o nome dele no arquivo ({', '.join(sorted(quem))});\n"
        f"  um áudio por fala ({len(falas)} arquivos, na ordem do texto).")


def _preparar(audio_: Path, pasta: Path, vocabulario: str) -> list[dict]:
    """Transcreve e corta o áudio (só da primeira vez: o resultado fica em pasta/)."""
    from .corte import cortar
    from .transcricao import transcrever
    pronto = pasta / "corte" / "palavras.json"
    if pronto.exists() and pronto.stat().st_mtime > audio_.stat().st_mtime:
        print(f"{audio_.name}: já transcrito e cortado, reaproveitado.")
        return ler_json(pronto)
    print(f"{audio_.name}: transcrevendo...")
    transcrever(audio_, pasta / "fala", vocabulario)
    cortar(audio_, pasta / "fala" / "palavras.json", pasta / "corte")
    return ler_json(pronto)


def _achar(falas: list[dict], numeros: list[int], ouvidas: list[dict], nome: str) -> dict[int, list[tuple]]:
    """O tempo de cada palavra de cada fala, achado nas palavras ouvidas (na ordem)."""
    escritas = [(n, k, p) for n in numeros for k, p in enumerate(falas[n]["texto"].split())]
    a = [normal(p) for _, _, p in escritas]
    b = [normal(p["texto"]) for p in ouvidas]
    par: dict[int, int] = {}
    for bloco in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
        for d in range(bloco.size):
            par[bloco.a + d] = bloco.b + d
    tempos: dict[int, list[tuple]] = {}
    i = 0
    for n in numeros:
        palavras = falas[n]["texto"].split()
        idx = list(range(i, i + len(palavras)))
        i += len(palavras)
        achadas = [par[j] for j in idx if j in par]
        if not achadas:
            raise SystemExit(f'A fala {n} ("{falas[n]["texto"][:60]}") não apareceu em {nome}. '
                             "Ela foi gravada? Confira a ordem das falas e o texto.")
        if len(achadas) < len(idx) / 2:
            print(f'Aviso: a fala {n} ("{falas[n]["texto"][:50]}") bateu em só {len(achadas)} de {len(idx)} '
                  "palavras com a gravação: ouça e confira.")
        # palavra sem par: o tempo vem das vizinhas que têm par, repartido por igual
        lista: list[tuple | None] = [(ouvidas[par[j]]["inicio"], ouvidas[par[j]]["fim"]) if j in par else None for j in idx]
        h0, h1 = min(achadas), max(achadas)
        # as palavras ouvidas logo antes e depois que não são de outra fala entram no começo e no fim
        livres = set(range(len(ouvidas))) - set(par.values())
        while h0 - 1 in livres and lista[0] is None:
            h0 -= 1
            livres.discard(h0)
            lista[0] = (ouvidas[h0]["inicio"], ouvidas[h0]["fim"])
        while h1 + 1 in livres and lista[-1] is None:
            h1 += 1
            livres.discard(h1)
            lista[-1] = (ouvidas[h1]["inicio"], ouvidas[h1]["fim"])
        ini_fala, fim_fala = ouvidas[h0]["inicio"], ouvidas[h1]["fim"]
        k = 0
        while k < len(lista):
            if lista[k] is not None:
                k += 1
                continue
            m = k
            while m < len(lista) and lista[m] is None:
                m += 1
            de = lista[k - 1][1] if k else ini_fala
            ate = lista[m][0] if m < len(lista) else fim_fala
            passo = max(ate - de, 0.06 * (m - k)) / (m - k)
            for q in range(k, m):
                lista[q] = (de + passo * (q - k), de + passo * (q - k + 1))
            k = m
        tempos[n] = lista
    return tempos


def falas_gravadas(texto: Path, audios: list[Path], saida: Path, vocabulario: str = "") -> None:
    conteudo = texto.read_text(encoding="utf-8")
    falas = ler_falas(conteudo)
    if falas is None:  # texto sem marcação: cada linha é uma fala do narrador
        falas = [{"quem": "narrador", "texto": l.strip()} for l in conteudo.splitlines() if l.strip()]
    for a in audios:
        if not a.exists():
            raise SystemExit(f"Não achei o áudio {a}.")
    geral = config().get("voz", {})
    grupos = _distribuir(falas, audios)
    trabalho = saida / "gravacao"
    trechos: dict[int, tuple] = {}  # fala -> (voz.wav, de, até, tempos das palavras, ganho)
    for i, numeros in grupos.items():
        if not numeros:
            continue
        pasta = trabalho / f"{i:02d}-{_limpa(audios[i].stem) or 'audio'}"
        ouvidas = _preparar(audios[i], pasta, vocabulario)
        tempos = _achar(falas, numeros, ouvidas, audios[i].name)
        voz = pasta / "corte" / "voz.wav"
        total = duracao(voz)
        # nível da fala desta gravação (a mediana das janelas com voz), para igualar as vozes
        db = niveis(audio(voz), 16000, 0.1)
        com_voz = sorted(x for x in db if x > -45)
        ganho = ALVO_DB - (com_voz[len(com_voz) // 2] if com_voz else ALVO_DB)
        for j, n in enumerate(numeros):
            ini = tempos[n][0][0] - 0.06
            fim = tempos[n][-1][1] + 0.15
            if j:  # não pega o fim da fala anterior do mesmo áudio
                ini = max(ini, (tempos[numeros[j - 1]][-1][1] + tempos[n][0][0]) / 2)
            if j + 1 < len(numeros):
                fim = min(fim, (tempos[n][-1][1] + tempos[numeros[j + 1]][0][0]) / 2)
            ini, fim = max(ini, 0.0), min(fim, total)
            trechos[n] = (voz, ini, fim, [(a - ini, b - ini) for a, b in tempos[n]], ganho)

    pasta_falas = saida / "falas"
    pasta_falas.mkdir(parents=True, exist_ok=True)
    partes, palavras, lista = [], [], []
    t = geral.get("inicio", 0.4)
    for n, f in enumerate(falas):
        voz, ini, fim, rel, ganho = trechos[n]
        arq = pasta_falas / f"{n:02d}.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{ini:.3f}", "-to", f"{fim:.3f}", "-i", str(voz),
                        "-af", f"volume={ganho:.2f}dB,afade=t=in:d=0.01,afade=t=out:st={max(fim - ini - 0.03, 0):.3f}:d=0.03",
                        "-ar", "48000", "-ac", "1", str(arq)], check=True)
        dur = fim - ini
        for txt, (a, b) in zip(f["texto"].split(), rel):
            palavras.append({"texto": txt, "inicio": round(t + a, 3), "fim": round(t + b, 3), "quem": f["quem"], "fala": n})
        lista.append({"quem": f["quem"], "texto": f["texto"], "inicio": round(t, 3), "fim": round(t + dur, 3)})
        partes.append((arq, t))
        t += dur + f.get("pausa", geral.get("pausa", 0.3))
    total = lista[-1]["fim"] + geral.get("fim", 1.0)
    args = ["ffmpeg", "-v", "error", "-y"]
    for p, _ in partes:
        args += ["-i", str(p)]
    filtro = [f"[{j}]aformat=sample_rates=48000:channel_layouts=mono,adelay={int(ini * 1000)}:all=1[a{j}]"
              for j, (_, ini) in enumerate(partes)]
    filtro.append("".join(f"[a{j}]" for j in range(len(partes)))
                  + f"amix=inputs={len(partes)}:normalize=0,apad=whole_dur={total:.3f},atrim=0:{total:.3f}[o]")
    args += ["-filter_complex", ";".join(filtro), "-map", "[o]", "-ar", "48000", "-ac", "1", str(saida / "voz.wav")]
    subprocess.run(args, check=True)
    gravar_json(saida / "palavras.json", palavras)
    gravar_json(saida / "falas.json", {"duracao": round(total, 3), "falas": lista})
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=black:s=1080x1920:r=30", "-i",
                    str(saida / "voz.wav"), "-t", f"{total:.3f}", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "256k", str(saida / "base.mp4")], check=True)
    quem = sorted({f["quem"] for f in falas})
    print(f"{len(falas)} falas ({', '.join(quem)}), {len(palavras)} palavras, {total:.2f} s em {saida}")
    print(f"Confira as falas com: {EDITAR} falas {rel(saida / 'palavras.json')}")
