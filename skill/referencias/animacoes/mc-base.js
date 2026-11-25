// Base do Estilo Motion claro: entra no script de cada cena com o comentário "#inclui mc-base.js", depois do mo-base.js
// (que traz T, impacto, vai, vira, conta, digita, cursor e sai).
const BONECO = '<svg viewBox="0 0 44 54"><circle cx="22" cy="14" r="11" fill="currentColor"/><path d="M2 54 C2 33 11 27 22 27 C33 27 42 33 42 54 Z" fill="currentColor"/></svg>';
const SETA = '<svg viewBox="0 0 26 30"><path d="M2 2 L2 24 L8 18.5 L12.5 28 L16.5 26.2 L12.2 17 L20.5 17 Z" fill="#161616" stroke="#fff" stroke-width="1.8" stroke-linejoin="round"/></svg>';
// o asterisco do Claude chapado (no cartão, no quadrado da roda)
const ASTER = (cor = "#ee6839") => `<svg viewBox="0 0 24 24"><g stroke="${cor}" stroke-width="2.6" stroke-linecap="round"><path d="M12 2.2v6.3M12 15.5v6.3M2.2 12h6.3M15.5 12h6.3M5 5l4.4 4.4M14.6 14.6L19 19M5 19l4.4-4.4M14.6 9.4L19 5"/></g></svg>`;
// o asterisco em 3D: raios grossos arredondados, luz de cima à esquerda e sombra embaixo
const ASTER3D = (id) => {
  const raios = Array.from({ length: 12 }, (_, k) => `<rect x="44" y="4" width="12" height="46" rx="6" transform="rotate(${k * 30} 50 50)"/>`).join("");
  return `<svg viewBox="0 0 100 100" style="overflow:visible"><defs>
    <radialGradient id="${id}l" cx="38%" cy="30%" r="75%"><stop offset="0" stop-color="#ffb08a"/><stop offset=".45" stop-color="#ee6839"/><stop offset="1" stop-color="#b8401a"/></radialGradient>
    <filter id="${id}s" x="-30%" y="-30%" width="160%" height="170%"><feDropShadow dx="0" dy="7" stdDeviation="4" flood-color="#5a2a10" flood-opacity=".35"/></filter></defs>
    <g fill="url(#${id}l)" filter="url(#${id}s)">${raios}<circle cx="50" cy="50" r="16"/></g></svg>`;
};
// o peão em 3D: cor no "color" do elemento, sombreado por cima (luz da esquerda)
const PEAO = (id) => `<svg viewBox="0 0 60 112" style="overflow:visible"><ellipse cx="30" cy="104" rx="30" ry="7" fill="rgba(60,40,20,.18)"/>
  <g fill="currentColor"><ellipse cx="30" cy="99" rx="25" ry="8"/><path d="M9 99 C11 72 19 60 23 51 L37 51 C41 60 49 72 51 99 Z"/><ellipse cx="30" cy="51" rx="13" ry="4.5"/><circle cx="30" cy="32" r="15"/></g>
  <g fill="url(#${id})"><ellipse cx="30" cy="99" rx="25" ry="8"/><path d="M9 99 C11 72 19 60 23 51 L37 51 C41 60 49 72 51 99 Z"/><circle cx="30" cy="32" r="15"/></g></svg>`;
const SOMBREADO = (id) => `<svg width="0" height="0" style="position:absolute"><defs><linearGradient id="${id}" x1="0" x2="1" y1="0" y2="0"><stop offset="0" stop-color="#fff" stop-opacity=".6"/><stop offset=".38" stop-color="#fff" stop-opacity=".08"/><stop offset=".62" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".3"/></linearGradient></defs></svg>`;
// um quadro da cena: entra num pulo curto e sai rápido
const quadro = (sel, de, ate, dura = .3) => {
  tl.fromTo(sel, { opacity: 0, y: 34, scale: .94 }, { opacity: 1, y: 0, scale: 1, duration: dura, ease: "back.out(1.6)", immediateRender: false }, de);
  if (ate) tl.to(sel, { opacity: 0, y: -24, duration: .16, ease: "power2.in" }, ate - .16);
};
// etiqueta que bate na tela e achata (comprimir e esticar), já na inclinação final
const cola = (sel, t, giro = -3) => impacto(sel, t, { de: 1.7, giro: giro * 3, fim: giro });
// carimbo: cai grande e gira, e bate
const carimbo = (sel, t, giro = -8) => {
  tl.fromTo(sel, { opacity: 0, scale: 2.2, rotation: giro - 18 }, { opacity: 1, scale: 1, rotation: giro, duration: .2, ease: "power4.in", immediateRender: false }, t);
  tl.to(sel, { keyframes: [{ scaleX: 1.12, scaleY: .86, duration: .06 }, { scaleX: 1, scaleY: 1, duration: .16, ease: "back.out(3)" }] }, t + .2);
};
// grade de bonecos: n bonecos em "colunas", com a cor no color de cada um. Devolve a lista.
const grade = (id, n, colunas, tam = 44, gap = 12) => {
  const g = document.getElementById(id);
  g.style.display = "grid"; g.style.gridTemplateColumns = `repeat(${colunas}, ${tam}px)`; g.style.gap = `${gap}px`;
  g.innerHTML = Array.from({ length: n }, () => `<div class="mc-boneco" style="width:${tam}px;height:${tam * 1.23}px">${BONECO}</div>`).join("");
  return Array.from(g.children);
};
