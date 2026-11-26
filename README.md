# Editor de vídeo da Rafaela

Edita os vídeos curtos (Reels, TikTok, Shorts) que a Rafaela grava falando para a câmera: escolhe as melhores tentativas, tira as pausas e os erros, trata a cor e o som, põe a legenda (e, nos estilos com mais edição, título, animação e efeito sonoro) e entrega o vídeo pronto para postar. A cada correção, aprende o gosto dela. Roda no computador, sem mandar o vídeo para fora.

Só edita: não escreve roteiro, não gera voz e não faz vídeo sem a Rafaela na tela.

## Os estilos

- **Cortes e Legenda:** o jeito que ela já edita, só os cortes e a legenda, com um rótulo no topo quando pedir. O padrão.
- **Yap:** um título no topo para cada ideia, frase de apoio manuscrita e a legenda pequena ao lado do rosto.
- **Títulos Desenhados:** um título desenhado para cada trecho, no alto escurecido, com a legenda numa caixinha abaixo do rosto.
- **Metade:** um painel na metade de cima mostra o que ela explica, e ela fica na metade de baixo.

**Cortes de live:** mande o link da live no YouTube. A IA lê a live inteira (pela legenda do YouTube ou transcrevendo no computador), escolhe os trechos que viram Reels e entrega todos editados: você aprova ou recusa cada um.

Estilo novo: mande o link de um vídeo com a edição que quer, e a IA monta o estilo a partir dele (só estilos com a pessoa na tela).

## Como instalar

Precisa de uma IA de terminal (Claude Code, Codex ou Gemini CLI) e do [Git](https://git-scm.com). O resto (Python, Node.js e ffmpeg) a IA verifica e instala com você.

Abra a IA na pasta onde quer o editor (uma pasta vazia) e cole:

```
Clone o repositório https://github.com/VitorioGomes/editor-video-rafaela em editor/.ferramenta (ou só em .ferramenta, se esta pasta estiver vazia) e siga o roteiro em .ferramenta/skill/EDITAR.md.
```

**As pastas:** em `brutos/` vai o que a Rafaela gravou, em `versoes/` aparecem os vídeos para assistir, em `editados/` ficam os aprovados e em `meu-estilo/`, o gosto que a IA aprendeu.

Para atualizar, peça à IA: "atualize o editor".

## O que saber antes

- **Gravação:** em pé (vertical), câmera parada. No Yap e nos Títulos Desenhados, com espaço livre acima da cabeça.
- **Live:** deitada também serve: o recorte em pé fica no meio. Nos estilos com título, o vídeo desce e o topo vira a parede desfocada, para o título caber.
- **Placa de vídeo** não é obrigatória; com uma placa NVIDIA, a transcrição fica mais rápida.
- Na primeira transcrição, os modelos de voz baixam sozinhos (uns 6 GB). Depois, tudo roda sem internet.
