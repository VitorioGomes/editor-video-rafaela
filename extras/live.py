"""Cortes de live: da live inteira (YouTube ou arquivo) aos trechos em pé, prontos para editar.

  python .ferramenta/extras/live.py baixar LINK_OU_ARQUIVO --saida .projetos/lives/NOME
  python .ferramenta/extras/live.py quadros .projetos/lives/NOME 125 840 1310
  python .ferramenta/extras/live.py abrir-topo .projetos/TRECHO/corte/base.mp4 .projetos/TRECHO/corte/base-topo.mp4 [--px 380]
  python .ferramenta/extras/live.py trecho .projetos/lives/NOME DE ATE --saida brutos/NOME-TRECHO.mp4 [--x 0.5] [--seguir | --metade]

baixar   baixa o vídeo e escreve a fala inteira com o tempo (fala.md, para ler, e fala.json). Usa a legenda automática
         do YouTube quando existe (segundos); sem ela, transcreve com o modelo rápido (no processador, uns 20 a 40 min
         por hora de live). Também monta quadros.jpg, um quadro por minuto, para ver o enquadramento.
quadros  tira quadros em tamanho cheio nos instantes pedidos, com a janela em pé desenhada (para escolher o --x).
trecho   corta DE..ATE (segundos) da live e, se ela for deitada, recorta a janela em pé 9:16 parada no meio (--x muda
         a posição: 0 = borda esquerda, 0.5 = meio, 1 = borda direita). Com --seguir, a janela segue o rosto (OpenCV):
         o Vitório achou tremido no primeiro teste (2026-11-26), por isso não é o padrão. Sai 1080x1920, 30 quadros.
         Com --metade (Estilo Metade), ela fica só na metade de baixo: uma janela quase quadrada da live, sem ampliar,
         embaixo de 860 px de parede desfocada, que o painel cobre. Sem recorte de fundo (Vitório, 2026-11-26).

Fica fora de sistema/ de propósito: o sistema/ vem da oficina do produto e é trocado inteiro a cada sincronização.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "sistema"))


def rodar(cmd: list[str]) -> subprocess.CompletedProcess:
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise SystemExit(f"Falhou: {' '.join(cmd[:3])}...\n{r.stderr[-1500:]}")
    return r


def dimensoes(video: Path) -> tuple[int, int, float]:
    r = rodar(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:format=duration",
               "-of", "json", str(video)])
    d = json.loads(r.stdout)
    s = d["streams"][0]
    return int(s["width"]), int(s["height"]), float(d["format"]["duration"])


def hms(t: float) -> str:
    t = int(t)
    return f"{t // 3600}:{t % 3600 // 60:02d}:{t % 60:02d}" if t >= 3600 else f"{t // 60}:{t % 60:02d}"


# ---------------------------------------------------------------- baixar

def legenda_youtube(pasta: Path) -> list[dict] | None:
    """Lê a legenda automática (json3) do YouTube: frases com o tempo de cada palavra."""
    arquivos = sorted(pasta.glob("live.*.json3"), key=lambda p: ("orig" not in p.name, p.name))
    if not arquivos:
        return None
    dados = json.loads(arquivos[0].read_text(encoding="utf-8"))
    frases = []
    for ev in dados.get("events", []):
        if "segs" not in ev:
            continue
        ini = ev.get("tStartMs", 0) / 1000
        palavras = []
        for s in ev["segs"]:
            texto = s.get("utf8", "").strip()
            if texto:
                palavras.append({"texto": texto, "inicio": round(ini + s.get("tOffsetMs", 0) / 1000, 2)})
        if palavras:
            fim = ini + ev.get("dDurationMs", 0) / 1000
            frases.append({"inicio": round(ini, 2), "fim": round(fim, 2), "texto": " ".join(p["texto"] for p in palavras)})
    return frases or None


def transcrever_rapido(video: Path) -> list[dict]:
    from motor.comum import audio
    from motor import transcricao
    print("Sem legenda do YouTube: transcrevendo com o modelo rápido (pode levar de 20 a 40 min por hora de live "
          "no processador)...", flush=True)
    y = audio(video)
    segs = transcricao.ouvir(y, palavras=False, rapido=True, vad_filter=True)
    return [{"inicio": round(s.start, 2), "fim": round(s.end, 2), "texto": s.text.strip()} for s in segs]


def escrever_fala(frases: list[dict], pasta: Path, link: str | None, origem: str) -> None:
    (pasta / "fala.json").write_text(json.dumps(frases, ensure_ascii=False, indent=1), encoding="utf-8")
    # Blocos de ~30 s, para ler a live como texto corrido, com o minuto na margem.
    linhas, bloco, comeco = [f"Fala da live ({origem}). Tempo em minutos:segundos." + (f" Link: {link}" if link else ""), ""], [], None
    for f in frases:
        if comeco is None:
            comeco = f["inicio"]
        bloco.append(f["texto"])
        if f["fim"] - comeco >= 30:
            linhas.append(f"[{hms(comeco)}] {' '.join(bloco)}")
            bloco, comeco = [], None
    if bloco:
        linhas.append(f"[{hms(comeco)}] {' '.join(bloco)}")
    (pasta / "fala.md").write_text("\n\n".join(linhas) + "\n", encoding="utf-8")


def folha_quadros(video: Path, pasta: Path, duracao: float) -> None:
    passo = 60 if duracao > 600 else 20
    linhas = max(1, min(12, -(-int(duracao // passo + 1) // 6)))  # uma live de 1 h: 61 quadros, 11 linhas
    rodar(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vf",
           f"fps=1/{passo},scale=320:-2,drawtext=text='%{{pts\\:hms}}':x=6:y=6:fontsize=18:fontcolor=white:box=1:boxcolor=black@0.6,"
           f"tile=6x{linhas}:padding=4", "-frames:v", "1", str(pasta / "quadros.jpg")])


def baixar(fonte: str, saida: Path) -> None:
    saida.mkdir(parents=True, exist_ok=True)
    link = None
    if Path(fonte).exists():
        video = saida / ("live" + Path(fonte).suffix.lower())
        if not video.exists():
            shutil.copy2(fonte, video)
    else:
        link = fonte
        if not shutil.which("yt-dlp") and not _modulo("yt_dlp"):
            raise SystemExit("Falta o yt-dlp: python -m pip install yt-dlp")
        base = [sys.executable, "-m", "yt_dlp"] if _modulo("yt_dlp") else ["yt-dlp"]
        # O node resolve o desafio do YouTube (sem ele, faltam formatos). A legenda vem num pedido à parte e uma
        # língua de cada vez: o YouTube recusa pedidos seguidos (erro 429), e legenda que falta não pode derrubar o vídeo.
        base += ["--js-runtimes", "node", "--no-playlist"]
        for lingua in ("pt-orig", "pt"):
            subprocess.run(base + ["--skip-download", "--write-auto-subs", "--write-subs", "--sub-langs", lingua,
                                   "--sub-format", "json3", "-o", str(saida / "live.%(ext)s"), link],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
            if list(saida.glob("live.*.json3")):
                break
        print("Baixando a live (pode levar alguns minutos)...", flush=True)
        rodar(base + ["-f", "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/b[height<=1080]/b", "--merge-output-format", "mp4",
                      "-o", str(saida / "live.%(ext)s"), link])
        video = saida / "live.mp4"
    largura, altura, duracao = dimensoes(video)
    frases, origem = (legenda_youtube(saida), "legenda automática do YouTube")
    if not frases:
        frases, origem = transcrever_rapido(video), "transcrição rápida"
    escrever_fala(frases, saida, link, origem)
    folha_quadros(video, saida, duracao)
    (saida / "live.json").write_text(json.dumps({"fonte": fonte, "video": video.name, "largura": largura, "altura": altura,
                                                 "duracao": round(duracao, 2), "fala": origem}, ensure_ascii=False, indent=1),
                                     encoding="utf-8")
    print(f"Pronto: {hms(duracao)} de live, {largura}x{altura} ({'deitada' if largura > altura else 'em pé'}).")
    print(f"Leia {saida / 'fala.md'} e olhe {saida / 'quadros.jpg'} (um quadro a cada {60 if duracao > 600 else 20} s).")


def _modulo(nome: str) -> bool:
    import importlib.util
    return importlib.util.find_spec(nome) is not None


# ---------------------------------------------------------------- quadros e trecho

def ler_live(pasta: Path) -> tuple[Path, dict]:
    info = pasta / "live.json"
    if not info.exists():
        raise SystemExit(f"{pasta} não tem live.json: rode o baixar antes.")
    d = json.loads(info.read_text(encoding="utf-8"))
    return pasta / d["video"], d


def janela(largura: int, altura: int, x: float) -> tuple[int, int]:
    """Largura e esquerda da janela 9:16 de altura cheia, centrada em x (0 a 1), sem sair do quadro."""
    w = round(altura * 9 / 16 / 2) * 2
    esquerda = round(min(max(x * largura - w / 2, 0), largura - w) / 2) * 2
    return w, esquerda


def quadros(pasta: Path, tempos: list[float]) -> None:
    video, d = ler_live(pasta)
    destino = pasta / "quadros"
    destino.mkdir(exist_ok=True)
    deitada = d["largura"] > d["altura"]
    for t in tempos:
        saida = destino / f"t_{t:.1f}.jpg"
        filtros = "scale=1280:-2"
        if deitada:
            # As janelas em pé em x = 0.25, 0.5 e 0.75, para escolher o --x olhando onde ela está.
            w, _ = janela(d["largura"], d["altura"], 0.5)
            k = 1280 / d["largura"]
            caixas = []
            for x, cor in ((0.25, "yellow"), (0.5, "white"), (0.75, "cyan")):
                _, esq = janela(d["largura"], d["altura"], x)
                caixas.append(f"drawbox=x={esq * k:.0f}:y=0:w={w * k:.0f}:h=ih:color={cor}@0.9:t=3")
            filtros += "," + ",".join(caixas)
        rodar(["ffmpeg", "-v", "error", "-y", "-ss", f"{t}", "-i", str(video), "-frames:v", "1", "-vf", filtros, str(saida)])
        print(saida)
    if deitada:
        print("Janelas desenhadas: amarela x=0.25, branca x=0.5, ciano x=0.75.")


def seguir_rosto(video: Path, de: float, dura: float, largura: int, altura: int) -> list[float]:
    """O centro do rosto (0 a 1, na largura) a cada 1/30 s do trecho, suavizado como uma câmera calma.

    Olha 5 quadros por segundo (o OpenCV acha o rosto de frente; de lado ou com a mão na frente, ele perde e vale a
    última posição), tira os saltos com uma mediana de 1 s e suaviza com uma média de 1,6 s."""
    import numpy as np
    try:
        import cv2
    except ImportError:
        raise SystemExit("Falta o OpenCV para seguir o rosto: python -m pip install opencv-python-headless "
                         "(ou passe --x 0.5 para um recorte parado).")
    w, h, fps = 480, round(480 * altura / largura / 2) * 2, 5
    bruto = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{de}", "-i", str(video), "-t", f"{dura:.3f}", "-vf",
                            f"fps={fps},scale={w}:{h},format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    quadros = np.frombuffer(bruto, np.uint8).reshape(-1, h, w)
    detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    achados: list[float | None] = []
    for q in quadros:
        rostos = detector.detectMultiScale(q, scaleFactor=1.1, minNeighbors=5, minSize=(h // 8, h // 8))
        if len(rostos):
            x, _, rw, _ = max(rostos, key=lambda r: r[2] * r[3])
            achados.append((x + rw / 2) / w)
        else:
            achados.append(None)
    vistos = [a for a in achados if a is not None]
    if not vistos:
        print("Não achei o rosto neste trecho: recorte parado no meio.")
        return [0.5] * max(1, round(dura * 30))
    # sem rosto: a posição de antes (no começo, a primeira vista)
    ultimo, cheio = vistos[0], []
    for a in achados:
        ultimo = a if a is not None else ultimo
        cheio.append(ultimo)
    arr = np.array(cheio)
    med = np.array([np.median(arr[max(0, i - 2):i + 3]) for i in range(len(arr))])
    k = 8
    suave = np.convolve(np.pad(med, (k // 2, k - k // 2 - 1), mode="edge"), np.ones(k) / k, mode="valid")
    tempos = np.arange(len(suave)) / fps
    print(f"Rosto achado em {len(vistos)} de {len(achados)} quadros; centro de {suave.min():.2f} a {suave.max():.2f}.")
    return list(np.interp(np.arange(round(dura * 30)) / 30, tempos, suave))


PAINEL = 860  # altura do painel do Estilo Metade no estado "meio" (mm-palco.html)


def trecho(pasta: Path, de: float, ate: float, saida: Path, x: float, seguir: bool = False, metade: bool = False) -> None:
    video, d = ler_live(pasta)
    if ate <= de:
        raise SystemExit("ATE tem de ser maior que DE.")
    saida = saida.resolve()
    saida.parent.mkdir(parents=True, exist_ok=True)
    if metade:
        trecho_metade(video, d, de, ate, saida, x)
        return
    quadro, cmds = "", None
    if d["largura"] > d["altura"]:
        w, esq = janela(d["largura"], d["altura"], x)
        quadro = f"crop={w}:{d['altura']}:{esq}:0,"
        if seguir:
            # A janela em pé anda com ela: um comando de posição por quadro (o crop aceita x mudando no tempo).
            centros = seguir_rosto(video, de, ate - de, d["largura"], d["altura"])
            cmds = pasta / "seguir.cmd"
            cmds.write_text("".join(f"{i / 30:.3f} crop x {janela(d['largura'], d['altura'], c)[1]};\n"
                                    for i, c in enumerate(centros)), encoding="utf-8")
            quadro = f"sendcmd=f=seguir.cmd,{quadro}"
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{de}", "-i", str(video.resolve()), "-t", f"{ate - de:.3f}",
                        "-vf", f"{quadro}fps=30,scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,setsar=1",
                        "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-pix_fmt", "yuv420p",
                        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", str(saida)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=pasta)
    if r.returncode != 0:
        raise SystemExit(f"O ffmpeg falhou ao cortar o trecho:\n{r.stderr[-1500:]}")
    print(f"{saida} ({ate - de:.1f} s, de {hms(de)} a {hms(ate)} da live"
          + (", seguindo o rosto)" if cmds else ")"))


def trecho_metade(video: Path, d: dict, de: float, ate: float, saida: Path, x: float) -> None:
    """Estilo Metade num corte de live: ela só na metade de baixo (1080 x 1060), numa janela da live com essa forma,
    sem ampliar; em cima, a faixa de parede do alto da janela, esticada e desfocada, que o painel cobre.
    O recorte de fundo vazou na live (cabelo claro em parede clara, imagem ampliada) e é pesado: não se usa
    (Vitório, 2026-11-26). Mesma duração e som do trecho normal: escolhas.json e cortar funcionam igual."""
    baixo = 1920 - PAINEL
    h = d["altura"]
    w = min(round(h * 1080 / baixo / 2) * 2, d["largura"])
    esq = round(min(max(x * d["largura"] - w / 2, 0), d["largura"] - w) / 2) * 2
    filtro = (f"[0:v]fps=30,crop={w}:{h}:{esq}:0,scale=1080:{baixo}:flags=lanczos,setsar=1,split[a][b];"
              f"[a]crop=1080:40:0:0,gblur=sigma=45:steps=3,scale=1080:{PAINEL},gblur=sigma=12[topo];"
              "[topo][b]vstack,format=yuv420p[v]")
    rodar(["ffmpeg", "-v", "error", "-y", "-ss", f"{de}", "-i", str(video.resolve()), "-t", f"{ate - de:.3f}",
           "-filter_complex", filtro, "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-crf", "16", "-preset", "medium",
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000", str(saida)])
    print(f"{saida} ({ate - de:.1f} s, de {hms(de)} a {hms(ate)} da live, metade de baixo para o Estilo Metade)")


def abrir_topo(entrada: Path, saida: Path, px: int, emenda: int = 200) -> None:
    """Abre espaço em cima para os estilos com título (Yap, Títulos Desenhados, Metade) num corte de live, em que a
    cabeça fica quase no topo: o vídeo desce px, na largura toda (sai um pouco do peito embaixo), e o espaço de cima
    é a faixa de parede do alto do quadro, esticada e desfocada, com uma emenda suave de `emenda` px, como se a
    parede continuasse.
    Encolher o vídeo, com faixas dos lados, ficou um quadro dentro do quadro (teste de 2026-11-26).
    Mesma duração e mesmo som: o palavras.json do corte continua valendo."""
    mascara = saida.with_name("mascara-topo.png")
    rodar(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=black:s=1080x1920", "-vf",
           f"format=gray,geq=lum='if(lt(Y\\,{emenda})\\,255*Y/{emenda}\\,255)'", "-frames:v", "1", str(mascara)])
    # O topo sai só da faixa de cima do quadro (a parede, onde ela não está), esticada e desfocada. Com o quadro
    # inteiro ampliado, a cabeça dela aparecia no topo como uma mancha escura (Vitório, 2026-11-26).
    faixa = 40
    filtro = (f"[0:v]split[a][b];[a]crop=1080:{faixa}:0:0,gblur=sigma=45:steps=3,scale=1080:{px + emenda},gblur=sigma=12,"
              f"pad=1080:1920:0:0[fundo];"
              "[b]format=yuva420p[frente0];[1:v]format=gray[m];[frente0][m]alphamerge[frente];"
              f"[fundo][frente]overlay=0:{px}:shortest=1,format=yuv420p,setsar=1[v]")
    rodar(["ffmpeg", "-v", "error", "-y", "-i", str(entrada), "-loop", "1", "-i", str(mascara), "-filter_complex", filtro,
           "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-crf", "17", "-preset", "fast", "-g", "30",
           "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-c:a", "copy", "-shortest",
           str(saida)])
    mascara.unlink(missing_ok=True)
    print(f"{saida}: o vídeo dela desceu {px} px; o topo é a parede do alto do quadro, desfocada.")


def main() -> None:
    ap = argparse.ArgumentParser(description="Cortes de live")
    sub = ap.add_subparsers(dest="acao", required=True)
    b = sub.add_parser("baixar")
    b.add_argument("fonte")
    b.add_argument("--saida", required=True)
    q = sub.add_parser("quadros")
    q.add_argument("pasta")
    q.add_argument("tempos", nargs="+", type=float)
    t = sub.add_parser("trecho")
    t.add_argument("pasta")
    t.add_argument("de", type=float)
    t.add_argument("ate", type=float)
    t.add_argument("--saida", required=True)
    t.add_argument("--x", type=float, default=0.5, help="posição do recorte parado (0 a 1)")
    t.add_argument("--seguir", action="store_true", help="a janela segue o rosto (OpenCV)")
    t.add_argument("--metade", action="store_true", help="ela só na metade de baixo, para o Estilo Metade")
    en = sub.add_parser("abrir-topo")
    en.add_argument("entrada")
    en.add_argument("saida")
    en.add_argument("--px", type=int, default=380, help="quanto o vídeo desce (o espaço livre em cima)")
    a = ap.parse_args()
    if a.acao == "abrir-topo":
        abrir_topo(Path(a.entrada), Path(a.saida), a.px)
    elif a.acao == "baixar":
        baixar(a.fonte, Path(a.saida))
    elif a.acao == "quadros":
        quadros(Path(a.pasta), a.tempos)
    else:
        trecho(Path(a.pasta), a.de, a.ate, Path(a.saida), a.x, a.seguir, a.metade)


if __name__ == "__main__":
    main()
