"""Acerta o tempo de cada palavra pelo som (alinhamento forçado), como o WhisperX faz.

O Whisper acerta as palavras, mas o tempo delas sai 0,1 a 0,3 s fora, e o texto na tela entra antes ou depois da fala.
Aqui um modelo que reconhece cada letra no som (wav2vec2) encontra onde cada palavra começa e termina, a uns 0,04 s.
Roda no processador ou na placa de vídeo. O modelo baixa sozinho na primeira vez (uns 1,2 GB).
Sem o torch instalado, ou num idioma sem modelo, as palavras ficam com o tempo do Whisper.
"""
from __future__ import annotations

MODELOS = {
    "pt": "jonatasgrosman/wav2vec2-large-xlsr-53-portuguese",
    "en": "jonatasgrosman/wav2vec2-large-xlsr-53-english",
    "es": "jonatasgrosman/wav2vec2-large-xlsr-53-spanish",
}
TAXA = 16000
_carregado: dict = {}


_UNID = ["zero", "um", "dois", "três", "quatro", "cinco", "seis", "sete", "oito", "nove", "dez", "onze", "doze", "treze",
         "quatorze", "quinze", "dezesseis", "dezessete", "dezoito", "dezenove"]
_DEZ = ["", "", "vinte", "trinta", "quarenta", "cinquenta", "sessenta", "setenta", "oitenta", "noventa"]
_CEM = ["", "cento", "duzentos", "trezentos", "quatrocentos", "quinhentos", "seiscentos", "setecentos", "oitocentos", "novecentos"]


