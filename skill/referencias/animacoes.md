# Como criar as animações

As animações de cada vídeo são criadas por você, para aquele vídeo. Não existe biblioteca pronta para reaproveitar: a fala de cada vídeo pede uma cena diferente, e animação repetida deixa todos os vídeos iguais. A pasta [animacoes/](animacoes/) tem exemplos de como uma animação bem feita fica. Leia alguns antes de criar a primeira, para pegar o nível de acabamento e o formato, mas **não copie**.

Quando a pessoa gostar muito de uma animação e quiser usar de novo (o fundo do estilo, a caixa de comentário do pedido final), guarde em `meu-estilo/animacoes/`.

## O formato de um arquivo

Um `.html` na pasta do projeto (ao lado do `roteiro.json`), com três partes: um `<style>`, a marcação e um `<script>`.

```html
<!-- O que a animação mostra. $R0 a palavra. M: [entra, gira]. -->
<style>
.xx-caixa { position: relative; width: 600px; height: 400px; }
.xx-palavra { font-family: var(--f-serifa), serif; font-size: 170px; color: var(--c-destaque); opacity: 0; }
</style>
<div class="xx-caixa">
  <div class="xx-palavra" id="$IDp">$R0</div>
</div>
<script>
  const a = t0 + M[0], b = t0 + M[1];
  tl.fromTo("#$IDp", { opacity: 0, scale: 1.2 }, { opacity: 1, scale: 1, duration: .18, ease: "power3.out" }, a);
  // flutuação até o fim da camada: repetição contada, nunca infinita (repeat: -1 quebra o render)
  tl.to("#$IDp", { rotation: -2, duration: 1.4, yoyo: true, repeat: Math.max(0, Math.floor((t0 + D - b) / 1.4) - 1), ease: "sine.inOut" }, b);
</script>
```

- **`$ID`** vira o id da camada. Use em todo id e seletor, para duas animações no mesmo vídeo não se misturarem.
- **`$R0` a `$R9`** recebem os textos de `"rotulos"` no `roteiro.json`.
- **No script:** `tl` é a linha do tempo (GSAP), `t0` é o segundo em que a camada entra, `D` é quanto ela dura, e `M` é a lista dos tempos de `"marcas"`, contados do início da camada. Para a animação andar com a fala, ponha as palavras em `"marcas"` (`["@cliente", "@pronto"]`) e use `t0 + M[0]`, `t0 + M[1]`.
- **`<!--#inclui arquivo.css-->`** traz um pedaço comum: o de CSS vai **dentro** do `<style>`, e o de JS, dentro do `<script>`. Cada CSS incluído entra uma vez só no vídeo, para todas as animações (todas dividem o mesmo estilo): prefixo próprio nas classes evita uma pisar na outra. Procura ao lado da animação, em `meu-estilo/animacoes/` e nas bases dos estilos desta pasta de exemplos: `mo-base.css` e `mo-base.js` (Motion) e `mm-base.css` (Metade) se incluem direto, sem copiar. O fundo do Motion (`mo-fundo.html`) e o painel do Metade (`mm-palco.html`) também podem ser usados direto no `roteiro.json`, pelo nome.
- **Prefixo próprio nas classes** (`xx-`), para o CSS de uma animação não pegar em outra.
- **Cores e fontes da marca** estão em variáveis: `var(--c-texto)`, `var(--c-destaque)`, `var(--c-alerta)`, `var(--c-acento)`, `var(--c-parede)`, `var(--c-motion)` e `var(--c-motion-fim)` (as do Motion), `var(--c-metade)` (a do Metade), `var(--f-serifa)`, `var(--f-mao)`, `var(--f-forte)`, `var(--f-lista)`, `var(--f-mono)`. Use as variáveis em vez de escrever a cor, para a animação seguir a marca da pessoa. Para um tom transparente da cor, `color-mix(in srgb, var(--c-motion) 20%, transparent)`.
- **`fromTo` mais de uma vez no mesmo elemento:** a partir do segundo, ponha `immediateRender: false`, ou o estado inicial aparece antes da hora.
- **Nada infinito:** `repeat: -1` e animação em CSS quebram o render. Tudo no `tl`, com repetição contada até o fim da camada.

