// Série Animada: bicho de quatro patas (cachorro, gato), de perfil, no mesmo traço de nanquim do boneco.
// Entra no <script> depois do sa-personagem.js: <!--#inclui sa-bicho.js-->. Sempre de perfil (olhando para a direita; vira: -1 espelha).
// As patas se resolvem sozinhas até o chão (nunca ficam no ar), e o passo sai da distância percorrida, como o andar da gente:
//   const b = Bicho.criar(g, Bicho.cachorro({ cor: '#9a6a3a', mancha: '#f2e6d0', orelha: 'caida' }));
//   const esc = Bicho.escala(altPorta, ficha);                     // o tamanho certo ao lado de uma porta (cachorro médio: ~32% de uma pessoa)
//   const c = S.caminhada(xDe, t, de, Bicho.passada(ficha, esc));   // andando: ph e amp
//   Bicho.posar(b, { x, y: chao, esc, ph: c.ph, amp: c.amp, boca, rabo, abana, orelha, cabeca, sentado, deitado, achata }, { olhaX, pisca, medo }, luz, ambiente);
(function () {
  const NS = 'http://www.w3.org/2000/svg', TINTA = '#17121c';
  let seqOlho = 0;
  const el = (tag, at, p) => { const e = document.createElementNS(NS, tag); for (const k in at) e.setAttribute(k, at[k]); if (p) p.appendChild(e); return e; };
  const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x)), lerp = (a, b, k) => a + (b - a) * k;
  const mix = (a, b, k) => Boneco.mix(a, b, k), mul = (a, b) => Boneco.mul(a, b);

  // ---------- fichas ----------
  // altura: a altura da cernelha (o alto das costas) como fração da altura de uma pessoa adulta
  const PORTE = { pequeno: 0.2, medio: 0.32, grande: 0.42 };
  function cachorro(o = {}) {
    return Object.assign({ tipo: 'cachorro', cor: '#9a6a3a', mancha: null, focinho: null, orelha: 'caida', rabo: 'longo', coleira: '#c0392b',
      altura: PORTE[o.porte || 'medio'] }, o);
  }
  function gato(o = {}) {
    return Object.assign({ tipo: 'gato', cor: '#5b5b66', mancha: null, focinho: null, orelha: 'pontuda', rabo: 'gato', coleira: null, altura: 0.15 }, o);
  }

  // medidas em unidades do desenho (chão em y 0). Cachorro e gato mudam corpo, perna, cabeça e focinho.
  // w: a grossura da perna (o porte grande tem perna mais grossa; "perna" na ficha muda à mão: 1.2 = 20% mais grossa)
  const M = f => {
    const m = f.tipo === 'gato'
      ? { rx: 118, ry: 42, cy: -150, ombro: [84, -158], quadril: [-88, -156], coxa: 62, canela: 66, w: 24, cab: 44, focinho: 22, pescoco: [92, -172], cabeca: [132, -214], cernelha: 196 }
      : { rx: 132, ry: 54, cy: -212, ombro: [92, -216], quadril: [-100, -214], coxa: 92, canela: 98, w: 36, cab: 54, focinho: 58, pescoco: [100, -236], cabeca: [152, -284], cernelha: 262 };
    m.w *= (f.perna || 1) * ({ pequeno: 0.9, medio: 1, grande: 1.15 }[f.porte] || 1);
    return m;
  };

  const passada = (f, esc) => (M(f).coxa + M(f).canela) * 0.55 * esc;

  // ---------- desenho ----------
  function criar(parent, f) {
    const m = M(f), raiz = el('g', {}, parent), ting = [];
    const pinta = (e, attr, cor) => { ting.push([e, attr, cor]); return e; };
    const S = c => mix(c, '#1a1424', 0.32);
    const corpoCor = f.cor, sombra = S(f.cor);
    const perna = (longe) => { // duas peças e a pata
      const g = el('g', {}, raiz), cor = longe ? sombra : corpoCor;
      const b = pinta(el('path', { fill: cor, stroke: TINTA, 'stroke-width': 6, 'stroke-linejoin': 'round' }, g), 'fill', cor); // canela embaixo
      const a = pinta(el('path', { fill: cor, stroke: TINTA, 'stroke-width': 6, 'stroke-linejoin': 'round' }, g), 'fill', cor); // a coxa cobre a junta
      const pata = pinta(el('ellipse', { rx: m.w * 0.7, ry: m.w * 0.42, fill: f.mancha && !longe ? f.mancha : cor, stroke: TINTA, 'stroke-width': 6 }, g), 'fill', f.mancha && !longe ? f.mancha : cor);
      return { g, a, b, pata };
    };
    const pernas = { tl: perna(true), dl: perna(true) }; // traseira e dianteira do lado de lá
    // rabo, atrás do corpo
    const rabo = el('g', {}, raiz);
    const raboT = el('path', { fill: 'none', stroke: TINTA, 'stroke-width': m.w * 0.62 + 12, 'stroke-linecap': 'round' }, rabo);
    const raboC = pinta(el('path', { fill: 'none', stroke: corpoCor, 'stroke-width': m.w * 0.62, 'stroke-linecap': 'round' }, rabo), 'stroke', corpoCor);
    // tronco: corpo, barriga mais clara ou mancha
    const tronco = el('g', {}, raiz);
    pinta(el('ellipse', { cx: 0, cy: m.cy, rx: m.rx, ry: m.ry, fill: corpoCor, stroke: TINTA, 'stroke-width': 7 }, tronco), 'fill', corpoCor);
    if (f.mancha) pinta(el('ellipse', { cx: m.rx * 0.35, cy: m.cy + m.ry * 0.45, rx: m.rx * 0.5, ry: m.ry * 0.45, fill: f.mancha }, tronco), 'fill', f.mancha);
    pinta(el('path', { d: `M ${-m.rx * 0.8} ${m.cy + m.ry * 0.5} Q 0 ${m.cy + m.ry * 1.05} ${m.rx * 0.8} ${m.cy + m.ry * 0.5}`, fill: 'none', stroke: sombra, 'stroke-width': 12, opacity: 0.6 }, tronco), 'stroke', sombra);
    const pernasPerto = { tp: perna(false), dp: perna(false) };
    // sentado, a coxa de trás vira uma massa redonda ao lado do corpo
    const anca = pinta(el('ellipse', { rx: m.coxa * 0.62, ry: m.coxa * 0.48, fill: corpoCor, stroke: TINTA, 'stroke-width': 6, opacity: 0 }, raiz), 'fill', corpoCor);
    // a luz de recorte: um filete claro no lombo e no alto da cabeça, do lado da luz (bicho escuro não some no escuro)
    const recorteC = el('path', { fill: 'none', 'stroke-width': 7, 'stroke-linecap': 'round', opacity: 0 }, tronco);
    // pescoço e cabeça
    const pesc = pinta(el('path', { fill: corpoCor, stroke: TINTA, 'stroke-width': 7, 'stroke-linejoin': 'round' }, raiz), 'fill', corpoCor);
    const col = f.coleira ? el('path', { fill: 'none', stroke: f.coleira, 'stroke-width': 14, 'stroke-linecap': 'round' }, raiz) : null;
    const cabeca = el('g', {}, raiz);
    const orelhaLonge = el('g', {}, cabeca);
    const cranio = pinta(el('circle', { cx: 0, cy: 0, r: m.cab, fill: corpoCor, stroke: TINTA, 'stroke-width': 7 }, cabeca), 'fill', corpoCor);
    const recorteK = el('path', { d: `M ${-m.cab * 0.75} ${-m.cab * 0.55} A ${m.cab * 0.92} ${m.cab * 0.92} 0 0 1 ${m.cab * 0.55} ${-m.cab * 0.72}`, fill: 'none', 'stroke-width': 6, 'stroke-linecap': 'round', opacity: 0 }, cabeca);
    const fc = f.focinho || (f.mancha || mix(corpoCor, '#ffffff', 0.15));
    const queixo = el('g', {}, cabeca); // a mandíbula, que abre no latido
    pinta(el('path', { d: f.tipo === 'gato' ? `M ${m.cab * 0.3} ${m.cab * 0.3} Q ${m.cab * 0.9} ${m.cab * 0.5} ${m.cab * 1.05} ${m.cab * 0.32} L ${m.cab * 0.4} ${m.cab * 0.15} Z` : `M ${m.cab * 0.2} ${m.cab * 0.35} L ${m.cab * 0.3 + m.focinho} ${m.cab * 0.45} Q ${m.cab * 0.45 + m.focinho} ${m.cab * 0.3} ${m.cab * 0.3 + m.focinho} ${m.cab * 0.18} L ${m.cab * 0.3} ${m.cab * 0.1} Z`, fill: fc, stroke: TINTA, 'stroke-width': 6, 'stroke-linejoin': 'round' }, queixo), 'fill', fc);
    const boca = el('path', { fill: '#3a141c', stroke: TINTA, 'stroke-width': 5, 'stroke-linejoin': 'round', opacity: 0 }, cabeca);
    const lingua = el('ellipse', { cx: m.cab * 0.75, cy: m.cab * 0.42, rx: m.cab * 0.32, ry: m.cab * 0.12, fill: '#d9606e', stroke: TINTA, 'stroke-width': 4, opacity: 0 }, cabeca);
    cabeca.insertBefore(boca, queixo); cabeca.insertBefore(lingua, queixo); // o vão e a língua atrás da mandíbula
    // focinho de cima
    pinta(el('path', { d: f.tipo === 'gato' ? `M ${m.cab * 0.55} ${-m.cab * 0.1} Q ${m.cab * 1.25} ${0} ${m.cab * 1.05} ${m.cab * 0.32} L ${m.cab * 0.35} ${m.cab * 0.3} Z` : `M ${m.cab * 0.45} ${-m.cab * 0.3} L ${m.cab * 0.3 + m.focinho} ${-m.cab * 0.12} Q ${m.cab * 0.5 + m.focinho} ${m.cab * 0.05} ${m.cab * 0.32 + m.focinho} ${m.cab * 0.24} L ${m.cab * 0.3} ${m.cab * 0.3} Z`, fill: fc, stroke: TINTA, 'stroke-width': 6, 'stroke-linejoin': 'round' }, cabeca), 'fill', fc);
    el('ellipse', { cx: f.tipo === 'gato' ? m.cab * 1.04 : m.cab * 0.36 + m.focinho, cy: f.tipo === 'gato' ? m.cab * 0.05 : -m.cab * 0.08, rx: f.tipo === 'gato' ? 7 : 13, ry: f.tipo === 'gato' ? 6 : 10, fill: '#1c1418' }, cabeca); // nariz
    if (f.tipo === 'gato') for (const dy of [-6, 6]) el('path', { d: `M ${m.cab * 0.95} ${m.cab * 0.18 + dy} L ${m.cab * 1.6} ${m.cab * 0.1 + dy * 2.2}`, stroke: '#e8e2d6', 'stroke-width': 2.5, opacity: 0.8 }, cabeca);
    // olho: o mesmo do boneco (círculo branco, pupila preta)
    const olho = el('g', { transform: `translate(${m.cab * 0.3} ${-m.cab * 0.25})` }, cabeca);
    const branco = el('circle', { r: m.cab * 0.26, fill: '#f8f4ec', stroke: TINTA, 'stroke-width': 5 }, olho);
    const pupila = el('circle', { r: m.cab * 0.15, fill: '#111' }, olho);
    const idOlho = (parent.ownerSVGElement.id || 'sa') + '-bo' + (++seqOlho);
    el('circle', { r: m.cab * 0.26 }, el('clipPath', { id: idOlho }, parent.ownerSVGElement.querySelector('defs')));
    const palpebra = pinta(el('rect', { x: -m.cab * 0.3, y: -m.cab * 0.3, width: m.cab * 0.6, height: 0, fill: corpoCor, 'clip-path': `url(#${idOlho})` }, olho), 'fill', corpoCor);
    el('circle', { r: m.cab * 0.26, fill: 'none', stroke: TINTA, 'stroke-width': 5 }, olho); // o contorno por cima da pálpebra
    // orelha
    const orelha = el('g', { transform: `translate(${-m.cab * 0.35} ${-m.cab * 0.7})` }, cabeca);
    const orelhaD = f.orelha === 'caida' ? `M 0 0 Q ${-m.cab * 0.75} ${m.cab * 0.2} ${-m.cab * 0.55} ${m.cab * 1.15} Q ${-m.cab * 0.1} ${m.cab * 1.0} ${m.cab * 0.25} ${m.cab * 0.25} Z`
      : `M ${-m.cab * 0.25} ${m.cab * 0.2} L ${-m.cab * 0.1} ${-m.cab * 0.75} L ${m.cab * 0.45} ${m.cab * 0.15} Z`;
    pinta(el('path', { d: orelhaD, fill: f.orelha === 'caida' ? S(corpoCor) : corpoCor, stroke: TINTA, 'stroke-width': 6, 'stroke-linejoin': 'round' }, orelha), 'fill', f.orelha === 'caida' ? S(corpoCor) : corpoCor);
    raiz.dados = { lingua, anca, recorteC, recorteK, f, m, ting, pernas: Object.assign(pernas, pernasPerto), rabo: [raboT, raboC], tronco, pesc, col, cabeca, queixo, boca, olho, pupila, palpebra, orelha };
    return raiz;
  }

  // dois segmentos do ponto S até o alvo T; o joelho dobra para trás (-x)
  function ik(S, T, l1, l2) {
    let dx = T[0] - S[0], dy = T[1] - S[1], d = Math.hypot(dx, dy);
    const dm = Math.min(d, l1 + l2 - 0.5); if (d > dm) { dx *= dm / d; dy *= dm / d; d = dm; }
    const a = Math.atan2(dy, dx), c = clamp((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d), -1, 1);
    const ang = a + Math.acos(c); // dobra para trás em quem olha para a direita
    return { J: [S[0] + Math.cos(ang) * l1, S[1] + Math.sin(ang) * l1], T: [S[0] + dx, S[1] + dy] };
  }
  const capsula = (A, B, w1, w2) => {
    const ang = Math.atan2(B[1] - A[1], B[0] - A[0]), nx = -Math.sin(ang), ny = Math.cos(ang);
    return `M ${A[0] + nx * w1 / 2} ${A[1] + ny * w1 / 2} L ${B[0] + nx * w2 / 2} ${B[1] + ny * w2 / 2} A ${w2 / 2} ${w2 / 2} 0 0 0 ${B[0] - nx * w2 / 2} ${B[1] - ny * w2 / 2} L ${A[0] - nx * w1 / 2} ${A[1] - ny * w1 / 2} A ${w1 / 2} ${w1 / 2} 0 0 0 ${A[0] + nx * w1 / 2} ${A[1] + ny * w1 / 2} Z`;
  };

  // p: x, y (o chão), esc, vira, ph e amp (o andar), corpo (inclina, graus), sentado 0..1, deitado 0..1, cabeca (graus, + abaixa),
  //    boca 0..1 (o latido), rabo (graus, + para cima), abana (graus de balanço), orelha (graus), achata (como no boneco)
  // F: olhaX (-1..1), pisca 0..1, medo 0..1
  function posar(raiz, p, F = {}, luz = {}, amb = '#ffffff') {
    const { lingua, anca, recorteC, recorteK, f, m, ting, pernas, rabo, tronco, pesc, col, cabeca, queixo, boca, pupila, palpebra, orelha } = raiz.dados;
    for (const [e, at, c] of ting) e.setAttribute(at, mul(c, amb));
    const ach = (p.achata || 0) * 0.12, esc = p.esc || 1, vira = p.vira ?? 1;
    raiz.setAttribute('transform', `translate(${p.x || 0} ${p.y || 0}) scale(${esc * vira * (1 + ach)} ${esc * (1 - ach)})`);
    const ph = p.ph || 0, amp = p.amp || 0, sent = clamp(p.sentado || 0), deit = clamp(p.deitado || 0);
    // o tronco: sentado, gira em volta do quadril e o quadril desce; deitado, tudo desce
    const bob = Math.abs(Math.sin(2 * ph)) * 6 * amp;
    const giro = (-(p.corpo || 0) - 26 * sent) * Math.PI / 180, Q = m.quadril;
    const desce = sent * (Q[1] * -0.55) + deit * (-m.cy - m.ry - 6) - bob;
    const T = ([x, y]) => { const dx = x - Q[0], dy = y - Q[1]; return [Q[0] + dx * Math.cos(giro) - dy * Math.sin(giro), Q[1] + dx * Math.sin(giro) + dy * Math.cos(giro) + desce]; };
    tronco.setAttribute('transform', `translate(0 ${desce}) rotate(${giro * 180 / Math.PI} ${Q[0]} ${Q[1]})`);
    const ombro = T(m.ombro), quadril = T(Q);
    anca.setAttribute('cx', quadril[0] + m.coxa * 0.25); anca.setAttribute('cy', quadril[1] + m.coxa * 0.15); anca.setAttribute('opacity', sent);
    const forca = luz.forca ?? 0.7, rc = luz.recorte || '#ffe7c4';
    for (const r of [recorteC, recorteK]) { r.setAttribute('stroke', rc); r.setAttribute('opacity', 0.55 * forca); }
    recorteC.setAttribute('d', `M ${-m.rx * 0.62} ${m.cy - m.ry * 0.62} Q 0 ${m.cy - m.ry * 0.9} ${m.rx * 0.58} ${m.cy - m.ry * 0.64}`); // por dentro do contorno
    // as patas: no chão, ou dobradas quando senta e deita
    const stride = (m.coxa + m.canela) * 0.55, lift = (m.coxa + m.canela) * 0.18;
    const passo = off => ({ dx: stride / 2 * Math.sin(ph + off) * amp, up: Math.max(0, Math.cos(ph + off)) * lift * amp });
    const alvo = (base, off, traseira) => {
      const s = passo(off);
      let x = base[0] + s.dx, y = -s.up;
      if (traseira) { x = lerp(x, base[0] + 75, sent); x = lerp(x, base[0] + 70, deit); }
      else { x = lerp(x, base[0] + 10, sent); x = lerp(x, base[0] + 90, deit); }
      return [x, y];
    };
    const desenhaPerna = (pp, S0, Tg) => {
      const r = ik(S0, Tg, m.coxa, m.canela);
      pp.a.setAttribute('d', capsula(S0, r.J, m.w * 1.7, m.w * 0.95));
      pp.b.setAttribute('d', capsula(r.J, r.T, m.w * 0.9, m.w * 0.75));
      pp.pata.setAttribute('cx', r.T[0] + m.w * 0.25); pp.pata.setAttribute('cy', r.T[1] - m.w * 0.15);
    };
    // trote: as patas em diagonal andam juntas
    desenhaPerna(pernas.dl, ombro, alvo([m.ombro[0] - 14, 0], Math.PI, false));
    desenhaPerna(pernas.tl, quadril, alvo([Q[0] + 14, 0], 0, true));
    desenhaPerna(pernas.dp, ombro, alvo([m.ombro[0], 0], 0, false));
    desenhaPerna(pernas.tp, quadril, alvo([Q[0], 0], Math.PI, true));
    // rabo
    const base = T([-m.rx * 0.95, m.cy - m.ry * 0.35]), angR = ((p.rabo ?? 20) + (p.abana || 0)) * Math.PI / 180;
    const L = f.rabo === 'curto' ? 45 : f.tipo === 'gato' ? 150 : 95;
    const ponta = [base[0] - Math.cos(angR) * L, base[1] - Math.sin(angR) * L];
    const meio = [base[0] - Math.cos(angR + 0.5) * L * 0.6, base[1] - Math.sin(angR + 0.5) * L * 0.6 - (f.tipo === 'gato' ? 20 : 0)];
    for (const r of rabo) r.setAttribute('d', `M ${base[0]} ${base[1]} Q ${meio[0]} ${meio[1]} ${ponta[0]} ${ponta[1]}`);
    // pescoço e cabeça
    const pB = T(m.pescoco), cA = (p.cabeca || 0);
    const cab = T(m.cabeca), cabeAng = cA + (p.corpo || 0) * -0.3;
    // sentado, o tronco sobe e o pescoço esticaria: a cabeça desce um pouco para perto do peito
    const cx = cab[0] + Math.sin(cA * Math.PI / 180) * 6 - sent * 18, cy = cab[1] + cA * 0.8 * (deit ? 0.4 : 1) + sent * 34;
    pesc.setAttribute('d', capsula(pB, [cx - m.cab * 0.3, cy + m.cab * 0.2], m.ry * 1.25, m.cab * 1.1));
    if (col) col.setAttribute('d', `M ${lerp(pB[0], cx, 0.45) - m.cab * 0.5} ${lerp(pB[1], cy, 0.45) - m.cab * 0.2} Q ${lerp(pB[0], cx, 0.45)} ${lerp(pB[1], cy, 0.45) + m.cab * 0.45} ${lerp(pB[0], cx, 0.45) + m.cab * 0.55} ${lerp(pB[1], cy, 0.45) + m.cab * 0.1}`);
    cabeca.setAttribute('transform', `translate(${cx} ${cy}) rotate(${cabeAng})`);
    const ab = clamp(p.boca || 0);
    const giroQ = ab * 38, rq = giroQ * Math.PI / 180, comp = f.tipo === 'gato' ? m.cab * 0.75 : m.focinho + m.cab * 0.05;
    queixo.setAttribute('transform', `rotate(${giroQ} ${m.cab * 0.25} ${m.cab * 0.2})`);
    boca.setAttribute('opacity', ab > 0.05 ? 1 : 0);
    // o vão entre o focinho de cima e a mandíbula que desceu: escuro, com a língua no fundo
    const px = m.cab * 0.25 + comp * Math.cos(rq), py = m.cab * 0.2 + comp * Math.sin(rq);
    boca.setAttribute('d', `M ${m.cab * 0.25} ${m.cab * 0.2} L ${m.cab * 0.3 + comp} ${m.cab * 0.24} L ${px} ${py} Z`);
    lingua.setAttribute('opacity', ab > 0.3 ? 1 : 0);
    lingua.setAttribute('transform', `rotate(${giroQ * 0.8} ${m.cab * 0.25} ${m.cab * 0.2})`);
    const medo = F.medo || 0; // com medo, a orelha vai para trás e a pupila encolhe
    orelha.setAttribute('transform', `translate(${-m.cab * 0.35} ${-m.cab * 0.7}) rotate(${(p.orelha || 0) - 25 * medo})`);
    pupila.setAttribute('cx', (F.olhaX ?? 0.4) * m.cab * 0.1); pupila.setAttribute('r', m.cab * 0.15 * (1 - medo * 0.35));
    palpebra.setAttribute('height', clamp(F.pisca || 0) * m.cab * 0.6);
  }

  // latido(t, picos, de): a abertura da boca no tempo t, com cada latido começando num dos picos (em s, contados de "de").
  // Os picos saem de "python .ferramenta/sistema/editar.py picos latido.wav"; "de" é quando o som começa no vídeo. Use em "boca" e no "achata".
  function latido(t, picos, de = 0) {
    let v = 0;
    for (const p of picos) { const d = t - de - p; if (d >= -0.03 && d < 0.32) v = Math.max(v, d < 0.05 ? (d + 0.03) / 0.08 : Math.exp(-(d - 0.05) * 9)); }
    return Math.min(1, v);
  }
  // escala(altPorta, ficha): o esc para o bicho ficar do tamanho certo ao lado de uma porta (a pessoa tem 83% da porta)
  window.Bicho = { latido, cachorro, gato, criar, posar, escala: (altPorta, f) => 0.83 * altPorta * f.altura / M(f).cernelha, passada, medidas: M };
})();
