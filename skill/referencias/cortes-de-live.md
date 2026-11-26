# Cortes de live

Da live inteira da Rafaela (link do YouTube ou o arquivo) aos Reels: você lê a live, propõe os trechos que funcionam sozinhos, **espera a aprovação** e edita só os aprovados, normalmente no [Estilo Cortes e Legenda](../estilos/cortes-e-legenda.md).

Comece quando mandarem uma live ("corta esta live", um link do YouTube, um arquivo grande de vídeo deitado).

## 1. Baixar e ler

```
python .ferramenta/extras/live.py baixar LINK_OU_ARQUIVO --saida .projetos/lives/NOME
```

NOME curto, sem acento: `pilula-6-corpo-fala`. Ele baixa o vídeo (até 1080p) e escreve a fala inteira com o tempo:

- **Com a legenda automática do YouTube** (o normal nas lives dela): uns 2 minutos para 25 minutos de live, sem transcrever nada.
- **Sem legenda** (arquivo, ou vídeo sem legenda): transcreve com o modelo rápido. No processador, de 20 a 40 minutos por hora de live: avise antes.

Saem `fala.md` (a live em blocos de 30 s, com o minuto na margem), `fala.json` (as frases com o tempo) e `quadros.jpg` (um quadro por minuto). **Leia o `fala.md` inteiro** antes de escolher. Olhe o `quadros.jpg` para saber se ela mostra algo (um objeto, um boneco do corpo, um slide), se sai do quadro, e se a live é deitada.

## 2. Escolher os trechos

Um bom trecho:

- **Funciona sozinho:** quem nunca viu a live entende do começo ao fim, sem "como eu disse antes" nem "aquela aluna de ontem".
- **Começa forte:** a primeira frase prende (uma pergunta, uma afirmação que contraria o senso comum, "eu não sou igual a toda a gente"). Pode começar no meio de um raciocínio, se a frase abre bem.
- **Uma ideia só**, de 30 a 90 s depois dos cortes (o bruto pode ter um pouco mais: os cortes tiram uns 10 a 15%).
- **Fecha:** termina numa conclusão, não no meio do pensamento.
- **É o assunto dela:** um sintoma explicado, uma metáfora ("o alarme de incêndio e o fogo"), uma pergunta para fazer a si mesmo, uma história curta dela, uma resposta a uma dúvida comum.

**Fica de fora:**

- Conversa com o chat ("escrevam aqui sim", "olá, Maria"), boas-vindas, "papel e caneta na mão".
- A venda da live: preço, "domingo às 21h", "só hoje", o nome do evento. Datas e ofertas passam; o Reel fica.
- Nome de paciente, aluno ou familiar e detalhe que identifique alguém.
- **O que pode ser lido como conselho médico:** deixar ou adiar medicação, não ir ao médico. Mesmo que na live o contexto esteja certo, cortado ele pode virar outra coisa. Se o trecho for muito bom, proponha com o aviso.
- Promessa de cura ou número que só vale no contexto da live.

Para cada trecho, ache o segundo exato no `fala.json`: o começo da primeira frase e o fim da última, com uns 0,5 s de folga.

## 3. Mandar para aprovar

**Não edite nada antes da aprovação.** Mande a lista numa mensagem só, com o link do YouTube já no segundo do trecho, para quem aprova abrir e ouvir:

> **1. "Ansiedade é o alarme, não o fogo"** (9:12 a 10:46, uns 80 s editado)\
> [Ouvir na live](https://www.youtube.com/watch?v=ID&t=552s)\
> Começa: "Eu não sou igual a toda a gente. Então, porque é que se trata toda a gente de forma igual?"\
> Por que funciona: a metáfora do alarme explica a raiz em 10 segundos.\
> Corto: a repetição do "não vos consigo dar essa resposta" e o "apontem no caderno".

Ordene do mais forte para o mais fraco. No fim, diga em uma linha o que ficou de fora e por quê (a venda, o chat, o trecho sobre medicação). Guarde a mesma lista em `.projetos/lives/NOME/trechos.md`.

Quem aprova responde com os números ("1, 3 e 5"), pode mudar o começo ou o fim ("o 2 começa em 'tonturas'") e pode pedir outro estilo. Anote a resposta no `trechos.md`.

## 4. Editar os aprovados

Para cada trecho aprovado, um projeto em `.projetos/NOME-DO-TRECHO/`, seguindo "Cada vídeo" do [EDITAR.md](../EDITAR.md), com estas diferenças:

1. **O bruto sai da live:**

   ```
   python .ferramenta/extras/live.py trecho .projetos/lives/NOME DE ATE --saida brutos/NOME-DO-TRECHO.mp4
   ```

   Numa live deitada, ele recorta a janela em pé que **segue o rosto** dela (ela se mexe bastante para os lados). Diz em quantos quadros achou o rosto: abaixo de uns 80%, olhe os quadros do bruto antes de seguir; se ela fica parada num lugar, `--x 0.5` deixa o recorte parado. Uns 45 s para 90 s de trecho.

2. **Tirar o que não serve é pelas tentativas, não pela transcrição.** Apagar uma palavra no `trocas.json` tira só o texto: a fala continua no vídeo. Para tirar uma repetição, o "eh"/"ah" longo, a conversa com o chat ou uma frase do meio, faça o `escolhas.json` com os pedaços que ficam (`tentativas conferir` e `tentativas cortar`), como numa gravação com tentativas. Depois `transcrever` e `cortar` normais.

3. **As pausas da live não ficam em silêncio:** o som da transmissão deixa o fundo em uns -50 dB, e o `cortar` só tira silêncio de verdade. Pausa curta (até uns 0,7 s) fica, e soa natural. Pausa longa ou "ah" no meio: tire no `escolhas.json`. Para achar, procure no `palavras.json` do corte os vãos acima de 0,6 s.

4. **A legenda segue a fala dela** em português de Portugal. A legenda do YouTube serve para escolher, não para legendar: a do vídeo sai do `transcrever`, que é melhor, e ainda assim confira (a transcrição troca a ordem de palavras e põe "Rafael" no lugar de "Rafaela").

5. Monte no estilo, olhe os quadros (o rosto inteiro em todos, a legenda abaixo do queixo), renderize e finalize. Mostre todos os aprovados juntos, com o nome de cada versão em `versoes/`.

## O que esperar

Teste de 2026-11-26, na live "Pílula 6 · O corpo fala" (25 min), no PC do Vitório: baixar e ler, 1,5 min; o trecho com o rosto seguido, 45 s; transcrever, cortar e montar, uns 2 min; render, 2 min para 70 s. No notebook dela, sem placa de vídeo, conte umas 3 a 4 vezes mais em cada passo.
