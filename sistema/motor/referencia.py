"""Engenharia reversa de um vídeo de referência: tudo o que a IA precisa para entender e montar um estilo.

O vídeo vem de um link público (Instagram, TikTok, YouTube) ou de um arquivo. Sai uma pasta com:
  resumo.md         ritmo, cores, som, fala e a lista das imagens para olhar
  gancho.jpg        os 3 primeiros segundos, 4 quadros por segundo
  cortes-N.jpg      um quadro logo depois de cada corte
  entradas-N.jpg    cada coisa que entra na tela sem corte (texto, print, animação), já entrada
  efeitos-N.jpg     a tela no instante de cada efeito sonoro
  video-N.jpg       o vídeo inteiro, um quadro por segundo
  palavras.json     a fala com o tempo de cada palavra
  medidas.json      os números, para comparar depois com o vídeo editado (comando "comparar")

Tudo roda no PC, sem serviço pago. O som é medido, não ouvido: a voz é separada do resto (Demucs), e o que sobra
mostra a música e cada efeito, com a duração e o timbre.
"""
from __future__ import annotations

import json
import math
import re
import subprocess
import sys
from pathlib import Path

from .comum import EDITAR, FONTES, duracao, gravar_json, ler_json, rodar

QUADRO_W, QUADRO_H = 270, 480  # miniatura nas folhas: dá para ler texto grande e ver a composição
TAXA_SOM = 22050
SEPARADOR = "htdemucs"  # o "_ft" separa a voz mais limpa, mas leva junto o clique que cai em cima da fala


# ---------------------------------------------------------------- vídeo

def obter(fonte: str, pasta: Path) -> tuple[Path, dict]:
    """Baixa na maior resolução (vídeo público, sem login) ou copia o arquivo."""
    video = pasta / "video.mp4"
    if Path(fonte).exists():
        if Path(fonte).resolve() != video:
            rodar(["ffmpeg", "-v", "error", "-y", "-i", fonte, "-c", "copy", video])
        return video, {"fonte": str(Path(fonte).resolve())}
    try:
        import yt_dlp  # noqa: F401
    except ImportError:
        sys.exit("Falta o yt-dlp para baixar o vídeo: python -m pip install yt-dlp\n"
                 "Ou baixe o vídeo à mão e passe o arquivo no lugar do link.")
    info = subprocess.run([sys.executable, "-m", "yt_dlp", "--dump-json", "--skip-download", "--no-warnings", fonte],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
    post = {"fonte": fonte}
    if info.returncode == 0:
        meta = json.loads(info.stdout)
        post.update({k: meta.get(k) for k in ("uploader", "timestamp", "view_count", "like_count", "comment_count",
                                              "duration", "description")})
    baixa = subprocess.run([sys.executable, "-m", "yt_dlp", "-q", "--no-warnings", "-f", "bv*+ba/b", "-S", "res,br",
                            "--merge-output-format", "mp4", "--force-overwrites", "-o", str(video), fonte],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
    if baixa.returncode or not video.exists():
        sys.exit(f"Não deu para baixar: {baixa.stderr.strip()[-300:]}\n"
                 "Vídeo privado ou que pede login não baixa. Baixe à mão (ou grave a tela) e passe o arquivo.")
    return video, post


def formato(video: Path) -> dict:
    r = rodar(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,r_frame_rate",
               "-of", "json", video])
    s = json.loads(r.stdout)["streams"][0]
    num, den = s["r_frame_rate"].split("/")
    return {"largura": s["width"], "altura": s["height"], "fps": round(float(num) / float(den), 2),
            "duracao": round(duracao(video), 2)}


def cortes(video: Path) -> list[float]:
    """Troca de cena acima de 0,3: corte seco, troca de plano ou zoom seco."""
    log = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(video), "-vf", "select='gt(scene,0.3)',showinfo",
                          "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
    return [round(float(t), 2) for t in re.findall(r"pts_time:([\d.]+)", log)]


def _cinza(video: Path, fps: int = 10, w: int = 108, h: int = 192):
    import numpy as np
    bruto = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-vf", f"fps={fps},scale={w}:{h},format=gray",
                            "-f", "rawvideo", "-"], capture_output=True).stdout
    return np.frombuffer(bruto, dtype=np.uint8).reshape(-1, h, w).astype(np.int16)