No `roteiro.json`, a camada é `{"tipo": "bloco", "arquivo": "minha-cena.html", ...}` (ver [camadas.md](camadas.md)).

## Princípios de movimento

Valem para todo estilo. Vêm dos 12 princípios da animação da Disney e dos princípios de movimento para interface (Issara Willenskomer, UX in Motion). Para cartão, tela e texto, que é quase tudo o que animamos, os que mais pesam são os de tempo, ordem e atenção.

**Os 12 da Disney, com o exemplo clássico de cada um e o que vira aqui:**

| Princípio | O exemplo | Na animação do vídeo |
|---|---|---|
| Comprimir e esticar | O quadrado que cai achata ao bater no chão e estica ao subir | Selo, etiqueta, ícone e botão que batem na tela achatam um instante e voltam (`impacto()`). Passa peso. Texto miúdo nunca deforma |
| Antecipação | A bola se agacha antes de pular | Antes de um movimento grande, um recuo curto no sentido contrário (`vai()`, `back.in` na saída, o cursor recuando antes do clique) |
| Encenação | Textos espalhados e girando ao mesmo tempo contra uma mensagem por vez, no lugar certo | **Uma coisa importante por vez.** Peça fixa o vídeo inteiro (um terminal, um painel com texto) divide a atenção. O que ainda não é a vez fica apagado |
| Ação direta e pose a pose | A chama desenhada quadro a quadro contra a bola com poses-chave | O GSAP trabalha pose a pose. Quadro a quadro só para o orgânico: fumaça, fogo, traço à mão |
| Continuidade e sobreposição | O carro freia e a antena continua indo e volta balançando | Num conjunto, cada parte chega um pouco depois (`conjunto()`): a janela, depois a barra, depois os itens. O que para assenta com um balanço curto |
| Aceleração e desaceleração | O carro que sai devagar e chega devagar parece real; o linear parece robô | Sempre com curva. Linear só no que é mecânico de verdade (fundo andando, contador de tempo). Entrada desacelera (`out`), saída acelera (`in`) |
| Arcos | O rosto que vira em arco, abaixando a cabeça no meio do giro | O que se desloca vai em curva: o cursor, a forma que muda de lugar, o objeto que voa. Basta x e y com curvas diferentes |
| Ação secundária | A sobrancelha acompanhando o giro da cabeça | Um movimento pequeno que apoia o principal: a sombra, o brilho, o cadeado que treme, o fundo andando. Nunca disputa com o principal |
| Temporização | A mesma bola, lenta, parece pesada; rápida, parece leve | O tempo diz tamanho e peso. **Tempos iguais em tudo deixam o vídeo mecânico** (tabela abaixo) |
| Exagero | O carro que arranca soltando fumaça e freia afundando | Na frase forte, o movimento vai um pouco além: o número bate maior, o selo gira mais. Só onde pede |
| Desenho volumétrico | O cubo que gira com a sombra mudando junto | Luz e sombra de um lado só, iguais em todos os elementos da cena |
| Apelo | O mesmo personagem sem graça e com olhos expressivos | Acabamento: cantos coerentes, ícones bem desenhados, nada feio. Elemento feio ninguém olha, mesmo bem animado |

Em vídeo com personagem (desenho, mascote, série animada), os de personagem pesam tanto quanto os outros: comprimir e esticar, antecipação, arcos, ação secundária e apelo fazem o personagem parecer vivo.

**O que a interface acrescenta:**

- **Atraso entre as partes:** o que entra com um pequeno atraso é lido como coisas separadas, na ordem; tudo junto vira um bloco só.
- **Transformação:** um elemento vira outro sem sumir (`vira()`). A pílula vira janela, a janela vira cartão, o cartão vira o selo do título.
- **Clonagem:** o novo nasce do que já está na tela, em vez de aparecer do nada: o quadradinho que se multiplica, o cartão que sai de trás do outro.
- **Máscara:** revelar parte de um elemento; o número que rola dentro de uma janela (`troca()`).
- **Mudança de valor:** número que conta mostra que tem algo vivo por trás (`conta()`).
- **Obscurecimento:** o que saiu do foco fica apagado, mostrando que existe sem roubar a atenção.
- **Paralaxe e zoom:** camadas em velocidades diferentes dão profundidade; aproximar a câmera de um elemento é "entrar" nele.

