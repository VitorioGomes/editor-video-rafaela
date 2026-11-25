"""Recorte da pessoa (para o texto ficar atrás dela) e a conferência do que está na parede.

O recorte usa o modelo local do HyperFrames. No Windows, roda sempre no processador (a placa de vídeo não acelera este passo);
no Mac com chip Apple, pode usar o CoreML. Demora uns 15 a 20 minutos para 80 segundos de vídeo, e mais se o computador
estiver fazendo outra coisa pesada ao mesmo tempo.
"""
from __future__ import annotations

import subprocess
import time
from pathlib import Path

from .comum import duracao, hyperframes

ESCALA = 4  # o recorte é lido a 1/4 do tamanho (270 x 480)
FPS = 5


def recortar(video: Path, saida: Path) -> None:
    import os
    import threading
    from .comum import HYPERFRAMES, npx
    dura = duracao(video)
    print(f"Recortando {dura:.0f} s de vídeo: uns {max(2, round(dura * 13 / 60))} minutos. Não feche o terminal.", flush=True)
    comeco = time.time()
    feito = threading.Event()

    def andando():
        while not feito.wait(60):
            print(f"  ... recortando há {(time.time() - comeco) / 60:.0f} min", flush=True)

    threading.Thread(target=andando, daemon=True).start()
    r = subprocess.run([npx(), "-y", HYPERFRAMES, "remove-background", str(video), "-o", str(saida), "--device", "auto",
                        "--quality", "balanced"], capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env={**os.environ, "HYPERFRAMES_SKIP_SKILLS": "1"})
    feito.set()
    if r.returncode:
        raise SystemExit(f"O recorte falhou:\n{(r.stderr or r.stdout)[-1500:]}")
    print(f"Recorte em {saida} ({(time.time() - comeco) / 60:.1f} min)")


def _caixas(projeto: Path) -> list[dict]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise SystemExit("A conferência da parede usa o Playwright (opcional): pip install playwright && playwright install chromium\n"
                         "Sem ele, confira olhando os quadros: npx hyperframes@0.9.9 snapshot --at ...")
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1920})
        pg.goto((projeto / "index.html").resolve().as_uri())
        pg.wait_for_timeout(1500)
        pg.evaluate("document.fonts.ready")
        pg.add_style_tag(content=".clip{display:block!important;visibility:visible!important}"
                         "#palco{transform:none!important}"
                         "#palco .clip *{opacity:1!important;transform:none!important}")
        pg.wait_for_timeout(300)
        # Mede os textos da parede: as linhas do motor e o que a animação marcar com data-confere.
        r = pg.evaluate("""() => {
          const out = [];
          document.querySelectorAll('#palco .clip').forEach(c => {
            if (c.tagName === 'VIDEO') return;
            c.querySelectorAll('.mao,.serifa,.destaque,.negrito,.italico,[data-confere]').forEach(e => {
              const t = e.textContent.trim();
              const q = e.getBoundingClientRect();
              if (!t || q.width < 2) return;
              out.push({clip: c.id, texto: t, de: +c.dataset.start, dura: +c.dataset.duration,
                        x: q.left, y: q.top, w: q.width, h: q.height});
            });
          });
          return out;
        }""")
        b.close()
    return r


def _alfa(recorte: Path):
    import numpy as np
    w, h = 1080 // ESCALA, 1920 // ESCALA
    cmd = ["ffmpeg", "-v", "error", "-c:v", "libvpx-vp9", "-i", str(recorte),
           "-vf", f"fps={FPS},alphaextract,scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    dados = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(dados, np.uint8).reshape(-1, h, w) > 127


def conferir_parede(projeto: Path, recorte: Path, limite: float = 0.12) -> None:
    """Quanto de cada texto da parede a pessoa cobre, quadro a quadro. Texto escondido não se lê no vídeo mudo:
    ele vai para a frente (no peito, no lugar da legenda) ou sobe para a faixa livre acima da cabeça."""
    cx, m = _caixas(projeto), _alfa(recorte)
    print(f"{len(cx)} textos na parede, {len(m)} quadros do recorte\n")
    ruins = 0
    for c in cx:
        q0, q1 = int(c["de"] * FPS), int((c["de"] + c["dura"]) * FPS)
        x0, y0 = max(0, int(c["x"] / ESCALA)), max(0, int(c["y"] / ESCALA))
        x1, y1 = int((c["x"] + c["w"]) / ESCALA), int((c["y"] + c["h"]) / ESCALA)
        trecho = m[q0:max(q1, q0 + 1), y0:y1, x0:x1]
        if trecho.size == 0:
            continue
        cobre = trecho.reshape(len(trecho), -1).mean(axis=1)
        media, pior = float(cobre.mean()), float(cobre.max())
        aviso = "  <<< ESCONDIDO" if media > limite else ""
        ruins += bool(aviso)
        print(f'{c["de"]:6.2f}s  {c["clip"]:>5}  {media:4.0%} média  {pior:4.0%} pior  '
              f'y {c["y"]:4.0f}-{c["y"] + c["h"]:4.0f}  {c["texto"][:30]}{aviso}')
    print(f"\n{ruins} escondidos")


def parede_livre(recorte: Path, de: float, ate: float) -> None:
    """Mapa da parede livre num trecho: % do pior quadro coberto pela pessoa, em quadrados de 120 px."""
    m = _alfa(recorte)
    t = m[int(de * FPS):int(ate * FPS) + 1]
    lado = 120 // ESCALA
    print(f"{de:.2f}s a {ate:.2f}s, pior quadro (. livre, % coberto)")
    print("      " + "".join(f"{x * 120:>5}" for x in range(9)))
    for y in range(1920 // 120):
        linha = []
        for x in range(9):
            bloco = t[:, y * lado:(y + 1) * lado, x * lado:(x + 1) * lado]
            v = bloco.reshape(len(bloco), -1).mean(axis=1).max()
            linha.append("    ." if v < .05 else f"{v:5.0%}")
        print(f"{y * 120:5} " + "".join(linha))
