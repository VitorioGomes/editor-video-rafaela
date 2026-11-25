"""Confere se o computador tem tudo para editar e diz, em português, o que falta e como instalar."""
from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys

from .comum import EDITAR as EDITAR_CMD, EFEITOS, FONTES, HYPERFRAMES, MEU_ESTILO, SISTEMA, chave_do_env, npx, rel

REQ = rel(SISTEMA / "requisitos.txt")

MAC = platform.system() == "Darwin"
WIN = platform.system() == "Windows"


def _saida(cmd: list[str]) -> str:
    try:
        # Sem instalar os manuais do HyperFrames por conta própria: isso é um passo à parte do EDITAR.md.
        env = {**os.environ, "HYPERFRAMES_SKIP_SKILLS": "1"}
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180, env=env)
        return (r.stdout or "") + (r.stderr or "")
    except Exception:
        return ""


def acharBlender() -> str | None:
    """O Blender, no mesmo lugar que o scripts/blender.mjs dos projetos 3D procura: a variável BLENDER, o caminho
    padrão do sistema (no Windows, a versão mais nova em Program Files/Blender Foundation; no Mac, o
    /Applications/Blender.app) e, por fim, o PATH."""
    from pathlib import Path
    if os.environ.get("BLENDER") and Path(os.environ["BLENDER"]).exists():
        return os.environ["BLENDER"]
    if MAC:
        p = Path("/Applications/Blender.app/Contents/MacOS/Blender")
        if p.exists():
            return str(p)
    if WIN:
        base = Path(os.environ.get("PROGRAMFILES", "C:/Program Files")) / "Blender Foundation"
        if base.exists():
            def num(d: Path) -> float:
                try:
                    return float("".join(c for c in d.name if c.isdigit() or c == ".") or 0)
                except ValueError:
                    return 0.0
            versoes = sorted((d for d in base.iterdir() if (d / "blender.exe").exists()), key=num, reverse=True)
            if versoes:
                return str(versoes[0] / "blender.exe")
    return shutil.which("blender")


