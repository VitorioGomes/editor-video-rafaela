// Base do Estilo Tela do Claude: entra no script de cada cena com o comentário "#inclui tc-base.js", depois do mo-base.js
// (que traz T, palavras, cursor, digita, conta, impacto, vai, vira, troca, conjunto e sai).
// O asterisco do Claude, o mascote de pixel e o cursor, prontos para pôr no HTML com innerHTML.
const ASTER = '<svg viewBox="0 0 24 24"><g stroke="#d4704e" stroke-width="2.5" stroke-linecap="round"><path d="M12 2.2v6.3M12 15.5v6.3M2.2 12h6.3M15.5 12h6.3M5 5l4.4 4.4M14.6 14.6L19 19M5 19l4.4-4.4M14.6 9.4L19 5"/></g></svg>';
const MASC = '<svg viewBox="0 0 16 11"><g fill="#d97757"><rect x="2" y="0" width="12" height="7"/><rect x="0" y="3" width="2" height="2"/><rect x="14" y="3" width="2" height="2"/><rect x="3" y="7" width="1" height="3"/><rect x="5" y="7" width="1" height="3"/><rect x="10" y="7" width="1" height="3"/><rect x="12" y="7" width="1" height="3"/></g><g fill="#1d1c1b"><rect x="4" y="2" width="1" height="2"/><rect x="11" y="2" width="1" height="2"/></g></svg>';
const SETA = '<svg viewBox="0 0 26 30"><path d="M2 2 L2 24 L8 18.5 L12.5 28 L16.5 26.2 L12.2 17 L20.5 17 Z" fill="#1d1c1b" stroke="#fff" stroke-width="1.8" stroke-linejoin="round"/></svg>';
// o mascote anda no lugar, em passos de pixel (degraus, não flutuação), até o fim da camada
const mascoteVivo = (id, t, ate) => {
  const n = Math.max(0, Math.floor((ate - t) / .5) - 1);
  tl.to(id, { y: -6, duration: .25, ease: "steps(1)", yoyo: true, repeat: n }, t);
};
// a palavra grande da cena: entra subindo, o sublinhado se desenha da esquerda; a anterior sai rápido
const titulo = (el, t, ate) => {
  tl.fromTo(el, { opacity: 0, y: 34 }, { opacity: 1, y: 0, duration: .3, ease: "power3.out" }, t);
  tl.fromTo(el.querySelector("i"), { scaleX: 0 }, { scaleX: 1, duration: .38, ease: "power3.inOut" }, t + .08);
  if (ate) tl.to(el, { opacity: 0, y: -20, duration: .14, ease: "power2.in" }, ate - .14);
};
// ondas de voz: n barras que sobem e descem até o fim, cada uma no seu ritmo (contado, nunca infinito)
const ondas = (sel, t, ate) => document.querySelectorAll(sel + " i").forEach((b, k) => {
  const d = .16 + (k % 5) * .035, n = Math.max(0, Math.floor((ate - t) / d) - 1);
  tl.fromTo(b, { scaleY: .2 }, { scaleY: .35 + ((k * 37) % 60) / 100, duration: d, ease: "sine.inOut", yoyo: true, repeat: n, immediateRender: false }, t + (k % 7) * .02);
});