O fade simples não conta história. Transformação, clonagem e máscara contam.

**As cenas se emendam.** A cena não sobe e some para a próxima começar do zero: ela termina com um elemento parado (`sai(id, fica)`), e a seguinte começa com esse elemento no mesmo lugar e o transforma. Sem corte, a forma só muda de papel. Varie a emenda ao longo do vídeo (transformação, clonagem, deslocamento em arco, número que rola), para não repetir a mesma.

**Tempos de partida** (convenção para vídeo; ajuste pelo olho de quem vai postar):

| Movimento | Tempo | Curva no GSAP |
|---|---|---|
| Detalhe entrando (palavra, ícone, ponto) | 0,15 a 0,25 s | `power3.out` ou `back.out(1.4 a 1.8)` |
| Elemento médio (cartão, pílula, etiqueta) | 0,3 a 0,4 s | `power3.out`; `back.out` se for de impacto |
| Elemento grande ou troca de cena (janela, painel, transformação) | 0,45 a 0,7 s | `power3.inOut` ou `expo.inOut` |
| Saída | 0,15 a 0,25 s | `power2.in` |
| Atraso entre partes de um conjunto | 0,04 a 0,1 s | `stagger` |
| Assentar depois de parar | 0,1 a 0,2 s a mais | balanço curto, `sine.out` |
| Antecipação antes de um movimento grande | 0,08 a 0,15 s | `back.inOut`, ou um recuo de 5 a 10% no sentido contrário |

`elastic` só em detalhe e com moderação: em excesso parece brinquedo.

**Texto em movimento:** o texto assenta rápido para ser lido; uma ideia por tela; contraste alto; palavra por palavra no tempo da fala, com a palavra forte entrando com mais força que as de ligação. Quando a cena já escreve a frase em grande, esconda a legenda nesse trecho, para a mesma frase não aparecer duas vezes.

## O que deixa a animação boa

- **Mostrar o que a fala diz, ao pé da letra.** Se a pessoa fala "a mensagem chega no WhatsApp", a tela mostra a mensagem chegando. Se fala "três passos", aparecem três cartões, um em cada palavra.
- **Cada coisa entra na palavra que a nomeia**, não antes. Texto que aparece antes da fala estraga a surpresa.
- **Nunca parada nem em saltos.** Depois de entrar, algo continua se mexendo até o fim. Prefira o movimento que conta algo (digitação letra por letra, um contador, um cursor, uma barra) à flutuação em loop, que parece artificial; uma flutuação bem leve só quando não houver o que mover. Mas **janela com texto miúdo fica parada** depois de assentar: flutuar faz o texto tremer.
- **Interface de mentira, bem feita:** quando mostrar um sistema, desenhe a tela inteira (janela, botões, conversa, tabela) com cuidado, sem marca de empresa que não seja da pessoa. Se o vídeo ensina uma ferramenta de verdade, a tela segue a de verdade: tela inventada para um programa real fica estranha.
- **Sai limpa:** a cena se emenda na próxima (ver acima). Quando não der, sai em fade curto (`"sai": .18`) ou subindo, para a próxima entrar sem corte seco.
- **Um efeito sonoro em cada ação** (clique quando algo é acionado, teclado na digitação, notificação na mensagem), em `"sons"` da camada. Som contínuo ou repetido só no instante que pede, e bem baixo.
- **Refine sempre:** a cada vídeo, melhore movimento, acabamento e detalhe, mesmo quando a pessoa aprovou o geral.

## Conferir antes de mostrar

**Os princípios são conferidos, não lembrados.** Antes de animar, o `movimento.md` do projeto diz, cena por cena, o principal e os princípios que entram (ver o passo 3 de "Montar" no EDITAR.md). Ao olhar os quadros, confira cada um, nesta ordem:

