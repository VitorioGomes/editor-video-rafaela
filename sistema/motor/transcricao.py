"""Transcrição com o tempo de cada palavra (faster-whisper).

Um motor só para tudo: usa a placa de vídeo NVIDIA se houver e o processador se não houver, igual no Windows e no Mac.
Placa NVIDIA sem as bibliotecas da NVIDIA: o motor para e explica, e a pessoa decide entre instalar ou seguir no
processador ("transcricao": {"dispositivo": "processador"} no marca.json). Ele não troca sozinho.
Os modelos baixam sozinhos na primeira vez (o "large-v3" tem uns 3 GB e o "turbo", uns 1,6 GB).
"""
from __future__ import annotations

from pathlib import Path

from .comum import SISTEMA, audio, config, gravar_json, rel

_modelos: dict = {}
INSTALAR_PLACA = "python -m pip install torch --index-url https://download.pytorch.org/whl/cu128"


def placa() -> tuple[bool, bool]:
    """(tem placa NVIDIA, as bibliotecas da NVIDIA carregam). As bibliotecas vêm com o torch feito para a placa."""
    try:
        import ctranslate2
        if ctranslate2.get_cuda_device_count() == 0:
            return False, False
    except Exception:
        return False, False
    import ctypes
    import sys
    try:
        import torch  # noqa: F401  o torch da placa traz o cuBLAS e o cuDNN
    except ImportError:
        pass
    nome = "cublas64_12.dll" if sys.platform == "win32" else "libcublas.so.12"
    try:
        ctypes.CDLL(nome)
        return True, True
    except OSError:
        return True, False


def sem_bibliotecas() -> SystemExit:
    return SystemExit(
        "DECISÃO DA PESSOA: este computador tem placa de vídeo NVIDIA, mas faltam as bibliotecas da NVIDIA para usá-la.\n"
        "Pergunte o que ela prefere:\n"
        f"  1. Instalar e usar a placa (transcrição bem mais rápida; baixa uns 3 GB): {INSTALAR_PLACA}\n"
        "     Se a placa for antiga ou o driver estiver desatualizado, atualize o driver em nvidia.com antes.\n"
        '  2. Seguir no processador (funciona igual, só mais devagar): ponha "transcricao": {"dispositivo": "processador"}\n'
        "     no meu-estilo/marca.json.\n"
        "Depois, rode de novo o mesmo comando.")


def dispositivo() -> tuple[str, str]:
    escolha = config()["transcricao"].get("dispositivo", "auto")
    if escolha == "processador":
        return "cpu", "int8"
    tem, pronta = placa()
    if tem and pronta:
        return "cuda", "float16"
    if tem:
        raise sem_bibliotecas()
    return "cpu", "int8"


def modelo(rapido: bool = False):
    """O modelo grande escreve melhor nome próprio e de ferramenta (a transcrição final); o rápido serve para listar
    as tentativas, em que só importa reconhecer a frase."""
    cfg = config()["transcricao"]
    nome = cfg.get("modelo_rapido", "turbo") if rapido else cfg["modelo"]
    if nome not in _modelos:
        from faster_whisper import WhisperModel
        onde, tipo = dispositivo()
        print(f"Carregando o modelo {nome} ({'placa de vídeo' if onde == 'cuda' else 'processador'})...", flush=True)
        try:
            _modelos[nome] = WhisperModel(nome, device=onde, compute_type=tipo)
        except RuntimeError as erro:
            if onde == "cuda" and any(x in str(erro).lower() for x in ("cublas", "cudnn", "cuda")):
                raise sem_bibliotecas()
            raise
    return _modelos[nome]


idioma_ouvido: str | None = None  # o idioma da última transcrição (útil quando ele é descoberto pelo som)


def ouvir(y, vocabulario: str = "", palavras: bool = True, rapido: bool = False, idioma: str | None = "",
          **extra):
    """Transcreve um trecho de áudio (16 kHz, mono). Devolve a lista de segmentos já lida.
    idioma: "" usa o do marca.json; None descobre pelo som (vídeo de referência, que pode ser em outra língua)."""
    global idioma_ouvido
    cfg = config()
    # vocabulario: "" usa o do marca.json; None transcreve sem vocabulário nenhum
    vocab = cfg["transcricao"].get("vocabulario", "") if vocabulario == "" else (vocabulario or "")
    opcoes = dict(language=(cfg.get("idioma") or None) if idioma == "" else idioma, word_timestamps=palavras, beam_size=5,
                  initial_prompt=f"{vocab}." if vocab else None, hotwords=vocab or None, **extra)
    try:
        segmentos, info = modelo(rapido).transcribe(y, **opcoes)
        lista = list(segmentos)
        idioma_ouvido = info.language
        return lista
    except RuntimeError as erro:
        # Biblioteca da NVIDIA que falta só na hora de transcrever (cuDNN, por exemplo): a pessoa decide.
        if any(x in str(erro).lower() for x in ("cublas", "cudnn", "cuda")):
            raise sem_bibliotecas()
        raise


