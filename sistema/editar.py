"""Editor de vídeo com IA: todos os comandos, numa porta só.

Todos os comandos rodam de dentro da pasta do editor (a que tem a .ferramenta/), e os caminhos são relativos a ela.

  python .ferramenta/sistema/editar.py verificar
      Confere a instalação e diz o que falta.
  python .ferramenta/sistema/editar.py comecar
      Cria as pastas (brutos, versoes, editados, meu-estilo, roteiros e .projetos), as portas de entrada e, se a
      pasta estiver num repositório Git, o .gitignore do backup. Não mexe no que existe.
  python sistema/editar.py comecar --migrar
      Leva a instalação antiga (os arquivos da pessoa dentro do clone) para o formato novo, sem perder nada.
  python .ferramenta/sistema/editar.py atualizar
      Baixa a versão nova da ferramenta (git pull). Os arquivos da pessoa não mudam.
  python .ferramenta/sistema/editar.py catalogo
      Abre o catálogo dos estilos no navegador.

As pastas: o bruto vem de brutos/, o trabalho de cada vídeo fica em .projetos/NOME/, cada versão para assistir
vai para versoes/NOME-vN.mp4 e a aprovada, para editados/NOME.mp4. O roteiro aprovado fica em roteiros/NOME.md.

Gravação com várias tentativas (repetições, frases pela metade):
  python .ferramenta/sistema/editar.py tentativas listar BRUTO --saida PASTA [--vocabulario "..."]
  python .ferramenta/sistema/editar.py tentativas detalhar PASTA 56.1 62.5 [mais pares início fim]
  python .ferramenta/sistema/editar.py tentativas conferir PASTA/escolhas.json
  python .ferramenta/sistema/editar.py tentativas cortar PASTA/escolhas.json --saida base_longa.mp4

Do vídeo ao projeto:
  python .ferramenta/sistema/editar.py transcrever VIDEO --saida PASTA [--vocabulario "Claude Code, skill"]
  python .ferramenta/sistema/editar.py cortar VIDEO PASTA/palavras.json --saida PASTA/corte [--manter-ate 0.4] [--trocas trocas.json]
  python .ferramenta/sistema/editar.py voz TEXTO.txt --saida PASTA                    (vídeo só com voz de IA, opcional; [nome] na linha = voz do personagem)
  python .ferramenta/sistema/editar.py falas-gravadas TEXTO.txt AUDIO [AUDIO ...] --saida PASTA   (as falas gravadas pela pessoa, no lugar da voz de IA,
                                                                          com personagens: um áudio só, um por personagem ou um por fala)
  python .ferramenta/sistema/editar.py efeito "descrição em inglês" --saida PASTA/sons/nome.wav [--segundos 4]   (som de história gerado na ElevenLabs)
  python .ferramenta/sistema/editar.py recortar PASTA/corte/base.mp4 --saida PASTA/recorte.webm
  python .ferramenta/sistema/editar.py palavras PALAVRAS.json [DE ATE]                (cada palavra com o tempo e a referência @palavra#n)
  python .ferramenta/sistema/editar.py retempo VIDEO PALAVRAS.json DE ATE [--so-mostrar]   (acerta pelo som o tempo de número, ano e valor)
  python .ferramenta/sistema/editar.py falas PALAVRAS.json                           (cada fala com o número, o tempo e quem fala)
  python .ferramenta/sistema/editar.py picos SOM.wav [--limite -30]                  (quando cada latido, batida ou tosse começa no arquivo)
  python .ferramenta/sistema/editar.py montar BASE.mp4 PALAVRAS.json ROTEIRO.json --saida PROJETO [--sem-efeitos]

Estilo novo a partir de um vídeo de referência (engenharia reversa):
  python .ferramenta/sistema/editar.py referencia analisar LINK_OU_ARQUIVO --saida .projetos/referencias/NOME
  python .ferramenta/sistema/editar.py referencia quadros PASTA 12.5 20.2              (quadros em tamanho cheio)
  python .ferramenta/sistema/editar.py referencia comparar PASTA VIDEO_EDITADO.mp4 --saida PASTA/comparacao

Conferir e entregar:
  python .ferramenta/sistema/editar.py renderizar .projetos/NOME/montagem [--saida .projetos/NOME/render.mp4] [--rascunho]
  python .ferramenta/sistema/editar.py escutar SEM_EFEITOS.mp4 COM_EFEITOS.mp4 PROJETO/deixas.json
  python .ferramenta/sistema/editar.py parede PROJETO recorte.webm                    (texto atrás da pessoa está visível?)
  python .ferramenta/sistema/editar.py parede-livre recorte.webm DE ATE               (onde a parede fica livre)
  python .ferramenta/sistema/editar.py titulos PROJETO VIDEO [--recorte recorte.webm]   (títulos no alto: cabeça, área e tamanho)
  python .ferramenta/sistema/editar.py finalizar .projetos/NOME/render.mp4            (volume das redes e conferência; sai em versoes/NOME-vN.mp4)
  python .ferramenta/sistema/editar.py aprovar versoes/NOME-vN.mp4             (a versão aprovada vai para editados/NOME.mp4)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="acao", required=True)
    sub.add_parser("verificar")
    x = sub.add_parser("comecar")
    x.add_argument("--migrar", action="store_true", help="leva a instalação antiga para o formato novo, sem perder nada")
    sub.add_parser("atualizar")
    sub.add_parser("catalogo")
    x = sub.add_parser("aprovar")
    x.add_argument("versao", type=Path)
    x = sub.add_parser("falas-gravadas")
    x.add_argument("texto", type=Path)
    x.add_argument("audios", type=Path, nargs="+")
    x.add_argument("--saida", type=Path, required=True)
    x.add_argument("--vocabulario", default="")

    t = sub.add_parser("tentativas")
    ts = t.add_subparsers(dest="passo", required=True)
    x = ts.add_parser("listar")
    x.add_argument("bruto", type=Path)
    x.add_argument("--saida", type=Path, required=True)
    x.add_argument("--vocabulario", default="")
    x = ts.add_parser("detalhar")
    x.add_argument("pasta", type=Path)
    x.add_argument("tempos", type=float, nargs="+")
    x = ts.add_parser("conferir")
    x.add_argument("escolhas", type=Path)
    x = ts.add_parser("cortar")
    x.add_argument("escolhas", type=Path)
    x.add_argument("--saida", type=Path, required=True)

    x = sub.add_parser("transcrever")
    x.add_argument("video", type=Path)
    x.add_argument("--saida", type=Path, required=True)
    x.add_argument("--vocabulario", default="")

    x = sub.add_parser("cortar")
    x.add_argument("video", type=Path)
    x.add_argument("palavras", type=Path)
    x.add_argument("--saida", type=Path, required=True)
    x.add_argument("--respiro", type=float, default=0.16, help="silêncio acima disso (s) é cortado")
    x.add_argument("--cauda", type=float, default=0.12, help="quanto da queda da voz (s) fica antes do corte")
    x.add_argument("--pausa", type=float, default=0.22, help="teto (s) do silêncio entre frases")
    x.add_argument("--manter-ate", type=float, default=0.0, help="segundos iniciais sem corte (gesto antes da fala)")
    x.add_argument("--manter", help="trechos sem fala que não são cortados, em segundos: a-b,c-d")
    x.add_argument("--trocas", type=Path, help='JSON {"número da palavra": "texto certo"}')
    x.add_argument("--sem-tratamento", action="store_true", help="não aplica o tratamento de cor e voz")

    x = sub.add_parser("voz")
    x.add_argument("texto", type=Path)
    x.add_argument("--saida", type=Path, required=True)
    x.add_argument("--voz", help="id da voz na ElevenLabs (o padrão vem do meu-estilo/marca.json)")

    x = sub.add_parser("efeito")
    x.add_argument("descricao")
    x.add_argument("--saida", type=Path, required=True)
    x.add_argument("--segundos", type=float)

    x = sub.add_parser("recortar")
    x.add_argument("video", type=Path)
    x.add_argument("--saida", type=Path, required=True)

    x = sub.add_parser("falas")
    x.add_argument("palavras", type=Path)

    x = sub.add_parser("picos")
    x.add_argument("som", type=Path)
    x.add_argument("--limite", type=float, default=-30.0)

    x = sub.add_parser("palavras")
    x.add_argument("palavras", type=Path)
    x.add_argument("de", type=float, nargs="?", default=0.0)
    x.add_argument("ate", type=float, nargs="?", default=1e9)

    x = sub.add_parser("retempo")
    x.add_argument("video", type=Path)
    x.add_argument("palavras", type=Path)
    x.add_argument("de", type=float)
    x.add_argument("ate", type=float)
    x.add_argument("--so-mostrar", action="store_true", help="mostra sem gravar no palavras.json")

    x = sub.add_parser("titulos")
    x.add_argument("projeto", type=Path)
    x.add_argument("video", type=Path, help="o corte (.projetos/NOME/corte/base.mp4)")
    x.add_argument("--recorte", type=Path, help="o recorte.webm, se já existir (senão faz um rápido)")
    x.add_argument("--margem", type=float, default=150, help="distância mínima das laterais, em px")

    x = sub.add_parser("montar")
    x.add_argument("base", type=Path)
    x.add_argument("palavras", type=Path)
    x.add_argument("roteiro", type=Path)
    x.add_argument("--saida", type=Path, required=True)
    x.add_argument("--sem-efeitos", action="store_true", help="para o render de comparação da escuta")

    r = sub.add_parser("referencia")
    rs = r.add_subparsers(dest="passo", required=True)
    x = rs.add_parser("analisar")
    x.add_argument("fonte")
    x.add_argument("--saida", type=Path, required=True)
    x = rs.add_parser("quadros")
    x.add_argument("pasta", type=Path)
    x.add_argument("tempos", type=float, nargs="+")
    x = rs.add_parser("comparar")
    x.add_argument("pasta", type=Path)
    x.add_argument("editado", type=Path)
    x.add_argument("--saida", type=Path, required=True)

    x = sub.add_parser("renderizar")
    x.add_argument("projeto", type=Path)
    x.add_argument("--saida", type=Path, help="padrão: render.mp4 ao lado da montagem, em .projetos/NOME/")
    x.add_argument("--rascunho", action="store_true", help="mais rápido, qualidade menor")

    x = sub.add_parser("escutar")
    x.add_argument("sem", type=Path)
    x.add_argument("com", type=Path)
    x.add_argument("deixas", type=Path)

    x = sub.add_parser("parede")
    x.add_argument("projeto", type=Path)
    x.add_argument("recorte", type=Path)
    x.add_argument("--limite", type=float, default=0.12)

    x = sub.add_parser("parede-livre")
    x.add_argument("recorte", type=Path)
    x.add_argument("de", type=float)
    x.add_argument("ate", type=float)

    x = sub.add_parser("finalizar")
    x.add_argument("video", type=Path)
    x.add_argument("--saida", type=Path, help="padrão: versoes/NOME-vN.mp4, a próxima versão")

    a = ap.parse_args()
    if a.acao == "verificar":
        from motor.verificar import verificar
        verificar()
    elif a.acao == "comecar":
        from motor.pastas import comecar
        comecar(a.migrar)
    elif a.acao == "atualizar":
        from motor.pastas import atualizar
        atualizar()
    elif a.acao == "catalogo":
        from motor.pastas import abrir_catalogo
        abrir_catalogo()
    elif a.acao == "aprovar":
        from motor.pastas import aprovar
        aprovar(a.versao.resolve())
    elif a.acao == "falas-gravadas":
        from motor.gravadas import falas_gravadas
        falas_gravadas(a.texto.resolve(), [x.resolve() for x in a.audios], a.saida.resolve(), a.vocabulario)
    elif a.acao == "tentativas":
        from motor import tentativas
        if a.passo == "listar":
            tentativas.listar(a.bruto.resolve(), a.saida.resolve(), a.vocabulario)
        elif a.passo == "detalhar":
            tentativas.detalhar(a.pasta.resolve(), a.tempos)
        elif a.passo == "conferir":
            tentativas.conferir(a.escolhas.resolve())
        else:
            tentativas.cortar(a.escolhas.resolve(), a.saida.resolve())
    elif a.acao == "transcrever":
        from motor.transcricao import transcrever
        transcrever(a.video.resolve(), a.saida.resolve(), a.vocabulario)
    elif a.acao == "cortar":
        from motor.corte import cortar
        cortar(a.video.resolve(), a.palavras.resolve(), a.saida.resolve(), a.respiro, a.trocas, a.manter_ate,
               a.cauda, a.pausa, a.manter, a.sem_tratamento)
    elif a.acao == "voz":
        from motor.voz import narrar
        narrar(a.texto.resolve(), a.saida.resolve(), a.voz)
    elif a.acao == "efeito":
        from motor.voz import gerar_efeito
        gerar_efeito(a.descricao, a.saida.resolve(), a.segundos)
    elif a.acao == "recortar":
        from motor.recorte import recortar
        recortar(a.video.resolve(), a.saida.resolve())
    elif a.acao == "falas":
        from motor.montagem import listar_falas
        listar_falas(a.palavras.resolve())
    elif a.acao == "picos":
        from motor.montagem import picos
        picos(a.som.resolve(), a.limite)
    elif a.acao == "palavras":
        from motor.montagem import listar_palavras
        listar_palavras(a.palavras.resolve(), a.de, a.ate)
    elif a.acao == "retempo":
        from motor.retempo import retempo
        retempo(a.video.resolve(), a.palavras.resolve(), a.de, a.ate, not a.so_mostrar)
    elif a.acao == "titulos":
        from motor.titulos import conferir_titulos
        conferir_titulos(a.projeto.resolve(), a.video.resolve(), a.recorte.resolve() if a.recorte else None, margem=a.margem)
    elif a.acao == "montar":
        from motor.montagem import montar
        montar(a.base.resolve(), a.palavras.resolve(), a.roteiro.resolve(), a.saida.resolve(), a.sem_efeitos)
    elif a.acao == "referencia":
        from motor import referencia
        if a.passo == "analisar":
            referencia.analisar(a.fonte, a.saida.resolve())
        elif a.passo == "quadros":
            referencia.quadros_cheios(a.pasta.resolve(), a.tempos)
        else:
            referencia.comparar(a.pasta.resolve(), a.editado.resolve(), a.saida.resolve())
    elif a.acao == "renderizar":
        from motor.entrega import renderizar
        projeto = a.projeto.resolve()
        renderizar(projeto, (a.saida or projeto.parent / "render.mp4").resolve(), a.rascunho)
    elif a.acao == "escutar":
        from motor.escuta import conferir
        conferir(a.sem.resolve(), a.com.resolve(), a.deixas.resolve())
    elif a.acao == "parede":
        from motor.recorte import conferir_parede
        conferir_parede(a.projeto.resolve(), a.recorte.resolve(), a.limite)
    elif a.acao == "parede-livre":
        from motor.recorte import parede_livre
        parede_livre(a.recorte.resolve(), a.de, a.ate)
    else:
        from motor.comum import nome_do_video, proxima_versao
        from motor.entrega import finalizar
        video = a.video.resolve()
        finalizar(video, (a.saida or proxima_versao(nome_do_video(video))).resolve())


if __name__ == "__main__":
    main()
