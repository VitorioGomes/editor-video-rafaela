"""Do projeto ao vídeo pronto para postar: render, volume padrão das redes e a conferência técnica."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from .comum import duracao, hyperframes, rodar

ALVO_LUFS, PICO = -14.0, -1.0  # o volume que Instagram, TikTok e YouTube esperam


def renderizar(projeto: Path, saida: Path, rascunho: bool = False) -> None:
    _check(projeto)
    saida.parent.mkdir(parents=True, exist_ok=True)
    hyperframes("render", "--quality", "draft" if rascunho else "looks", "-o", saida.resolve(), cwd=projeto)
    print(f"Render em {saida}")


def _check(projeto: Path) -> None:
    """Roda o check do HyperFrames e mostra os erros de verdade. Aviso não para o render (ver animacoes.md)."""
    import os
    import subprocess
    from .comum import HYPERFRAMES, npx
    r = subprocess.run([npx(), "-y", HYPERFRAMES, "check", "--json"], cwd=projeto, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env={**os.environ, "HYPERFRAMES_SKIP_SKILLS": "1"})
    try:
        dados = json.loads(r.stdout[r.stdout.index("{"):])
    except ValueError:
        sys.exit(f"O check do HyperFrames não respondeu:\n{(r.stderr or r.stdout)[-1500:]}")
    erros, avisos = [], {}
    for secao, v in dados.items():
        if isinstance(v, dict):
            for f in v.get("findings", []):
                if f.get("severity") == "error":
                    erros.append(f"[{secao}] {f.get('code')}: {f.get('message')}" + (f" ({f.get('text')})" if f.get("text") else ""))
                else:
                    onde = f.get("selector") or f.get("text") or f.get("src") or ""
                    if f.get("time") is not None:
                        onde = f"{onde} em {float(f['time']):.1f} s".strip()
                    avisos.setdefault(f.get("code"), []).append(onde)
    if avisos:
        # Cada aviso com os elementos que o geraram, para saber se é de propósito (ver o guia do estilo) ou se é para corrigir.
        print("Avisos do check (não param o render):")
        for k, lista in sorted(avisos.items()):
            exemplos = list(dict.fromkeys(x for x in lista if x))[:3]
            print(f"  {k} {len(lista)}" + (f": {'; '.join(exemplos)}" + (" ..." if len(set(lista)) > 3 else "") if exemplos else ""))
    if erros or not dados.get("ok", True):
        sys.exit("O check do HyperFrames achou erro (o render não roda):\n" + "\n".join(erros))


def _medir(video: Path) -> dict:
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(video), "-af",
                        f"loudnorm=I={ALVO_LUFS}:TP={PICO}:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return json.loads(re.findall(r"\{[^{}]*\}", r.stderr)[-1])


def finalizar(video: Path, saida: Path) -> None:
    """Volume em -14 LUFS (duas passadas, sem bombear) e a conferência do arquivo final."""
    if not video.exists():
        sys.exit(f"Não achei {video}: o render rodou? (se o check do HyperFrames parou, o render não sai)")
    saida.parent.mkdir(parents=True, exist_ok=True)
    m = _medir(video)
    filtro = (f"loudnorm=I={ALVO_LUFS}:TP={PICO}:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
              f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    rodar(["ffmpeg", "-v", "error", "-y", "-i", video, "-c:v", "copy", "-af", filtro, "-ar", "48000",
           "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", saida])
    conferir_arquivo(saida)


def conferir_arquivo(video: Path) -> None:
    v = json.loads(rodar(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,pix_fmt,r_frame_rate", "-of", "json", video]).stdout)["streams"][0]
    m = _medir(video)
    dur = duracao(video)
    linhas = [
        ("tamanho", f"{v['width']}x{v['height']}", (v["width"], v["height"]) == (1080, 1920)),
        ("cor", v["pix_fmt"], v["pix_fmt"] == "yuv420p"),
        ("quadros", v["r_frame_rate"], v["r_frame_rate"] in ("30/1", "30000/1001")),
        ("volume", f"{float(m['input_i']):.1f} LUFS", abs(float(m["input_i"]) - ALVO_LUFS) <= 1.0),
        ("pico", f"{float(m['input_tp']):.1f} dBTP", float(m["input_tp"]) <= PICO + 0.5),
        ("duração", f"{dur:.1f} s", dur <= 180),
    ]
    for nome, valor, ok in linhas:
        print(f"{'ok  ' if ok else 'FALHA'} {nome:9s} {valor}")
    if not all(ok for *_, ok in linhas):
        sys.exit(1)
    print(f"Pronto para postar: {video}")
