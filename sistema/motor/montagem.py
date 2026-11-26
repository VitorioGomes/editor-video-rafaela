"""Monta o projeto HyperFrames (1080x1920) a partir do vídeo cortado, das palavras e do roteiro de camadas.

As cores e as fontes vêm da configuração (o padrao.json da ferramenta com o meu-estilo/marca.json por cima).
Cada camada já traz um efeito sonoro padrão do SFX Kit; "som": "id" troca e "som": false tira.
"""
from __future__ import annotations

import html
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from .comum import EFEITOS, FONTES, MEU_ESTILO, REFERENCIAS, config, duracao, gravar_json, ler_json, normal

# Paletas com rodízio: repetir o mesmo som fica chato.
PALETAS = {
    "__clique__": ["click-mouse-medium", "click-snap-soft", "click-mouse-firm", "click-tap-firm", "click-clip-medium", "click-snap-medium"],
    "__imagem__": ["whoosh-fast-soft", "swish-soft", "whoosh-fast-medium", "swish-medium", "zip-out-soft"],
    "__dinheiro__": ["money-register", "money-coin-drop", "money-coin-stack", "money-notes"],
}
QUADRO = 1 / 30  # O som entra um quadro depois da imagem: adiantado incomoda mais que atrasado.


class Tempo:
    """"de" e "ate" aceitam segundos ou uma palavra da fala: "@CRM", "@CRM#2" (a segunda vez que ela aparece),
    "@CRM+0.4" (0,4 s depois dela) e "@CRM#2-0.2".
    A busca ignora maiúscula e acento."""

    def __init__(self, palavras: list[dict]):
        self.palavras = palavras

    def __call__(self, valor) -> float:
        if isinstance(valor, (int, float)):
            return float(valor)
        achado = re.fullmatch(r"@(.+?)(?:#(\d+))?([+-]\d+(?:\.\d+)?)?", str(valor))
        if not achado:
            sys.exit(f"Tempo inválido no roteiro: {valor}")
        alvo, vez = normal(achado.group(1)), int(achado.group(2) or 1)
        iguais = [p for p in self.palavras if normal(p["texto"]) == alvo]
        if len(iguais) < vez:
            sys.exit(f"A palavra {valor} não está na fala (ou aparece menos de {vez} vez). Veja palavras.json.")
        return max(iguais[vez - 1]["inicio"] + float(achado.group(3) or 0), 0.0)  # "@CRM+0.4": 0,4 s depois da palavra


def listar_palavras(arquivo: Path, de: float = 0.0, ate: float = 1e9) -> None:
    """Cada palavra com o tempo e a referência pronta para o roteiro ("@CRM#2"), para não contar as repetições à mão."""
    palavras = ler_json(arquivo)
    vezes: dict[str, int] = {}
    for n, p in enumerate(palavras):
        chave = normal(p["texto"])
        vezes[chave] = vezes.get(chave, 0) + 1
        if de <= p["inicio"] <= ate and chave:
            ref = f"@{p['texto'].strip('.,;:!?')}" + (f"#{vezes[chave]}" if vezes[chave] > 1 else "")
            print(f"{n:4d}  {p['inicio']:7.3f}  {p['fim']:7.3f}  {ref}")


def listar_falas(arquivo: Path) -> None:
    """As falas com o número de cada uma (o i do S.em(i, 'palavra') da Série Animada), o tempo e quem fala."""
    palavras = ler_json(arquivo)
    falas: dict[int, list[dict]] = {}
    for n, p in enumerate(palavras):
        falas.setdefault(p.get("fala", n), []).append(p)
    for i, (k, ps) in enumerate(sorted(falas.items())):
        quem = ps[0].get("quem", "narrador")
        print(f"{i:3d}  {ps[0]['inicio']:7.3f}  {ps[-1]['fim']:7.3f}  {quem:10s} {' '.join(p['texto'] for p in ps)}")


def picos(arquivo: Path, limite: float = -30.0, intervalo: float = 0.12) -> None:
    """Quando cada som começa num arquivo (o latido, a batida, a tosse): para prender a boca ou o tranco ao som.
    Um pico é quando o volume sobe acima do limite (dB) depois de ficar abaixo dele por mais que o intervalo (s)."""
    import array
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(arquivo), "-ac", "1", "-ar", "8000", "-f", "s16le", "-"], capture_output=True, check=True)
    a = array.array("h"); a.frombytes(r.stdout)
    jan, ultimo, achados = 80, -9.0, []  # janelas de 10 ms
    for i in range(0, len(a) - jan, jan):
        bloco = a[i:i + jan]
        rms = (sum(x * x for x in bloco) / jan) ** 0.5 / 32768
        db = 20 * __import__("math").log10(rms) if rms > 0 else -99
        t = i / 8000
        if db > limite:
            if t - ultimo > intervalo:
                achados.append(t)
            ultimo = t
    print(f"{len(achados)} picos em {arquivo.name} (acima de {limite} dB):")
    print(", ".join(f"{t:.2f}" for t in achados))


def _palavras_da_cena(palavras: list[dict]) -> str:
    """A fala inteira para a animação que pede (a Série Animada desenha a legenda e a boca de quem fala):
    const PALAVRAS = [{texto, inicio, fim, quem, fala}], com quem fala e o número da fala quando o "voz" gravou."""
    campos = ("texto", "inicio", "fim", "quem", "fala")
    lista = [{k: p[k] for k in campos if k in p} for p in palavras]
    return f"const PALAVRAS = {json.dumps(lista, ensure_ascii=False)};"