def _extenso(n: int) -> str:
    """Número inteiro por extenso, em português (até 999.999.999)."""
    if n < 20:
        return _UNID[n]
    if n < 100:
        return _DEZ[n // 10] + ("" if n % 10 == 0 else " e " + _UNID[n % 10])
    if n < 1000:
        if n == 100:
            return "cem"
        return _CEM[n // 100] + ("" if n % 100 == 0 else " e " + _extenso(n % 100))
    if n < 1_000_000:
        mil, resto = divmod(n, 1000)
        frente = "mil" if mil == 1 else _extenso(mil) + " mil"
        if not resto:
            return frente
        return frente + (" e " if resto < 100 or resto % 100 == 0 else " ") + _extenso(resto)
    milhao, resto = divmod(n, 1_000_000)
    frente = "um milhão" if milhao == 1 else _extenso(milhao) + " milhões"
    return frente if not resto else frente + " " + _extenso(resto)


def falado(texto: str, idioma: str | None) -> str:
    """Como o número soa, para o alinhador achar no som: "2026" vira "dois mil e vinte e seis", "19,90" vira
    "dezenove e noventa", "23%" vira "vinte e três por cento". Fora do português, o texto volta igual."""
    import re
    if idioma != "pt" or not re.search(r"\d", texto):
        return texto

    def troca(m):
        inteiro, decimal = m.group(1).replace(".", ""), m.group(2)
        dito = _extenso(int(inteiro)) if len(inteiro) < 10 else inteiro
        if decimal and int(decimal):
            dito += " e " + _extenso(int(decimal))
        return " " + dito + " "
    texto = re.sub(r"(\d{1,3}(?:\.\d{3})+|\d+)(?:,(\d+))?", troca, texto)
    texto = texto.replace("%", " por cento ").replace("R$", " ")
    return re.sub(r"\s+", " ", texto).strip()


def disponivel(idioma: str | None) -> bool:
    if idioma not in MODELOS:
        return False
    try:
        import torch  # noqa: F401
        import transformers  # noqa: F401
        return True
    except ImportError:
        return False


def _modelo(idioma: str):
    if idioma not in _carregado:
        import torch
        from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
        onde = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Carregando o alinhador ({'placa de vídeo' if onde == 'cuda' else 'processador'})...", flush=True)
        processador = Wav2Vec2Processor.from_pretrained(MODELOS[idioma])
        modelo = Wav2Vec2ForCTC.from_pretrained(MODELOS[idioma]).to(onde).eval()
        _carregado[idioma] = (processador, modelo, onde)
    return _carregado[idioma]


def _caminho(emissao, alvos: list[int], branco: int) -> list[int] | None:
    """Viterbi do CTC: o quadro em que cada letra do texto é dita. None se o trecho for curto demais para o texto."""
    import numpy as np
    quadros, n = emissao.shape[0], len(alvos)
    if n == 0 or n > quadros:
        return None
    alvo = np.array(alvos)
    grade = np.full((quadros + 1, n + 1), -np.inf, dtype=np.float32)
    grade[0, 0] = 0.0
    for t in range(quadros):
        grade[t + 1, 0] = grade[t, 0] + emissao[t, branco]
        grade[t + 1, 1:] = np.maximum(grade[t, 1:] + emissao[t, branco], grade[t, :-1] + emissao[t, alvo])
    inicio = [0] * n
    j, t = n, quadros
    while j > 0 and t > 0:
        ficou = grade[t - 1, j] + emissao[t - 1, branco]
        andou = grade[t - 1, j - 1] + emissao[t - 1, alvo[j - 1]]
        t -= 1
        if andou >= ficou:
            inicio[j - 1] = t
            j -= 1
    return inicio if j == 0 else None


def alinhar(y, segmentos: list[dict], idioma: str) -> int:
    """segmentos: [{"inicio", "fim", "palavras": [{"texto", "inicio", "fim"}, ...]}]. Ajusta os tempos no lugar.
    Devolve quantas palavras foram alinhadas pelo som."""
    import numpy as np
    import torch
    processador, modelo, onde = _modelo(idioma)
    vocab = processador.tokenizer.get_vocab()
    branco = processador.tokenizer.pad_token_id
    separador = vocab.get("|")
    total = len(y) / TAXA
    alinhadas = 0
    for s in segmentos:
        a, b = max(0.0, s["inicio"] - 0.1), min(total, s["fim"] + 0.1)
        trecho = y[int(a * TAXA):int(b * TAXA)]
        if len(trecho) < TAXA // 10:
            continue
        entrada = processador(trecho, sampling_rate=TAXA, return_tensors="pt").input_values.to(onde)
        with torch.inference_mode():
            emissao = torch.log_softmax(modelo(entrada).logits[0], dim=-1).float().cpu().numpy()
        passo = (b - a) / emissao.shape[0]
        # As letras de cada palavra, com o separador entre as palavras; letra fora do vocabulário (número, símbolo) fica de fora.
        alvos, dono = [], []
        for k, p in enumerate(s["palavras"]):
            # Número escrito em algarismos entra por extenso, para ter letra que o alinhador ache no som.
            letras = [vocab[c] for c in falado(p["texto"], idioma).lower().replace(" ", "") if c in vocab and c != "|"]
            if alvos and separador is not None and letras:
                alvos.append(separador)
                dono.append(-1)
            alvos += letras
            dono += [k] * len(letras)
        inicio = _caminho(emissao, alvos, branco)
        if inicio is None:
            continue
        quadros: dict[int, list[int]] = {}
        for pos, k in enumerate(dono):
            if k >= 0:
                quadros.setdefault(k, []).append(inicio[pos])
        for k, qs in quadros.items():
            p = s["palavras"][k]
            p["inicio"] = round(a + qs[0] * passo, 3)
            p["fim"] = round(max(a + (qs[-1] + 1) * passo, p["inicio"] + 0.04), 3)
            alinhadas += 1
        # Palavra sem letra alinhável (um símbolo solto) fica entre as vizinhas.
        lista = s["palavras"]
        for k, p in enumerate(lista):
            if k not in quadros:
                antes = lista[k - 1]["fim"] if k else a
                depois = next((lista[x]["inicio"] for x in range(k + 1, len(lista)) if x in quadros), b)
                p["inicio"] = round(max(p["inicio"], antes), 3)
                p["fim"] = round(min(max(p["fim"], p["inicio"] + 0.04), depois), 3)
    return alinhadas