def entradas(video: Path, lista_cortes: list[float], altura: int) -> list[dict]:
    """O que entra na tela sem corte: um pedaço da imagem muda de repente enquanto o resto fica.
    Fala e gesto mudam pouco e espalhado; texto, print e animação mudam muito num lugar só."""
    import numpy as np
    fps = 10
    q = _cinza(video, fps)
    if len(q) < 3:
        return []
    mud = np.abs(q[2:] - q[:-2]) > 28  # 0,2 s: pega também o que entra em fade curto
    fracao = mud.mean(axis=(1, 2))
    achados, ultimo = [], -1.0
    for i in range(1, len(fracao) - 1):
        t = (i + 2) / fps
        janela = fracao[max(0, i - 15):i + 15]
        if fracao[i] < max(0.01, 3 * float(np.median(janela))) or fracao[i] < fracao[i - 1] or fracao[i] < fracao[i + 1]:
            continue
        if any(abs(t - c) < 0.35 for c in lista_cortes) or t - ultimo < 0.3 or fracao[i] > 0.6:
            continue
        ys = np.nonzero(mud[i].any(axis=1))[0]
        if not len(ys):
            continue
        y0, y1 = np.percentile(ys, [5, 95]) * altura / mud.shape[1]
        achados.append({"t": round(t, 2), "y": [int(y0), int(y1)], "area": round(float(fracao[i]), 3)})
        ultimo = t
    return achados


def _eventos(lista: list[dict]) -> list[dict]:
    """Os efeitos certos, com cada rajada contada uma vez (o primeiro toque, com quantos vieram juntos)."""
    eventos = []
    for e in lista:
        if not e["certo"]:
            continue
        if e.get("rajada"):
            eventos[-1]["toques"] = eventos[-1].get("toques", 1) + 1
        else:
            eventos.append(dict(e))
    return eventos


def cores(video: Path, total: float) -> dict:
    """As cores que dominam e as cores fortes (as de texto e destaque costumam estar aqui)."""
    import numpy as np
    from PIL import Image
    passo = max(total / 24, 0.5)
    bruto = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-vf", f"fps=1/{passo:.3f},scale=90:160",
                            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    px = np.frombuffer(bruto, dtype=np.uint8).reshape(-1, 3)
    if not len(px):
        return {}

    def paleta(pontos, n):
        if len(pontos) < n:
            return []
        img = Image.fromarray(pontos.reshape(1, -1, 3)).quantize(colors=n, method=Image.Quantize.MEDIANCUT)
        pal = img.getpalette()[:n * 3]
        conta = np.bincount(np.asarray(img).ravel(), minlength=n)
        saida = [("#%02x%02x%02x" % tuple(pal[k * 3:k * 3 + 3]), round(100 * conta[k] / conta.sum(), 1))
                 for k in range(n)]
        return sorted(saida, key=lambda c: -c[1])

    rgb = px.astype(float) / 255
    mx, mn = rgb.max(1), rgb.min(1)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    fortes = px[(sat > 0.45) & (mx > 0.35)]
    return {"dominantes": paleta(px, 8), "fortes": paleta(fortes, 6),
            "fortes_porcento": round(100 * len(fortes) / len(px), 1)}


# ---------------------------------------------------------------- folhas de quadros

