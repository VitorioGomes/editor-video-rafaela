"""Peças usadas por todo o motor: caminhos, configuração, ffmpeg e a busca de palavra na fala."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

SISTEMA = Path(__file__).resolve().parents[1]
# A ferramenta (o clone do GitHub, com skill/ e sistema/) mora em .ferramenta/, escondida dentro da pasta do editor,
# e os arquivos da pessoa ficam soltos na pasta do editor, fora dela (2026-11-21). Assim o git pull só mexe na
# ferramenta, e o gosto e os roteiros entram no backup da pessoa. Fora de uma .ferramenta/ (a oficina, ou a
# instalação antiga antes do comecar --migrar), a pasta do editor é a própria ferramenta.
FERRAMENTA = SISTEMA.parent
EDITOR = FERRAMENTA.parent if FERRAMENTA.name == ".ferramenta" else FERRAMENTA
RAIZ = EDITOR  # nome antigo: a pasta principal, a de quem usa
MEU_ESTILO = EDITOR / "meu-estilo"
FONTES = SISTEMA / "fontes"
EFEITOS = SISTEMA / "efeitos"
REFERENCIAS = FERRAMENTA / "skill" / "referencias" / "animacoes"
HYPERFRAMES = "hyperframes@0.9.9"

# As pastas da pessoa, soltas na pasta do editor:
#   brutos/     onde ela põe o vídeo ou o áudio gravado
#   versoes/    cada versão que ela assiste antes de aprovar (NOME-v1.mp4, NOME-v2.mp4...)
#   editados/   o vídeo aprovado, pronto para postar
#   meu-estilo/ o gosto dela
#   roteiros/   os roteiros aprovados (NOME.md)
# O trabalho de cada vídeo (corte, transcrição, roteiro.json, animações, render) fica em .projetos/NOME/, escondida.
BRUTOS = EDITOR / "brutos"
VERSOES = EDITOR / "versoes"
EDITADOS = EDITOR / "editados"
ROTEIROS = EDITOR / "roteiros"
PROJETOS = EDITOR / ".projetos"
ENV = EDITOR / ".env"  # a chave da ElevenLabs: fora da ferramenta (sobrevive a baixar de novo) e fora do backup


def rel(caminho: Path) -> str:
    """O caminho como a pessoa (e a IA) escreve nos comandos: relativo à pasta do editor."""
    try:
        return Path(caminho).resolve().relative_to(EDITOR).as_posix()
    except ValueError:
        return str(caminho)


EDITAR = f"python {rel(SISTEMA / 'editar.py')}"  # o comando, de dentro da pasta do editor


def chave_do_env(nome: str) -> str | None:
    """Uma linha NOME=valor do .env da pasta do editor (ou da ferramenta, onde ficava na versão antiga)."""
    for env in (ENV, FERRAMENTA / ".env"):
        if env.exists():
            for linha in env.read_text(encoding="utf-8", errors="replace").splitlines():
                if linha.strip().startswith(nome + "="):
                    return linha.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def nome_do_video(arquivo: Path) -> str:
    """O NOME do vídeo a partir de um arquivo dele: a pasta em .projetos/NOME/ (ou projetos/NOME/ e videos/NOME/,
    das versões antigas), ou o nome do arquivo sem o "-v2" do fim."""
    partes = Path(arquivo).resolve().parts
    for raiz in (".projetos", "projetos", "videos"):
        if raiz in partes:
            i = len(partes) - 1 - partes[::-1].index(raiz)
            if i + 1 < len(partes) - 1:
                return partes[i + 1]
    return re.sub(r"-v\d+$", "", Path(arquivo).stem)


def proxima_versao(nome: str) -> Path:
    """versoes/NOME-vN.mp4, com o primeiro N livre."""
    VERSOES.mkdir(parents=True, exist_ok=True)
    n = 1
    while (VERSOES / f"{nome}-v{n}.mp4").exists():
        n += 1
    return VERSOES / f"{nome}-v{n}.mp4"


def config() -> dict:
    """padrao.json com o meu-estilo/marca.json por cima: a marca da pessoa só precisa ter o que muda."""
    base = json.loads((SISTEMA / "padrao.json").read_text(encoding="utf-8"))
    marca = MEU_ESTILO / "marca.json"
    if marca.exists():
        _juntar(base, json.loads(marca.read_text(encoding="utf-8")))
    return base


def _juntar(base: dict, por_cima: dict) -> None:
    for k, v in por_cima.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _juntar(base[k], v)
        else:
            base[k] = v


def rodar(cmd: list, env: dict | None = None) -> subprocess.CompletedProcess:
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env={**os.environ, "PYTHONIOENCODING": "utf-8", **(env or {})})
    if r.returncode:
        sys.exit(f"Falhou: {' '.join(str(c) for c in cmd)[:200]}\n{(r.stderr or r.stdout)[-800:]}")
    return r


def npx() -> str:
    """No Windows o npx é npx.cmd; o which acha o certo nos dois sistemas."""
    caminho = shutil.which("npx")
    if not caminho:
        sys.exit(f"Node.js não encontrado (falta o npx). Rode: {EDITAR} verificar")
    return caminho


def hyperframes(*args, cwd: Path | None = None) -> subprocess.CompletedProcess:
    env = {**os.environ, "HYPERFRAMES_SKIP_SKILLS": "1", "PYTHONIOENCODING": "utf-8"}
    r = subprocess.run([npx(), "-y", HYPERFRAMES, *[str(a) for a in args]], cwd=cwd, env=env,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        sys.exit(f"HyperFrames falhou: {' '.join(str(a) for a in args)[:200]}\n{(r.stderr or r.stdout)[-1500:]}")
    return r


def duracao(video: Path) -> float:
    return float(rodar(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", video]).stdout)


def eh_hdr(video: Path) -> bool:
    """Celular moderno grava em HDR (PQ ou HLG). Sem converter, a cor fica lavada."""
    r = rodar(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=color_transfer",
               "-of", "csv=p=0", video])
    # o ffprobe 8+ põe uma vírgula no fim ("arib-std-b67,"), e sem tirar ela o HDR nunca era reconhecido
    return r.stdout.strip().splitlines()[0].strip().strip(",") in ("smpte2084", "arib-std-b67") if r.stdout.strip() else False


def tem_video(arquivo: Path) -> bool:
    """Áudio sozinho (a voz gravada no celular, para o Motion) vira vídeo preto com a voz."""
    r = rodar(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=codec_type,disposition",
               "-of", "json", arquivo])
    fluxos = json.loads(r.stdout).get("streams", [])
    return any(not f.get("disposition", {}).get("attached_pic") for f in fluxos)  # capa de .m4a não conta


def preto(segundos: float) -> list[str]:
    """Entrada de vídeo preto com a duração exata da voz (o -shortest não vale com filter_complex)."""
    return ["-f", "lavfi", "-i", f"color=c=black:s=1080x1920:r=30:d={segundos:.3f}"]


def audio(video: Path, taxa: int = 16000):
    """O áudio do vídeo em mono, como números, sem arquivo intermediário."""
    import numpy as np
    bruto = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-map", "0:a:0", "-ac", "1", "-ar", str(taxa),
                            "-f", "f32le", "-"], capture_output=True).stdout
    return np.frombuffer(bruto, dtype=np.float32)


def niveis(y, taxa: int, passo: float):
    """Volume em dB a cada passo (s)."""
    import numpy as np
    h = int(taxa * passo)
    rms = np.sqrt(np.convolve(y ** 2, np.ones(h) / h, "same"))[::h]
    return 20 * np.log10(rms + 1e-7)


def normal(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFD", texto.lower())
    return re.sub(r"[^\w%]", "", "".join(c for c in sem_acento if unicodedata.category(c) != "Mn"))


def ler_json(caminho: Path):
    return json.loads(Path(caminho).read_text(encoding="utf-8"))


def gravar_json(caminho: Path, dados) -> None:
    Path(caminho).write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
