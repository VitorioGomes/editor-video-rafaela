# Estilo novo a partir de um vídeo

A pessoa viu um vídeo com uma edição que ela quer para os dela ("quero editar igual a esse"). Você estuda o vídeo quadro a quadro, escreve o guia do estilo e edita o vídeo dela nele. Daí em diante, o estilo é dela e vale tanto quanto os que vêm prontos.

## 1. Igual ou inspirado

Antes de tudo, pergunte: **"Quer igual a esse, ou pegar a ideia com as suas cores e fontes?"**

- **Inspirado** (o que a maioria quer): vem da referência o jeito de editar (onde o texto fica, como entra, o ritmo, o que ilustra cada frase, o som). As cores e as fontes são as da marca dela, do `meu-estilo/marca.json`.
- **Igual**: vêm também as cores, o tipo de letra (a fonte do Google Fonts mais parecida) e a composição de cada tela.

Nos dois casos, o que aparece na tela sai do vídeo dela, da fala dela. Nunca use o nome, o logo, o personagem ou a cara da marca de outra pessoa.

**Meme, cena de filme, GIF de reação, print real:** o sistema não traz nada disso, e não é seu pegar da internet. Se a referência depende deles, conte à pessoa antes de editar e deixe ela escolher: ela manda os clipes e prints dela (o print real do resultado dela convence mais que um cartão desenhado), ou você troca por algo desenhado (janela, emoji, ilustração), sabendo que fica menos engraçado. Emoji sai com a cara da fonte do computador (no Mac é diferente do Windows).

Peça **2 ou 3 vídeos** do mesmo estilo, se ela tiver: com um só, não dá para separar o que é estilo do que é só daquele vídeo.

## 2. Analisar

```
python .ferramenta/sistema/editar.py referencia analisar LINK_OU_ARQUIVO --saida .projetos/referencias/NOME
```

Aceita link público do Instagram, TikTok ou YouTube, ou o arquivo. Vídeo privado não baixa: peça para ela baixar ou gravar a tela do celular e passar o arquivo. Leva uns 2 minutos para 1 minuto de vídeo; na primeira vez baixa o separador de voz (uns 80 MB).

Ele mede o ritmo (cortes e coisas que entram na tela por minuto), as cores, a música, cada efeito sonoro (com a duração, o timbre e o que acontece na tela no mesmo instante) e transcreve a fala, em qualquer língua. E monta folhas de quadros: o gancho, cada corte, cada coisa que entra na tela, cada efeito sonoro e o vídeo inteiro, um quadro por segundo.

**O som é medido, não ouvido.** Os efeitos certos saem a menos de 0,1 s; os marcados "fraco" podem ser som da própria gravação (mão, objeto, ambiente). O tipo de cada efeito você tira da duração, do timbre e da tela: estalo agudo quando um texto aparece é clique; som médio numa troca de cena é whoosh; som grave quando algo grande bate na tela é impacto.

## 3. Ler

Leia o `resumo.md` e abra **todas** as folhas, na ordem que ele dá. Para ver um detalhe (a fonte, um texto pequeno), tire o quadro em tamanho cheio: `python .ferramenta/sistema/editar.py referencia quadros .projetos/referencias/NOME 12.5 20.2`.

Anote, com números (px, segundos, cores):

| O quê | O que olhar |
|---|---|
| A tela | A pessoa aparece? Onde e de que tamanho? Tela cheia, dividida, só animação, fundo trocado, texto atrás dela? |
| Texto | Onde fica (o `y` das entradas), tamanho, tipo de letra (serifada, sem serifa grossa, manuscrita), cor, caixa alta, quantas palavras por vez, como entra (palavra por palavra, digitando, pulando, deslizando) e quando sai |
| Legenda | Tem? Onde, que tamanho, palavra por palavra ou frase, palavra-chave em outra cor |
| O que ilustra a fala | Prints, janelas de sistema, ícones, emojis, setas, cursor, vídeos de apoio, memes. É literal (fala "planilha", aparece planilha) ou metáfora? |
| Ritmo | Cortes e entradas por minuto. Quanto tempo a tela fica sem nada novo. O que continua se mexendo depois de entrar |
| Câmera | Zoom lento, zoom seco, quando |
| Transição | Corte seco, deslize, a tela que encolhe, o painel que sobe |
| Cores | As dominantes (fundo) e as fortes (texto e destaque) |
| Som | Música (e quão baixa)? Efeitos por minuto e em que acontece cada tipo: clique em cada texto, whoosh em cada troca, impacto na frase forte |
| Gancho | Os 3 primeiros segundos, quadro a quadro: o que prende |
| Fim | Como pede o comentário, o seguir ou o clique |