def clip(id_: str, inicio: float, fim: float, classe: str, conteudo: str, trilha: int, estilo: str = "") -> str:
    st = f' style="{estilo}"' if estilo else ""
    return (f'<div id="{id_}" class="clip {classe}" data-start="{inicio:.3f}" data-duration="{fim - inicio:.3f}" '
            f'data-track-index="{trilha}" data-layout-allow-overlap{st}>{conteudo}</div>')


def achar_animacao(nome: str, roteiro: Path) -> Path:
    """A animação é feita para o vídeo, ao lado do roteiro. As que a pessoa guardou para reusar ficam em meu-estilo/animacoes."""
    # As bases dos estilos (o fundo do Motion, o painel do Metade) também podem vir direto das referências.
    for pasta in (roteiro.parent, roteiro.parent / "animacoes", MEU_ESTILO / "animacoes", REFERENCIAS):
        if (pasta / nome).exists():
            return pasta / nome
    sys.exit(f"Animação {nome} não encontrada ao lado do roteiro, em animacoes/, em meu-estilo/animacoes nem nas referências.")


def css_fontes(cfg: dict, projeto: Path) -> str:
    regras = []
    for f in cfg["arquivos_de_fonte"]:
        origem = next((p / f["arquivo"] for p in (MEU_ESTILO / "fontes", FONTES) if (p / f["arquivo"]).exists()), None)
        if not origem:
            sys.exit(f"Fonte {f['arquivo']} não encontrada em meu-estilo/fontes nem nas fontes da ferramenta.")
        shutil.copy(origem, projeto / "assets" / "fonts" / origem.name)
        regras.append(f'@font-face {{ font-family: "{f["familia"]}"; src: url("assets/fonts/{origem.name}"); '
                      f'font-weight: {f.get("peso", 400)}; font-style: {f.get("estilo", "normal")}; }}')
    return "\n".join(regras)


def _cor_legenda(leg: dict) -> str:
    """"legenda": {"cor": "destaque"} usa uma cor da marca; "#fbf6c9" vale direto. Sem "cor", a cor de legenda da marca."""
    c = leg.get("cor")
    if not c:
        return "var(--c-legenda)"
    return c if c.startswith("#") else f"var(--c-{c.replace('_', '-')})"


