"""Narração com voz de IA (ElevenLabs), para vídeo sem gravação. Opcional: usa a chave e a conta da própria pessoa.

Lê o texto como ele aparece na tela, troca as palavras do meu-estilo/pronuncia.md pela grafia que a voz fala certo,
e grava na pasta de saída:
  voz.wav        a narração, já na velocidade final
  palavras.json  o tempo de cada palavra da tela (o formato do "montar")
  base.mp4       vídeo preto 1080x1920 com a narração, para o "montar"
A chave fica no arquivo .env da pasta do editor (fora da ferramenta e fora do backup): ELEVENLABS_API_KEY=... Cobra um crédito da ElevenLabs por caractere.
Com personagens ([nome] no começo da linha), cada fala sai com a sua voz, e grava também falas.json e falas/ (o cache
de cada fala: refazer uma fala não gasta as outras de novo).
"""
from __future__ import annotations

import base64
import json
import os
import re
import subprocess
import urllib.request
from pathlib import Path

from .comum import MEU_ESTILO, chave_do_env, config, gravar_json


def chave() -> str:
    if os.environ.get("ELEVENLABS_API_KEY"):  # a chave pode vir do ambiente, sem arquivo
        return os.environ["ELEVENLABS_API_KEY"].strip()
    achada = chave_do_env("ELEVENLABS_API_KEY")
    if achada:
        return achada
    raise SystemExit("Falta ELEVENLABS_API_KEY no arquivo .env da pasta do editor.")


_PASTA_DO_TEXTO: Path | None = None  # a pasta do vídeo que está sendo narrado (o pronuncia.md dela vale só para ele)


def trocas() -> list[tuple[str, str]]:
    """Linhas da tabela do pronuncia.md: | Na tela | Para a voz |. Traço quer dizer sem troca.
    O pronuncia.md ao lado do texto vale só para aquele vídeo ("1" falado "um" numa série) e vem antes do banco da
    pessoa (meu-estilo/pronuncia.md), que vale para todos os vídeos dela."""
    res = []
    for banco in ([_PASTA_DO_TEXTO / "pronuncia.md"] if _PASTA_DO_TEXTO else []) + [MEU_ESTILO / "pronuncia.md"]:
        if banco.exists():
            res += _ler_banco(banco)
    return res


def _ler_banco(banco: Path) -> list[tuple[str, str]]:
    res = []
    for linha in banco.read_text(encoding="utf-8").splitlines():
        cel = [c.strip() for c in linha.strip().strip("|").split("|")]
        if len(cel) >= 2 and cel[0] not in ("Na tela", "") and not set(cel[0]) <= {"-", ":"} and cel[1] not in ("—", "-", ""):
            res.append((cel[0], cel[1]))
    return res


def _limpa(p: str) -> str:
    return re.sub(r"[^\w%]", "", p.lower())