def corrigir(lista: list[dict]) -> list[dict]:
    """Aplica as correções do marca.json ("transcricao": {"correcoes": {"crowdcode": "Claude Code"}}): o erro, em uma
    ou mais palavras, vira o texto certo, e o tempo do trecho se reparte entre as palavras novas."""
    from .comum import normal
    regras = config()["transcricao"].get("correcoes", {})
    if not regras:
        return lista
    # A regra casa com o erro escrito junto ou separado: "crowdcoach" pega "crowd coach", e "cloud code" pega "cloudcode".
    padroes = [("".join(normal(x) for x in errado.split()), certo.split()) for errado, certo in regras.items()]
    saida, i, trocadas = [], 0, 0
    while i < len(lista):
        for k in (4, 3, 2, 1):
            junto = "".join(normal(p["texto"]) for p in lista[i:i + k])
            certo = next((c for e, c in padroes if e == junto), None) if len(lista[i:i + k]) == k else None
            if certo:
                ini, fim = lista[i]["inicio"], lista[i + k - 1]["fim"]
                pontuacao = lista[i + k - 1]["texto"][len(lista[i + k - 1]["texto"].rstrip(".,;:!?")):]
                passo = (fim - ini) / len(certo)
                for j, palavra in enumerate(certo):
                    saida.append({"texto": palavra + (pontuacao if j == len(certo) - 1 else ""),
                                  "inicio": round(ini + j * passo, 3), "fim": round(ini + (j + 1) * passo, 3)})
                i += k
                trocadas += 1
                break
        else:
            saida.append(lista[i])
            i += 1
    if trocadas:
        print(f"{trocadas} correções do marca.json aplicadas.")
    return saida


def _segmentos(resultado, desloca: float = 0.0) -> list[dict]:
    saida = []
    for s in resultado:
        palavras = [{"texto": w.word.strip(), "inicio": round(w.start + desloca, 3), "fim": round(w.end + desloca, 3)}
                    for w in s.words or [] if w.word.strip()]
        if palavras:
            saida.append({"inicio": s.start + desloca, "fim": s.end + desloca, "palavras": palavras})
    return saida


def _buracos(y, segmentos: list[dict], taxa: int = 16000) -> list[tuple[float, float]]:
    """Trechos com voz e sem palavra: o Whisper às vezes pula uma frase inteira (mais com vocabulário) e estica a
    palavra vizinha por cima dela. Palavra com mais de 0,8 s só conta os primeiros 0,8 s."""
    import numpy as np
    from .comum import niveis
    passo = 0.02
    db = niveis(y, taxa, passo)
    voz = db > max(float(np.percentile(db, 95)) - 28, -50)
    coberto = np.zeros(len(db), dtype=bool)
    for s in segmentos:
        for p in s["palavras"]:
            a = int(max(p["inicio"] - 0.15, 0) / passo)
            b = int((min(p["fim"], p["inicio"] + 0.8) + 0.15) / passo)
            coberto[a:b] = True
    sobra = voz & ~coberto
    buracos, i = [], 0
    while i < len(sobra):
        if not sobra[i]:
            i += 1
            continue
        j, falha = i, 0
        while j < len(sobra) and falha < 15:  # junta pedaços separados por menos de 0,3 s
            falha = 0 if sobra[j] else falha + 1
            j += 1
        j -= falha
        if sobra[i:j].sum() * passo >= 0.5:
            buracos.append((round(i * passo, 2), round(j * passo, 2)))
        i = j + 1
    return buracos


def transcrever(video: Path, saida: Path, vocabulario: str = "", idioma: str | None = "", corrige: bool = True) -> list:
    """Gera saida/palavras.json: [{"texto", "inicio", "fim"}, ...], com o tempo de cada palavra acertado pelo som."""
    from . import alinhamento
    saida.mkdir(parents=True, exist_ok=True)
    y = audio(video)
    segmentos = _segmentos(ouvir(y, vocabulario, idioma=idioma, condition_on_previous_text=False))
    idioma = idioma_ouvido
    # Voz sem palavra: transcreve de novo o trecho com as frases em volta, sem o vocabulário (que às vezes é o que
    # faz pular), e fica com a versão nova se ela tiver mais palavras.
    for a, b in _buracos(y, segmentos):
        vizinhos = [s for s in segmentos if s["fim"] > a - 0.5 and s["inicio"] < b + 0.5]
        ini = max(min([a] + [s["inicio"] for s in vizinhos]) - 0.3, 0)
        fim = max([b] + [s["fim"] for s in vizinhos]) + 0.3
        novos = _segmentos(ouvir(y[int(ini * 16000):int(fim * 16000)], None, idioma=idioma,
                                 condition_on_previous_text=False), ini)
        antes = sum(len(s["palavras"]) for s in vizinhos)
        depois = sum(len(s["palavras"]) for s in novos)
        if depois > antes:
            segmentos = [s for s in segmentos if s not in vizinhos] + novos
            texto = " ".join(p["texto"] for s in novos for p in s["palavras"])
            print(f"Voz sem palavra em {a:.1f}-{b:.1f} s; o trecho transcrito de novo ficou: \"{texto}\"")
        elif not vizinhos:
            print(f"Aviso: voz sem palavra em {a:.1f}-{b:.1f} s (riso, respiro ou uma frase pulada?): confira.")
    segmentos.sort(key=lambda s: s["inicio"])
    lista = [p for s in segmentos for p in s["palavras"]]
    if alinhamento.disponivel(idioma):
        feitas = alinhamento.alinhar(y, segmentos, idioma)
        print(f"Tempo acertado pelo som em {feitas} de {len(lista)} palavras.")
    else:
        print("Aviso: sem o alinhador (torch e transformers), o tempo das palavras pode sair até 0,3 s fora. "
              f"Instale com: python -m pip install -r {rel(SISTEMA / 'requisitos.txt')}")
    lista.sort(key=lambda p: p["inicio"])
    for p, seguinte in zip(lista, lista[1:]):  # a palavra esticada por cima da frase pulada termina onde a outra começa
        p["fim"] = round(min(p["fim"], max(seguinte["inicio"], p["inicio"] + 0.05)), 3)
    if corrige:
        lista = corrigir(lista)
    gravar_json(saida / "palavras.json", lista)
    if not corrige:  # referência: o texto vai para o resumo
        return lista
    print(" ".join(p["texto"] for p in lista))
    print(f"{len(lista)} palavras em {saida / 'palavras.json'}. Conferir o texto com o roteiro antes de usar.")
    return lista
