// Base do Estilo Motion: entra no <script> de cada cena com <!--#inclui mo-base.js-->. Tempos absolutos: T(i) = t0 + M[i].
const T = (i) => t0 + M[Math.min(i, M.length - 1)];
// texto palavra por palavra: cada .w entra no seu tempo (um tempo por palavra; faltando, repete o último), saindo do desfoque.
// Tempos variados, não iguais: a palavra apagada (.mo-cinza, a de ligação) entra leve e rápida, a palavra forte (.mo-lar, .mo-selo,
// .mo-serif ou .forte) entra com mais força e passa um pouco do ponto, e as outras ficam no meio.
// O desfoque anda numa curva própria, sem repique: no back.out ele passava de zero, ficava inválido e a palavra travava borrada.
const palavras = (sel, tempos) => document.querySelectorAll(sel + " .w").forEach((e, i) => {
  const t = tempos[Math.min(i, tempos.length - 1)];
  const leve = e.matches(".mo-cinza"), forte = !leve && e.matches(".mo-lar, .mo-selo, .mo-serif, .forte");
  const de = forte ? { y: 50, scale: .82 } : leve ? { y: 18, scale: .98 } : { y: 34, scale: .94 };
  tl.fromTo(e, { opacity: 0, ...de }, { opacity: 1, y: 0, scale: 1, duration: forte ? .32 : leve ? .2 : .26, ease: forte ? "back.out(2.2)" : leve ? "power3.out" : "back.out(1.6)" }, t);
  tl.fromTo(e, { filter: "blur(10px)" }, { filter: "blur(0px)", duration: leve ? .16 : .2, ease: "power2.out" }, t);
});
// cursor, sem nome
// pts = [[tempo, x, y, clica], ...], x/y da ponta da seta na tela. Anda em arco (x e y com curvas diferentes, como a mão)
// e, antes de cada clique, recua um tiquinho (antecipação).
const cursor = (id, pts) => {
  tl.set(id, { x: pts[0][1], y: pts[0][2], opacity: 0 }, t0);
  tl.to(id, { opacity: 1, duration: .12 }, Math.max(t0, pts[0][0] - .12));
  for (let i = 1; i < pts.length; i++) {
    const d = Math.min(.5, Math.max(.14, pts[i][0] - pts[i - 1][0] - .05));
    tl.to(id, { x: pts[i][1], duration: d, ease: "power2.inOut" }, pts[i][0] - d);
    tl.to(id, { y: pts[i][2], duration: d, ease: "power3.inOut" }, pts[i][0] - d);
  }
  pts.forEach((p) => { if (p[3]) tl.fromTo(id + " svg", { scale: 1 }, { keyframes: [{ scale: 1.08, duration: .06, ease: "power1.out" }, { scale: .78, duration: .06, ease: "power2.in" }, { scale: 1, duration: .14, ease: "back.out(2)" }], transformOrigin: "15% 10%", immediateRender: false }, p[0] - .06); });
};
// digita o texto de um elemento, letra por letra, em "dura" segundos. O texto inteiro já ocupa o lugar desde o início
// (só fica transparente), então nada muda de tamanho nem empurra a linha de baixo enquanto digita.
const digita = (id, t, dura) => {
  const el = document.getElementById(id);
  const txt = el.textContent;
  el.innerHTML = txt.split("").map((l) => `<span style="opacity:0">${l}</span>`).join("");
  tl.set(el.children, { opacity: 1, stagger: dura / Math.max(1, txt.length) }, t);
};
// pulo de entrada para pílulas, cartões e objetos sem texto miúdo
const entra = (id, t, de = { y: 60 }) => tl.fromTo(id, { opacity: 0, scale: .9, ...de }, { opacity: 1, scale: 1, x: 0, y: 0, rotation: 0, duration: .32, ease: "back.out(1.7)" }, t);
// entrada de janela com texto: sobe e assenta, sem repique e sem escala, e depois fica parada.
const janela = (id, t) => tl.fromTo(id, { opacity: 0, y: 70 }, { opacity: 1, y: 0, duration: .4, ease: "power3.out" }, t);
// saída no fim da cena: sobe e some, para a próxima entrar limpa (sem escala, que também faz o texto tremer).
// fica: seletor do que NÃO sai, porque a cena seguinte começa com ele no mesmo lugar (a emenda, ver vira()).
// Tudo o mais some um pouco antes, e o que fica continua na tela até o último quadro.
const sai = (id, fica) => {
  if (!fica) return tl.to(id, { opacity: 0, y: -50, duration: .18, ease: "power2.in" }, t0 + D - .18);
  const raiz = document.querySelector(id), manter = Array.from(raiz.querySelectorAll(fica)), vao = [];
  const anda = (el) => Array.from(el.children).forEach((f) => {
    if (manter.includes(f)) return;
    if (manter.some((m) => f.contains(m))) anda(f); else vao.push(f);
  });
  anda(raiz);
  if (vao.length) tl.to(vao, { opacity: 0, y: -40, duration: .2, ease: "power2.in" }, t0 + D - .24);
};
// número contando de "de" até "ate" em "dura" segundos, com o milhar do Brasil (7.400.000.000).
// casas: casas decimais; antes e depois: o texto em volta ("R$ ", "%").
const conta = (id, t, de, ate, dura, casas = 0, antes = "", depois = "") => {
  const el = document.getElementById(id), o = { v: de };
  const fmt = (v) => antes + v.toLocaleString("pt-BR", { minimumFractionDigits: casas, maximumFractionDigits: casas }) + depois;
  el.textContent = fmt(de);
  tl.to(o, { v: ate, duration: dura, ease: "power2.out", onUpdate: () => { el.textContent = fmt(o.v); } }, t);
};
// barra (.mo-enche) enchendo até "pct" (de 0 a 1)
const barra = (id, t, pct, dura = .8) => tl.fromTo(id, { scaleX: 0 }, { scaleX: pct, duration: dura, ease: "power2.out", immediateRender: false }, t);
// multidão: n bonecos numa grade de "colunas", entrando em onda a partir de t. Devolve a lista de elementos,
// para colorir depois: tl.to(lista.slice(0, 12), { color: "var(--c-motion)", stagger: .02, duration: .2 }, T(2)).
const multidao = (id, t, n, colunas) => {
  const g = document.getElementById(id);
  g.style.gridTemplateColumns = `repeat(${colunas}, auto)`;
  const corpo = '<svg viewBox="0 0 46 62"><circle cx="23" cy="13" r="11" fill="currentColor"/><path d="M4 62 C4 38 12 30 23 30 C34 30 42 38 42 62 Z" fill="currentColor"/></svg>';
  g.innerHTML = Array.from({ length: n }, () => `<div class="mo-pessoa">${corpo}</div>`).join("");
  const lista = Array.from(g.children);
  tl.fromTo(lista, { opacity: 0, y: 20, scale: .6 }, { opacity: 1, y: 0, scale: 1, duration: .25, ease: "back.out(2)", stagger: { each: Math.min(.012, .8 / n), from: "center" } }, t);
  return lista;
};