| Pergunta | Se a resposta for não |
|---|---|
| Em cada momento, há uma coisa só chamando a atenção? | Apague ou tire o que disputa |
| O movimento grande tem um recuo antes (antecipação)? | Ponha um recuo de 5 a 10% no sentido contrário, de 0,08 a 0,15 s |
| O que bate na tela (ou o personagem que pousa, se assusta, levanta peso) achata e volta? | `impacto()`; no boneco, `achata` na pose |
| O que se desloca vai em curva, e não em linha reta? | x e y com curvas diferentes; no boneco, `S.arco()` |
| As partes de um conjunto chegam uma depois da outra? | `conjunto()`, ou um atraso de 0,04 a 0,1 s entre elas |
| Algo pequeno acompanha o movimento principal (ação secundária)? | Sombra, brilho, cabelo, roupa, sobrancelha |
| Os tempos variam (grande devagar, detalhe rápido)? | Use a tabela de tempos |
| A cena se emenda na próxima? | Transformação, clonagem, deslocamento, ou o dissolve do estilo |
| Com personagem: o olho e a expressão reagem a cada virada da história? | Medo, susto, desconfiança, o piscar segurado no susto |
| Com personagem: a perna anda o que o corpo anda (sem patinar, sem andar parado, sem disparar)? | A fase do passo sai da distância percorrida (`S.caminhada`) |
| Com personagem: cada um fica numa vista só (perfil ou frente), e de frente sem inclinar? | Andando ou fazendo algo, de perfil; de frente só parado |
| Ponto ou objeto que segue um caminho desenhado anda sobre essa mesma linha, sem voltar e sem rastro? | Use a mesma lista de pontos para o desenho e para o movimento |
| Botão, cartão e selo entram com movimento de interface (de um lado, com pulo e atraso), e não só aparecendo? | Entrada com deslocamento e `back.out`; fade sozinho não conta |

Monte o projeto e olhe os quadros nos momentos da animação:

```
npx hyperframes@0.9.9 snapshot --at 3.2,3.6,4.1
```

As imagens ficam em `.hyperframes/artifacts/snapshots/` dentro da pasta da montagem. Rode o snapshot em paralelo com o recorte, que demora: dá para criar e conferir as animações enquanto ele roda. Abra e confira: entrou na hora da fala, nada cortado na borda, nada importante acima de 220 px nem a menos de 110 px das laterais, texto legível, nada encostado na legenda.

Na Série Animada e em todo bloco que desenha em SVG, também são normais: `duplicate_audio_track` (vários efeitos na mesma trilha), `container_overflow` e `canvas_overflow` (a câmera anda e o desenho passa da tela de propósito), `gsap_callback_dom_measurement` (o desenho mede o texto a cada quadro), `text_below_floor` e `contrast_aa_failure` em texto desenhado dentro da cena (confira no quadro se lê bem). O `npx hyperframes@0.9.9 check` (o `renderizar` roda antes do render) pode dar avisos que não são erro aqui: `line_unread` (texto pouco tempo na tela, normal no Motion, em que o texto é a própria fala), `nested_structure_needs_subcomposition` e arquivo grande (vêm do jeito que o `montar` junta as animações). Só erro para o render, e o `renderizar` mostra qual foi. Sobreposição de propósito (uma etiqueta por cima de um cartão) dá o erro `text_occluded`: ponha `data-layout-allow-occlusion` no elemento que fica por cima.

## Técnicas prontas do HyperFrames

O HyperFrames tem um catálogo de técnicas (transições, câmera, títulos, gráficos, cursor arrastando, traço de luz). Quando precisar de uma, veja como é feita e refaça no visual do estilo da pessoa: `npx hyperframes@0.9.9 catalog`.

## Os exemplos

