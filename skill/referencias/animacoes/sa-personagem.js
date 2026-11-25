// Série Animada: o boneco articulado em SVG, com acabamento de nanquim. Entra no <script> da cena com <!--#inclui sa-personagem.js-->.
// Duas vistas: PERFIL (padrão, olhando para a direita; vira: -1 espelha) e FRENTE (simétrica, para quando a pessoa olha para a câmera).
// Cada peça (tronco, cabeça, braço, antebraço, coxa, canela) gira na articulação. Uma pose é uma lista de ângulos,
// ou a mão (ou o pé) num ponto, e o cotovelo (ou o joelho) se resolve sozinho.
// Acabamento em toda peça: contorno de nanquim, sombra em dois tons do lado oposto à luz e luz de recorte do lado da luz.
// Aqui não há personagem pronto: os da história são criados para ela, com Boneco.pessoa({...}) e uma marca forte cada um.
(function () {
  const NS = 'http://www.w3.org/2000/svg';
  const TINTA = '#17121c';
  let seq = 0;

  // ---------- cores ----------
  function hex2rgb(h) { h = h.replace('#', ''); return [0, 2, 4].map(i => parseInt(h.substr(i, 2), 16)); }
  function rgb2hex(c) { return '#' + c.map(v => Math.max(0, Math.min(255, Math.round(v))).toString(16).padStart(2, '0')).join(''); }
  function mix(a, b, k) { const A = hex2rgb(a), B = hex2rgb(b); return rgb2hex(A.map((v, i) => v + (B[i] - v) * k)); }
  function mul(a, b) { const A = hex2rgb(a), B = hex2rgb(b); return rgb2hex(A.map((v, i) => v * B[i] / 255)); }
  const sombraDe = c => mix(c, '#1a1424', 0.3); // o segundo tom, quando a pessoa não diz qual

  function el(tag, attrs, parent) {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }
  // id único por desenho: duas cenas no mesmo vídeo não dividem clipPath
  const novoId = (svg, letra) => (svg.id || 'sa') + '-' + letra + (++seq);

  // ---------- formas ----------
  function capsula(len, w1, w2) {
    const a = w1 / 2, b = w2 / 2;
    return `M ${-a} 0 A ${a} ${a} 0 0 1 ${a} 0 L ${b} ${len} A ${b} ${b} 0 0 1 ${-b} ${len} Z`;
  }
  // tronco: do quadril (y=0) ao pescoço (y=-alt); a frente é o lado +x
  function tronco(alt, largCima, largBaixo, barriga) {
    const t = largCima / 2, b = largBaixo / 2, r = Math.min(40, t * 0.7), bz = barriga || 0;
    return `M ${-b} 6 L ${-t} ${-alt + r} Q ${-t} ${-alt} ${-t + r} ${-alt} L ${t - r} ${-alt} Q ${t} ${-alt} ${t} ${-alt + r} C ${t + bz} ${-alt * 0.55} ${b + bz} ${-alt * 0.25} ${b} 6 Q ${b} 26 ${b - 24} 26 L ${-b + 24} 26 Q ${-b} 26 ${-b} 6 Z`;
  }
  function circulo(r, cx = 0, cy = 0) { return `M ${cx + r} ${cy} A ${r} ${r} 0 1 0 ${cx - r} ${cy} A ${r} ${r} 0 1 0 ${cx + r} ${cy} Z`; }

  // ---------- peça com acabamento ----------
  function peca(parent, d, cor, sombra, opts = {}) {
    const svg = parent.ownerSVGElement, defs = svg.querySelector('defs');
    const id = novoId(svg, 'p');
    const clip = el('clipPath', { id: id + 'c' }, defs);
    el('path', { d }, clip);
    const lit = el('clipPath', { id: id + 'l' }, defs);
    const litRect = el('rect', { x: -2000, y: -4000, width: 2000, height: 8000 }, lit);
    const g = el('g', {}, parent);
    const base = el('path', { d, fill: cor }, g);
    const gs = el('g', { 'clip-path': `url(#${id}c)` }, g);
    const esfera = opts.esfera;
    const sh = esfera
      ? el('path', { d: `M -4000 -4000 H 4000 V 4000 H -4000 Z ${circulo(esfera * 1.08)}`, 'fill-rule': 'evenodd', fill: sombra }, gs)
      : el('rect', { x: 0, y: -4000, width: 4000, height: 8000, fill: sombra }, gs);
    const extra = el('g', { 'clip-path': opts.solto ? '' : `url(#${id}c)` }, g); // estampa, listras: presas dentro da peça
    const gr = el('g', { 'clip-path': `url(#${id}c)` }, g);
    const gr2 = el('g', { 'clip-path': `url(#${id}l)` }, gr);
    const rim = el('path', { d, fill: 'none', stroke: '#fff', 'stroke-width': 13, 'stroke-linejoin': 'round', opacity: 0 }, gr2);
    const linha = el('path', { d, fill: 'none', stroke: TINTA, 'stroke-width': opts.linha || 7, 'stroke-linejoin': 'round' }, g);
    const fora = el('g', {}, g); // detalhes que passam da borda (gola, chinelo, curativo)
    return { g, base, sh, rim, litRect, extra, fora, linha, cor, sombra, cx: opts.cx || 0, cy: opts.cy || 0, w: opts.w, esfera };
  }

  // a sombra fica do lado oposto à luz, e a luz de recorte do lado dela; ambiente é a cor da luz da cena (tinge tudo)
  function sombrear(p, anguloMundo, luz, ambiente) {
    const rel = luz.ang - anguloMundo;
    const rad = rel * Math.PI / 180, lx = Math.cos(rad), ly = Math.sin(rad);
    if (p.esfera) {
      const k = p.esfera * 0.42;
      p.sh.setAttribute('transform', `translate(${p.cx + lx * k} ${p.cy + ly * k})`);
      p.litRect.setAttribute('transform', `translate(${p.cx} ${p.cy}) rotate(${rel + 180}) translate(-8 0)`);
    } else {
      const lado = lx >= 0 ? 1 : -1;
      const larg = (p.w || 60) * (0.5 - 0.3 * Math.min(1, Math.abs(lx) + 0.3));
      p.sh.setAttribute('transform', `translate(${p.cx - lado * larg} 0) rotate(${lado > 0 ? 180 : 0})`);
      p.litRect.setAttribute('transform', `translate(${p.cx + lado * ((p.w || 60) * 0.5 - 9)} 0) rotate(${lado > 0 ? 180 : 0})`);
    }
    p.base.setAttribute('fill', mul(p.cor, ambiente));
    p.sh.setAttribute('fill', mul(p.sombra, ambiente));
    p.rim.setAttribute('stroke', luz.recorte || '#ffd9a0');
    p.rim.setAttribute('opacity', (luz.forca ?? 0.9) * 0.85);
  }

  // ---------- rosto ----------
  // Olho simples: círculo branco com contorno grosso e pupila preta grande. Sem íris, sem cílio.
  function olho(g, P) {
    const og = el('g', {}, g);
    const svg = g.ownerSVGElement, id = novoId(svg, 'o');
    el('ellipse', { rx: 17, ry: 20 }, el('clipPath', { id }, svg.querySelector('defs')));
    const branco = el('ellipse', { rx: 17, ry: 20, fill: '#f8f4ec' }, og);
    const gi = el('g', { 'clip-path': `url(#${id})` }, og);
    const pupila = el('circle', { r: 8.5, fill: TINTA }, gi);
    const brilho = el('circle', { r: 2.8, fill: '#fff' }, gi);
    const palp = el('rect', { x: -30, y: -60, width: 60, height: 0, fill: P.pele }, gi);
    el('ellipse', { rx: 17, ry: 20, fill: 'none', stroke: TINTA, 'stroke-width': 5.5 }, og);
    const linhaPalp = el('path', { d: '', fill: 'none', stroke: TINTA, 'stroke-width': 5.5, 'stroke-linecap': 'round' }, og);
    const sobr = el('path', { d: '', fill: 'none', stroke: P.sobrancelha || TINTA, 'stroke-width': 7, 'stroke-linecap': 'round' }, g);
    return { og, pupila, brilho, palp, linhaPalp, sobr, branco };
  }

  function rosto(parent, r, P) {
    const g = el('g', {}, parent);
    const olhos = [olho(g, P), olho(g, P)];
    const bochecha = [0, 1].map(() => el('ellipse', { rx: 14, ry: 8, fill: '#d9614f', opacity: 0.2 }, g));
    const nariz = el('path', { d: '', fill: 'none', stroke: TINTA, 'stroke-width': 5, 'stroke-linecap': 'round' }, g);
    const boca = el('path', { d: '', fill: '#4d1820', stroke: TINTA, 'stroke-width': 5, 'stroke-linejoin': 'round', 'stroke-linecap': 'round' }, g);
    return { g, olhos, bochecha, nariz, boca, r };
  }

  // F = {olhaX, olhaY, pisca 0..1, desconfia 0..1, medo 0..1, bravo 0..1, boca 0..1, sorriso -1..1}
  // De perfil: um olho só, nariz e boca na frente da cabeça. De frente: dois olhos, tudo simétrico.
  function desenhaRosto(R, F, P, ambiente, frente) {
    const r = R.r, medo = F.medo ?? 0, bravo = F.bravo ?? 0;
    const pele = mul(P.pele, ambiente);
    const pos = frente ? [[-r * 0.36, -r * 0.06], [r * 0.36, -r * 0.06]] : [[r * 0.46, -r * 0.08]];
    R.olhos.forEach((o, i) => {
      if (!pos[i]) { o.og.setAttribute('opacity', 0); o.sobr.setAttribute('opacity', 0); return; }
      o.og.setAttribute('opacity', 1); o.sobr.setAttribute('opacity', 1);
      const [x, y] = pos[i];
      const k = 1 + medo * 0.15;
      o.og.setAttribute('transform', `translate(${x} ${y}) scale(${k})`);
      o.branco.setAttribute('fill', mul('#f8f4ec', mix(ambiente, '#ffffff', 0.55)));
      const ox = Math.max(-1, Math.min(1, F.olhaX ?? (frente ? 0 : 0.55))) * 8, oy = Math.max(-1, Math.min(1, F.olhaY ?? 0)) * 10;
      const pr = 8.5 * (1 - medo * 0.35); // com medo, a pupila encolhe
      o.pupila.setAttribute('cx', ox); o.pupila.setAttribute('cy', oy); o.pupila.setAttribute('r', pr);
      o.brilho.setAttribute('cx', ox + 2.5); o.brilho.setAttribute('cy', oy - 3); o.brilho.setAttribute('r', pr * 0.33);
      // pálpebra: só aparece quando fecha (piscar, desconfiança, raiva)
      const fech = Math.max(F.pisca ?? 0, F.desconfia ?? 0, bravo * 0.35) * (1 - medo);
      const yb = -20 + fech * 40;
      o.palp.setAttribute('height', yb + 60); o.palp.setAttribute('fill', pele);
      o.linhaPalp.setAttribute('d', fech > 0.04 ? `M -19 ${yb} L 19 ${yb}` : '');
      // sobrancelha reta e grossa: o medo levanta o lado de dentro; a raiva abaixa
      const dentro = frente ? (i === 0 ? 1 : -1) : -1;
      const by = y - 30 - medo * 10 + bravo * 3;
      const ini = -medo * 12 + bravo * 10, fim = medo * 2 - bravo * 4;
      const xi = x + dentro * 12, xf = x - dentro * 18;
      o.sobr.setAttribute('d', `M ${xi} ${by + ini} L ${xf} ${by + fim}`);
      o.sobr.setAttribute('stroke', mul(P.sobrancelha || TINTA, ambiente));
    });
    const bpos = frente ? [[-r * 0.55, r * 0.28], [r * 0.55, r * 0.28]] : [[r * 0.4, r * 0.3]];
    R.bochecha.forEach((b, i) => {
      if (!bpos[i]) { b.setAttribute('opacity', 0); return; }
      b.setAttribute('cx', bpos[i][0]); b.setAttribute('cy', bpos[i][1]); b.setAttribute('opacity', P.semBochecha ? 0 : 0.18);
    });
    if (frente) R.nariz.setAttribute('d', `M ${-4} ${r * 0.14} Q ${6} ${r * 0.24} ${-2} ${r * 0.3}`);
    else R.nariz.setAttribute('d', `M ${r * 0.84} ${r * 0.08} Q ${r * 0.98} ${r * 0.22} ${r * 0.82} ${r * 0.28}`);
    // boca: traço fechado; aberta vira uma forma escura
    const b = Math.max(0, Math.min(1, F.boca ?? 0)), s = F.sorriso ?? 0;
    const [mx, my, w] = frente ? [0, r * 0.52, 30] : [r * 0.7, r * 0.52, 26];
    if (b < 0.05) {
      R.boca.setAttribute('d', frente
        ? `M ${mx - w / 2} ${my - s * 5 + medo * 3} Q ${mx} ${my + s * 8 - medo * 4} ${mx + w / 2} ${my - s * 5 + medo * 3}`
        : `M ${mx - w / 2} ${my + s * 2} Q ${mx} ${my + s * 7 - medo * 3} ${mx + w / 2} ${my - s * 5}`);
      R.boca.setAttribute('fill', 'none');
    } else {
      const h = 6 + b * 26;
      R.boca.setAttribute('d', `M ${mx - w / 2} ${my - s * 3} Q ${mx} ${my - 6} ${mx + w / 2} ${my - s * 4} Q ${mx + w / 2 - 2} ${my + h} ${mx} ${my + h} Q ${mx - w / 2 + 2} ${my + h} ${mx - w / 2} ${my - s * 3} Z`);
      R.boca.setAttribute('fill', mul('#4d1820', ambiente));
    }
  }

  // ---------- montagem do boneco ----------
  // pose: x, y, esc, vira, frente, tronco, cabeca, achata (comprimir e esticar), quadrilY, bracoF/bracoT/pernaF/pernaT
  // P: pele, peleSombra, camisa, camisaSombra, calca, calcaSombra, sapato, sapatoSombra, manga, antebraco, canela (e as sombras),
  // sobrancelha, escala, medidas, barriga, detalhes(ctx) (cabelo, roupa, marca), atualiza(ctx) (o que muda com a vista ou a pose)
  function criar(svg, P) {
    const raiz = el('g', {}, svg);
    const corpo = el('g', {}, raiz);
    const E = P.escala || 1;
    const M = Object.assign({ tronco: 300, ombro: 170, prof: 118, cintura: 116, braco: 150, ante: 138, coxa: 196, canela: 190, cabeca: 100, pescoco: 34, wb: 50, wa: 44, wc: 66, wk: 54 }, P.medidas || {});
    const S = k => P[k + 'Sombra'] || sombraDe(P[k] || '#888888');
    const pecas = {};
    function membro(nome, len1, len2, w1, w2, cor1, sombra1, cor2, sombra2, mao, maoCor, maoSombra, pe) {
      const g1 = el('g', {}, corpo);
      const p1 = peca(g1, capsula(len1, w1, w1 * 0.92), cor1, sombra1, { cy: len1 / 2, w: w1 });
      const g2 = el('g', {}, g1);
      const p2 = peca(g2, capsula(len2, w2, w2 * 0.84), cor2, sombra2, { cy: len2 / 2, w: w2 });
      let p3 = null;
      if (mao) p3 = peca(g2, circulo(w2 * 0.6, 0, len2 + 4), maoCor, maoSombra, { cy: len2 + 4, w: w2 * 1.2, esfera: w2 * 0.6 });
      if (pe) p3 = peca(g2, `M ${-w2 * 0.55} ${len2 - 16} L ${w2 * 0.5} ${len2 - 16} Q ${w2 * 2.0} ${len2 - 10} ${w2 * 2.05} ${len2 + 12} Q ${w2 * 2.0} ${len2 + 20} ${w2 * 1.8} ${len2 + 20} L ${-w2 * 0.62} ${len2 + 20} Q ${-w2 * 0.76} ${len2} ${-w2 * 0.55} ${len2 - 16} Z`, pe.cor, pe.sombra, { cy: len2 + 6, w: w2 * 2, solto: true });
      const prop = mao ? el('g', { transform: `translate(0 ${len2})` }, g2) : null; // o que a mão segura (celular, vela)
      pecas[nome] = { g1, g2, p1, p2, p3, prop, len1, len2 };
      return pecas[nome];
    }
    const pele = P.pele, peleS = S('pele');
    const manga = P.manga || P.camisa, mangaS = P.manga ? S('manga') : S('camisa');
    const ante = P.antebraco || pele, anteS = P.antebraco ? S('antebraco') : peleS;
    const canela = P.canela || P.calca, canelaS = P.canela ? S('canela') : S('calca');
    const sapato = { cor: P.sapato || '#2a2630', sombra: S('sapato') };
    // ordem: braço de trás, perna de trás, tronco, perna da frente, pescoço e cabeça, braço da frente
    membro('bracoT', M.braco, M.ante, M.wb, M.wa, manga, mangaS, ante, anteS, true, pele, peleS);
    membro('pernaT', M.coxa, M.canela, M.wc, M.wk, P.calca, S('calca'), canela, canelaS, false, null, null, sapato);
    const gT = el('g', {}, corpo);
    const atrasTronco = el('g', {}, gT); // capuz, mochila
    const pt = peca(gT, tronco(M.tronco, M.prof, M.cintura * 0.92, P.barriga || 0), P.camisa, S('camisa'), { cy: -M.tronco / 2, w: M.prof });
    const ptF = peca(gT, tronco(M.tronco, M.ombro, M.cintura), P.camisa, S('camisa'), { cy: -M.tronco / 2, w: M.ombro });
    pecas.tronco = { g1: gT, p1: pt, pF: ptF, atras: atrasTronco };
    membro('pernaF', M.coxa, M.canela, M.wc, M.wk, P.calca, S('calca'), canela, canelaS, false, null, null, sapato);
    const gPesc = el('g', {}, corpo);
    const pesc = peca(gPesc, capsula(M.pescoco + 24, 44, 50), pele, peleS, { cy: 20, w: 46 });
    const gCab = el('g', {}, gPesc);
    const atrasCabelo = el('g', {}, gCab);
    const pc = peca(gCab, circulo(M.cabeca), pele, peleS, { w: M.cabeca * 2, esfera: M.cabeca });
    const R = rosto(gCab, M.cabeca, P);
    const frente = el('g', {}, gCab); // cabelo, óculos, barba, chapéu
    const pescFrente = el('g', {}, gPesc); // gola, cordão, fone no pescoço
    pecas.cabeca = { g1: gPesc, g2: gCab, p1: pesc, p2: pc, R, atrasCabelo, frente, pescFrente };
    membro('bracoF', M.braco, M.ante, M.wb, M.wa, manga, mangaS, ante, anteS, true, pele, peleS);
    pecas.pares = [];
    if (P.detalhes) P.detalhes({ el, pecas, M, P, TINTA, mix, mul, circulo, cabelo, par, CABELOS });
    // toda cor de detalhe (cabelo, estampa, acessório) recebe a luz da cena em cada pose
    const tingiveis = [];
    raiz.querySelectorAll('*').forEach(e => {
      for (const at of ['fill', 'stroke']) {
        const v = e.getAttribute(at);
        if (v && /^#[0-9a-f]{6}$/i.test(v) && v.toLowerCase() !== TINTA) tingiveis.push([e, at, v]);
      }
    });
    raiz.dados = { pecas, M, P, E, corpo, tingiveis };
    return raiz;
  }

  // dois ossos: do ombro (sx,sy) até o alvo (tx,ty). Devolve {a,b} (0 = para baixo; positivo gira no sentido do relógio).
  function ik(l1, l2, sx, sy, tx, ty, dobra, base) {
    const dx = tx - sx, dy = ty - sy;
    const d = Math.max(1, Math.min(l1 + l2 - 0.5, Math.hypot(dx, dy)));
    const phiT = Math.atan2(dy, dx);
    const alfa = Math.acos(Math.max(-1, Math.min(1, (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d))));
    const phi1 = phiT + dobra * alfa;
    const ex = sx + Math.cos(phi1) * l1, ey = sy + Math.sin(phi1) * l1;
    const phi2 = Math.atan2(ty - ey, tx - ex);
    const g = 180 / Math.PI;
    return { a: phi1 * g - 90 - base, b: (phi2 - phi1) * g };
  }

  // pose: {x, y (o quadril), esc, vira (1 direita, -1 esquerda), frente, quadrilY, tronco, cabeca,
  //        bracoF/bracoT {a, b, punho} ou {mao: [x, y], dobra}, pernaF/pernaT {a, b, pe} ou {mao: [x, y], dobra}}
  // F: o rosto (ver desenhaRosto). luz: {ang, recorte, forca}. ambiente: a cor da luz da cena.
  function posar(raiz, pose, F, luz, ambiente) {
    const { pecas, M, P, E, corpo, tingiveis } = raiz.dados;
    F = F || {};
    ambiente = ambiente || '#ffffff';
    for (const [e, at, v] of tingiveis) e.setAttribute(at, mul(v, ambiente));
    const vira = pose.vira ?? 1, frente = !!pose.frente;
    // achata: comprimir (+) e esticar (-) o corpo todo, com os pés no mesmo chão. 1 = 12% mais baixo e mais largo.
    // Para o susto (estica), o pouso, o peso que se levanta e o passo. O volume fica: o que perde em altura ganha em largura.
    const ach = (pose.achata || 0) * 0.12, pernas = (M.coxa + M.canela + 20) * (pose.esc || 1) * E;
    const sx = (pose.esc || 1) * E * vira * (1 + ach), sy = (pose.esc || 1) * E * (1 - ach);
    raiz.setAttribute('transform', `translate(${pose.x || 0} ${(pose.y || 0) + pernas * ach}) scale(${sx} ${sy})`);
    const L = Object.assign({}, luz, { ang: vira > 0 ? luz.ang : 180 - luz.ang });
    const aT = pose.tronco || 0;
    corpo.setAttribute('transform', `translate(0 ${pose.quadrilY || 0})`);
    // de perfil o tronco é estreito (profundidade); de frente é largo (ombros)
    pecas.tronco.p1.g.setAttribute('display', frente ? 'none' : '');
    pecas.tronco.pF.g.setAttribute('display', frente ? '' : 'none');
    pecas.tronco.g1.setAttribute('transform', `rotate(${aT})`);
    sombrear(frente ? pecas.tronco.pF : pecas.tronco.p1, aT, L, ambiente);
    const rot = (x, y, a) => { const r = a * Math.PI / 180; return [x * Math.cos(r) - y * Math.sin(r), x * Math.sin(r) + y * Math.cos(r)]; };
    const ombroY = -M.tronco + 30;
    // braços e pernas presos no mesmo ponto do corpo, de perfil
    const enc = {
      bracoT: frente ? [-M.ombro * 0.4, ombroY] : [-6, ombroY],
      bracoF: frente ? [M.ombro * 0.4, ombroY] : [6, ombroY],
      pernaT: frente ? [-M.cintura * 0.24, 0] : [-8, 0],
      pernaF: frente ? [M.cintura * 0.24, 0] : [8, 0],
    };
    for (const nome of ['bracoT', 'bracoF', 'pernaT', 'pernaF']) {
      const m = pecas[nome], q = Object.assign({ a: 0, b: 0 }, pose[nome] || {});
      const ehBraco = nome.startsWith('braco');
      let [x, y] = enc[nome], base = 0;
      if (ehBraco) { [x, y] = rot(x, y, aT); base = aT; }
      if (q.mao) Object.assign(q, ik(m.len1, m.len2, x, y, q.mao[0], q.mao[1], q.dobra ?? (ehBraco ? 1 : -1), base));
      m.g1.setAttribute('transform', `translate(${x} ${y}) rotate(${base + q.a})`);
      m.g2.setAttribute('transform', `translate(0 ${m.len1}) rotate(${q.b})`);
      const amb = nome.endsWith('T') && !frente ? mul(ambiente, '#bdbbc6') : ambiente; // o membro de trás fica mais escuro
      const giro = (ehBraco ? q.punho : q.pe) || 0;
      if (m.p3) m.p3.g.setAttribute('transform', `rotate(${giro} 0 ${m.len2})`);
      if (m.prop) m.prop.setAttribute('transform', `translate(0 ${m.len2}) rotate(${giro})`);
      sombrear(m.p1, base + q.a, L, amb);
      sombrear(m.p2, base + q.a + q.b, L, amb);
      if (m.p3) sombrear(m.p3, base + q.a + q.b, L, amb);
    }
    const c = pecas.cabeca;
    const [nx, ny] = rot(frente ? 0 : 8, -M.tronco - M.pescoco + 6, aT);
    c.g1.setAttribute('transform', `translate(${nx} ${ny}) rotate(${aT})`);
    c.g2.setAttribute('transform', `translate(${frente ? 0 : 6} ${-M.cabeca * 0.78}) rotate(${pose.cabeca || 0})`);
    sombrear(c.p1, aT, L, ambiente);
    sombrear(c.p2, aT + (pose.cabeca || 0), L, ambiente);
    desenhaRosto(c.R, F, P, ambiente, frente);
    liga(pecas.pares, frente);
    if (P.atualiza) P.atualiza({ pecas, M, P, F, pose, frente, ambiente, mul, mix, luz: L });
  }

  // altura do boneco em pé, do chão ao alto da cabeça, em px de desenho (sem esc): para a escala real (porta de 2,1 m, gente de 1,75 m)
  function altura(P) {
    const M = Object.assign({ tronco: 300, coxa: 196, canela: 190, cabeca: 100, pescoco: 34 }, P.medidas || {});
    return (M.coxa + M.canela + 20 + M.tronco + M.pescoco + M.cabeca * 1.8) * (P.escala || 1);
  }
  // y do quadril para os pés pisarem em "chao"
  function quadrilNo(P, chao, esc = 1) {
    const M = Object.assign({ coxa: 196, canela: 190 }, P.medidas || {});
    return chao - (M.coxa + M.canela + 20) * esc * (P.escala || 1);
  }

  // ---------- cabelo com volume ----------
  // ext: o contorno de fora (da frente, por cima, até a nuca), em frações do raio da cabeça; int: a linha do cabelo no rosto.
  // onda > 0: contorno em cachos (arcos); onda = 0: pontas retas (arrepiado); onda < 0: curva lisa.
  // O cabelo passa do contorno da cabeça: cabelo colado parece liso e igual em todos.
  function caminhoCabelo(r, ext, int, onda) {
    const P = ext.map(([x, y]) => [x * r, y * r]), Q = int.map(([x, y]) => [x * r, y * r]);
    let d = `M ${P[0][0]} ${P[0][1]}`;
    for (let i = 1; i < P.length; i++) {
      const [x0, y0] = P[i - 1], [x1, y1] = P[i];
      if (onda > 0) { const rr = Math.hypot(x1 - x0, y1 - y0) * onda; d += ` A ${rr} ${rr} 0 0 0 ${x1} ${y1}`; }
      else if (onda < 0) {
        const p0 = P[Math.max(0, i - 2)], p3 = P[Math.min(P.length - 1, i + 1)];
        const c1 = [x0 + (x1 - p0[0]) / 6, y0 + (y1 - p0[1]) / 6], c2 = [x1 - (p3[0] - x0) / 6, y1 - (p3[1] - y0) / 6];
        d += ` C ${c1[0]} ${c1[1]} ${c2[0]} ${c2[1]} ${x1} ${y1}`;
      }
      else d += ` L ${x1} ${y1}`;
    }
    const L = [P[P.length - 1], ...Q];
    for (let i = 0; i < L.length - 1; i++) {
      const p0 = L[Math.max(0, i - 1)], p1 = L[i], p2 = L[i + 1], p3 = L[Math.min(L.length - 1, i + 2)];
      const c1 = [p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6], c2 = [p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6];
      d += ` C ${c1[0]} ${c1[1]} ${c2[0]} ${c2[1]} ${p2[0]} ${p2[1]}`;
    }
    return d + ' Z';
  }
  // cor, contorno, textura (traços mais claros: [x0,y0, cx,cy, x1,y1] em frações do raio) e brilho; devolve o grupo
  function cabelo(el_, parent, tinta, r, ext, int, onda, cor, textura, brilho) {
    const g = el('g', {}, parent);
    el('path', { d: caminhoCabelo(r, ext, int, onda), fill: cor, stroke: TINTA, 'stroke-width': 6, 'stroke-linejoin': 'round' }, g);
    for (const t of textura || []) el('path', { d: `M ${t[0] * r} ${t[1] * r} Q ${t[2] * r} ${t[3] * r} ${t[4] * r} ${t[5] * r}`, fill: 'none', stroke: brilho, 'stroke-width': 4.5, 'stroke-linecap': 'round', opacity: 0.85 }, g);
    return g;
  }

  // cada personagem guarda pares {perfil, frente} e liga um ou outro conforme a vista
  function par(perfil, frente) { return { perfil, frente }; }
  function liga(pares, frente) { for (const p of pares || []) { p.perfil.setAttribute('display', frente ? 'none' : ''); p.frente.setAttribute('display', frente ? '' : 'none'); } }

  // ---------- cabelos prontos (perfil e frente), para figurantes e como ponto de partida ----------
  const CABELOS = {
    crespo: { p: [[[0.6, -0.62], [0.68, -0.88], [0.48, -1.1], [0.18, -1.24], [-0.16, -1.26], [-0.5, -1.15], [-0.82, -0.94], [-1.08, -0.6], [-1.18, -0.22], [-1.1, 0.14], [-0.86, 0.36]], [[-0.62, 0.2], [-0.48, -0.1], [-0.18, -0.38], [0.2, -0.52], [0.6, -0.62]], 0.62],
              f: [[[-0.86, -0.16], [-1.06, -0.5], [-0.94, -0.92], [-0.62, -1.18], [-0.2, -1.28], [0.2, -1.28], [0.62, -1.18], [0.94, -0.92], [1.06, -0.5], [0.86, -0.16]], [[0.72, -0.42], [0.36, -0.58], [0, -0.6], [-0.36, -0.58], [-0.72, -0.42], [-0.86, -0.16]], 0.62] },
    curto: { p: [[[0.5, -0.64], [0.74, -0.84], [0.62, -1.1], [0.2, -1.24], [-0.3, -1.22], [-0.74, -1.04], [-1.04, -0.66], [-1.1, -0.2], [-0.92, 0.2]], [[-0.66, 0.1], [-0.44, -0.24], [-0.1, -0.46], [0.2, -0.54], [0.5, -0.64]], -1],
             f: [[[-0.97, -0.14], [-1.08, -0.56], [-0.94, -0.96], [-0.52, -1.22], [0, -1.28], [0.52, -1.22], [0.94, -0.96], [1.08, -0.56], [0.97, -0.14]], [[0.84, -0.38], [0.46, -0.56], [0, -0.6], [-0.46, -0.56], [-0.84, -0.38], [-0.97, -0.14]], -1] },
    topete: { p: [[[0.5, -0.64], [0.78, -0.86], [0.7, -1.14], [0.3, -1.32], [-0.22, -1.32], [-0.7, -1.16], [-1.04, -0.84], [-1.14, -0.42], [-1.06, -0.02], [-0.9, 0.2]], [[-0.68, 0.1], [-0.46, -0.22], [-0.12, -0.44], [0.2, -0.54], [0.5, -0.64]], -1],
              f: [[[-0.98, -0.16], [-1.14, -0.58], [-1.0, -1.0], [-0.6, -1.3], [0.02, -1.38], [0.6, -1.3], [1.0, -1.0], [1.14, -0.58], [0.98, -0.16]], [[0.86, -0.36], [0.5, -0.56], [0.1, -0.62], [-0.14, -0.52], [-0.5, -0.58], [-0.86, -0.36], [-0.98, -0.16]], -1] },
    comprido: { p: [[[0.55, -0.7], [0.68, -1.0], [0.3, -1.24], [-0.25, -1.26], [-0.75, -1.06], [-1.08, -0.6], [-1.18, 0.0], [-1.12, 0.7], [-0.95, 1.35], [-0.6, 1.45]], [[-0.5, 0.9], [-0.55, 0.2], [-0.35, -0.25], [0.0, -0.5], [0.55, -0.7]], -1],
                f: [[[-0.95, 1.4], [-1.15, 0.6], [-1.15, -0.3], [-0.9, -0.95], [-0.4, -1.28], [0.2, -1.3], [0.75, -1.08], [1.12, -0.5], [1.16, 0.4], [1.0, 1.35]], [[0.78, 1.2], [0.86, 0.3], [0.8, -0.25], [0.45, -0.55], [0, -0.62], [-0.45, -0.55], [-0.8, -0.25], [-0.86, 0.3], [-0.78, 1.2], [-0.95, 1.4]], -1] },
    armado: { p: [[[0.55, -0.66], [0.66, -0.98], [0.36, -1.2], [-0.04, -1.32], [-0.5, -1.28], [-0.92, -1.05], [-1.26, -0.66], [-1.38, -0.2], [-1.3, 0.26], [-1.04, 0.58], [-0.68, 0.62]], [[-0.5, 0.26], [-0.42, -0.14], [-0.15, -0.48], [0.2, -0.6], [0.55, -0.66]], 0.58],
              f: [[[-0.9, 0.18], [-1.26, -0.14], [-1.34, -0.6], [-1.1, -1.02], [-0.7, -1.28], [-0.2, -1.4], [0.3, -1.38], [0.76, -1.24], [1.12, -0.98], [1.34, -0.58], [1.26, -0.14], [0.9, 0.18]], [[0.84, -0.24], [0.56, -0.54], [0.16, -0.62], [-0.24, -0.6], [-0.6, -0.5], [-0.86, -0.2], [-0.9, 0.18]], 0.58] },
    careca: { p: [[[-0.5, 0.0], [-0.8, -0.3], [-1.04, -0.2], [-1.06, 0.12], [-0.9, 0.3]], [[-0.7, 0.2], [-0.5, 0.0]], -1],
              f: [[[-0.98, -0.3], [-1.06, 0.0], [-0.98, 0.2]], [[-0.86, 0.0], [-0.98, -0.3]], -1] },
  };
  const MEDIDAS_CRIANCA = { tronco: 220, ombro: 150, prof: 116, cintura: 128, braco: 118, ante: 106, coxa: 140, canela: 128, cabeca: 104, wb: 50, wa: 44, wc: 62, wk: 54 };
  const MEDIDAS_IDOSO = { tronco: 285, prof: 128, ombro: 168, cintura: 140, coxa: 186, canela: 180 };

  // pessoa({...}): um personagem a partir de poucas escolhas. Os da história ganham uma marca forte em "detalhes";
  // os figurantes variam cabelo, pele, roupa, idade e gênero (nunca um personagem da história como figurante).
  // o: pele, camisa, calca, sapato (e *Sombra, opcionais), cabelo (nome em CABELOS), corCabelo, luzCabelo, texturaCabelo,
  //    mangaCurta, vestido, coque, oculos, crianca, idoso, medidas, barriga, escala, detalhes(ctx), atualiza(ctx)
  function pessoa(o) {
    const P = Object.assign({ sobrancelha: o.corCabelo || TINTA, sapato: '#2a2630' }, o);
    // vestido: a coxa fica escondida pela saia e a canela é de pele (ou de meia, com "canela"); nada de calça aparecendo
    if (o.vestido) { P.calca = o.saia || o.camisa; P.canela = o.canela || o.pele; P.canelaSombra = o.canelaSombra || o.peleSombra; }
    if (o.crianca) { P.escala = o.escala || 0.66; P.medidas = Object.assign({}, MEDIDAS_CRIANCA, o.medidas || {}); }
    if (o.idoso) P.medidas = Object.assign({}, MEDIDAS_IDOSO, o.medidas || {});
    P.detalhes = function (ctx) {
      const { el, pecas, M } = ctx, c = pecas.cabeca, r = M.cabeca;
      if (o.cabelo) {
        const h = CABELOS[o.cabelo], cor = o.corCabelo || '#2a1f1b', luz = o.luzCabelo || mix(cor, '#ffffff', 0.22);
        const tx = o.texturaCabelo || {};
        const cp = cabelo(el, c.frente, TINTA, r, h.p[0], h.p[1], h.p[2], cor, tx.p || [], luz);
        const cf = cabelo(el, c.frente, TINTA, r, h.f[0], h.f[1], h.f[2], cor, tx.f || [], luz);
        if (o.coque) { el('circle', { cx: -r * 0.78, cy: -r * 0.95, r: r * 0.34, fill: cor, stroke: TINTA, 'stroke-width': 6 }, cp); el('circle', { cx: 0, cy: -r * 1.3, r: r * 0.32, fill: cor, stroke: TINTA, 'stroke-width': 6 }, cf); }
        if (o.oculos) for (const g of [cp, cf]) { const fr = g === cf; for (const s of fr ? [-1, 1] : [0]) el('rect', { x: (fr ? s * r * 0.36 : r * 0.46) - 22, y: -r * 0.08 - 18, width: 44, height: 34, rx: 10, fill: 'none', stroke: TINTA, 'stroke-width': 5 }, g); }
        pecas.pares.push(par(cp, cf));
      }
      if (o.mangaCurta) for (const n of ['bracoF', 'bracoT']) {
        el('rect', { x: -40, y: M.braco * 0.62, width: 80, height: M.braco, fill: o.pele }, pecas[n].p1.extra);
        el('path', { d: `M -30 ${M.braco * 0.62} L 30 ${M.braco * 0.62}`, stroke: TINTA, 'stroke-width': 6 }, pecas[n].p1.extra);
      }
      if (o.vestido) { // a saia: uma peça só, por cima das duas coxas, entre a perna da frente e o braço da frente
        const corpo = pecas.pernaF.g1.parentNode;
        // guardada nas peças deste boneco: a mesma ficha pode virar vários bonecos
        const saia = pecas.saia = el('path', { fill: o.saia || o.camisa, stroke: TINTA, 'stroke-width': 6, 'stroke-linejoin': 'round' });
        corpo.insertBefore(saia, pecas.pernaF.g1.nextSibling);
        const bainha = pecas.bainha = el('path', { fill: 'none', stroke: mix(o.saia || o.camisa, '#1a1424', 0.35), 'stroke-width': 8, 'stroke-linecap': 'round' });
        corpo.insertBefore(bainha, saia.nextSibling);
      }
      if (o.detalhes) o.detalhes(ctx);
    };
    // a saia segue os joelhos: da cintura até um pouco abaixo deles, cobrindo as duas coxas em qualquer pose
    P.atualiza = function (ctx) {
      if (ctx.pecas.saia && ctx.pecas.pernaF.g1.parentNode.getCTM()) { // escondido (plano fora de cena), não há o que medir
        const { pecas, M, frente } = ctx, saia = pecas.saia, bainha = pecas.bainha, corpo = pecas.pernaF.g1.parentNode, inv = corpo.getCTM().inverse();
        const joelho = n => { const m = inv.multiply(pecas[n].g2.getCTM()); return [m.e, m.f]; };
        const tornozelo = n => { const m = inv.multiply(pecas[n].g2.getCTM()); return [m.e + m.c * pecas[n].len2, m.f + m.d * pecas[n].len2]; };
        const [a, b] = [joelho('pernaF'), joelho('pernaT')];
        const longo = (P.comprimento || o.comprimento) === 'longo', curto = (P.comprimento || o.comprimento) === 'curto';
        const meia = (frente ? M.cintura : M.prof) * 0.55, xs = [a[0], b[0]];
        // de pé, a saia cai até um pouco abaixo dos joelhos; sentada, cobre o colo e cai do joelho
        // comprimento: 'curto' (acima do joelho), 'joelho' (o padrão, um pouco abaixo) ou 'longo' (até perto do tornozelo)
        if (longo) { const [c, d] = [tornozelo('pernaF'), tornozelo('pernaT')]; xs.push(c[0], d[0]); }
        const x1 = Math.max(...xs) + M.wc * 0.7, x0 = Math.min(Math.min(...xs) - M.wc * 0.7, -meia);
        const fundo = longo ? Math.max(tornozelo('pernaF')[1], tornozelo('pernaT')[1]) - M.wk * 0.6 : Math.max(a[1], b[1]) + (curto ? -M.coxa * 0.15 : M.coxa * 0.28);
        const topoJoelho = Math.max(-12, Math.min(a[1], b[1]) - M.wc * 0.55), y = Math.max(fundo, Math.max(a[1], b[1]) * 0.5);
        const atras = Math.min(...xs) > meia ? Math.min(...xs) - M.wc * 0.7 : x0; // sentada: a barra fica sob os joelhos
        saia.setAttribute('d', `M ${-meia} -12 L ${meia} -12 L ${x1} ${topoJoelho} L ${x1 + 6} ${y} Q ${(atras + x1) / 2} ${y + 14} ${atras} ${y} L ${x0} ${Math.max(a[1], b[1]) * 0.5 + M.wc * 0.4} Z`);
        bainha.setAttribute('d', `M ${atras + 6} ${y - 4} Q ${(atras + x1) / 2} ${y + 10} ${x1} ${y - 4}`);
      }
      if (o.atualiza) o.atualiza(ctx);
    };
    return P;
  }

  // maoEm(pose, ficha, [x, y]): o ponto da cena (a maçaneta, a lanterna, o rosto de alguém) na medida que o "mao" da pose usa.
  // A pose precisa ter x, y, esc e vira; o mesmo vale para o pé: pernaF: { mao: Boneco.maoEm(pose, ficha, [x, y]) }.
  // Conta o quadrilY e o achata da pose (a mão não escorrega no tranco). No pé, o alvo é o tornozelo (uns 20 px acima da sola,
  // na medida do boneco), e o joelho para a frente pede dobra: -1.
  function maoEm(pose, ficha, [X, Y]) {
    const E = ficha.escala || 1, e = (pose.esc || 1) * E, v = pose.vira ?? 1, ach = (pose.achata || 0) * 0.12;
    const Mm = Object.assign({ coxa: 196, canela: 190 }, ficha.medidas || {}), pernas = (Mm.coxa + Mm.canela + 20) * (pose.esc || 1) * E;
    const y0 = (pose.y || 0) + pernas * ach;
    return [(X - (pose.x || 0)) / (e * v * (1 + ach)), (Y - y0) / (e * (1 - ach)) - (pose.quadrilY || 0)];
  }
  // ondeEsta(boneco, 'bracoF', grupo): onde está a mão (ou o pé, com 'pernaF') agora, nas medidas do grupo (o plano, por padrão o pai
  // do boneco). Serve para a luz sair da lanterna ou do celular na mão: desenhe o facho a partir desse ponto, depois do posar.
  function ondeEsta(raiz, peca = 'bracoF', grupo = raiz.parentNode) {
    const p = raiz.dados.pecas[peca], m = grupo.getCTM() && p.g2.getCTM() ? grupo.getCTM().inverse().multiply(p.g2.getCTM()) : null;
    if (!m) return [0, 0];
    return [m.e + m.c * p.len2, m.f + m.d * p.len2];
  }
  window.Boneco = { maoEm, ondeEsta, criar, posar, pessoa, altura, quadrilNo, cabelo, caminhoCabelo, par, liga, CABELOS, mix, mul, el, TINTA, sombraDe };
})();