def _fonte(tamanho: int):
    """A Inter que vem com o produto (tem acento); a fonte padrão do Pillow, se ela não abrir."""
    from PIL import ImageFont
    try:
        return ImageFont.truetype(str(FONTES / "Inter-Bold.woff2"), tamanho)
    except OSError:
        try:
            return ImageFont.load_default(size=tamanho)
        except TypeError:
            return ImageFont.load_default()


def quadro(video: Path, t: float, largura: int = QUADRO_W):
    from io import BytesIO

    from PIL import Image
    png = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(t, 0):.3f}", "-i", str(video), "-frames:v", "1",
                          "-vf", f"scale={largura}:-2", "-f", "image2pipe", "-c:v", "png", "-"], capture_output=True).stdout
    return Image.open(BytesIO(png)).convert("RGB") if png else None


def folhas(video: Path, itens: list[tuple[float, str]], nome: Path, colunas: int = 6, linhas: int = 3) -> list[Path]:
    """Miniaturas com o tempo embaixo, em folhas de até colunas×linhas. Devolve os arquivos."""
    from PIL import Image, ImageDraw
    feitas, porfolha = [], colunas * linhas
    fonte = _fonte(22)
    for n in range(0, len(itens), porfolha):
        grupo = itens[n:n + porfolha]
        lin = math.ceil(len(grupo) / colunas)
        folha = Image.new("RGB", (colunas * (QUADRO_W + 6), lin * (QUADRO_H + 36)), (24, 24, 24))
        d = ImageDraw.Draw(folha)
        for k, (t, rotulo) in enumerate(grupo):
            img = quadro(video, t)
            x, y = (k % colunas) * (QUADRO_W + 6), (k // colunas) * (QUADRO_H + 36)
            if img:
                folha.paste(img.resize((QUADRO_W, QUADRO_H)), (x, y))
            d.text((x + 6, y + QUADRO_H + 6), rotulo, fill=(255, 230, 120), font=fonte)
        arquivo = nome.with_name(f"{nome.stem}-{n // porfolha + 1}.jpg") if len(itens) > porfolha else nome.with_suffix(".jpg")
        folha.save(arquivo, quality=88)
        feitas.append(arquivo)
    return feitas


# ---------------------------------------------------------------- som

def _demucs():
    """Carrega o Demucs sem as partes que ele usa só para treinar (dora) nem o torchaudio, que pede uma versão exata do
    torch e trocaria o torch da placa de vídeo. Instalação: ver requisitos.txt."""
    import importlib.util
    import types
    if "dora.log" not in sys.modules:
        dora, log = types.ModuleType("dora"), types.ModuleType("dora.log")
        log.fatal = lambda *a, **k: (_ for _ in ()).throw(SystemExit(" ".join(map(str, a))))
        log.bold = lambda s: s
        dora.log = log
        sys.modules.update({"dora": dora, "dora.log": log})
    if "openunmix.filtering" not in sys.modules:
        achado = importlib.util.find_spec("openunmix")
        if not achado:
            raise ImportError("openunmix")
        pacote = types.ModuleType("openunmix")
        pacote.__path__ = []
        spec = importlib.util.spec_from_file_location("openunmix.filtering",
                                                      Path(achado.submodule_search_locations[0]) / "filtering.py")
        filtro = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(filtro)
        pacote.filtering = filtro
        sys.modules.update({"openunmix": pacote, "openunmix.filtering": filtro})
    from demucs.apply import apply_model
    from demucs.pretrained import get_model
    return get_model, apply_model


def separar(video: Path, pasta: Path):
    """Voz e o resto (música + efeitos + ambiente), em mono a 22 kHz. None se o Demucs não estiver instalado."""
    import numpy as np
    pasta.mkdir(parents=True, exist_ok=True)
    cache = pasta / f"som-{SEPARADOR}.npz"
    if cache.exists():
        d = np.load(cache)
        return d["voz"], d["resto"]
    try:
        get_model, apply_model = _demucs()
        import torch
    except ImportError:
        return None
    print("Separando a voz do resto do som (Demucs; na primeira vez baixa uns 80 MB)...", flush=True)
    modelo = get_model(SEPARADOR)
    modelo.eval()
    taxa = modelo.samplerate
    bruto = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-map", "0:a:0", "-ac", "2", "-ar", str(taxa),
                            "-f", "f32le", "-"], capture_output=True).stdout
    y = torch.from_numpy(np.frombuffer(bruto, dtype=np.float32).reshape(-1, 2).T.copy())
    ref = y.mean(0)
    media, desvio = ref.mean(), ref.std() + 1e-8
    onde = "cuda" if torch.cuda.is_available() else "cpu"
    with torch.no_grad():
        fontes = apply_model(modelo, ((y - media) / desvio)[None], device=onde, shifts=1, split=True, overlap=0.25,
                             progress=False)[0]
    fontes = fontes * desvio + media
    i = modelo.sources.index("vocals")
    voz = fontes[i].mean(0).cpu().numpy()
    resto = (fontes.sum(0) - fontes[i]).mean(0).cpu().numpy()

    def reduz(x):  # 44,1 kHz para 22,05 kHz: média de pares basta para medir
        x = x[:len(x) // 2 * 2]
        return x.reshape(-1, 2).mean(1).astype(np.float32)
    voz, resto = reduz(voz), reduz(resto)
    np.savez_compressed(cache, voz=voz, resto=resto)
    return voz, resto


def _db(x, passo: int):
    import numpy as np
    n = len(x) // passo
    rms = np.sqrt((x[:n * passo].reshape(n, passo) ** 2).mean(1))
    return 20 * np.log10(rms + 1e-7)


def musica(voz, resto) -> dict:
    """Trilha contínua nunca deixa o fundo sem voz chegar perto do silêncio."""
    import numpy as np
    seg = TAXA_SOM
    fundo, fala = _db(resto, seg), _db(voz, seg)
    if not len(fundo):
        return {"tem": False}
    calado = float(np.mean(fundo < -50))
    com_som = fundo > -45
    tem = calado < 0.15 and float(np.mean(com_som)) > 0.7
    falando = fala > float(np.percentile(fala, 60)) - 6
    abaixo = float(np.median(fala[falando] - fundo[falando])) if tem and falando.any() else None
    return {"tem": bool(tem), "segundos_em_silencio": int((fundo < -50).sum()),
            "abaixo_da_voz_db": round(abaixo, 1) if abaixo is not None else None}


def _timbre(resto, t: float, dura: float) -> str:
    """Grave, médio ou agudo: o centro de energia do que subiu acima do fundo."""
    import numpy as np
    a, b = int(t * TAXA_SOM), int((t + max(dura, 0.04)) * TAXA_SOM)
    trecho = resto[a:b]
    if len(trecho) < 256:
        return "?"
    esp = np.abs(np.fft.rfft(trecho * np.hanning(len(trecho)))) ** 2
    f = np.fft.rfftfreq(len(trecho), 1 / TAXA_SOM)
    centro = float((esp * f).sum() / (esp.sum() + 1e-12))
    return "grave" if centro < 500 else "agudo" if centro > 2500 else "médio"


def efeitos(resto, voz) -> list[dict]:
    """Ataques no som sem voz: um salto de volume rápido, bem acima do fundo daquele trecho.
    Teste (2026-11-17), no vídeo do Estilo Parede com os efeitos conhecidos: achou 22 dos 23 que tocam, a menos de 0,1 s;
    no mesmo vídeo sem efeitos, nenhum falso marcado como certo (os sons da gravação saem como "fraco")."""
    import numpy as np
    passo = int(0.01 * TAXA_SOM)  # 10 ms
    nivel = _db(resto, passo)
    fala = _db(voz, passo)
    if len(nivel) < 50:
        return []
    piso = float(np.percentile(nivel, 20))
    voz_alta = float(np.percentile(fala, 90))
    achados, ultimo = [], -1.0
    for i in range(15, len(nivel) - 10):
        antes = float(nivel[i - 15:i].min())   # o mais baixo nos 150 ms antes
        pico = float(nivel[i:i + 8].max())     # o mais alto nos 80 ms depois
        if pico - antes < 9 or pico < piso + 14 or nivel[i] - nivel[i - 1] < 3:
            continue
        # resto de voz que o separador deixou passar acompanha a fala: só conta se ficar perto do volume da voz
        if pico < fala[i:i + 8].max() - 26:
            continue
        t = i * 0.01
        if t - ultimo < 0.12:
            continue
        topo = i + int(np.argmax(nivel[i:i + 8]))
        fim = topo
        while fim < len(nivel) - 1 and nivel[fim] > max(pico - 15, antes + 3) and fim - topo < 300:
            fim += 1
        dura = round((fim - i) * 0.01, 2)
        perto_voz = round(pico - voz_alta, 1)
        forca = round(pico - antes, 1)
        achados.append({"t": round(t, 2), "forca_db": forca, "volume_vs_voz_db": perto_voz, "dura": dura,
                        "curto": "estalo" if dura < 0.1 else "médio" if dura < 0.5 else "longo",
                        "timbre": _timbre(resto, t, dura),
                        # fraco: pode ser som da própria gravação (objeto, mão, ambiente), não efeito de edição
                        "certo": forca >= 25 and perto_voz >= -26})
        ultimo = t
    # Rajada: toques a menos de 0,2 s um do outro (teclado digitando, cliques em sequência) contam como um efeito só,
    # senão o número de efeitos por minuto mede quantos segundos de digitação há no vídeo.
    for e, anterior in zip(achados[1:], achados):
        e["rajada"] = anterior.get("rajada", 0) + 1 if e["certo"] and anterior["certo"] and e["t"] - anterior["t"] < 0.2 else 0
    return achados


# ---------------------------------------------------------------- análise

def medir(video: Path, pasta: Path, com_fala: bool = True) -> dict:
    """Mede um vídeo (a referência ou o editado) e grava as folhas de quadros."""
    import numpy as np
    pasta.mkdir(parents=True, exist_ok=True)
    f = formato(video)
    total = f["duracao"]
    print(f"Vídeo: {f['largura']}x{f['altura']}, {f['fps']} quadros/s, {total:.1f} s. Medindo cortes e entradas...", flush=True)
    lista_cortes = cortes(video)
    lista_entradas = entradas(video, lista_cortes, f["altura"])
    planos = np.diff([0.0, *lista_cortes, total])
    m = {**f, "cortes": lista_cortes, "entradas": lista_entradas, "cores": cores(video, total),
         "ritmo": {"cortes_por_min": round(len(lista_cortes) * 60 / total, 1),
                   "plano_medio_s": round(float(np.mean(planos)), 2),
                   "plano_mais_longo_s": round(float(np.max(planos)), 2),
                   "entradas_por_min": round(len(lista_entradas) * 60 / total, 1),
                   # zoom seco em parede lisa sai como entrada, e não como corte: o número que compara é a soma
                   "mudancas_por_min": round((len(lista_cortes) + len(lista_entradas)) * 60 / total, 1)}}
    som = separar(video, pasta)
    if som is None:
        m["som"] = None
        print("Aviso: sem o Demucs, a música e os efeitos sonoros não são medidos. Instale como diz o requisitos.txt.")
    else:
        voz, resto = som
        lista_efeitos = efeitos(resto, voz)
        m["som"] = {"musica": musica(voz, resto), "efeitos": lista_efeitos,
                    "efeitos_por_min": round(len(_eventos(lista_efeitos)) * 60 / total, 1)}
    if com_fala:
        from . import transcricao
        print("Transcrevendo a fala (o idioma é descoberto pelo som)...", flush=True)
        palavras = transcricao.transcrever(video, pasta, idioma=None, corrige=False)
        falado = sum(p["fim"] - p["inicio"] for p in palavras)
        m["fala"] = {"idioma": transcricao.idioma_ouvido, "palavras": len(palavras),
                     "palavras_por_min": round(len(palavras) * 60 / total, 0),
                     "primeira_palavra_s": palavras[0]["inicio"] if palavras else None,
                     "com_fala_porcento": round(100 * falado / total, 0)}
    gravar_json(pasta / "medidas.json", m)
    return m


def _frases(palavras: list[dict]) -> list[str]:
    linhas, atual, inicio = [], [], 0.0
    for p in palavras:
        if not atual:
            inicio = p["inicio"]
        atual.append(p["texto"])
        if p["texto"][-1:] in ".?!" or len(atual) >= 14:
            linhas.append(f"- {inicio:5.1f} s: {' '.join(atual)}")
            atual = []
    if atual:
        linhas.append(f"- {inicio:5.1f} s: {' '.join(atual)}")
    return linhas


def analisar(fonte: str, pasta: Path) -> None:
    pasta.mkdir(parents=True, exist_ok=True)
    video, post = obter(fonte, pasta)
    gravar_json(pasta / "post.json", post)
    m = medir(video, pasta)
    total = m["duracao"]
    print("Montando as folhas de quadros...", flush=True)
    imagens = {
        "gancho": folhas(video, [(k / 4, f"{k / 4:.2f} s") for k in range(12)], pasta / "gancho"),
        "cortes": folhas(video, [(c + 0.15, f"corte {c:.1f} s") for c in m["cortes"]], pasta / "cortes"),
        "entradas": folhas(video, [(e["t"] + 0.3, f"{e['t']:.1f} s  y {e['y'][0]}-{e['y'][1]}") for e in m["entradas"]],
                           pasta / "entradas"),
        "video": folhas(video, [(float(t), f"{t} s") for t in range(int(total))], pasta / "video"),
    }
    if m.get("som"):
        imagens["efeitos"] = folhas(video, [(e["t"] + 0.05, f"{e['t']:.1f} s {e['curto']} {e['timbre']}")
                                            for e in m["som"]["efeitos"] if e["certo"]], pasta / "efeitos")
    palavras = ler_json(pasta / "palavras.json")

    r, c = m["ritmo"], m["cores"]
    toques = {e["t"]: e.get("toques", 1) for e in _eventos((m.get("som") or {}).get("efeitos", []))}

    def rajada(e):
        return f"rajada de {toques[e['t']]} toques" if toques.get(e["t"], 1) > 1 else ""
    linhas = [f"Vídeo de referência: {post.get('fonte')}", ""]
    if post.get("uploader"):
        linhas.append(f"Perfil: {post['uploader']}. Visualizações: {post.get('view_count') or '?'}, curtidas: "
                      f"{post.get('like_count') or '?'}, comentários: {post.get('comment_count') or '?'}.")
    linhas += [f"{m['largura']}x{m['altura']}, {m['fps']} quadros/s, {total:.1f} s.", "", "## Ritmo", "",
               f"- {len(m['cortes'])} cortes ou zooms secos ({r['cortes_por_min']} por minuto); plano médio de "
               f"{r['plano_medio_s']} s, o mais longo {r['plano_mais_longo_s']} s.",
               f"- {len(m['entradas'])} coisas entram na tela sem corte ({r['entradas_por_min']} por minuto).",
               f"- Mudanças na tela (cortes + entradas): {r['mudancas_por_min']} por minuto. É o número que se compara: "
               "zoom seco em fundo liso pode sair como entrada, e coisa pequena entrando (um cartão, uma linha digitada) "
               "pode não ser contada; confira nas folhas.",
               "", "## Cores", "",
               "- Dominantes: " + ", ".join(f"{h} ({p}%)" for h, p in c.get("dominantes", [])),
               f"- Fortes ({c.get('fortes_porcento', 0)}% da imagem): " + ", ".join(f"{h} ({p}%)" for h, p in c.get("fortes", [])),
               "", "## Som", ""]
    som = m.get("som")
    if som is None:
        linhas.append("- Não medido (falta o Demucs).")
    else:
        mu = som["musica"]
        if mu["tem"]:
            linhas.append(f"- Música contínua, uns {abs(mu['abaixo_da_voz_db'] or 0):.0f} dB abaixo da voz. "
                          "Com música, efeito baixo pode passar despercebido na lista abaixo.")
        else:
            linhas.append(f"- Sem música contínua (o fundo fica em silêncio em {mu['segundos_em_silencio']} s do vídeo).")
        certos = _eventos(som["efeitos"])
        rajadas = [e for e in certos if e.get("toques")]
        linhas.append(f"- {len(certos)} efeitos sonoros ({som['efeitos_por_min']} por minuto), contando como um só cada "
                      f"rajada de toques seguidos ({len(rajadas)} rajadas, como teclado digitando), mais "
                      f"{len(som['efeitos']) - len(certos)} fracos que podem ser som da própria gravação. O tipo de cada "
                      "um (clique, whoosh, pop, ding) sai da duração, do timbre e do que entra na tela no mesmo instante: "
                      "veja as folhas efeitos-N.jpg.")
        if som["efeitos"]:
            linhas += ["", "| tempo | duração | timbre | volume perto da voz | o que acontece na tela | |",
                       "|---|---|---|---|---|---|"]
            for e in [x for x in som["efeitos"] if not x.get("rajada")]:
                junto = [x for x in m["entradas"] if abs(x["t"] - e["t"]) < 0.25]
                corte = [x for x in m["cortes"] if abs(x - e["t"]) < 0.25]
                tela = "corte" if corte else (f"entrada em y {junto[0]['y'][0]}-{junto[0]['y'][1]}" if junto else "")
                linhas.append(f"| {e['t']:.2f} s | {e['curto']} ({e['dura']} s) | {e['timbre']} | "
                              f"{e['volume_vs_voz_db']:+.0f} dB | {tela} | {'fraco' if not e['certo'] else rajada(e)} |")
    f = m.get("fala", {})
    linhas += ["", "## Fala", "",
               f"- Idioma: {f.get('idioma')}. {f.get('palavras')} palavras, {f.get('palavras_por_min')} por minuto; "
               f"fala em {f.get('com_fala_porcento')}% do tempo; a primeira palavra em {f.get('primeira_palavra_s')} s.",
               "", *_frases(palavras), "", "## Imagens para olhar, nesta ordem", ""]
    nomes = {"gancho": "os 3 primeiros segundos", "cortes": "logo depois de cada corte",
             "entradas": "cada coisa que entra na tela, já entrada (y = faixa da tela que mudou, de 0 no topo a "
                         f"{m['altura']} embaixo)", "efeitos": "a tela no instante de cada efeito sonoro",
             "video": "o vídeo inteiro, um quadro por segundo"}
    for chave in ("gancho", "entradas", "cortes", "efeitos", "video"):
        for arq in imagens.get(chave, []):
            linhas.append(f"- `{arq.name}`: {nomes[chave]}")
    linhas += ["", f"Quadro em tamanho cheio de um instante: `{EDITAR} referencia quadros PASTA 12.5 20.2`"]
    (pasta / "resumo.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print("\n".join(linhas[:30]))
    print(f"\nResumo completo e imagens em {pasta}")


def quadros_cheios(pasta: Path, tempos: list[float]) -> None:
    destino = pasta / "quadros"
    destino.mkdir(exist_ok=True)
    for t in tempos:
        img = quadro(pasta / "video.mp4", t, 1080)
        if img:
            arq = destino / f"t_{t:.2f}.jpg"
            img.save(arq, quality=92)
            print(arq)


def comparar(ref: Path, editado: Path, pasta: Path) -> None:
    """Põe a referência e o vídeo editado lado a lado: os números e os quadros nos mesmos pontos do vídeo."""
    from PIL import Image, ImageDraw
    a = ler_json(ref / "medidas.json")
    b = medir(editado, pasta, com_fala=False)

    def linha(nome, x, y):
        return f"| {nome} | {x} | {y} |"

    def som(m, chave):
        s = m.get("som") or {}
        if chave == "musica":
            mu = s.get("musica") or {}
            return "?" if not s else ("sim" if mu.get("tem") else "não")
        return s.get(chave, "?")

    def cor(m, k):
        return ", ".join(h for h, _ in (m.get("cores", {}).get(k) or [])[:4])

    tabela = ["| | referência | editado |", "|---|---|---|",
              linha("duração", f"{a['duracao']} s", f"{b['duracao']} s"),
              linha("cortes por minuto", a["ritmo"]["cortes_por_min"], b["ritmo"]["cortes_por_min"]),
              linha("plano médio", f"{a['ritmo']['plano_medio_s']} s", f"{b['ritmo']['plano_medio_s']} s"),
              linha("entradas na tela por minuto", a["ritmo"]["entradas_por_min"], b["ritmo"]["entradas_por_min"]),
              linha("**mudanças na tela por minuto** (cortes + entradas)", a["ritmo"].get("mudancas_por_min", "?"),
                    b["ritmo"]["mudancas_por_min"]),
              linha("**efeitos por minuto** (rajada conta um)", som(a, "efeitos_por_min"), som(b, "efeitos_por_min")),
              linha("música", som(a, "musica"), som(b, "musica")),
              linha("cores dominantes", cor(a, "dominantes"), cor(b, "dominantes")),
              linha("cores fortes", cor(a, "fortes"), cor(b, "fortes"))]
    # Quadros lado a lado nos mesmos pontos relativos do vídeo (o editado pode ter outra duração).
    pontos = [0.0, 0.5, 1.0, 1.5, 2.5] + [a["duracao"] * k / 10 for k in range(1, 10)]
    fonte = _fonte(22)
    feitas = []
    for n in range(0, len(pontos), 4):
        grupo = pontos[n:n + 4]
        folha = Image.new("RGB", (len(grupo) * (2 * QUADRO_W + 24), QUADRO_H + 40), (24, 24, 24))
        d = ImageDraw.Draw(folha)
        for k, t in enumerate(grupo):
            tb = t if t <= 3 else t * b["duracao"] / a["duracao"]
            x = k * (2 * QUADRO_W + 24)
            for j, (v, tt) in enumerate(((ref / "video.mp4", t), (editado, tb))):
                img = quadro(v, tt)
                if img:
                    folha.paste(img.resize((QUADRO_W, QUADRO_H)), (x + j * (QUADRO_W + 4), 0))
            d.text((x + 6, QUADRO_H + 8), f"ref {t:.1f} s | editado {tb:.1f} s", fill=(255, 230, 120), font=fonte)
        arq = pasta / f"lado-a-lado-{n // 4 + 1}.jpg"
        folha.save(arq, quality=88)
        feitas.append(arq)
    texto = ["Referência à esquerda, editado à direita em cada par. Os números que se comparam estão em negrito; as "
             "cores só contam num estilo copiado igual. Os pares de quadros são do gancho (mesmo segundo) e depois dos "
             "mesmos pontos do vídeo em proporção: servem para comparar acabamento, tamanho e densidade, não o conteúdo.",
             "", *tabela, "",
             *[f"- `{f.name}`" for f in feitas]]
    (pasta / "comparacao.md").write_text("\n".join(texto) + "\n", encoding="utf-8")
    print("\n".join(texto))
    print(f"\nEm {pasta}")