| Arquivo | O que mostra |
|---|---|
| `mp-quadro.html` | Parede: a palavra pintada na parede vira quadro de museu, com moldura e plaquinha |
| `mp-espia.html` | Parede: a palavra escondida atrás da cabeça sai espiando |
| `chips-parede.html` | Parede: etiquetas coladas na parede, uma por palavra |
| `carimbo.html` | Um carimbo batendo na tela |
| `mm-palco.html` e `mm-base.css` | Metade: o painel que divide a tela e cresce, encolhe e sobe entre as montagens; a base dos cartões (vale dentro de um `<div class="mm">`) |
| `mm-titulo.html` | Metade: o título do gancho num cartão, com etiquetas entrando |
| `mm-tres-chips.html` | Três etiquetas pequenas no peito, uma por palavra |
| `mm-comentario.html` | O pedido "comenta X": a caixa de comentário com a palavra sendo digitada |
| `mm-link.html`, `mm-link-setas.html`, `mm-link-etiqueta.html` | O final de anúncio: o botão, as setas e a etiqueta apontando para o link |
| `mo-fundo.html`, `mo-base.css` e `mo-base.js` | Motion: o fundo que fica o vídeo inteiro, a base visual e as funções de movimento: palavra por palavra (com tempos por peso da palavra), cursor em arco, digitação, entrada de cartão e de janela, `conjunto()` (as partes chegam depois do recipiente), `impacto()` (comprimir e esticar), `vai()` (antecipação, arco e assentamento), `vira()` (a emenda entre cenas por transformação), `troca()` (valor que rola), `conta()`, `barra()` e `sai(id, fica)` |
| `mo-r-palavra.html` | Motion: a frase entrando palavra por palavra, com a onda da voz embaixo |
| `tc-base.css`, `tc-base.js`, `tc-fundo.html` | Tela do Claude: a base (o app do Claude copiado, a caixa de pedido, os cartões claros, as pílulas, o mascote, a legenda do estilo) e o fundo claro do vídeo inteiro |
| `tc-gancho.html`, `tc-hud.html`, `tc-titulo.html` | Tela do Claude: o cartão que conta até 60 e a comparação; o cartão virando o cronômetro, com o progresso "1/5"; a palavra grande sublinhada de cada parte |
| `tc-app.html` | Tela do Claude: o app inteiro numa cena só, do download ao seletor de modelos, cada ação no tempo da fala (abas, pedido e resposta, pasta, código, anexos, voz, projetos) |
| `tc-modelos.html` | Tela do Claude: o seletor de modelos virando o cartão de escolha, com pílulas e barras de força e de limite |
| `mc-base.css`, `mc-base.js`, `mc-fundo.html` | Colagem: a base (cartões de contorno grosso, etiquetas, carimbos, balão, grade de bonecos, peão e asterisco em 3D, a legenda do estilo) e o fundo com o chão em perspectiva e as abas de capítulo |
| `td-base.css`, `td-base.js`, `td-sombra.html` | Títulos Desenhados: a base (tipografia condensada e manuscrita, peças, traços à mão, árvore, calendário), as funções de movimento (`tdDigita`, `tdPalavra`, `tdArco`, `tdRisca`, `tdTracejado`, `tdPisca`, `tdBoia`, `tdGira`, `tdVai`, `tdFolhas`, `tdSai`) e o degradê do alto |
| `td-gancho.html`, `td-icones.html`, `td-troca.html`, `td-arvore.html`, `td-calendario.html` | Títulos Desenhados: um vídeo inteiro, um título por trecho (a palavra grande riscada; a fila de ícones de verdade; a troca com a seta; a árvore de pastas com a chave; o calendário virando). Os ícones (`td-icone-*.svg`: Claude, ChatGPT, Gemini, Cursor, VS Code, Chrome, Google, Planilhas Google, planilha genérica, Notion, WhatsApp, YouTube, Instagram, GitHub, n8n, terminal, pasta; e `td-estrela.svg`) entram na marcação com `<!--#inclui ...svg-->`; a tabela com a licença de cada um está no [guia do estilo](../estilos/titulos-desenhados.md#ícones) |
| `mc-ideia.html`, `mc-prompt.html`, `mc-teste.html`, `mc-prova.html`, `mc-fim.html` | Colagem: um vídeo inteiro, uma cena por aba (os 100 peões, as fichas e o recibo; o pedido, a ficha preenchendo, a roda e os motivos; a caixa 3D com o preço e a fala; a lupa e o cliente de IA contra o de verdade; o comentário final) |
