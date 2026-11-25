"""A conferência dos títulos no alto da tela, quadro a quadro: cobrem a cabeça? estão na área? estão grandes?

Os títulos são medidos de verdade, com a animação andando (o Playwright abre a montagem e anda a linha do tempo).
O topo da cabeça vem do recorte da pessoa: o recorte.webm do projeto, se houver, ou um recorte rápido só para esta
conferência (5 quadros por segundo, em tamanho pequeno: uns 30 s para um vídeo de 30 s, no processador).

Réguas (as do Estilo Títulos Desenhados; mude com as opções):
- nada do título abaixo do topo da cabeça naquela coluna, com uma folga de 12 px (o título não encosta no cabelo);
- nada acima de 220 px (o nome do perfil cobre) nem fora de 150 a 930 px na largura (o Instagram aproxima o vídeo);
- a palavra principal com pelo menos 110 px de fonte; o título ocupando pelo menos 60% da largura útil (780 px);
- nenhum texto visível com menos de 32 px de fonte (não se lê no celular);
- a legenda com a base acima de 1.700 px.
"""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from .comum import HYPERFRAMES, duracao, npx
from .recorte import ESCALA, FPS, _alfa

MEDIR = r"""(t) => {
  const tl = window.__timelines && window.__timelines.main;
  const ids = window.__tdIds || (window.__tdIds = new WeakMap());
  let proximo = window.__tdProx || 0;
  const chave = (e) => { if (!ids.has(e)) { ids.set(e, ++proximo); window.__tdProx = proximo; } return ids.get(e); };
  const vis = (e) => { let o = 1; for (let x = e; x && x !== document.body; x = x.parentElement) {
      const s = getComputedStyle(x); if (s.display === 'none' || s.visibility === 'hidden') return 0; o *= +s.opacity; } return o; };
  // O que um ancestral com overflow escondido corta (a palavra que sobe de trás de uma máscara) não aparece.
  const corta = (e, r) => { let {left: x0, top: y0, right: x1, bottom: y1} = r;
    for (let x = e.parentElement; x && x !== document.body; x = x.parentElement) {
      const s = getComputedStyle(x);
      if (s.overflow !== 'visible' || s.overflowX !== 'visible' || s.overflowY !== 'visible') {
        const q = x.getBoundingClientRect(); x0 = Math.max(x0, q.left); y0 = Math.max(y0, q.top); x1 = Math.min(x1, q.right); y1 = Math.min(y1, q.bottom); } }
    return {x0, y0, x1, y1}; };
  const coleta = () => {
    const out = [];
    document.querySelectorAll('#root > .clip').forEach(c => {
      if (c.tagName === 'VIDEO' || c.tagName === 'AUDIO' || c.id === 'palco') return;
      const de = +c.dataset.start, dura = +c.dataset.duration;
      if (!(t >= de && t < de + dura)) return;
      const leg = c.classList.contains('leg');
      const pecas = [];
      const olhar = (e) => {
        if (e.tagName === 'svg') {
          // Desenho: conta só o que está pintado (o traço do X antes de ser desenhado não conta).
          const o = vis(e);
          let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
          e.querySelectorAll('path,line,polyline,polygon,rect,circle,ellipse,text').forEach(f => {
            if (f.closest('defs,mask,clipPath')) return;
            if (o * +getComputedStyle(f).opacity < 0.3) return;
            const r = f.getBoundingClientRect();
            if (r.width < 1 && r.height < 1) return;
            x0 = Math.min(x0, r.left); y0 = Math.min(y0, r.top); x1 = Math.max(x1, r.right); y1 = Math.max(y1, r.bottom);
          });
          if (x1 > x0) { const q = corta(e, {left: x0, top: y0, right: x1, bottom: y1});
            if (q.x1 - q.x0 > 1 && q.y1 - q.y0 > 1) pecas.push({k: chave(e), ...q, fonte: 0, texto: (e.id || (e.parentElement && e.parentElement.id) || 'desenho') + ''}); }
          return;
        }
        if (e.children.length === 0 || [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) {
          const r = e.getBoundingClientRect();
          const vazio = e.children.length === 0 && !e.textContent.trim() && getComputedStyle(e).backgroundColor === 'rgba(0, 0, 0, 0)';
          if (r.width < 2 || r.height < 2 || vazio || vis(e) < 0.3) return;
          const q = corta(e, r);
          if (q.x1 - q.x0 < 2 || q.y1 - q.y0 < 2) return;
          const temTexto = e.textContent.trim().length > 0;
          // A letra solta (.td-l) leva o nome da palavra inteira, para o aviso dizer qual palavra.
          const dono = e.classList.contains('td-l') && e.parentElement ? e.parentElement : e;
          pecas.push({k: chave(e), ...q, fonte: temTexto ? parseFloat(getComputedStyle(e).fontSize) : 0,
                      texto: temTexto ? dono.textContent.trim().slice(0, 24) : (e.id || e.className || e.tagName) + ''});
        }
        for (const f of e.children) olhar(f);
      };
      olhar(c);
      if (pecas.length) out.push({id: c.id, de, dura, leg, pecas});
    });
    return out;
  };
  // Só conta o que já assentou: a peça que ainda está chegando (em arco, subindo de trás da máscara) passa pela área
  // de propósito. Parada é a que andou menos de 4 px nos últimos 0,12 s.
  if (tl) tl.seek(Math.max(0, t - 0.12), false);
  const antes = new Map();
  coleta().forEach(c => c.pecas.forEach(p => antes.set(p.k, p)));
  if (tl) tl.seek(t, false);
  return coleta().map(c => ({...c, pecas: c.pecas.map(p => { const a = antes.get(p.k);
    return {...p, parada: !!(a && Math.abs(a.x0 - p.x0) < 4 && Math.abs(a.y0 - p.y0) < 4 && Math.abs(a.y1 - p.y1) < 4)}; })}));
}"""