def para_voz(tela: list[str]) -> tuple[list[str], list[tuple[int, int]]]:
    """Troca as palavras do banco. A grafia da voz pode ter outro número de palavras ("QR code" vira "quê erre côudi"):
    mapa[i] diz quais palavras da voz formam a palavra i da tela."""
    regras = sorted(((t.split(), v.split()) for t, v in trocas()), key=lambda r: -len(r[0]))
    voz, mapa, i = [], [], 0
    while i < len(tela):
        for tt, vv in regras:
            k = len(tt)
            if [_limpa(x) for x in tela[i:i + k]] == [_limpa(x) for x in tt]:
                antes = re.match(r"^[^\w%]*", tela[i]).group(0)
                depois = re.search(r"[^\w%]*$", tela[i + k - 1]).group(0)
                # o sinal que faz parte da própria palavra da regra ("/" de "/clear") não volta para a voz: ela já
                # diz "barra clír", e o "/" a mais saía como "barra barra"
                proprio_antes = re.match(r"^[^\w%]*", tt[0]).group(0)
                proprio_depois = re.search(r"[^\w%]*$", tt[-1]).group(0)
                if proprio_antes and antes.endswith(proprio_antes):
                    antes = antes[: len(antes) - len(proprio_antes)]
                if proprio_depois and depois.startswith(proprio_depois):
                    depois = depois[len(proprio_depois):]
                vs = vv[:]
                vs[0], vs[-1] = antes + vs[0], vs[-1] + depois
                j0, m = len(voz), len(vs)
                voz += vs
                for q in range(k):  # reparte as palavras da voz entre as da tela
                    a = j0 + m * q // k
                    mapa.append((a, max(a + 1, j0 + m * (q + 1) // k)))
                i += k
                break
        else:
            mapa.append((len(voz), len(voz) + 1))
            voz.append(tela[i])
            i += 1
    return voz, mapa


def narrar(texto: Path, saida: Path, voz_id: str | None = None) -> None:
    global _PASTA_DO_TEXTO
    _PASTA_DO_TEXTO = texto.parent  # o pronuncia.md ao lado do texto vale só para este vídeo
    falas = ler_falas(texto.read_text(encoding="utf-8"))
    if falas is not None:  # texto com [personagem] ou [pausa]: um narrador e uma voz para cada personagem
        return narrar_falas(falas, saida, voz_id)
    cfg = config()
    # texto sem marcação: a voz é a do "voz", ou a do narrador em "vozes" (quem já montou personagens só tem esta)
    ajustes_voz = {**cfg.get("vozes", {}).get("narrador", {}), **cfg.get("voz", {})}
    voz_id = voz_id or ajustes_voz.get("id")
    if not voz_id:
        raise SystemExit('Escolha a voz: "voz": {"id": "..."} (ou "vozes": {"narrador": {"id": "..."}}) no meu-estilo/marca.json, ou --voz ID.')
    modelo = ajustes_voz.get("modelo", "eleven_v4")
    # A voz de IA costuma soar rápida: o áudio é desacelerado depois (o ffmpeg não muda o tom) e os tempos esticam junto.
    velocidade = ajustes_voz.get("velocidade", 0.95)
    saida.mkdir(parents=True, exist_ok=True)
    tt = texto.read_text(encoding="utf-8").split()
    vt, mapa = para_voz(tt)
    fala = " ".join(vt)
    print("voz:", fala)
    k = chave()
    preferencias = json.loads(urllib.request.urlopen(urllib.request.Request(
        f"https://api.elevenlabs.io/v1/voices/{voz_id}/settings", headers={"xi-api-key": k})).read())
    preferencias["speed"] = 1.0
    corpo = {"text": fala, "model_id": modelo, "voice_settings": preferencias}
    if cfg.get("idioma"):
        corpo["language_code"] = cfg["idioma"]
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voz_id}/with-timestamps?output_format=mp3_44100_128",
        data=json.dumps(corpo).encode(), headers={"xi-api-key": k, "Content-Type": "application/json"})
    d = json.loads(urllib.request.urlopen(req).read())
    (saida / "voz-original.mp3").write_bytes(base64.b64decode(d["audio_base64"]))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(saida / "voz-original.mp3"), "-af", f"atempo={velocidade}",
                    "-ar", "48000", str(saida / "voz.wav")], check=True)
    fator = 1 / velocidade
    al = d["alignment"]
    blocos, cur = [], None
    for c, ini, fim in zip(al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]):
        if c.isspace():
            if cur:
                blocos.append(cur)
                cur = None
        elif cur is None:
            cur = [ini, fim]
        else:
            cur[1] = fim
    if cur:
        blocos.append(cur)
    if len(blocos) != len(vt):
        raise SystemExit(f"Alinhamento com {len(blocos)} palavras, voz com {len(vt)}")
    gravar_json(saida / "palavras.json", [{"texto": t, "inicio": round(blocos[j0][0] * fator, 3),
                                           "fim": round(blocos[j1 - 1][1] * fator, 3)} for t, (j0, j1) in zip(tt, mapa)])
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                str(saida / "voz.wav")], capture_output=True, text=True).stdout)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=black:s=1080x1920:r=30", "-i", str(saida / "voz.wav"),
                    "-af", "apad=pad_dur=0.6", "-t", f"{dur + .6:.3f}", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "256k", str(saida / "base.mp4")], check=True)
    print(f"{len(tt)} palavras, {dur + .6:.2f} s em {saida}")


# ---------- várias vozes: um narrador e uma voz para cada personagem (a Série Animada) ----------
# No texto, uma fala por linha. Linha sem marcação é do narrador; "[nome] fala" é de um personagem, com a voz de
# "vozes": {"nome": {"id": "...", "velocidade": 1.05}} no meu-estilo/marca.json; "[pausa 0.6]" sozinha numa linha
# muda o silêncio depois da fala de cima (o padrão é "voz": {"pausa": 0.3}).
MARCA = re.compile(r"^\[([^\]\s]+)(?:\s+(\d+(?:[.,]\d+)?))?\]\s*(.*)$")


