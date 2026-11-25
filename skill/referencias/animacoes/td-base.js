// Títulos Desenhados: as funções de movimento dos títulos. Inclua no <script>: <!--#inclui td-base.js-->
// Todas recebem o tempo em segundos do vídeo (use t0 + M[k], a palavra da fala em "marcas").
// Os princípios estão no nome: antecipação, arco, achatar no impacto, conjunto em sequência, algo sempre vivo.

// Parte o texto do elemento em letras .td-l (nascem escondidas). Rode antes de animar as letras.
function tdQuebra(sel) {
  document.querySelectorAll(sel).forEach((el) => {
    const texto = el.textContent;
    el.innerHTML = [...texto].map((c) => `<span class="td-l">${c === " " ? "&nbsp;" : c}</span>`).join("");
  });
}
// A manuscrita digitada letra por letra, no ritmo da fala (passo de 0,04 a 0,05 s por letra).
function tdDigita(sel, t, passo) { tl.set(sel + " .td-l", { opacity: 1, stagger: passo || 0.045 }, t); }
// Achatar no impacto: alarga e baixa um instante e volta com um balanço. Nunca em texto miúdo.
function tdAchata(sel, t, forca) {
  const f = forca || 1;
  tl.to(sel, { scaleX: 1 + 0.12 * f, scaleY: 1 - 0.14 * f, duration: 0.07, ease: "power2.out" }, t);
  tl.to(sel, { scaleX: 1, scaleY: 1, duration: 0.26, ease: "back.out(3)" }, t + 0.07);
}
// Entrada em arco: o x desacelera e o y acelera, então o caminho é uma curva. dx e dy dizem de onde vem; giro em graus.
// Achata ao pousar. Use em ícone, logo e peça; o elemento pode começar com opacity 0.
function tdArco(sel, t, dx, dy, dura, giro) {
  dura = dura || 0.34;
  tl.fromTo(sel, { x: dx }, { x: 0, duration: dura, ease: "power2.out", immediateRender: false }, t);
  tl.fromTo(sel, { y: dy }, { y: 0, duration: dura, ease: "power3.in", immediateRender: false }, t);
  tl.fromTo(sel, { opacity: 0 }, { opacity: 1, duration: 0.08, immediateRender: false }, t);
  if (giro) tl.fromTo(sel, { rotation: giro }, { rotation: 0, duration: dura, ease: "power2.out", immediateRender: false }, t);
  tdAchata(sel, t + dura, 1);
}
// Antecipação: encolhe e desce um pouco logo antes da palavra grande entrar.
function tdAntecipa(sel, t) {
  tl.to(sel, { scale: 0.94, y: 8, duration: 0.09, ease: "power1.in" }, t - 0.09);
  tl.to(sel, { scale: 1, y: 0, duration: 0.2, ease: "power2.out" }, t);
}
// As letras de uma palavra grande chegando uma depois da outra, esticadas, assentando com back.out.
function tdLetras(sel, t, dura, passo) {
  tl.fromTo(sel + " .td-l", { y: 70, scaleY: 1.3, scaleX: 0.8, opacity: 0 },
    { y: 0, scaleY: 1, scaleX: 1, opacity: 1, duration: dura || 0.34, ease: "back.out(1.7)", stagger: passo || 0.035 }, t);
}
// A palavra grande inteira: antecipação, letras em sequência e o achatar quando a última assenta.
function tdPalavra(sel, t, forca) {
  tdAntecipa(sel, t);
  tdLetras(sel, t - 0.03, 0.34, 0.035);
  const n = document.querySelectorAll(sel + " .td-l").length;
  tdAchata(sel, t + 0.1 + n * 0.035, forca || 0.7);
}
// Desenho à mão: o traço (path, line) se desenha do começo ao fim. Ele só aparece na hora, sem ponto antes.
function tdRisca(sel, t, dura) {
  const p = document.querySelector(sel); const n = p.getTotalLength();
  tl.set(sel, { strokeDasharray: n, strokeDashoffset: n }, 0);
  tl.set(sel, { opacity: 1 }, t);
  tl.to(sel, { strokeDashoffset: 0, duration: dura || 0.18, ease: "power2.inOut" }, t);
}
// Depois de desenhado, o traço vira tracejado correndo (seta e galho vivos até o fim).
function tdTracejado(sel, t, ate, passo) {
  passo = passo || 12;
  tl.set(sel, { strokeDasharray: passo + " " + passo, strokeDashoffset: 0 }, t);
  tl.to(sel, { strokeDashoffset: -passo * 2 * Math.max(1, Math.round((ate - t) / 0.4)), duration: ate - t, ease: "none" }, t);
}
// Estrelinha que nasce girando e fica piscando até "ate", num ritmo próprio (use ritmos diferentes em cada uma).
function tdPisca(sel, t, ate, ritmo) {
  const n = Math.max(1, Math.floor((ate - t - 0.2) / ritmo));
  tl.fromTo(sel, { scale: 0, rotation: -30, opacity: 0 }, { scale: 1, rotation: 0, opacity: 1, duration: 0.2, ease: "back.out(2)" }, t);
  tl.to(sel, { scale: 0.45, opacity: 0.55, rotation: 45, duration: ritmo / 2, ease: "sine.inOut", yoyo: true, repeat: n }, t + 0.2);
}
// Boiar de leve até "ate" (ícone, logo). Texto não boia. Passe o id da peça (o .td-ic do ícone), não uma classe:
// um seletor como "#fila .td-svg" pega também o SVG do selo que está dentro do ícone, e cada um boia por conta.
// Por segurança, só boiam os elementos de fora: o que está dentro de outro escolhido acompanha o de fora.
function tdBoia(sel, t, ate, amp, per) {
  per = per || 0.9;
  const n = Math.max(1, Math.floor((ate - t) / per));
  const todos = [...document.querySelectorAll(sel)];
  const fora = todos.filter((e) => !todos.some((o) => o !== e && o.contains(e)));
  if (fora.length) tl.to(fora, { y: -(amp || 5), duration: per, ease: "sine.inOut", yoyo: true, repeat: n }, t);
}
// Girar devagar até "ate" (a faísca, um selo).
function tdGira(sel, t, ate, graus) { tl.to(sel, { rotation: "+=" + (graus || 120), duration: Math.max(0.3, ate - t), ease: "sine.inOut" }, t); }
// Tremer e apagar (o "errado", o que foi riscado).
function tdTreme(sel, t) {
  tl.to(sel, { x: 12, duration: 0.05, ease: "power1.inOut", yoyo: true, repeat: 5 }, t);
}
// Apaga o que foi riscado: perde a cor e fica meio transparente. O X vermelho (.td-traco) que estiver dentro não
// apaga: ele continua vermelho por cima. Melhor ainda é deixar o X fora do elemento apagado, como nos exemplos.
function tdApaga(sel, t) {
  const alvos = [];
  document.querySelectorAll(sel).forEach((el) => {
    const filhos = [...el.children];
    if (filhos.length && filhos.some((f) => f.classList.contains("td-traco"))) {
      filhos.filter((f) => !f.classList.contains("td-traco")).forEach((f) => alvos.push(f));
    } else alvos.push(el);
  });
  tl.set(alvos, { filter: "grayscale(0)" }, 0);
  tl.to(alvos, { opacity: 0.5, filter: "grayscale(1)", duration: 0.25, ease: "power2.out" }, t);
}
// Mover para o lado com antecipação (recua antes de ir): a fila que abre espaço para o próximo ícone.
function tdVai(sel, t, x, dura) {
  tl.to(sel, { x: "+=8", duration: 0.1, ease: "power1.in" }, t - 0.1);
  tl.to(sel, { x: x, duration: dura || 0.4, ease: "power3.inOut" }, t);
}
// Saída: tudo sobe um pouco e some, as partes uma depois da outra, acelerando. Use t = fim da camada - 0,25.
function tdSai(sels, t) { tl.to(sels, { y: -18, opacity: 0, duration: 0.18, ease: "power2.in", stagger: 0.04 }, t); }
// Calendário: as folhas viram uma a uma, rápidas, até a última, que assenta com um balanço.
function tdFolhas(prefixo, n, t, passo) {
  passo = passo || 0.058;
  for (let i = 0; i < n - 1; i++) {
    tl.to(prefixo + i, { rotationX: -100, opacity: 0, duration: 0.09, ease: "power2.in" }, t + i * passo);
  }
  tl.fromTo(prefixo + (n - 1), { rotationX: 14 }, { rotationX: 0, duration: 0.3, ease: "back.out(3)", immediateRender: false }, t + (n - 1) * passo);
}