// ---------- movimento com os princípios de animação (ver animacoes.md, "Princípios de movimento") ----------
// Tempos de partida: detalhe .2 s, elemento médio .35, elemento grande ou troca de cena .55, saída .2, atraso entre partes .06.

// dentro("#a", ".b, .c") = "#a .b, #a .c": o seletor das partes vale só dentro do recipiente
const dentro = (id, partes) => partes.split(",").map((p) => id + " " + p.trim()).join(", ");

// conjunto: o recipiente chega e as partes de dentro chegam depois, uma atrás da outra (continuidade e sobreposição).
// partes: seletor das partes dentro do recipiente, na ordem de leitura. Recipiente e partes começam com opacity: 0 no CSS.
const conjunto = (id, t, partes, { de = { y: 60 }, cada = .06, atraso = .12, dura = .45 } = {}) => {
  tl.fromTo(id, { opacity: 0, ...de }, { opacity: 1, x: 0, y: 0, duration: dura, ease: "power3.out" }, t);
  if (partes) tl.fromTo(dentro(id, partes), { opacity: 0, y: 16 }, { opacity: 1, y: 0, duration: .3, ease: "power3.out", stagger: cada }, t + atraso);
};

// impacto: o objeto cai na tela, achata ao bater e volta à forma (comprimir e esticar). Passa peso.
// Só em selo, etiqueta, ícone e botão; texto miúdo nunca deforma. de: o tamanho de onde vem; giro e fim: a rotação.
const impacto = (id, t, { de = 1.6, giro = 0, fim = 0 } = {}) => {
  tl.fromTo(id, { opacity: 0, scale: de, rotation: giro }, { opacity: 1, scale: 1, rotation: fim, duration: .17, ease: "power3.in" }, t);
  tl.to(id, { keyframes: [{ scaleX: 1.14, scaleY: .84, duration: .06, ease: "power1.out" }, { scaleX: .96, scaleY: 1.05, duration: .1, ease: "sine.inOut" }, { scaleX: 1, scaleY: 1, duration: .14, ease: "sine.out" }] }, t + .17);
};