def verificar() -> None:
    faltas, avisos = [], []

    def linha(ok: bool, nome: str, detalhe: str, como: str = "", opcional: bool = False) -> None:
        print(f"{'ok   ' if ok else ('---  ' if opcional else 'FALTA')} {nome:22s} {detalhe}")
        if not ok:
            (avisos if opcional else faltas).append((nome, como))

    print(f"Sistema: {platform.system()} {platform.machine()}, Python {platform.python_version()}\n")
    linha(sys.version_info >= (3, 10), "Python 3.10 ou mais", platform.python_version(),
          "Instale o Python 3.12 em python.org" + (" (marque 'Add python.exe to PATH')" if WIN else ""))

    ff = shutil.which("ffmpeg")
    versao = _saida(["ffmpeg", "-version"]).split("\n")[0][:60] if ff else "não encontrado"
    linha(bool(ff) and bool(shutil.which("ffprobe")), "ffmpeg e ffprobe", versao,
          "brew install ffmpeg" if MAC else "winget install Gyan.FFmpeg (e feche e abra o terminal)")
    if ff:
        filtros = _saida(["ffmpeg", "-hide_banner", "-filters"])
        linha("zscale" in filtros, "ffmpeg com zscale", "converte vídeo HDR de celular",
              "brew reinstall ffmpeg" if MAC else "winget install Gyan.FFmpeg (a versão completa tem)")
        linha("libvpx-vp9" in _saida(["ffmpeg", "-hide_banner", "-decoders"]), "ffmpeg com VP9", "lê o recorte da pessoa",
              "reinstale o ffmpeg completo")

    node = shutil.which("node")
    vnode = _saida(["node", "-v"]).strip() if node else "não encontrado"
    maior = int(vnode.lstrip("v").split(".")[0]) if vnode.startswith("v") else 0
    linha(maior >= 22, "Node.js 22 ou mais", vnode, "brew install node" if MAC else "winget install OpenJS.NodeJS.LTS")

    if maior >= 22:
        hf = _saida([npx(), "-y", HYPERFRAMES, "--version"]).strip().split("\n")[-1]
        linha("0.9.9" in hf, "HyperFrames", hf[:60] or "não respondeu",
              f"npx -y {HYPERFRAMES} --version (precisa de internet na primeira vez)")

    for modulo, nome in (("numpy", "numpy"), ("PIL", "pillow"), ("faster_whisper", "faster-whisper"),
                         ("torch", "torch"), ("transformers", "transformers")):
        try:
            __import__(modulo)
            linha(True, nome, "instalado")
        except ImportError:
            linha(False, nome, "não instalado", f"{sys.executable} -m pip install -r {REQ}")
    try:
        import yt_dlp  # noqa: F401
        linha(True, "yt-dlp", "baixa o vídeo de referência")
    except ImportError:
        linha(False, "yt-dlp", "baixa o vídeo de referência", f"{sys.executable} -m pip install -r {REQ}")
    try:
        from .referencia import _demucs
        _demucs()
        linha(True, "separador de voz", "mede a música e os efeitos da referência")
    except Exception:
        linha(False, "separador de voz", "mede a música e os efeitos da referência",
              f"{sys.executable} -m pip install -r {REQ} e depois "
              f"{sys.executable} -m pip install --no-deps -r {rel(SISTEMA / 'requisitos-separador.txt')}")

    from .comum import config
    from .transcricao import INSTALAR_PLACA, placa
    tem, pronta = placa()
    escolha = config()["transcricao"].get("dispositivo", "auto")
    if tem and pronta:
        print("\nPlaca de vídeo NVIDIA: sim, pronta. A transcrição fica mais rápida.")
    elif tem and escolha == "processador":
        print("\nPlaca de vídeo NVIDIA sem as bibliotecas; a pessoa escolheu seguir no processador.")
    elif tem:
        print("\nDECISÃO DA PESSOA: tem placa de vídeo NVIDIA, mas faltam as bibliotecas da NVIDIA para usá-la. Pergunte:\n"
              f"  1. instalar e usar a placa (mais rápido; uns 3 GB): {INSTALAR_PLACA}\n"
              '  2. seguir no processador (mais devagar): "transcricao": {"dispositivo": "processador"} no meu-estilo/marca.json')
    else:
        print("\nSem placa de vídeo NVIDIA: a transcrição roda no processador, só mais devagar.")
    if MAC and platform.machine() == "arm64":
        print("Mac com Apple Silicon: o recorte usa o chip (CoreML) e fica mais rápido.")

    linha(any(FONTES.glob("*.woff2")), "fontes", str(FONTES))
    linha((EFEITOS / "sounds.json").exists(), "efeitos sonoros", str(EFEITOS))
    linha(MEU_ESTILO.exists(), "meu-estilo/", "o gosto da pessoa (nasce na primeira conversa)",
          "A IA cria na primeira conversa", opcional=True)
    try:
        import playwright  # noqa: F401
        linha(True, "playwright (opcional)", "confere o texto atrás da pessoa e os títulos no alto")
    except ImportError:
        linha(False, "playwright (opcional)", "confere o texto atrás da pessoa e os títulos no alto",
              f"{sys.executable} -m pip install playwright && {sys.executable} -m playwright install chromium", opcional=True)
    # O Blender só serve aos estilos 3D (Curta 3D e Estilo Conversa), quando o vídeo pede uma peça que o kit não tem.
    # Modelar e exportar a peça não precisa de placa de vídeo.
    bl = acharBlender()
    vbl = (_saida([bl, "--version"]).strip().splitlines() or [""])[0][:40] if bl else "não encontrado"
    linha(bool(bl) and vbl.startswith("Blender"), "Blender (opcional)", (vbl + " · " + bl) if bl else "só para peça 3D nova (Curta 3D e Conversa)",
          "Só para os estilos 3D, quando o vídeo pede uma peça fora do kit (não precisa de placa de vídeo): "
          + ("brew install --cask blender" if MAC else "winget install BlenderFoundation.Blender")
          + " (ou blender.org, versão 4.2 ou mais nova). Em outro lugar, defina BLENDER com o caminho do executável",
          opcional=True)
    tem_voz = bool(os.environ.get("ELEVENLABS_API_KEY") or chave_do_env("ELEVENLABS_API_KEY"))
    linha(tem_voz, "voz de IA (opcional)", "ElevenLabs, com a chave da pessoa no .env",
          "Só para vídeo com voz de IA: ELEVENLABS_API_KEY=... no arquivo .env da pasta do editor", opcional=True)
    from .pastas import formato_antigo
    if formato_antigo():
        print(f"\nINSTALAÇÃO NO FORMATO ANTIGO: rode {EDITAR_CMD} comecar --migrar (não perde nada).")

    if faltas:
        print("\nFalta instalar:")
        for nome, como in faltas:
            print(f"- {nome}: {como}")
        sys.exit(1)
    print("\nTudo pronto para editar." + (" Opcionais acima com ---." if avisos else ""))