def _medidas(projeto: Path, tempos: list[float]) -> list[tuple[float, list]]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise SystemExit("A conferência dos títulos usa o Playwright: pip install playwright && playwright install chromium")
    saida = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1920})
        # Fora do HyperFrames não existe o __timelines: sem ele a linha do tempo não se registra e nada anda.
        pg.add_init_script("window.__timelines = window.__timelines || {};")
        pg.goto((projeto / "index.html").resolve().as_uri())
        pg.wait_for_timeout(1500)
        pg.evaluate("document.fonts.ready")
        for t in tempos:
            saida.append((t, pg.evaluate(MEDIR, t)))
        b.close()
    return saida


def _recorte_rapido(video: Path, pasta: Path) -> Path:
    """Um recorte só para achar a cabeça: 5 quadros por segundo, a 540 x 960. Fica guardado na montagem."""
    import os
    destino = pasta / "cabeca.webm"
    if destino.exists() and destino.stat().st_mtime > video.stat().st_mtime:
        return destino
    print("Recortando a pessoa em tamanho pequeno, só para achar a cabeça (uns 30 s a 1 min)...", flush=True)
    with tempfile.TemporaryDirectory() as tmp:
        leve = Path(tmp) / "leve.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vf", f"fps={FPS},scale=540:960", "-an",
                        "-c:v", "libx264", "-crf", "20", str(leve)], check=True)
        r = subprocess.run([npx(), "-y", HYPERFRAMES, "remove-background", str(leve), "-o", str(destino), "--device", "auto",
                            "--quality", "fast"], capture_output=True, text=True, encoding="utf-8", errors="replace",
                           env={**os.environ, "HYPERFRAMES_SKIP_SKILLS": "1"})
        if r.returncode:
            raise SystemExit(f"O recorte falhou:\n{(r.stderr or r.stdout)[-1200:]}")
    return destino


def _topo_cabeca(m, quadro: int, x0: float, x1: float) -> float | None:
    """A primeira linha (em px do vídeo) em que a pessoa aparece entre as colunas x0 e x1. None se ela não está ali."""
    import numpy as np
    q = min(max(quadro, 0), len(m) - 1)
    c0, c1 = max(0, int(x0 / ESCALA)), min(m.shape[2], int(x1 / ESCALA) + 1)
    if c1 <= c0:
        return None
    linhas = np.nonzero(m[q, :, c0:c1].sum(axis=1) >= 2)[0]
    return float(linhas[0] * ESCALA) if len(linhas) else None