def ler_falas(texto: str) -> list[dict] | None:
    """As falas do texto, ou None se o texto não tem marcação (o uso de sempre, uma voz só)."""
    falas, marcado = [], False
    for linha in texto.splitlines():
        linha = linha.strip()
        if not linha:
            continue
        achado = MARCA.match(linha)
        quem, resto = "narrador", linha
        if achado:
            marcado = True
            nome, numero, resto = achado.groups()
            if _limpa(nome) == "pausa":
                if falas:
                    falas[-1]["pausa"] = float((numero or "0.5").replace(",", "."))
                continue
            quem = _limpa(nome)
        if resto:
            falas.append({"quem": quem, "texto": resto})
    return falas if marcado else None


def _blocos(alinhamento: dict) -> list[list[float]]:
    """O tempo de cada palavra falada, a partir do tempo de cada letra que a ElevenLabs devolve."""
    blocos, cur = [], None
    for c, ini, fim in zip(alinhamento["characters"], alinhamento["character_start_times_seconds"],
                           alinhamento["character_end_times_seconds"]):
        if c.isspace():
            if cur:
                blocos.append(cur)
                cur = None
        elif cur is None:
            cur = [ini, fim]
        else:
            cur[1] = fim
    if cur:
        blocos.append(cur)
    return blocos


def narrar_falas(falas: list[dict], saida: Path, voz_id: str | None = None) -> None:
    """Uma chamada à ElevenLabs por fala, cada uma com a sua voz e a sua velocidade, juntadas com as pausas.
    Fala já gerada com o mesmo texto e a mesma voz é reaproveitada (não gasta crédito de novo)."""
    cfg = config()
    geral = cfg.get("voz", {})
    vozes = {_limpa(k): v for k, v in cfg.get("vozes", {}).items()}
    modelo = geral.get("modelo", "eleven_v4")
    narrador = vozes.get("narrador", {})

    def voz_de(quem: str) -> dict:
        if quem == "narrador":
            v = {"id": voz_id or narrador.get("id") or geral.get("id"),
                 "velocidade": narrador.get("velocidade", geral.get("velocidade", 0.95))}
        else:
            if not vozes.get(quem, {}).get("id"):
                raise SystemExit(f'Falta a voz de "{quem}": "vozes": {{"{quem}": {{"id": "..."}}}} no meu-estilo/marca.json.')
            v = {"id": vozes[quem]["id"], "velocidade": vozes[quem].get("velocidade", geral.get("velocidade", 0.95))}
        if not v["id"]:
            raise SystemExit('Escolha a voz do narrador: "voz": {"id": "..."} no meu-estilo/marca.json, ou --voz ID.')
        v["modelo"] = vozes.get(quem, {}).get("modelo", modelo)
        return v

    pasta = saida / "falas"
    pasta.mkdir(parents=True, exist_ok=True)
    k, preferencias, gastos, reaproveitadas = None, {}, 0, 0
    partes, palavras, lista = [], [], []
    t = geral.get("inicio", 0.4)  # um respiro antes da primeira fala
    for n, f in enumerate(falas):
        v = voz_de(f["quem"])
        tt = f["texto"].split()
        vt, mapa = para_voz(tt)
        fala = " ".join(vt)
        d = pasta / f"{n:02d}"
        d.mkdir(exist_ok=True)
        assinatura = f"{v['id']} {v['modelo']}\n{fala}"
        guardada = d / "assinatura.txt"
        if guardada.exists() and guardada.read_text(encoding="utf-8") == assinatura \
                and (d / "alinhamento.json").exists() and (d / "voz-original.mp3").exists():
            reaproveitadas += 1
        else:
            k = k or chave()
            if v["id"] not in preferencias:
                preferencias[v["id"]] = json.loads(urllib.request.urlopen(urllib.request.Request(
                    f"https://api.elevenlabs.io/v1/voices/{v['id']}/settings", headers={"xi-api-key": k})).read())
                preferencias[v["id"]]["speed"] = 1.0
            corpo = {"text": fala, "model_id": v["modelo"], "voice_settings": preferencias[v["id"]]}
            if cfg.get("idioma"):
                corpo["language_code"] = cfg["idioma"]
            print(f"gerando a fala {n} ({f['quem']}): {fala}")
            req = urllib.request.Request(
                f"https://api.elevenlabs.io/v1/text-to-speech/{v['id']}/with-timestamps?output_format=mp3_44100_128",
                data=json.dumps(corpo).encode(), headers={"xi-api-key": k, "Content-Type": "application/json"})
            resposta = json.loads(urllib.request.urlopen(req).read())
            (d / "voz-original.mp3").write_bytes(base64.b64decode(resposta["audio_base64"]))
            gravar_json(d / "alinhamento.json", resposta["alignment"])
            guardada.write_text(assinatura, encoding="utf-8")
            gastos += len(fala)
        # velocidade final: o ffmpeg muda o ritmo sem mudar o tom; o narrador pode ir mais rápido que os personagens
        vel = v["velocidade"]
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(d / "voz-original.mp3"), "-af", f"atempo={vel}",
                        "-ar", "48000", "-ac", "1", str(d / "voz-final.wav")], check=True)
        blocos = _blocos(json.loads((d / "alinhamento.json").read_text(encoding="utf-8")))
        if len(blocos) != len(vt):
            raise SystemExit(f"Fala {n}: alinhamento com {len(blocos)} palavras, voz com {len(vt)}")
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                    str(d / "voz-final.wav")], capture_output=True, text=True).stdout)
        for txt, (j0, j1) in zip(tt, mapa):
            palavras.append({"texto": txt, "inicio": round(t + blocos[j0][0] / vel, 3),
                             "fim": round(t + blocos[j1 - 1][1] / vel, 3), "quem": f["quem"], "fala": n})
        lista.append({"quem": f["quem"], "texto": f["texto"], "inicio": round(t, 3), "fim": round(t + dur, 3)})
        partes.append((d / "voz-final.wav", t))
        t += dur + f.get("pausa", geral.get("pausa", 0.3))
    # o vídeo acaba 1 s depois da última fala (fim seco: parado no fim, a pessoa sai e o alcance cai)
    total = lista[-1]["fim"] + geral.get("fim", 1.0)
    args = ["ffmpeg", "-v", "error", "-y"]
    for p, _ in partes:
        args += ["-i", str(p)]
    filtro = [f"[{j}]aformat=sample_rates=48000:channel_layouts=mono,adelay={int(ini * 1000)}:all=1[a{j}]"
              for j, (_, ini) in enumerate(partes)]
    filtro.append("".join(f"[a{j}]" for j in range(len(partes)))
                  + f"amix=inputs={len(partes)}:normalize=0,apad=whole_dur={total:.3f},atrim=0:{total:.3f}[o]")
    args += ["-filter_complex", ";".join(filtro), "-map", "[o]", "-ar", "48000", "-ac", "1", str(saida / "voz.wav")]
    subprocess.run(args, check=True)
    gravar_json(saida / "palavras.json", palavras)
    gravar_json(saida / "falas.json", {"duracao": round(total, 3), "falas": lista})
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=black:s=1080x1920:r=30", "-i", str(saida / "voz.wav"),
                    "-t", f"{total:.3f}", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k",
                    str(saida / "base.mp4")], check=True)
    quem = sorted({f["quem"] for f in falas})
    print(f"{len(falas)} falas ({', '.join(quem)}), {len(palavras)} palavras, {total:.2f} s em {saida}")
    print(f"Créditos: {gastos} caracteres gerados agora; {reaproveitadas} falas reaproveitadas sem gastar.")