def css_base(cfg: dict, leg: dict) -> str:
    c, f = cfg["cores"], cfg["fontes"]
    variaveis = " ".join([*(f"--c-{k.replace('_', '-')}: {v};" for k, v in c.items()),
                          *(f'--f-{k}: "{v}";' for k, v in f.items())])
    sombra = "0 0 3px rgba(0,0,0,.95), 0 0 8px rgba(0,0,0,.9), 0 2px 14px rgba(0,0,0,.8)"
    return f""":root {{ {variaveis} }}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{ width: 1080px; height: 1920px; overflow: hidden; background: #000; }}
#root {{ position: relative; width: 100%; height: 100%; overflow: hidden; }}
#base {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; object-fit: cover; }}
.topo {{ position: absolute; left: 80px; right: 80px; top: 250px; text-align: center; z-index: 10; color: var(--c-texto);
  text-shadow: 0 2px 16px rgba(0,0,0,.6), 0 0 3px rgba(0,0,0,.35); }}
.serifa {{ font-family: var(--f-serifa), serif; font-size: 124px; line-height: .94; letter-spacing: -.02em; -webkit-text-stroke: 1px currentColor; }}
.manuscrita, .mao {{ font-family: var(--f-mao), cursive; font-style: italic; font-weight: 600; font-size: 72px; line-height: 1.12; margin-top: 12px; color: #fff; letter-spacing: .01em; }}
.destaque {{ font-family: var(--f-serifa), serif; font-size: 170px; line-height: .98; letter-spacing: -.02em; color: var(--c-destaque); margin-top: 2px; -webkit-text-stroke: 1px currentColor; }}
.negrito, .frase {{ font-family: var(--f-forte), sans-serif; font-style: italic; font-weight: 800; font-size: 76px; line-height: 1.08; letter-spacing: -.02em; color: #fff; }}
.frase {{ font-size: 70px; }}
.italico {{ font-family: var(--f-serifa), serif; font-style: italic; font-size: 140px; line-height: .95; text-transform: uppercase; letter-spacing: -.01em; color: #fff; }}
.tela {{ display: block; width: 100%; height: auto; border-radius: 22px; box-shadow: 0 8px 30px rgba(0,0,0,.35); }}
.letra {{ opacity: 0; }}
.risco-caixa {{ position: relative; display: inline-block; }}
.risco {{ position: absolute; left: -24px; right: -24px; top: 54%; height: 10px; background: var(--c-alerta); transform-origin: left center; display: block; }}
.lista {{ text-align: left; left: 90px; right: 90px; }}
.item {{ font-family: var(--f-lista), cursive; font-weight: 600; font-size: 74px; line-height: 1.04; opacity: 0; }}
.leg {{ position: absolute; left: {leg["x"]}px; width: {leg["largura"]}px; top: {leg["y"]}px; z-index: 12; text-align: center; line-height: 1; color: {_cor_legenda(leg)}; }}
.leg-serifa {{ font-family: var(--f-serifa), serif; font-size: 66px; text-shadow: {sombra}; }}
.leg-grande {{ font-family: var(--f-serifa), serif; font-size: 112px; -webkit-text-stroke: 1.5px currentColor; text-shadow: 0 0 4px rgba(0,0,0,.9), 0 3px 18px rgba(0,0,0,.75); }}
.leg-forte {{ font-family: var(--f-forte), sans-serif; font-weight: 700; font-size: 74px; letter-spacing: -.02em; text-shadow: 0 0 4px rgba(0,0,0,.85), 0 3px 16px rgba(0,0,0,.6); }}
.leg-clara {{ color: var(--c-parede); text-shadow: 0 0 10px rgba(255,255,255,.7), 0 0 3px rgba(255,255,255,.6); -webkit-text-stroke: 0; }}
.leg-destaque {{ color: var(--c-legenda-destaque); -webkit-text-stroke-color: var(--c-legenda-destaque); }}
.leg-futura {{ opacity: .34; }}
.leg-dinamica {{ font-family: var(--f-forte), sans-serif; font-weight: 900; font-size: 104px; line-height: .98; letter-spacing: -.03em; text-transform: uppercase; -webkit-text-stroke: 7px #0d0d0d; paint-order: stroke fill; text-shadow: 0 8px 22px rgba(0,0,0,.55); }}
.leg-dinamica .leg-futura {{ opacity: 1; color: #a7a7a7; -webkit-text-stroke-color: #0d0d0d; }}
.leg-caixa {{ font-family: var(--f-forte), sans-serif; font-weight: 700; font-size: 50px; letter-spacing: -.01em; color: #161616; }}
.leg.leg-caixa {{ display: flex; justify-content: center; }}
.leg-caixa .leg-q {{ display: inline-block; background: #fff; border: 3px solid #161616; box-shadow: 6px 6px 0 #161616; padding: 10px 24px 12px; }}
.leg-caixa .leg-destaque, .leg-caixa.leg-destaque {{ color: var(--c-motion); -webkit-text-stroke: 0; }}
.leg-pilula {{ font-family: var(--f-caixinha), var(--f-forte), sans-serif; font-weight: 700; font-size: 50px; line-height: 1.25; letter-spacing: -.01em; color: #141414; }}
.leg.leg-pilula {{ display: flex; justify-content: center; }}
.leg-pilula .leg-q {{ display: inline-block; white-space: nowrap; background: rgba(255,255,255,.86); border-radius: 26px; padding: 12px 28px 10px; box-shadow: 0 8px 22px rgba(0,0,0,.2); }}
.leg-pilula .leg-futura {{ opacity: 1; color: #a6a29c; }}
.leg-pilula .leg-destaque, .leg-pilula.leg-destaque {{ color: var(--c-motion); }}
#palco, #palco-recorte {{ position: absolute; inset: 0; transform-origin: 50% 12%; }}
#palco-recorte {{ z-index: 6; pointer-events: none; }}
.parede {{ z-index: 4; }}
.parede .serifa, .parede .destaque {{ color: var(--c-destaque); -webkit-text-stroke: 1px currentColor; }}
.parede .mao {{ color: #fff; }}
.parede.escura, .parede.escura .serifa, .parede.escura .destaque, .parede.escura .mao {{ color: var(--c-parede); text-shadow: none; }}
#recorte {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; object-fit: cover; z-index: 8; }}
.print {{ position: absolute; z-index: 11; }}
.print-corpo {{ position: relative; }}
.print img {{ display: block; width: 100%; height: auto; border-radius: 22px; box-shadow: 0 8px 30px rgba(0,0,0,.35); }}
.marca {{ position: absolute; inset: 0; width: 100%; height: 100%; overflow: visible; }}
.marca ellipse {{ fill: none; stroke: var(--c-alerta); stroke-width: 7px; vector-effect: non-scaling-stroke; stroke-dasharray: 4000; stroke-dashoffset: 4000; }}
.meme {{ position: absolute; left: 180px; width: 720px; top: 250px; z-index: 11; }}
.meme img, .meme video {{ display: block; width: 100%; height: auto; }}"""