// vai: deslocamento grande com antecipação e assentamento. O back.inOut recua um pouco antes de ir e passa um pouco do
// ponto antes de parar. Em arco: x e y andam com curvas diferentes, e o caminho sai curvo em vez de reto.
// para: { x, y, scale, rotation }, os valores de chegada do GSAP.
const vai = (id, t, para, dura = .6, arco = true) => {
  const { x, y, ...resto } = para;
  if (x !== undefined) tl.to(id, { x, duration: dura, ease: "back.inOut(1.3)" }, t);
  if (y !== undefined) tl.to(id, { y, duration: dura, ease: arco ? "power3.inOut" : "back.inOut(1.3)" }, t);
  if (Object.keys(resto).length) tl.to(id, { ...resto, duration: dura, ease: "power3.inOut" }, t);
};

// vira: a emenda entre cenas (transformação). Um elemento nasce do retângulo de outro e cresce até o seu lugar: a pílula
// vira janela, a janela vira cartão, o cartão vira etiqueta. A cena anterior termina com o elemento de origem parado
// (sai(id, fica)), e esta começa com a forma no mesmo lugar, então não há corte: a forma só muda.
// de e para: [x, y, largura, altura, raio], em px da tela (1080 x 1920). O elemento tem position: absolute, opacity: 0 e,
// no CSS, o tamanho e o lugar de "para". partes: o conteúdo, que aparece quando a forma assenta.
// cor: [cor de origem, cor final] do fundo, se mudar. eco: seletor de uma cópia do conteúdo antigo, que some no começo.
const vira = (id, t, de, para, { dura = .55, partes = null, cor = null, eco = null } = {}) => {
  // de = null: parte do lugar e do tamanho atuais do elemento (a forma que já está na tela muda de papel)
  const ir = (a, b, ease) => de ? tl.fromTo(id, a, { ...b, duration: dura, ease }, t) : tl.to(id, { ...b, duration: dura, ease }, t);
  if (de) tl.set(id, { opacity: 1 }, t);
  ir(de && { left: de[0], width: de[2] }, { left: para[0], width: para[2] }, "power3.inOut");
  ir(de && { top: de[1], height: de[3] }, { top: para[1], height: para[3] }, "expo.inOut");  // curva diferente: o caminho sai em arco
  if (para[4] !== undefined) ir(de && { borderRadius: de[4] ?? 30 }, { borderRadius: para[4] }, "power2.inOut");
  if (cor) ir({ backgroundColor: cor[0] }, { backgroundColor: cor[1] }, "power2.inOut");
  if (eco) tl.to(eco, { opacity: 0, duration: .12, ease: "power1.in" }, t);
  if (partes) tl.fromTo(dentro(id, partes), { opacity: 0, y: 16 }, { opacity: 1, y: 0, duration: .3, ease: "power3.out", stagger: .06 }, t + dura * .75);
};

// troca: o valor muda rolando, o velho sobe e o novo vem de baixo, dentro de uma máscara (mudança de valor).
// O texto novo entra no lugar do velho.
const troca = (id, t, novo, dura = .4) => {
  const el = document.getElementById(id), velho = el.textContent;
  // a máscara corta só em cima e embaixo: o texto novo pode ser mais largo que o velho
  el.style.clipPath = "inset(0 -2000px)"; el.style.position = el.style.position || "relative"; el.style.display = el.style.display || "inline-block"; el.style.whiteSpace = "nowrap";
  el.innerHTML = `<span style="display:block">${velho}</span><span style="display:block;position:absolute;left:0;right:0;top:0">${novo}</span>`;
  const [a, b] = el.children;
  tl.fromTo(a, { yPercent: 0 }, { yPercent: -110, duration: dura, ease: "power3.inOut" }, t);
  tl.fromTo(b, { yPercent: 110 }, { yPercent: 0, duration: dura, ease: "back.out(1.4)" }, t + .05);
};
