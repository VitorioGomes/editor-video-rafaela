# Cortes de live

Da live inteira da Rafaela (link do YouTube ou o arquivo) aos Reels: você lê a live, escolhe os trechos que funcionam sozinhos, **edita todos** no [Estilo Cortes e Legenda](../estilos/cortes-e-legenda.md) (ou no estilo pedido) e entrega os vídeos prontos. Quem opera assiste e aprova ou recusa cada um. É assim que vão pedir (Vitório, 2026-11-26): não mande uma lista de trechos para aprovar antes de editar.

Comece quando mandarem uma live ("corta esta live", um link do YouTube, um arquivo grande de vídeo deitado).

## 1. Baixar e ler

```
python .ferramenta/extras/live.py baixar LINK_OU_ARQUIVO --saida .projetos/lives/NOME
```

NOME curto, sem acento: `pilula-6-corpo-fala`. Ele baixa o vídeo (até 1080p) e escreve a fala inteira com o tempo:

- **Com a legenda automática do YouTube** (o normal nas lives dela): uns 2 minutos para 25 minutos de live, sem transcrever nada.
- **Sem legenda** (um arquivo, um vídeo sem legenda automática, ou o YouTube recusou baixar a legenda): o `baixar` transcreve sozinho no computador, com o modelo rápido. Nunca pare por falta de legenda. No processador, de 20 a 40 minutos por hora de live: avise antes. Com placa de vídeo, uns 2 minutos para 25 minutos de live.

Saem `fala.md` (a live em blocos de 30 s, com o minuto na margem), `fala.json` (as frases com o tempo) e `quadros.jpg` (um quadro por minuto). **Leia o `fala.md` inteiro** antes de escolher. Olhe o `quadros.jpg` para saber se ela mostra algo (um objeto, um boneco do corpo, um slide), se sai do quadro, e se a live é deitada.

## 2. Escolher os trechos

**Antes, leia os `trechos.md` das lives anteriores** (`.projetos/lives/*/trechos.md`): o que foi aprovado e recusado, e por quê. A escolha melhora com isso.

Um bom trecho:

- **Funciona sozinho:** quem nunca viu a live entende do começo ao fim, sem "como eu disse antes" nem "aquela aluna de ontem".
- **Começa forte:** a primeira frase prende (uma pergunta, uma afirmação que contraria o senso comum, "eu não sou igual a toda a gente"). Pode começar no meio de um raciocínio, se a frase abre bem.
- **Uma ideia só**, de 30 a 90 s depois dos cortes (o bruto pode ter um pouco mais: os cortes tiram de 15 a 30% numa live).
- **Fecha:** termina numa conclusão, não no meio do pensamento.
- **É o assunto dela:** um sintoma explicado, uma metáfora ("o alarme de incêndio e o fogo"), uma pergunta para fazer a si mesmo, uma história curta dela, uma resposta a uma dúvida comum.

**Fica de fora:**

- Conversa com o chat ("escrevam aqui sim", "olá, Maria"), boas-vindas, "papel e caneta na mão".
- A venda da live: preço, "domingo às 21h", "só hoje", o nome do evento. Datas e ofertas passam; o Reel fica.
- Nome de paciente, aluno ou familiar e detalhe que identifique alguém.
- **O que pode ser lido como conselho médico:** deixar ou adiar medicação, não ir ao médico. Mesmo que na live o contexto esteja certo, cortado ele pode virar outra coisa.
- Promessa de cura ou número que só vale no contexto da live.

Para cada trecho, ache o segundo exato no `fala.json`: o começo da primeira frase e o fim da última, com uns 0,5 s de folga. Guarde a lista em `.projetos/lives/NOME/trechos.md`, do mais forte para o mais fraco, com o tempo na live e o que vai ser cortado. Live longa, com mais de uns 10 trechos bons: diga quantos são e quanto tempo leva editar todos antes de começar.

## 3. Editar todos

Para cada trecho, um projeto em `.projetos/NOME-DO-TRECHO/`, seguindo "Cada vídeo" do [EDITAR.md](../EDITAR.md), com estas diferenças:

1. **O bruto sai da live:**

   ```
   python .ferramenta/extras/live.py trecho .projetos/lives/NOME DE ATE --saida brutos/NOME-DO-TRECHO.mp4
   ```

   Numa live deitada, ele recorta a janela em pé **parada no meio** (`--x` muda a posição, se ela estiver toda de um lado). Ela se mexe para os lados e às vezes sai um pouco do quadro: tudo bem. `--seguir` faz a janela seguir o rosto, mas no teste o Vitório achou tremido e estranho (2026-11-26): use só se pedirem.

