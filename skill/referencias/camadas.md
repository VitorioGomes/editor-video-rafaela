# O roteiro de camadas (roteiro.json)

O `montar` lê um `roteiro.json` com tudo o que entra por cima do vídeo: texto, imagem, animação, zoom e som. Você escreve esse arquivo para cada vídeo, na pasta do projeto, a partir da fala (`palavras.json`) e do guia do estilo escolhido.

## Tempo

`de`, `ate` e `em` aceitam segundos ou uma palavra da fala:

- `"@CRM"`: a primeira vez que "CRM" é falado.
- `"@CRM#2"`: a segunda vez.
- `"@CRM+0.4"`: 0,4 s depois da palavra (e `"@CRM#2-0.2"`, 0,2 s antes da segunda vez). Bom para um som ou um movimento que vem logo depois da fala.
- A busca ignora maiúscula e acento: `"@Eu"` também acha o "eu" no meio da frase, e `"@e"` acha o "é". Por isso, **use o comando `palavras`** (abaixo), que já dá a referência certa de cada palavra.

Prefira a palavra aos segundos: se o corte mudar, o texto continua entrando na hora da fala. Para não contar as repetições à mão, `python .ferramenta/sistema/editar.py palavras PALAVRAS.json [DE ATE]` lista cada palavra com o tempo e a referência pronta (`@CRM#2`).

## Tela

O vídeo tem 1080 x 1920. **Área segura:** nada importante acima de 220 px (o nome do perfil cobre) nem a menos de 110 px das laterais (o Instagram aproxima o vídeo ao postar). A legenda fica embaixo, no lugar que a marca da pessoa define.

## Campos do topo

| Campo | Para quê |
|---|---|
| `camadas` | A lista de camadas, na ordem em que entram na tela |
| `recorte` | O vídeo recortado da pessoa (`recorte.webm`), para pôr texto atrás dela (Parede e Metade) |
| `cabeca_por_cima` | `true` no Metade: o painel fica entre o vídeo e o recorte, e a cabeça passa por cima dele |
| `legenda` | Muda a legenda só neste vídeo: `classe`, `x`, `largura`, `y` e `destaques` (palavras em destaque) |
| `efeitos` | `{"ganho": -2}`: sobe ou desce todos os efeitos sonoros, em dB |
| `css` | CSS a mais, só deste vídeo |

Classes de legenda: `leg-forte` (sem serifa, grossa), `leg-grande` (serifada grande), `leg-serifa` (serifada menor), mais `leg-clara` (escura, para fundo claro). `leg-dinamica`: grossa, em caixa alta, com contorno preto e sombra, as palavras que ainda vêm em cinza. `leg-caixa`: a frase numa caixa branca de contorno preto e sombra dura (bom no fundo claro). `leg-pilula`: a frase numa caixinha branca translúcida e arredondada, em Poppins, com a palavra falada escura e as próximas cinza (a do Estilo Títulos Desenhados; use com `"modo": "karaoke"`). O `y` da legenda é sempre o topo dela. Na `"legenda"` do roteiro: `x`, `largura` e `y` (posição), `classe`, `destaques` (palavras na cor de destaque), `cor` (uma cor da marca, como `"destaque"`, ou `#hex`) e `"modo": "karaoke"`: a frase curta (até `caracteres`, 26 por padrão) aparece inteira e apagada, e cada palavra acende quando é falada; sem o modo, a legenda é uma palavra por vez. No karaokê, a frase troca no ponto e na pausa da fala (mais de 0,3 s; `"pausa"` muda), e o "?" e o "!" do fim ficam na tela; `"quebra_virgula": true` também troca a frase na vírgula, e `"juntas": ["VS Code", "Claude Code"]` impede que um nome de duas palavras se parta entre duas frases.

## Tipos de camada