def conferir_titulos(projeto: Path, video: Path, recorte: Path | None = None, passo: float = 0.2, folga: float = 12,
                     margem: float = 150, fonte_minima: float = 32, palavra_minima: float = 110,
                     largura_minima: float = 0.6, topo: float = 220, base_legenda: float = 1700) -> None:
    total = duracao(video)
    tempos = [round(i * passo, 3) for i in range(int(total / passo) + 1)]
    m = _alfa(recorte if recorte else _recorte_rapido(video, projeto))
    medidas = _medidas(projeto, tempos)

    titulos: dict[str, dict] = {}
    legenda_baixa = []
    for t, clips in medidas:
        quadro = int(round(t * FPS))
        for c in clips:
            if c["leg"]:
                fundo = max(p["y1"] for p in c["pecas"])
                if fundo > base_legenda:
                    legenda_baixa.append((t, fundo))
                continue
            d = titulos.setdefault(c["id"], {"de": c["de"], "ate": c["de"] + c["dura"], "cabeca": [], "area": [], "miudo": {},
                                             "fonte": 0.0, "largura": 0.0, "nome": ""})
            for p in c["pecas"]:  # o tamanho da letra conta mesmo com a peça andando
                if p["fonte"] > d["fonte"]:
                    d["fonte"], d["nome"] = p["fonte"], p["texto"]
                if 0 < p["fonte"] < fonte_minima:
                    d["miudo"][p["texto"]] = p["fonte"]
            paradas = [p for p in c["pecas"] if p["parada"]]
            if not paradas:
                continue
            x0 = min(p["x0"] for p in paradas)
            x1 = max(p["x1"] for p in paradas)
            d["largura"] = max(d["largura"], x1 - x0)
            for p in paradas:
                enfeite = p["fonte"] == 0 and p["x1"] - p["x0"] < 40 and p["y1"] - p["y0"] < 40  # estrelinha: pode passar um pouco
                if p["y0"] < topo - 2 or (not enfeite and (p["x0"] < margem - 2 or p["x1"] > 1080 - margem + 2)):
                    d["area"].append((t, p["texto"], p["x0"], p["y0"], p["x1"]))
                cabeca = _topo_cabeca(m, quadro, p["x0"], p["x1"])
                if cabeca is not None and p["y1"] > cabeca - folga:
                    d["cabeca"].append((t, p["texto"], p["y1"], cabeca))

    util = 1080 - 2 * margem
    problemas = 0
    print(f"{len(titulos)} títulos medidos a cada {passo} s; cabeça pelo {'recorte' if recorte else 'recorte rápido'}.\n")
    for cid, d in sorted(titulos.items(), key=lambda x: x[1]["de"]):
        avisos = []
        if d["cabeca"]:
            pior = max(d["cabeca"], key=lambda x: x[2] - x[3])
            t, texto, base, cab = pior
            quando = f"{d['cabeca'][0][0]:.1f} a {d['cabeca'][-1][0]:.1f} s"
            avisos.append(f"ENCOSTA NA CABEÇA ({quando}): \"{texto}\" vai até {base:.0f} px e o cabelo começa em {cab:.0f} px "
                          f"em {t:.1f} s. Suba {base - cab + folga:.0f} px ou diminua")
        if d["area"]:
            t, texto, x0, y0, x1 = d["area"][0]
            avisos.append(f"FORA DA ÁREA em {t:.1f} s: \"{texto}\" em x {x0:.0f}-{x1:.0f}, y {y0:.0f} "
                          f"(o certo: y acima de {topo:.0f}, x entre {margem:.0f} e {1080 - margem:.0f})")
        if d["fonte"] < palavra_minima:
            avisos.append(f"PALAVRA PEQUENA: a maior (\"{d['nome']}\") tem {d['fonte']:.0f} px; o mínimo é {palavra_minima:.0f}")
        if d["largura"] < largura_minima * util:
            avisos.append(f"ESTREITO: o título ocupa {d['largura'] / util:.0%} da largura útil; o mínimo é {largura_minima:.0%}")
        if d["miudo"]:
            lista = ", ".join(f"\"{k}\" {v:.0f} px" for k, v in list(d["miudo"].items())[:4])
            avisos.append(f"TEXTO MIÚDO (menos de {fonte_minima:.0f} px, não se lê no celular): {lista}")
        problemas += bool(avisos)
        cabeca = "ok"
        print(f"{d['de']:6.2f}-{d['ate']:5.2f}s  {cid:>5}  maior fonte {d['fonte']:4.0f} px  largura {d['largura'] / util:4.0%}  "
              f"{'ok' if not avisos else 'REVER'}")
        for a in avisos:
            print(f"        - {a}")
    if legenda_baixa:
        t, fundo = legenda_baixa[0]
        problemas += 1
        print(f"\nLEGENDA BAIXA: em {t:.1f} s a base vai a {fundo:.0f} px (máximo {base_legenda:.0f}).")
    print(f"\n{problemas} com problema." + ("" if problemas else " Os títulos estão na área, longe da cabeça e grandes."))
    print("Falta o olho: a legenda fora da boca e da barba, e se cada título explica a fala. Confira nos quadros.")
    if problemas:
        raise SystemExit(1)