Olhe também o que se repete em todos os vídeos da referência: isso é o estilo. O que aparece em um só é daquele vídeo.

## 4. Escrever o guia do estilo

Crie `meu-estilo/estilos/NOME.md` no mesmo formato dos guias de `.ferramenta/skill/estilos/` (leia um deles antes): a ideia em duas linhas, **Gravação**, **Na tela**, **Som** e **Como montar**. Escreva com os números que você anotou, para o próximo vídeo sair igual sem rever a referência. No fim, **De onde veio**: o link, a data e se é igual ou inspirado. Guarde 2 ou 3 quadros da referência em `meu-estilo/estilos/imagens/` para ela reconhecer o estilo.

Depois, traduza o estilo para o motor:

- O que o motor já faz vai direto no `roteiro.json` (ver [camadas.md](camadas.md)): texto, serifa, legenda, lista, print, tela, zoom, recorte da pessoa, efeitos.
- O que se repete em todo vídeo vira uma base em `meu-estilo/animacoes/` (o CSS dos cartões, o fundo, o cursor), incluída com `#inclui` em cada animação, como as bases dos exemplos (`mm-base.css`, `mo-base.css`).
- As cenas de cada vídeo são animações novas, criadas para a fala dele (ver [animacoes.md](animacoes.md)).
- **O estilo pede algo que o sistema não tem** (trocar o fundo, vídeos de apoio de banco de imagens, 3D): diga à pessoa o que falta, o que custa e de onde viria, e só siga com o sim dela. Não troque por algo mais simples sem avisar.
- **O estilo pede outra gravação** (parede lisa atrás, espaço acima da cabeça, câmera mais longe): explique na seção **Gravação** e avise a pessoa antes de ela gravar.

Na seção do estilo no `meu-estilo/regras.md`, anote que ele existe e onde está o guia.

## 5. Editar o primeiro vídeo

Siga "Cada vídeo" no [EDITAR.md](../EDITAR.md), com o guia novo no lugar do guia de `.ferramenta/skill/estilos/`.

## 6. Comparar antes de mostrar

```
python .ferramenta/sistema/editar.py referencia comparar .projetos/referencias/NOME versoes/NOME-v1.mp4 --saida .projetos/NOME/comparacao
```

Ele mede o vídeo editado do mesmo jeito e põe referência e editado lado a lado, nos mesmos pontos do vídeo. Abra as folhas `lado-a-lado-N.jpg` e procure o que a referência tem e o seu não tem: tamanho do texto, contraste entre o grande e o pequeno, quantidade de coisas na tela, movimento, acabamento das janelas e dos cartões.

Nos números, **mudanças na tela por minuto e efeitos por minuto devem ficar perto dos da referência** (uns 30% para mais ou para menos). Bem abaixo é sinal de edição parada; bem acima, de poluição. Os números são indício, não meta: o medidor não vê coisa pequena entrando, e uma rajada de teclado conta como um efeito só. Antes de mexer no vídeo por causa de um número, confira nas folhas se a diferença é de verdade. Se for, corrija e renderize de novo **antes de mostrar**. O vídeo dela não pode sair mais fraco que a referência. As cores só se comparam num estilo copiado igual.

## 7. Mostrar e guardar

Mostre como em "Cada vídeo". O que ela corrigir vai para o guia do estilo (`meu-estilo/estilos/NOME.md`) e para o `meu-estilo/regras.md`, como qualquer correção. Quando ela aprovar, o estilo está pronto: da próxima vez, basta ela dizer o nome.
