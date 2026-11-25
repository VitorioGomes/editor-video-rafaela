# Regras de edição

Valem para todo vídeo, em qualquer estilo. Foram tiradas de muitas rodadas de correção em vídeos de verdade. O gosto da pessoa, que vai se acumulando em `meu-estilo/regras.md`, vem por cima destas: quando ela pedir diferente, vale o que ela pediu.

## O corte

- **Corte pelo silêncio medido, nunca pela borda de palavra da transcrição.** A transcrição erra a borda: estica uma palavra sobre o silêncio ou corta o começo da seguinte. O `cortar` já mede a energia do áudio.
- **O fim da palavra soa baixo.** Cortar antes de a voz chegar ao fundo come o final ("reais" vira "rea"). O `cortar` espera a queda, e a `--cauda` limita quanto dela fica.
- **Pausa curta entre as frases.** A pessoa quase sempre prefere corte apertado. Sala com eco deixa a pausa longa: o `--pausa 0.22` (o padrão) põe um teto de uns 0,2 s.
- **Fim logo depois da última palavra.** Depois de falar, a pessoa olha para o lado ou para o roteiro, e isso não pode aparecer.
- **Gesto sem fala que importa fica:** a mão saindo da câmera no começo (`--manter-ate SEGUNDOS`) ou um gesto no meio que é o gancho visual (`--manter a-b`).

## As tentativas

Quem grava sozinho repete a frase várias vezes até sair boa, e deixa frases pela metade. É normal.

- **Escolha a tentativa melhor**, mesmo que fuja do roteiro: frase completa, sem gaguejo, com a melhor clareza, ritmo e entonação. A última tentativa não tem preferência: a pessoa repete sem saber qual ficou melhor. As medidas são indício; na dúvida, liste as opções para a pessoa ouvir.
- **O Whisper esconde repetição dentro de um trecho** ("e com IA, e com IA" sai como uma frase só). Rode sempre `tentativas detalhar` nos trechos escolhidos e leia os avisos do `tentativas conferir`. Pedaço curto no começo do trecho é falsa partida até prova em contrário.
- **Duas frases da mesma tentativa ficam num trecho só**, para a junção não comer o fim da palavra.
- **Confira que o `palavras.json` tem todas as frases** do corte antes de montar: o Whisper às vezes pula uma frase inteira.

## A legenda

- **Sempre conferida com o roteiro.** A transcrição erra nome de ferramenta e marca ("Claude Code" vira "Cloud Code"), concordância e palavra curta. Corrija com `--trocas trocas.json` (`{"número da palavra": "texto certo"}`) e ponha os nomes no `--vocabulario`.
- **A legenda segue o que a pessoa quis dizer.** Se ela falou uma palavra errada, a legenda pode trazer a certa.
- **Texto grande na frente com a mesma fala:** a legenda some ali, para não repetir.
- **Com imagem grande na tela, a legenda desce** para baixo dela.

## O que entra na tela

- **Texto entra na hora em que a palavra é falada**, nem antes nem depois. Isso vale também para a primeira linha de um bloco: o topo pode ficar vazio até a palavra.
- **Número é o ponto fraco do tempo:** número escrito em algarismos ("R$ 19,90") não tem letra para o alinhador achar no som e fica com o tempo estimado. Em valor, número, ano e lista rápida, acerte o tempo pelo som com `python .ferramenta/sistema/editar.py retempo VIDEO PALAVRAS.json DE ATE` (ouve o trecho de novo, acha o número por extenso no som, mostra a energia e corrige o `palavras.json`, com cópia do original).
- **Nada encostado nas laterais** (uns 110 a 150 px de margem) **nem no alto** (nada importante acima de 220 px): o Instagram aproxima o vídeo e põe o nome do perfil em cima.
- **Sem frase grande solta na cara da pessoa**, com corte seco: quebra a edição.
- **Troca de montagem sem corte seco:** de tela cheia para tela dividida, uma transição leve, que mal se vê.
- **Pouco emoji no texto.**
- **Animação fiel ao real:** quando o vídeo ensina uma ferramenta, a tela mostra a ferramenta de verdade. Tela inventada com mascote fica estranha.
- **Sempre refinar as animações**, a cada vídeo, mesmo quando a pessoa aprova o geral.

## Som

- **Sempre com efeito sonoro, e variado.** Sem efeito, o vídeo fica morto; o mesmo som repetido fica chato. O motor já faz rodízio.
- **Som contínuo ou repetido só no instante que pede, e bem baixo.** Um tique-taque de 11 s cansa; um som quase na altura da voz atrapalha.
- **Sem música por padrão** nos vídeos falados: a voz é o que importa. Se a pessoa quiser música, bem baixa, por baixo da voz.

## Leitura

- **Texto claro em fundo claro some** (parede branca, camiseta clara, céu). O check do render avisa com `contrast_aa_failure`. Na frente da pessoa: sombra forte ou contorno escuro no texto, ou, se o estilo pede texto sem sombra, um véu escuro suave só atrás da área do texto. Na parede, atrás da pessoa: `"tinta": "escura"`.

## Cor e som da gravação

- **O tratamento leve vem ligado:** um pouco de contraste e saturação, um toque de nitidez, o grave da voz abaixo de 80 Hz cortado e uma compressão leve. Fica em `tratamento` no `meu-estilo/marca.json`, e a pessoa pode mudar ("a parede está rosa demais", "a voz está abafada"): ajuste o filtro dela lá, não o do sistema.
- **Celular grava em HDR**, e sem converter a cor fica lavada. O motor converte sozinho.

## Conferir antes de mostrar

1. **Olhe os quadros** (`npx hyperframes@0.9.9 snapshot --at ...`) nos momentos de cada camada.
2. **Escute com a medição:** renderize também uma versão com `montar --sem-efeitos` em outra pasta e rode `escutar SEM.mp4 COM.mp4 PROJETO/deixas.json`. Ela diz se cada efeito entrou, quando e quão alto. Não diz se ficou bom.
3. **Parede:** rode `parede PROJETO recorte.webm`.
4. **`finalizar`:** põe o volume no padrão das redes (-14 LUFS) e confere tamanho, cor e quadros.
5. **O gosto é da pessoa.** A medição não diz se ficou bom: mostre o vídeo e pergunte.