2. **Tirar o que não serve é pelas tentativas, não pela transcrição.** Apagar uma palavra no `trocas.json` tira só o texto: a fala continua no vídeo. Transcreva o bruto, escolha as palavras que ficam e faça o `escolhas.json` com os pedaços: corte as repetições, o "eh"/"ah", a conversa com o chat, uma frase do meio que não serve, e as hesitações longas (vão de mais de uns 0,9 s entre duas palavras). Depois `tentativas cortar`, `transcrever` e `cortar` normais.

3. **As pausas da live não ficam em silêncio:** o som da transmissão deixa o fundo em uns -50 dB, e o `cortar` só tira silêncio de verdade. Por isso as hesitações saem no `escolhas.json` (item 2). Pausa curta, até uns 0,7 s, fica e soa natural.

4. **A legenda segue a fala dela** em português de Portugal. A legenda do YouTube serve para escolher, não para legendar: a do vídeo sai do `transcrever`, que é melhor, e ainda assim confira. Erros que já apareceram: ordem de palavras trocada ("não faço onde ideia"), "Rafael" no lugar de "Rafaela", "quem não era" no lugar de "quem me dera", palavra duplicada com o mesmo tempo, e uma palavra inventada no fim do áudio ("Obrigada", "Tchau", "Música"), que sai. A transcrição também separa o pronome com hífen ("proteger -nos", "levanta -se"): junte na palavra de antes no `trocas.json` (`{"16": "proteger-nos", "17": ""}`), ou a legenda sai partida.

5. Monte no estilo, olhe os quadros (a legenda abaixo do queixo), renderize e finalize.

**Corte de live num estilo com título (Yap, Títulos Desenhados)** (Vitório, 2026-11-26): na live, a cabeça fica quase no topo e não sobra lugar para o título. Depois do `cortar`, abra espaço em cima. (O Metade não usa isso: o bruto sai com `trecho --metade`, ver [metade.md](../estilos/metade.md).)

```
python .ferramenta/extras/live.py abrir-topo .projetos/NOME-DO-TRECHO/corte/base.mp4 .projetos/NOME-DO-TRECHO/corte/base-topo.mp4
```

O vídeo dela desce 380 px na largura toda (sai um pouco do peito embaixo), e o espaço de cima é a faixa de parede do alto do quadro, esticada e desfocada, com a emenda suave: parece a parede continuando. Com o quadro inteiro desfocado no topo, a cabeça dela aparecia como uma mancha escura (Vitório, 2026-11-26): por isso só a faixa de cima. Monte com o `base-topo.mp4` no lugar do `base.mp4` (o `palavras.json` é o mesmo). Encolher o vídeo com faixas dos lados foi testado e ficou um quadro dentro do quadro: não use.

- **O topo é a parede clara dela:** título e legenda escuros, nas cores da marca (`#1E293B` e o azul escurecido `#2F6478`), com um halo claro nas letras e um véu claro suave atrás do bloco (`.topo::before` com um degradê radial). Sem o véu, a letra que passa por uma parte escura do fundo reprova no contraste do render.
- **A legenda do Yap fica logo abaixo do título** (por volta de y 495), e não ao lado do rosto: o rosto ocupa a largura. Some na palavra gigante (`"esconde_legenda": true`).
- **Efeitos baixos** (`"efeitos": {"ganho": -6}`): o tom dela é calmo. O roteiro completo do teste está no guia do [Yap](../estilos/yap.md).

## 4. Entregar para aprovar

Mande todos de uma vez, do mais forte para o mais fraco, cada um com o nome em `versoes/`, uma linha do que ele fala e o tempo na live (com o link do YouTube no segundo, quando a live vem do YouTube). No fim, uma linha com o que ficou de fora e por quê (a venda, o chat, o trecho sobre medicação).

Quem aprova assiste e responde ("aprovo 1, 3 e 5"), pode pedir ajuste ("o 2 começa em 'tonturas'") ou outro estilo. O aprovado vai para `editados/` (`aprovar`); o recusado fica em `versoes/` até pedirem para apagar. **Anote no `trechos.md` o que foi aprovado e recusado, com o motivo quando disserem.**

## O que esperar

Teste de 2026-11-26, na live "Pílula 6 · O corpo fala" (25 min), no PC do Vitório, com placa de vídeo: baixar e ler, 1,5 min (sem a legenda do YouTube, 1m48 transcrevendo); cada trecho, uns 5 min do bruto ao vídeo pronto. No notebook dela, sem placa de vídeo, conte umas 3 a 4 vezes mais em cada passo.