| Tipo | O que é | Campos |
|---|---|---|
| `texto` | Bloco de texto no topo, com linhas de formatos diferentes | `linhas`: `t` (texto), `f` (`serifa`, `mao`, `destaque`, `negrito`, `italico`), `tamanho` (px), `em` (entra nessa palavra), `digita` (letra por letra), `cor` (nome de cor da marca, como `alerta`, ou `#hex`). `y` (altura do bloco), `x` e `largura` (para tirar do centro), `atras` (`true` põe na parede, atrás da pessoa), `tinta` (`"escura"` na parede clara, quando o texto claro não aparece) |
| `serifa` | Título em serifada com uma linha manuscrita digitada embaixo | `texto`, `manuscrita`, `digita_em`, `tamanho`, `y`, `x`, `largura` |
| `frase` | Frase em sem serifa grossa | `texto`, `y` |
| `riscado` | Texto que é riscado e trocado por outro (a virada "não é X, é Y") | `texto`, `depois`, `risca_em`, `depois_em`, `tamanho_depois`, `y` |
| `lista` | Lista que se acumula, um item por vez | `itens`: `texto` e `em`. `y` |
| `print` | Imagem (print, foto), com círculo desenhado se quiser | `src`, `x`, `y`, `largura`, `circulo` (`[cx, cy, rx, ry]` em % da imagem), `cobre_legenda` |
| `tela` | Gravação de tela, sem som | `src`, `x`, `y`, `largura`, `origem` (de onde a gravação começa), `cliques` (segundos da gravação com clique), `altura_tela` (px, faz a legenda descer) |
| `meme` | Imagem ou vídeo curto que ilustra a fala | `src` |
| `bloco` | Animação em HTML feita para o vídeo (ver [animacoes.md](animacoes.md)) | `arquivo`, `x`, `y`, `largura`, `altura`, `rotulos`, `marcas`, `sons`, `troca`, `sai`, `atras`, `legenda_y`, `legenda_classe`, `legenda_fica`, `esconde_legenda`. **Dois padrões escondidos:** o bloco na frente empurra a legenda para baixo dele (para `y + altura + 70`; com a altura padrão de 870, a legenda vai para 940 mesmo num bloco de tela cheia): use `legenda_y` para pôr a legenda onde quer, ou `"legenda_fica": true` para ela não se mexer. E todo bloco toca um whoosh ao entrar: `"som": false` tira |
| `zoom` | Zoom no vídeo (e na parede e no recorte junto) | `em`, `escala`, `x`, `y`, `dura` (0 é corte seco; mais que 0, empurrão suave) |
| `som` | Um efeito sonoro solto | `em`, `id`, `dura`, `ganho` |

Toda camada visível aceita `esconde_legenda: true` (a legenda some naquele trecho, para não repetir o texto que já está grande na tela).

## Som

Cada camada já traz um efeito sonoro padrão, variando para não repetir: clique para texto, whoosh para imagem e animação, dinheiro para valor com "R$", teclado para digitação, caneta para risco e círculo. Em qualquer camada, `"som": "id"` troca o efeito e `"som": false` tira. Num `bloco`, `"sons": [{"em": "@palavra", "id": "...", "ganho": -2}]` põe efeitos nos momentos da animação. **Atenção:** nos `"sons"` de um `bloco`, `"em"` com número conta **a partir do início da camada** (0,5 é meio segundo depois de ela entrar), e não do início do vídeo; com palavra (`"@clique"`), vale o tempo da fala. O `montar` avisa quando um efeito cai fora do vídeo. O catálogo está em `.ferramenta/sistema/efeitos/catalogue.md`, e como escolher em `.ferramenta/sistema/efeitos/GUIDE.md`. Uma camada `som` sozinha toca um efeito num momento: `{"tipo": "som", "em": "@porta", "id": "..."}`, ou um arquivo seu ou gerado com `efeito` (`"arquivo": "sons/porta.wav"`, nivelado sozinho, sem o pico passar de -6 dB antes do `ganho`); `"dura"` corta o som e `"ate": "@palavra"` faz ele acabar com a cena, sumindo em 0,4 s. Para tocar de novo, outra camada `som` (não há repetição automática: som contínuo só no trecho que pede).

## Exemplo

```json
{
  "recorte": "recorte.webm",
  "legenda": { "classe": "leg-grande", "x": 0, "largura": 1080, "y": 1250, "destaques": ["setup", "fácil"] },
  "camadas": [
    { "tipo": "zoom", "em": 0, "escala": 1.0 },
    { "tipo": "zoom", "em": 0.05, "escala": 1.08, "dura": 7.4 },
    { "tipo": "texto", "atras": true, "de": "@criando", "ate": "@estilos", "y": 190, "linhas": [
      { "t": "tô criando um", "f": "mao", "tamanho": 76 },
      { "t": "SETUP", "f": "serifa", "tamanho": 300, "em": "@setup" } ] },
    { "tipo": "riscado", "de": "@difícil", "ate": "@fácil", "texto": "Horas editando", "depois": "Saiu sozinho", "risca_em": "@mas" },
    { "tipo": "print", "de": "@resultado", "ate": "@pronto", "src": "print.png", "x": 200, "y": 1300, "largura": 640, "circulo": [50, 50, 44, 40] },
    { "tipo": "bloco", "de": "@comenta", "ate": 58, "arquivo": "comentario.html", "x": 110, "y": 1180, "largura": 860,
      "rotulos": ["EDITAR"], "marcas": ["@comenta", "@link"] },
    { "tipo": "som", "em": "@dinheiro", "id": "money-register" }
  ]
}
```
