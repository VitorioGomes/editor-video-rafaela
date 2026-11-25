"""A pasta do editor: a instalação (comecar), a migração da versão antiga, a atualização e o vídeo aprovado.

A pasta do editor tem a ferramenta escondida (.ferramenta/, o clone do GitHub, com skill/ e sistema/) e os
arquivos da pessoa soltos, fora dela:

  brutos/      onde a pessoa põe o vídeo ou o áudio gravado
  versoes/     as versões que ela assiste antes de aprovar
  editados/    os vídeos aprovados, prontos para postar
  meu-estilo/  o gosto dela: marca.json (vazio = os padrões de cada estilo) e regras.md
  roteiros/    os roteiros aprovados
  .projetos/   o trabalho de cada vídeo (escondida; a pessoa não precisa abrir)

O trabalho fica em .projetos/, ao lado da .ferramenta/ e não dentro dela: assim a ferramenta pode ser apagada e
baixada de novo, o git pull nunca esbarra num arquivo da pessoa e a .ferramenta/ continua sendo só o clone.
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

from .comum import (BRUTOS, EDITADOS, EDITOR, FERRAMENTA, MEU_ESTILO, PROJETOS, ROTEIROS, VERSOES,
                    nome_do_video)

WIN = platform.system() == "Windows"
OFICINA = (FERRAMENTA / "publicacao").is_dir()  # a oficina de quem faz o produto: nada de migrar nem mexer no git
PORTAS = ("CLAUDE.md", "AGENTS.md", "GEMINI.md")  # Claude Code, Codex e Gemini CLI
MARCA_PORTA = ".ferramenta/skill/EDITAR.md"
MIDIA = ("mp4", "mov", "m4v", "mkv", "webm", "avi", "mts", "wav", "mp3", "m4a", "aac", "flac", "ogg", "opus", "aif", "aiff")
# o que pode estar na pasta do editor; outra coisa quer dizer que a pasta é de outro uso
NOSSOS = {".ferramenta", ".projetos", "brutos", "versoes", "editados", "meu-estilo", "roteiros", ".env", ".gitignore",
          ".git", ".claude", ".codex", ".gemini", ".DS_Store", "desktop.ini", "Thumbs.db", *PORTAS}

REGRAS = """# O meu estilo

O que a IA aprendeu com as correções e as aprovações. Cada linha com a data.

## Perfil

- Nicho e público: (sai do primeiro roteiro ou vídeo)
- Voz nos estilos sem rosto: (ia ou gravada)

## Todos os estilos

## Título

## Títulos Desenhados

## Parede

## Metade

## Motion

## Tela do Claude

## Colagem

## Série Animada

## Curta 3D

