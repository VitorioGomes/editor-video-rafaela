# Manutenção (para o Vitório)

Versão do Editor IA feita só para a Rafaela (criada em 2026-11-25). Repositório público (desde 2026-11-25, pedido do Vitório): `VitorioGomes/editor-video-rafaela`.

## O que é diferente do produto

- **Só edição de vídeo com rosto.** Sem roteiro, sem voz de IA, sem estilos sem rosto, sem 3D e sem Blender.
- **Estilos:** Cortes e Legenda (o padrão, o jeito que ela já edita, 2026-11-26), Yap (o Estilo Título do produto, com o nome que o Vitório usa), Títulos Desenhados e Metade (Vitório, 2026-11-25). O Rótulo fixo da pesquisa do nicho entrou como opção do Cortes e Legenda.
- **Cortes de live** (Vitório, 2026-11-26): `extras/live.py` (baixar, ler a fala pela legenda do YouTube, recortar em pé, parado no meio; seguir o rosto com o OpenCV ficou como opção, porque o Vitório achou tremido) e o roteiro em `skill/referencias/cortes-de-live.md`. A IA escolhe os trechos, edita todos e entrega para aprovar; aprovados e recusados ficam anotados no `trechos.md` de cada live, para a escolha melhorar.
- **Estilos novos:** a engenharia reversa fica (`skill/referencias/estilo-novo.md`), limitada a estilos com a pessoa na tela. O Vitório quer acrescentar estilos à versão dela.
- **Texto na tela em português de Portugal**, com os nomes da marca e o vocabulário da transcrição já no `EDITAR.md`.
- **Cores e fontes:** as de cada estilo (decisão do Vitório, 2026-11-25). Ajustar com o uso.
- **Quem opera:** o Vitório no começo, depois alguém da equipa dela. O roteiro responde na língua de quem escreve.

## De onde vem cada parte

| Parte | Origem | Como atualizar |
|---|---|---|
| `sistema/` (o motor) | Cópia do `sistema/` da oficina (`D:\Meu\Produto 3 - Edicao de video`) | `node scripts/sincronizar.mjs`, olhar o `git diff --stat sistema`, commit e push. Não editar aqui: correção de motor vai para a oficina e chega por este comando |
| `skill/` | Própria. Os guias `metade.md`, `titulos-desenhados.md` e `yap.md` (do `titulo.md`), as referências e os exemplos de animação vieram da oficina em 2026-11-25 | À mão. Quando um guia mudar na oficina, avaliar se a mudança vale para ela |
| `extras/` | Própria: o que é só da Rafaela e precisa de código (os cortes de live). Fica fora do `sistema/` porque o `sincronizar` troca o `sistema/` inteiro | À mão |
| `skill/catalogo.html` | O da oficina, só com os três estilos | Estilo novo para todos: cartão novo aqui, com o vídeo em `skill/estilos/videos/` e o completo em `videos/completos/` |

## Estilo novo para a Rafaela

Um estilo criado no computador dela fica em `meu-estilo/estilos/` (só lá). Para ele entrar na ferramenta e no catálogo: trazer o guia para `skill/estilos/`, as imagens e um trecho do vídeo aprovado (360 px, VP9, uns 5 s) para o catálogo, citar em "Qual estilo" do `EDITAR.md` e no README, commit e push. Ela recebe com "atualize o editor".