def gerar_efeito(descricao: str, saida: Path, segundos: float | None = None) -> None:
    """Efeito sonoro gerado na ElevenLabs, para o som de história que o kit não tem (fogo, tosse, porta, multidão).
    A descrição vai em inglês, que a ElevenLabs entende melhor. Gasta créditos: gere uma vez e reaproveite."""
    saida = saida.with_suffix(".wav")
    if saida.exists():
        print(f"{saida} já existe: reaproveite, ou apague para gerar de novo.")
        return
    corpo = {"text": descricao, "prompt_influence": 0.5}
    if segundos:
        corpo["duration_seconds"] = segundos
    req = urllib.request.Request("https://api.elevenlabs.io/v1/sound-generation?output_format=mp3_44100_128",
                                 data=json.dumps(corpo).encode(),
                                 headers={"xi-api-key": chave(), "Content-Type": "application/json"})
    saida.parent.mkdir(parents=True, exist_ok=True)
    mp3 = saida.with_suffix(".mp3")
    mp3.write_bytes(urllib.request.urlopen(req, timeout=180).read())
    # sem o silêncio do começo: a ElevenLabs entrega o som com uns 0,15 a 0,2 s mudos, e ele ficava atrasado no vídeo
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(mp3), "-af", "silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.01",
                    "-ar", "48000", "-ac", "2", str(saida)], check=True)
    mp3.unlink()
    print(f"Efeito em {saida}")