## Conversa
"""


def formato_antigo() -> bool:
    """A ferramenta fora de uma .ferramenta/: a instalação antiga (os arquivos da pessoa dentro do clone), ou um clone
    feito no lugar errado. As duas se resolvem com o comecar --migrar."""
    return FERRAMENTA.name != ".ferramenta" and not OFICINA and (FERRAMENTA / ".git").exists()


def _git(*args, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *map(str, args)], cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                          errors="replace")


def _livre(alvo: Path) -> Path:
    n = 2
    destino = alvo
    while destino.exists():
        destino = alvo.with_name(f"{alvo.stem}-{n}{alvo.suffix}")
        n += 1
    return destino


def _juntar_pasta(de: Path, para: Path) -> None:
    """Move de para para; se para já existe, move item por item, sem sobrescrever nada."""
    if not para.exists():
        shutil.move(str(de), str(para))
        return
    for item in sorted(de.iterdir()):
        alvo = para / item.name
        if item.is_dir() and alvo.is_dir():
            _juntar_pasta(item, alvo)
        else:
            shutil.move(str(item), str(_livre(alvo)))
    if not any(de.iterdir()):
        de.rmdir()


def _esconder(pasta: Path) -> None:
    """No Windows, o ponto no nome não esconde: marca como oculta. No Mac, o ponto já basta.
    Só pastas: no Windows, um arquivo oculto não pode ser regravado por quem abre com "w" (dá acesso negado)."""
    if WIN and pasta.is_dir():
        subprocess.run(["attrib", "+h", str(pasta)], capture_output=True)


def _raiz_git(de: Path) -> Path | None:
    """O repositório Git em que a pasta está, procurando o .git subindo as pastas (o da .ferramenta/ não conta)."""
    for d in (de, *de.parents):
        if (d / ".git").exists():
            return d
    return None


# ---------------------------------------------------------------- as portas de entrada

def _porta_da_pasta() -> str:
    for base in (FERRAMENTA, EDITOR / ".ferramenta"):  # logo depois do --migrar, FERRAMENTA ainda é o caminho antigo
        modelo = base / "skill" / "entradas" / "pasta-do-editor.md.modelo"
        if modelo.exists():
            return modelo.read_text(encoding="utf-8")
    raise SystemExit("Falta skill/entradas/pasta-do-editor.md.modelo na ferramenta.")


def _secao(caminho: str) -> str:
    pasta = "esta pasta" if caminho == "." else f"`{caminho}/`"
    prefixo = "" if caminho == "." else f"{caminho}/"
    return ("## Editor de vídeo com IA\n\n"
            f"Para editar vídeo (Reels, TikTok, Shorts) ou mexer nos vídeos de {pasta}, leia "
            f"`{prefixo}{MARCA_PORTA}` e siga aquele roteiro, com os comandos rodando de dentro de {pasta}.\n")


def _acrescentar(arquivo: Path, texto: str, marca: str) -> bool:
    """Acrescenta no fim, sem apagar nada do que a pessoa tem. Não repete se já estiver lá."""
    atual = arquivo.read_text(encoding="utf-8", errors="replace")
    if marca in atual:
        return False
    with arquivo.open("a", encoding="utf-8", newline="") as f:
        f.write(("" if not atual else "\n" if atual.endswith("\n") else "\n\n") + texto)
    return True


def _portas(feito: list[str]) -> None:
    """A IA da pessoa acha o roteiro quando é aberta na pasta do editor e também na pasta acima, onde ela abriu a IA
    para instalar (o segundo cérebro). Ali só se acrescenta uma seção ao CLAUDE.md, AGENTS.md ou GEMINI.md que já
    existe, sem apagar nada."""
    for nome in PORTAS:
        arq = EDITOR / nome
        if not arq.exists():
            arq.write_text(_porta_da_pasta(), encoding="utf-8")
            feito.append(nome)
        elif _acrescentar(arq, _secao("."), MARCA_PORTA):
            feito.append(f"{nome} (seção nova, o resto ficou como estava)")

    aberta = Path.cwd().resolve()
    if aberta == EDITOR or aberta not in EDITOR.parents:
        return
    caminho = EDITOR.relative_to(aberta).as_posix()
    existentes = [aberta / n for n in PORTAS if (aberta / n).exists()]
    for arq in existentes:
        if _acrescentar(arq, _secao(caminho), f"{caminho}/{MARCA_PORTA}"):
            feito.append(f"{arq.name} de {aberta.name}/ (seção nova, o resto ficou como estava)")
    if not existentes:
        print(f"Em {aberta.name}/ não há CLAUDE.md, AGENTS.md nem GEMINI.md: da próxima vez, abra a IA em {caminho}/.")


# ---------------------------------------------------------------- o backup da pessoa

def _backup(feito: list[str]) -> None:
    """Se a pasta do editor está dentro de um repositório Git (o segundo cérebro com backup no GitHub), o .gitignore
    dele ganha a ferramenta, o trabalho, os vídeos, a mídia pesada e o .env: o meu-estilo/ e os roteiros/ entram
    no backup, e os vídeos não. Fora de um repositório, nada muda."""
    raiz = _raiz_git(EDITOR)
    if raiz is None:
        return
    rel = EDITOR.relative_to(raiz).as_posix()
    base = "" if rel == "." else "/" + rel
    linhas = [f"{base}/.ferramenta/", f"{base}/.projetos/", f"{base}/brutos/", f"{base}/versoes/", f"{base}/editados/",
              f"{base}/.env", *[f"{base}/**/*.{ext}" for ext in MIDIA]]
    gi = raiz / ".gitignore"
    atual = gi.read_text(encoding="utf-8", errors="replace") if gi.exists() else ""
    tem = {l.strip() for l in atual.splitlines()}
    novas = [l for l in linhas if l not in tem]
    if novas:
        bloco = "" if not atual else "\n" if atual.endswith("\n") else "\n\n"
        bloco += "# Editor de vídeo com IA: a ferramenta, o trabalho de cada vídeo e os vídeos ficam fora do backup\n"
        bloco += "\n".join(novas) + "\n"
        with gi.open("a", encoding="utf-8", newline="") as f:
            f.write(bloco)
        feito.append(f".gitignore de {raiz.name}/ ({len(novas)} linhas)")
    # A instalação antiga era um repositório dentro do repositório: o Git da pessoa pode ter guardado a pasta como
    # repositório embutido (gitlink), e aí nada de dentro entrava no backup. Sai só do índice; os arquivos ficam.
    if rel != ".":
        r = _git("ls-files", "-s", "--", rel, cwd=raiz)
        if r.returncode == 0 and r.stdout.startswith("160000"):
            _git("rm", "--cached", "-q", rel, cwd=raiz)
            feito.append(f"{rel}/ deixou de ser repositório embutido no Git de {raiz.name}/")
    print("BACKUP: a pasta está num repositório Git. Diga à pessoa, numa frase: o gosto e os roteiros entram no "
          "backup dela; os vídeos ficam no computador, porque o GitHub não aceita arquivo acima de 100 MB (o lugar "
          "deles é um Google Drive ou um HD).")


# ---------------------------------------------------------------- migração da versão antiga

def _migrar() -> None:
    """A instalação antiga: o clone era a pasta principal, com editor/, projetos/ e meu-estilo/ dentro dele.
    A pasta continua a mesma e vira a pasta do editor: o clone vai para .ferramenta/, os vídeos saem de editor/
    para a pasta, projetos/ vira .projetos/ e os roteiros aprovados ganham uma cópia em roteiros/. Nada é apagado."""
    pasta = FERRAMENTA
    nova = pasta / ".ferramenta"
    if nova.exists():
        raise SystemExit(f"Já existe {nova}: a migração não roda duas vezes.")
    r = _git("ls-tree", "--name-only", "HEAD", cwd=pasta)
    if r.returncode or not r.stdout.strip():
        raise SystemExit("Não consegui ler o repositório da ferramenta (git ls-tree). Nada foi mexido.")
    da_ferramenta = [".git", *[n for n in r.stdout.splitlines() if n.strip()]]
    nova.mkdir()
    for nome in da_ferramenta:
        if (pasta / nome).exists():
            shutil.move(str(pasta / nome), str(nova / nome))
    print(f"A ferramenta foi para .ferramenta/ ({len(da_ferramenta) - 1} itens e o histórico do git).")

    antiga = pasta / "editor"
    for sub in ("brutos", "versoes", "editados"):
        if (antiga / sub).is_dir():
            _juntar_pasta(antiga / sub, pasta / sub)
            print(f"  editor/{sub}/ -> {sub}/")
    if antiga.is_dir() and not any(antiga.iterdir()):
        antiga.rmdir()
    elif antiga.is_dir():
        print("  editor/ ficou, com o que não era das três pastas de vídeo: " + ", ".join(p.name for p in antiga.iterdir()))

    if (pasta / "projetos").is_dir():
        _juntar_pasta(pasta / "projetos", pasta / ".projetos")
        print("  projetos/ -> .projetos/")

    videos = pasta / "videos"  # a versão de antes da editor/: o bruto, o corte e o pronto.mp4 juntos
    if videos.is_dir():
        (pasta / "editados").mkdir(exist_ok=True)
        (pasta / ".projetos").mkdir(exist_ok=True)
        for v in sorted(p for p in videos.iterdir() if p.is_dir()):
            for pronto in sorted(v.glob("pronto*.mp4")):
                shutil.move(str(pronto), str(_livre(pasta / "editados" / f"{v.name}{pronto.stem[len('pronto'):]}.mp4")))
            shutil.move(str(v), str(_livre(pasta / ".projetos" / v.name)))
        if not any(videos.iterdir()):
            videos.rmdir()
        print("  videos/ -> .projetos/ (os pronto.mp4 em editados/)")

    projetos = pasta / ".projetos"
    if projetos.is_dir():
        (pasta / "roteiros").mkdir(exist_ok=True)
        for rot in sorted(projetos.glob("*/roteiro.md")):
            alvo = pasta / "roteiros" / f"{rot.parent.name}.md"
            if not alvo.exists():
                shutil.copy2(rot, alvo)
                print(f"  .projetos/{rot.parent.name}/roteiro.md -> roteiros/{alvo.name} (cópia)")
        # o bruto das tentativas apontava para ../../../editor/brutos/
        for esc in projetos.rglob("escolhas.json"):
            try:
                dados = json.loads(esc.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            b = str(dados.get("bruto", "")).replace("\\", "/")
            if b and not (esc.parent / b).exists() and "editor/brutos/" in b:
                novo = b.replace("editor/brutos/", "brutos/")
                if (esc.parent / novo).exists():
                    dados["bruto"] = novo
                    esc.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")


# ---------------------------------------------------------------- comecar e atualizar

def comecar(migrar: bool = False) -> None:
    """Cria o que falta, sem mexer no que já existe. Pode rodar quantas vezes quiser."""
    if formato_antigo():
        if not migrar:
            raise SystemExit("INSTALAÇÃO NO FORMATO ANTIGO (os arquivos da pessoa dentro da ferramenta). Rode: "
                             "python sistema/editar.py comecar --migrar  (não perde nada).")
        _migrar()
    elif migrar and not OFICINA:
        print("Nada a migrar: a instalação já está no formato novo.")
        migrar = False

    if not OFICINA and not migrar and not MEU_ESTILO.exists():  # primeira instalação: a pasta tem que ser só do editor
        outros = sorted(p.name for p in EDITOR.iterdir()
                        if p.name not in NOSSOS and p.suffix.lower().lstrip(".") not in MIDIA)
        if outros:
            raise SystemExit(
                f"A pasta {EDITOR} já tinha outras coisas ({', '.join(outros[:6])}{'...' if len(outros) > 6 else ''}). "
                "O editor fica numa pasta só dele: crie uma pasta editor/ aqui dentro (ou editor-de-video/, se já houver "
                "uma editor/ de outro uso), mova a .ferramenta/ para dentro dela e rode o comecar de novo.")

    feito: list[str] = []
    for pasta in (BRUTOS, VERSOES, EDITADOS, MEU_ESTILO, ROTEIROS, PROJETOS):
        if not pasta.exists():
            pasta.mkdir(parents=True)
            feito.append(pasta.name + "/")
    marca = MEU_ESTILO / "marca.json"
    if not marca.exists():
        marca.write_text("{}\n", encoding="utf-8")  # vazio: valem as cores e fontes de cada estilo
        feito.append("meu-estilo/marca.json")
    regras = MEU_ESTILO / "regras.md"
    if not regras.exists():
        regras.write_text(REGRAS, encoding="utf-8")
        feito.append("meu-estilo/regras.md")

    if not OFICINA:
        _esconder(EDITOR / ".ferramenta")
        _esconder(PROJETOS)
        _portas(feito)
        _backup(feito)
    print("Criado: " + ", ".join(feito) if feito else "Tudo já existia.")
    print("A pessoa só precisa abrir brutos/ (o que ela grava), versoes/ (para assistir) e editados/ (aprovados).")


def atualizar() -> None:
    """Baixa a versão nova da ferramenta (git pull na .ferramenta/). Os arquivos da pessoa ficam fora dela e não mudam."""
    if formato_antigo():
        raise SystemExit("Antes de atualizar, rode: python sistema/editar.py comecar --migrar")
    if OFICINA:
        raise SystemExit("Esta é a oficina: a atualização é a publicação, não o git pull.")
    antes = _git("rev-parse", "HEAD", cwd=FERRAMENTA).stdout.strip()
    r = _git("pull", "--ff-only", cwd=FERRAMENTA)
    if r.returncode:
        raise SystemExit("A atualização não passou (provavelmente um arquivo da ferramenta foi mudado aqui):\n"
                         + (r.stderr or r.stdout)[-800:] + "\nVeja com: git -C .ferramenta status")
    depois = _git("rev-parse", "HEAD", cwd=FERRAMENTA).stdout.strip()
    if antes == depois:
        print("A ferramenta já estava na versão mais nova.")
        return
    print("Atualizado. O que mudou:")
    print(_git("log", "--oneline", "--no-decorate", f"{antes}..{depois}", cwd=FERRAMENTA).stdout.rstrip())
    mudou = _git("diff", "--name-only", antes, depois, cwd=FERRAMENTA).stdout.split()
    for req in ("requisitos.txt", "requisitos-separador.txt"):
        if f"sistema/{req}" in mudou:
            extra = "--no-deps " if "separador" in req else ""
            print(f"Os requisitos mudaram: python -m pip install {extra}-r .ferramenta/sistema/{req}")
    # a versão nova pode trazer uma pasta ou uma porta nova: roda o comecar dela, num processo novo
    sys.stdout.flush()
    subprocess.run([sys.executable, str(FERRAMENTA / "sistema" / "editar.py"), "comecar"], cwd=os.getcwd())


def aprovar(versao: Path) -> None:
    """A versão que a pessoa aprovou vai para editados/NOME.mp4. As outras versões ficam em versoes/."""
    if not versao.exists():
        raise SystemExit(f"Não achei {versao}.")
    EDITADOS.mkdir(parents=True, exist_ok=True)
    destino = _livre(EDITADOS / f"{nome_do_video(versao)}{versao.suffix}")
    shutil.move(str(versao), destino)
    print(f"Aprovado: {destino}")


def abrir_catalogo() -> None:
    """O catálogo dos estilos no navegador da pessoa (Windows e Mac). Abre sem internet."""
    import webbrowser
    catalogo = FERRAMENTA / "skill" / "catalogo.html"
    if not catalogo.exists():
        raise SystemExit(f"Não achei o catálogo em {catalogo}.")
    if webbrowser.open(catalogo.resolve().as_uri()):
        print("Catálogo aberto no navegador.")
    else:
        print(f"Não consegui abrir o navegador. Abra este arquivo: {catalogo}")