def montar(base: Path, arquivo: Path, roteiro: Path, projeto: Path, sem_efeitos: bool = False) -> None:
    cfg = config()
    palavras = ler_json(arquivo)
    dados = ler_json(roteiro)
    tempo, total = Tempo(palavras), duracao(base)
    # Não apaga a pasta: ela guarda o histórico do projeto (.hyperframes). Só sobrescreve o que gera aqui.
    (projeto / "assets" / "fonts").mkdir(parents=True, exist_ok=True)
    shutil.copy(base, projeto / "assets" / "base.mp4")
    fontes = css_fontes(cfg, projeto)
    leg = {**cfg["legenda"], **dados.get("legenda", {})}

    def midia(caminho: str) -> str:
        origem = (roteiro.parent / caminho).resolve()
        if not origem.exists():
            sys.exit(f"Arquivo do roteiro não encontrado: {caminho}")
        destino = f"assets/{origem.name}"
        shutil.copy(origem, projeto / destino)
        return destino

    def cor(nome: str | None) -> str:
        if not nome:
            return ""
        valor = cfg["cores"].get(nome, nome)  # aceita o nome de uma cor da marca ou um #hex
        return f"color:{valor};-webkit-text-stroke-color:{valor};"

    catalogo = {s["id"]: s for s in ler_json(EFEITOS / "sounds.json")["sounds"]}
    ganho_geral = dados.get("efeitos", {}).get("ganho", cfg["efeitos"]["ganho"])
    sons, deixas, giro, medias = [], [], {}, {}

    def som_arquivo(caminho: str, momento: float, dura: float | None, ganho: float, saida: float) -> None:
        """Som que não é do SFX Kit (gerado para a história, ou da pessoa), ao lado do roteiro.
        Os arquivos vêm com volumes diferentes: cada um é nivelado (média de -20 dB) antes do "ganho"."""
        if sem_efeitos:
            return
        origem = (roteiro.parent / caminho).resolve()
        if not origem.exists():
            sys.exit(f"Som do roteiro não encontrado: {caminho}")
        if origem not in medias:
            r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(origem), "-af", "volumedetect", "-f", "null", "-"],
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
            media = re.search(r"mean_volume: (-?[\d.]+)", r.stderr)
            pico = re.search(r"max_volume: (-?[\d.]+)", r.stderr)
            # nivela pela média, mas sem o pico passar de -6 dB: num arquivo quase todo em silêncio (uma porta rangendo),
            # a média baixa demais faria o som subir até estourar e passar da voz
            media = float(media.group(1)) if media else -20.0
            pico = float(pico.group(1)) if pico else -6.0
            medias[origem] = -20 - min(-20 - media, -6 - pico)
        tamanho = min(duracao(origem), dura if dura else 1e9, total - momento)
        if tamanho <= 0.01:
            print(f"aviso: o som {caminho} em {momento:.2f} s cai fora do vídeo ({total:.2f} s) e ficou de fora.")
            return
        db = -20 - medias[origem] + ganho_geral + ganho
        (projeto / "assets" / "sfx").mkdir(exist_ok=True)
        shutil.copy(origem, projeto / "assets" / "sfx" / origem.name)
        fade = f' data-fade-out="{saida}"' if dura and saida else ""
        sons.append(f'<audio id="s{len(sons)}" class="clip" src="assets/sfx/{origem.name}" data-start="{momento:.3f}" '
                    f'data-duration="{tamanho:.3f}" data-track-index="9" data-volume="{10 ** (db / 20):.3f}"{fade}></audio>')
        deixas.append({"t": round(momento, 3), "ataque": round(momento, 3), "som": origem.stem, "db": round(db, 1)})

    def som(pedido, padrao, momento: float, dura: float | None = None, ganho: float = 0, saida: float | None = None) -> None:
        """Põe o ponto de sincronia do efeito no momento, com a queda que o SFX Kit indica para ficar sob a voz."""
        escolhido = padrao if pedido is None else pedido
        if not escolhido or sem_efeitos:
            return
        if escolhido in PALETAS:
            chave = escolhido
            escolhido = PALETAS[chave][giro.get(chave, 0) % len(PALETAS[chave])]
            giro[chave] = giro.get(chave, 0) + 1
        if escolhido not in catalogo:
            sys.exit(f"Efeito {escolhido} não existe. Veja .ferramenta/sistema/efeitos/catalogue.md.")
        s = catalogo[escolhido]
        inicio_som = momento + QUADRO - s["sync"]["at"]
        corte = max(0.0, -inicio_som)
        tamanho = min(s["duration"] - corte, dura if dura else s["duration"], total - max(inicio_som, 0))
        if tamanho <= 0.01:
            print(f"aviso: o efeito {escolhido} em {momento:.2f} s cai fora do vídeo ({total:.2f} s) e ficou de fora.")
            return
        db = s["under_voiceover_db"] + ganho_geral + ganho
        (projeto / "assets" / "sfx").mkdir(exist_ok=True)
        shutil.copy(EFEITOS / s["file"], projeto / "assets" / "sfx" / f"{escolhido}.wav")
        fade = f' data-fade-out="{saida or 0.04}"' if dura and dura < s["duration"] else ""
        sons.append(f'<audio id="s{len(sons)}" class="clip" src="assets/sfx/{escolhido}.wav" data-start="{max(inicio_som, 0):.3f}" '
                    f'data-duration="{tamanho:.3f}" data-media-start="{corte:.3f}" data-track-index="9" '
                    f'data-volume="{10 ** (db / 20):.3f}"{fade}></audio>')
        # "ataque": quando o som começa a soar de verdade (o ponto de sincronia pode vir depois, como num whoosh).
        ataque = max(inicio_som, 0) + max(s["timing"]["onset"] - corte, 0)
        deixas.append({"t": round(momento, 3), "ataque": round(ataque, 3), "som": escolhido, "db": db})

    e = html.escape
    incluidos: set[str] = set()  # cada base incluída entra uma vez: repetida, a cópia de baixo apagava os ajustes de cima
    atras = []  # camadas entre o vídeo e o recorte da pessoa: a parede
    sem_legenda = [(tempo(c["de"]), min(tempo(c["ate"]), total)) for c in dados.get("camadas", []) if c.get("esconde_legenda")]
    camadas, gsap, estilos, abaixo = [], [], [], []  # abaixo: (início, fim, y, classe) dos trechos com imagem grande
    for n, c in enumerate(dados.get("camadas", [])):
        id_, tipo = f"c{n}", c["tipo"]
        pedido = c.get("som")
        if tipo == "som":
            quando, dura = tempo(c["em"]), c.get("dura")
            if c.get("ate") is not None:  # "ate": o som acaba com a cena, sumindo em 0,4 s até esse instante
                dura = max(0.5, tempo(c["ate"]) - quando)
            if c.get("arquivo"):
                som_arquivo(c["arquivo"], quando, dura, c.get("ganho", 0), 0.4 if c.get("ate") is not None else 0)
            else:
                som(c["id"], None, quando, dura, c.get("ganho", 0), 0.4 if c.get("ate") is not None else None)
            continue
        if tipo == "zoom":
            # Zoom no palco (vídeo, parede e recorte). "dura" 0 é corte seco; maior que 0, empurrão suave.
            quando = tempo(c["em"])
            alvo = f'scale:{c.get("escala", 1)},x:{c.get("x", 0)},y:{c.get("y", 0)}'
            alvos = "#palco,#palco-recorte" if dados.get("cabeca_por_cima") else "#palco"
            if c.get("dura"):
                gsap.append(f'tl.to("{alvos}",{{{alvo},duration:{c["dura"]},ease:"power2.inOut"}},{quando:.3f});')
            else:
                gsap.append(f'tl.set("{alvos}",{{{alvo}}},{quando:.3f});')
            continue
        inicio, fim = tempo(c["de"]), min(tempo(c["ate"]), total)
        # "x" e "largura" tiram o texto do centro (para a parede livre de um lado, por exemplo).
        lado = (f'left:{c.get("x", 80)}px;right:auto;width:{c.get("largura", 920)}px;'
                if ("x" in c or "largura" in c) and tipo in ("texto", "serifa", "frase", "riscado", "lista") else "")
        if tipo == "texto":
            # Linhas com formatos diferentes: serifa, mao, destaque, negrito ou italico.
            miolo = ""
            som(pedido, "__clique__", inicio)
            for k, l in enumerate(c["linhas"]):
                idl = f"{id_}l{k}"
                estilo = (f'font-size:{l["tamanho"]}px;' if l.get("tamanho") else "") + cor(l.get("cor"))
                if l.get("digita"):
                    em = tempo(l.get("em", inicio))
                    conteudo = "".join(f'<span class="letra">{e(x)}</span>' for x in l["t"])
                    gsap.append(f'tl.set("#{idl} .letra",{{opacity:1,stagger:0.035}},{em:.3f});')
                    som(l.get("som"), "keyboard-typing-quick-medium", em, len(l["t"]) * 0.035)
                elif l.get("em"):
                    em = tempo(l["em"])
                    conteudo, estilo = e(l["t"]), estilo + "opacity:0;"
                    gsap.append(f'tl.set("#{idl}",{{opacity:1}},{em:.3f});')
                    if abs(em - inicio) > 0.05 or "som" in l:  # entrando junto com a camada, o clique dela já toca
                        som(l.get("som"), "__dinheiro__" if "R$" in l["t"] else "__clique__", em)
                else:
                    conteudo = e(l["t"])
                miolo += f'<div class="{l.get("f", "serifa")}" id="{idl}" style="{estilo}">{conteudo}</div>'
            feito = clip(id_, inicio, fim, ("topo parede" + (" escura" if c.get("tinta") == "escura" else "")) if c.get("atras") else "topo", miolo, 2, f'{lado}top:{c.get("y", 250)}px')
            (atras if c.get("atras") else camadas).append(feito)
            if c.get("atras"):
                for k, l in enumerate(c["linhas"]):
                    if not l.get("digita"):
                        quando = tempo(l["em"]) if l.get("em") else inicio
                        gsap.append(f'tl.fromTo("#{id_}l{k}",{{scale:.86}},{{scale:1,duration:.2,ease:"back.out(1.7)"}},{quando:.3f});')
        elif tipo == "bloco":
            # Animação em HTML feita para o vídeo: <style>, a marcação e um <script> que recebe tl, t0, D e M.
            caminho = achar_animacao(c["arquivo"], roteiro)
            fonte = caminho.read_text(encoding="utf-8")
            # <!--#inclui base.css--> traz um pedaço comum a várias animações: da mesma pasta, do meu-estilo/animacoes
            # ou das bases dos estilos em skill/referencias/animacoes (mo-base.css, mo-base.js, mm-base.css).
            def incluir(m):
                if m.group(1).endswith(".css"):
                    if m.group(1) in incluidos:
                        return ""
                    incluidos.add(m.group(1))
                for pasta in (caminho.parent, MEU_ESTILO / "animacoes", REFERENCIAS):
                    if (pasta / m.group(1)).exists():
                        texto = (pasta / m.group(1)).read_text(encoding="utf-8")
                        # A base entra dentro de um <style> ou <script>: "<style>" escrito nela, mesmo num comentário,
                        # abriria ou fecharia a tag e quebraria o render.
                        return re.sub(r"<(/?)(style|script)\b", r"‹\1\2", texto, flags=re.I)
                sys.exit(f"{c['arquivo']} inclui {m.group(1)}, que não está ao lado dela, no meu-estilo/animacoes nem nas referências.")
            fonte = re.sub(r"<!--#inclui (\S+)-->", incluir, fonte)
            fonte = fonte.replace("$ID", id_)
            for antes, depois in c.get("troca", {}).items():  # ajuste pontual no HTML da animação
                antes, depois = antes.replace("$ID", id_), depois.replace("$ID", id_)
                if antes not in fonte:
                    print(f"aviso: troca não achada em {c['arquivo']}: {antes[:60]}")
                fonte = fonte.replace(antes, depois)
            rotulos = c.get("rotulos", [])
            for k in range(10):
                fonte = fonte.replace(f"$R{k}", html.escape(rotulos[k]) if k < len(rotulos) else "")
            fonte = re.sub(r"<!--.*?-->", "", fonte, flags=re.S)
            estilo = re.search(r"<style>(.*?)</style>", fonte, re.S)
            codigo = re.search(r"<script>(.*?)</script>", fonte, re.S)
            if not estilo or not codigo:
                sys.exit(f"A animação {c['arquivo']} precisa de um <style> e de um <script>.")
            miolo = fonte.replace(estilo.group(0), "").replace(codigo.group(0), "").strip()
            estilos.append(estilo.group(1))
            pos = f'left:{c.get("x", 40)}px;top:{c.get("y", 440)}px;width:{c.get("largura", 1000)}px' + (";z-index:4" if c.get("atras") else "")
            (atras if c.get("atras") else camadas).append(clip(id_, inicio, fim, "print", miolo, 3, pos))
            # M: tempos das palavras em "marcas", contados do início da camada, para a animação andar com a fala.
            marcas = [round(tempo(m) - inicio, 3) for m in c.get("marcas", [])]
            gsap.append(f"(function (tl, t0, D, M) {{ {codigo.group(1)} }})(tl, {inicio:.3f}, {fim - inicio:.3f}, {json.dumps(marcas)});")
            if c.get("sai"):  # sai em fade, em vez de sumir de uma vez
                gsap.append(f'tl.to("#{id_}",{{opacity:0,duration:{c["sai"]}}},{fim - c["sai"]:.3f});')
            if c.get("legenda_y") is not None or c.get("legenda_classe"):
                abaixo.append((inicio, fim, c.get("legenda_y"), c.get("legenda_classe", "")))
            elif not c.get("atras") and not c.get("legenda_fica"):
                abaixo.append((inicio, fim, c.get("y", 440) + c.get("altura", 870) + 70, ""))
            som(pedido, "__imagem__", inicio)
            for s in c.get("sons", []):
                # "em" aceita segundos desde o início da camada ou uma palavra da fala.
                quando = tempo(s["em"]) if isinstance(s["em"], str) else inicio + s["em"]
                som(s["id"], None, quando, s.get("dura"), s.get("ganho", 0))
        elif tipo == "tela":
            # Gravação de tela sem som, grande. "origem" escolhe de onde a gravação começa.
            x, y, w = c.get("x", 130), c.get("y", 460), c.get("largura", 820)
            src = midia(c["src"])
            camadas.append(f'<div class="print" style="left:{x}px;top:{y}px;width:{w}px;z-index:11"><video id="{id_}" class="clip tela" src="{src}" muted playsinline '
                           f'data-start="{inicio:.3f}" data-duration="{fim - inicio:.3f}" data-media-start="{c.get("origem", 0)}" data-track-index="3"></video></div>')
            if c.get("altura_tela"):
                abaixo.append((inicio, fim, y + c["altura_tela"] + 30, ""))
            som(pedido, "__imagem__", inicio)
            for k in c.get("cliques", []):  # cliques do cursor, em segundos da gravação
                instante = inicio + k - c.get("origem", 0)
                if inicio < instante < fim:
                    som(None, "click-mouse-soft", instante)
        elif tipo == "serifa":
            tam = f' style="font-size:{c["tamanho"]}px"' if c.get("tamanho") else ""
            linhas = f'<div class="serifa"{tam}>{e(c["texto"])}</div>'
            som(pedido, "__clique__", inicio)
            if c.get("manuscrita"):
                letras = "".join(f'<span class="letra">{e(l)}</span>' for l in c["manuscrita"])
                linhas += f'<div class="manuscrita" id="{id_}m">{letras}</div>'
                entra = tempo(c.get("digita_em", inicio))
                gsap.append(f'tl.set("#{id_}m .letra",{{opacity:1,stagger:{c.get("letra", 0.035)}}},{entra:.3f});')
                som(c.get("som_digitar"), "keyboard-typing-quick-medium", entra, len(c["manuscrita"]) * c.get("letra", 0.035))
            camadas.append(clip(id_, inicio, fim, "topo", linhas, 2, lado + (f'top:{c["y"]}px' if c.get("y") else "")))
        elif tipo == "frase":
            camadas.append(clip(id_, inicio, fim, "topo", f'<div class="frase">{e(c["texto"])}</div>', 2, lado + (f'top:{c["y"]}px' if c.get("y") else "")))
            som(pedido, "__clique__", inicio)
        elif tipo == "riscado":
            risco = f'<div class="risco-caixa"><span class="serifa">{e(c["texto"])}</span><i class="risco" id="{id_}r"></i></div>'
            if c.get("depois"):
                visivel = "opacity:0;" if c.get("depois_em") else ""
                tam = f'font-size:{c["tamanho_depois"]}px;' if c.get("tamanho_depois") else ""
                risco += f'<div class="destaque" id="{id_}d" style="{visivel}{tam}">{e(c["depois"])}</div>'
                if c.get("depois_em"):
                    em = tempo(c["depois_em"])
                    gsap.append(f'tl.set("#{id_}d",{{opacity:1}},{em:.3f});')
                    som(c.get("som_depois"), "__clique__", em)
            camadas.append(clip(id_, inicio, fim, "topo", risco, 2, f'{lado}top:{c.get("y", 250)}px'))
            risca = tempo(c.get("risca_em", inicio))
            gsap.append(f'tl.fromTo("#{id_}r",{{scaleX:0}},{{scaleX:1,duration:.28,ease:"power2.out"}},{risca:.3f});')
            som(pedido, "__clique__", inicio)
            som(c.get("som_risco"), "writing-marker-draw", risca, 0.3)
        elif tipo == "lista":
            itens = "".join(f'<div class="item" id="{id_}i{k}">{e(i["texto"])}</div>' for k, i in enumerate(c["itens"]))
            camadas.append(clip(id_, inicio, fim, "topo lista", itens, 2, lado + (f'top:{c["y"]}px' if c.get("y") else "")))
            for k, i in enumerate(c["itens"]):
                gsap.append(f'tl.set("#{id_}i{k}",{{opacity:1}},{tempo(i["em"]):.3f});')
                som(i.get("som"), "__imagem__", tempo(i["em"]))
        elif tipo == "print":
            x, y, w = c.get("x", 240), c.get("y", 1340), c.get("largura", 600)
            marca = ""
            if c.get("circulo"):
                cx, cy, rx, ry = c["circulo"]
                marca = (f'<svg class="marca" viewBox="0 0 100 100" preserveAspectRatio="none">'
                         f'<ellipse id="{id_}o" cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" /></svg>')
                gsap.append(f'tl.fromTo("#{id_}o",{{strokeDashoffset:4000}},{{strokeDashoffset:0,duration:.45,ease:"power1.inOut"}},{inicio + .3:.3f});')
                som(c.get("som_circulo"), "writing-marker-draw", inicio + .3, 0.45)
            if w >= 700:
                from PIL import Image
                with Image.open((roteiro.parent / c["src"]).resolve()) as foto:
                    abaixo.append((inicio, fim, y + w * foto.height / foto.width + 30, ""))
            imagem = f'<div class="print-corpo" id="{id_}p"><img src="{midia(c["src"])}" alt="" />{marca}</div>'
            camadas.append(clip(id_, inicio, fim, "print", imagem, 3,
                                f'left:{x}px;top:{y}px;width:{w}px;z-index:{13 if c.get("cobre_legenda") else 11}'))
            gsap.append(f'tl.fromTo("#{id_}p",{{scale:.92,opacity:0}},{{scale:1,opacity:1,duration:.14,ease:"power2.out"}},{inicio:.3f});')
            som(pedido, "__imagem__", inicio)
        elif tipo == "meme":
            src = midia(c["src"])
            som(pedido, False, inicio)
            if src.endswith((".mp4", ".webm", ".mov")):
                camadas.append(f'<div class="meme"><video id="{id_}v" class="clip" src="{src}" muted playsinline data-start="{inicio:.3f}" '
                               f'data-duration="{fim - inicio:.3f}" data-track-index="5"></video></div>')
            else:
                camadas.append(clip(id_, inicio, fim, "meme", f'<img src="{src}" alt="" />', 4))
        else:
            sys.exit(f"Tipo de camada desconhecido: {tipo}. Tipos: texto, serifa, frase, riscado, lista, print, tela, meme, bloco, zoom, som.")

    # Legenda: uma palavra por vez, troca seca.
    destaques = [normal(x) for x in leg.get("destaques", [])]
    legendas = []
    # Karaokê ("modo": "karaoke"): a frase curta aparece inteira, apagada, e cada palavra acende quando é falada.
    trecho_de: dict[int, list[int]] = {}
    if leg.get("modo") == "karaoke":
        limite, atual, letras = leg.get("caracteres", 26), [], 0
        # "juntas": ["VS Code", "Claude Code"]: nomes de duas palavras que não se partem entre duas frases da legenda.
        juntas = {normal(j.split()[0]) + " " + normal(j.split()[-1]) for j in leg.get("juntas", []) if len(j.split()) == 2}
        # "sem_ponta_curta": true: a frase da legenda não termina em palavra de ligação ("igual a", "perguntar mas");
        # ela passa para a frase seguinte, junto com a palavra que ela liga. Desligado por padrão.
        curtas = {"a", "o", "as", "os", "e", "de", "da", "do", "das", "dos", "em", "no", "na", "nos", "nas", "que", "um",
                  "uma", "ao", "aos", "pelo", "pela", "pelos", "pelas", "num", "numa", "mas", "por", "para", "pra", "com", "se", "me", "te", "lhe", "nao", "the", "of", "to",
                  "and"} if leg.get("sem_ponta_curta") else set()
        for n, p in enumerate(palavras):
            # Sem ponto na transcrição entre duas frases, a pausa da fala separa: duas frases nunca numa caixinha só.
            pausa = n and p["inicio"] - palavras[n - 1]["fim"] > leg.get("pausa", 0.3)
            if atual and (letras + len(p["texto"]) > limite or pausa):
                par = normal(palavras[n - 1]["texto"]) + " " + normal(p["texto"])
                ponta = palavras[n - 1]["texto"]
                curta = normal(ponta) in curtas and ponta[-1:] not in ".,;:!?"
                leva = [atual.pop()] if (par in juntas or curta) and len(atual) > 1 and not pausa else []
                for k in atual:
                    trecho_de[k] = atual
                atual = leva
                letras = sum(len(palavras[k]["texto"]) + 1 for k in leva)
            atual.append(n)
            letras += len(p["texto"]) + 1
            if p["texto"][-1:] in (".?!," if leg.get("quebra_virgula") else ".?!"):
                for k in atual:
                    trecho_de[k] = atual
                atual, letras = [], 0
        for k in atual:
            trecho_de[k] = atual

    def texto_legenda(n: int) -> str:
        if n not in trecho_de:
            return e(palavras[n]["texto"].strip(".,;:!?"))
        partes = []
        for k in trecho_de[n]:
            c = "leg-destaque" if normal(palavras[k]["texto"]) in destaques else ""
            c += " leg-futura" if k > n else ""
            # No karaokê, o "?" e o "!" do fim ficam: a pergunta continua pergunta.
            partes.append(f'<span class="{c.strip()}">{e(palavras[k]["texto"].strip(".,;:").rstrip(".,;:"))}</span>')
        return " ".join(partes)

    for n, p in enumerate(palavras):
        fim = palavras[n + 1]["inicio"] if n + 1 < len(palavras) else min(p["fim"] + 0.3, total)
        fim = max(fim, p["inicio"] + 0.04)
        if any(a <= p["inicio"] < b for a, b in sem_legenda):
            continue  # texto grande na frente com a mesma fala: a legenda some ali, para não repetir a palavra
        classe = f'leg {leg["classe"]}'
        if normal(p["texto"]) in destaques and n not in trecho_de:
            classe += " leg-destaque"
        if n in trecho_de and n != trecho_de[n][-1]:
            fim = palavras[n + 1]["inicio"]  # dentro do trecho, a troca é na palavra seguinte
        elif n in trecho_de and n + 1 < len(palavras):
            fim = min(palavras[n + 1]["inicio"], p["fim"] + 0.6)  # o trecho some logo depois da última palavra
        fim = max(fim, p["inicio"] + 0.04)
        desce, cara = next(((y, k) for a, b, y, k in abaixo if a <= p["inicio"] < b), (None, ""))
        if cara:
            classe += " " + cara
        # Com imagem grande na tela, a legenda desce para baixo dela, centralizada.
        estilo = f"left:0;width:1080px;top:{desce:.0f}px" if desce is not None else ""
        conteudo = texto_legenda(n)
        if "leg-caixa" in classe or "leg-pilula" in classe:
            conteudo = f'<span class="leg-q">{conteudo}</span>'
        legendas.append(clip(f"p{n}", p["inicio"], min(fim, total), classe, conteudo, 1, estilo))

    recorte = ""
    if dados.get("recorte"):
        recorte = (f'<video id="recorte" class="clip" src="{midia(dados["recorte"])}" muted playsinline data-start="0" data-duration="{total:.3f}" '
                   f'data-track-index="1" data-layout-allow-occlusion></video>')
    video_base = f'<video id="base" class="clip" src="assets/base.mp4" data-start="0" data-duration="{total:.3f}" data-track-index="0" data-has-audio="true" playsinline></video>'
    if dados.get("cabeca_por_cima"):
        # Metade: o painel fica fora do palco, entre o vídeo e o recorte, e a cabeça passa por cima da borda dele.
        palco_html = "\n".join(['<div id="palco">', video_base, '</div>', *atras, '<div id="palco-recorte">', recorte, '</div>'])
    else:
        palco_html = "\n".join(['<div id="palco">', video_base, *atras, recorte, '</div>'])
    pagina = f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
<style>
{fontes}
{css_base(cfg, leg)}
{chr(10).join(estilos)}
{dados.get('css', '')}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{total:.3f}" data-width="1080" data-height="1920">
{palco_html}
{chr(10).join(camadas)}
{chr(10).join(legendas)}
{chr(10).join(sons)}
</div>
<script>
const tl = gsap.timeline({{ paused: true }});{chr(10) + _palavras_da_cena(palavras) if any("PALAVRAS" in g for g in gsap) else ""}
{chr(10).join(gsap)}
window.__timelines["main"] = tl;
</script>
</body>
</html>
"""
    (projeto / "index.html").write_text(pagina, encoding="utf-8")
    gravar_json(projeto / "hyperframes.json", {"$schema": "https://hyperframes.heygen.com/schema/hyperframes.json"})
    gravar_json(projeto / "meta.json", {"id": projeto.name, "name": projeto.name})
    gravar_json(projeto / "deixas.json", deixas)
    print(f"Projeto em {projeto} ({total:.2f} s, {len(palavras)} palavras, {len(camadas) + len(atras)} camadas, {len(sons)} efeitos)")
