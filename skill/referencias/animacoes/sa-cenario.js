// Série Animada: as peças de cenário. Entra no <script> depois do sa-base.js: const K = Cenario.kit(S).
// Cada peça desenha num <g> e devolve o que dá para mexer depois (a folha da porta, a fresta da cortina, os atores).
// Os lugares da história (o corredor do prédio, a cozinha da fazenda, a sala de aula) são montados com estas peças
// no arquivo da própria cena: aqui não há lugar pronto, só o que se repete em qualquer lugar.
// Tudo em traço de nanquim (contorno escuro de 6 px), cor chapada com um segundo tom e luz que sai de algum lugar.
(function () {
  function kit(S) {
    const { el, TINTA, W, H, clamp, lerp, ruido, hash, u, texto } = S;
    const L = (p, x1, y1, x2, y2, cor = TINTA, w = 6) => el('path', { d: `M ${x1} ${y1} L ${x2} ${y2}`, stroke: cor, 'stroke-width': w, 'stroke-linecap': 'round' }, p);
    const R = (p, x, y, w, h, fill, extra = {}) => el('rect', Object.assign({ x, y, width: w, height: h, fill, stroke: TINTA, 'stroke-width': 6, 'stroke-linejoin': 'round' }, extra), p);
    const C = (p, cx, cy, r, fill, extra = {}) => el('circle', Object.assign({ cx, cy, r, fill, stroke: TINTA, 'stroke-width': 6 }, extra), p);
    const P = (p, d, fill, extra = {}) => el('path', Object.assign({ d, fill, stroke: TINTA, 'stroke-width': 6, 'stroke-linejoin': 'round' }, extra), p);
    const escuro = (c, k = 0.25) => Boneco.mix(c, '#140f1c', k);
    let nId = 0;
    const novoId = l => (S.svg.id || 'sa') + '-k' + l + (++nId);
    function recorte(parent, forma) { // clipPath com id próprio: devolve um <g> recortado pela forma
      const id = novoId('r');
      const cp = el('clipPath', { id }, S.svg.querySelector('defs'));
      forma(cp);
      return el('g', { 'clip-path': `url(#${id})` }, parent);
    }

    // ---------- escala ----------
    // Uma porta tem uns 2,1 m e uma pessoa adulta uns 1,75 m: a pessoa fica com uns 83% da altura da porta.
    // escala(altPorta, ficha): o "esc" do Boneco.posar para essa ficha ficar na altura certa ao lado dessa porta.
    // Criança: use a escala de um adulto da cena (a ficha de criança já é menor).
    const escala = (altPorta, ficha) => 0.83 * altPorta / Boneco.altura(Object.assign({}, ficha, { escala: 1 }));
    // y do quadril para os pés pisarem no chão (ninguém flutua): pose.y = pe(ficha, chao, esc)
    const pe = (ficha, chao, esc) => Boneco.quadrilNo(ficha, chao, esc);

    // ---------- superfícies ----------
    function fundo(g, cor) { return el('rect', { x: -2000, y: -2000, width: W + 4000, height: H + 4000, fill: cor }, g); }
    // parede de x0 a x1, de y0 a y1, com listras (papel de parede) ou bolinhas
    function parede(g, o = {}) {
      const x0 = o.x0 ?? -1200, x1 = o.x1 ?? W + 1200, y0 = o.y0 ?? -600, y1 = o.y1 ?? 1600;
      const p = el('g', {}, g);
      el('rect', { x: x0, y: y0, width: x1 - x0, height: y1 - y0, fill: o.cor || '#6b5f55' }, p);
      if (o.listras) for (let x = x0; x < x1; x += o.listras.passo || 70) el('rect', { x, y: y0, width: o.listras.larg || 26, height: y1 - y0, fill: o.listras.cor }, p);
      if (o.bolinhas) for (let y = y0; y < y1; y += 120) for (let x = x0; x < x1; x += 120) el('circle', { cx: x + ((y - y0) / 120 % 2) * 60, cy: y, r: 10, fill: o.bolinhas }, p);
      return p;
    }
    // azulejo (banheiro, cozinha, área): quadrados com rejunte
    function azulejo(g, o) {
      const p = el('g', {}, g), passo = o.passo || 90;
      el('rect', { x: o.x, y: o.y, width: o.w, height: o.h, fill: o.rejunte || '#8b949c' }, p);
      for (let y = o.y; y < o.y + o.h; y += passo) for (let x = o.x; x < o.x + o.w; x += passo)
        el('rect', { x: x + 3, y: y + 3, width: passo - 6, height: passo - 6, rx: 4, fill: hash(x * 0.37 + y * 0.11) > 0.85 ? escuro(o.cor, 0.08) : o.cor }, p);
      return p;
    }
    // chão de y para baixo: tábuas em perspectiva (fuga no centro) ou ladrilho
    function chao(g, o = {}) {
      const y = o.y ?? 1600, cor = o.cor || '#3b2c26', p = el('g', {}, g);
      el('rect', { x: -2000, y, width: W + 4000, height: 2000, fill: cor }, p);
      const fx = o.fuga ?? W / 2;
      if (o.tipo !== 'liso') for (let x = -2000; x < W + 2000; x += o.passo || 160) L(p, x, y, fx + (x - fx) * 1.8, y + 1200, escuro(cor, 0.18), 5);
      L(p, -2000, y, W + 2000, y, TINTA, 8);
      return p;
    }
    function rodape(g, y, cor = '#4a4038', alt = 30) { return el('rect', { x: -2000, y: y - alt, width: W + 4000, height: alt, fill: cor, stroke: TINTA, 'stroke-width': 5 }, g); }

    // ---------- porta na parede, de frente ----------
    // o: {x (esquerda do batente), chao, larg 330, alt 1080, cor, numero, placa, macaneta 'dir'|'esq', olho, metal}
    // abrir(k): 0 fechada, 0.1 encostada (uma fresta escura), 1 aberta. A fresta mostra o que estiver em "vao".
    function porta(g, o) {
      const larg = o.larg || 330, alt = o.alt || 1080, x = o.x, ch = o.chao, topo = ch - alt;
      const cor = o.cor || '#6d4632', p = el('g', {}, g);
      // as medidas internas são frações da porta: a mesma porta de longe (pequena) fica com os painéis certos
      const k = larg / 330, bt = 30 * k, pn = 64 * k;
      R(p, x, topo, larg, alt, escuro(cor, 0.2));                          // batente
      const vao = el('g', {}, p);
      el('rect', { x: x + bt, y: topo + bt, width: larg - 2 * bt, height: alt - bt, fill: o.vaoCor || '#07060a' }, vao);
      const folha = el('g', {}, p);
      R(folha, x + bt, topo + bt, larg - 2 * bt, alt - bt, cor);
      if (o.metal) { R(folha, x + 35 * k, topo + alt * 0.32, larg - 70 * k, 26 * k, escuro(cor, 0.15), { 'stroke-width': 4 }); }
      else { R(folha, x + pn, topo + 70 * k, larg - 2 * pn, alt * 0.38, 'none', { stroke: escuro(cor, 0.25), 'stroke-width': 6 }); R(folha, x + pn, topo + alt * 0.52, larg - 2 * pn, alt * 0.4, 'none', { stroke: escuro(cor, 0.25), 'stroke-width': 6 }); }
      const mx = o.macaneta === 'esq' ? x + 70 * k : x + larg - 70 * k;
      if (o.metal) R(folha, mx - 17, ch - alt * 0.53, 34, 120, '#c9ced6', { rx: 8, 'stroke-width': 4 });
      else C(folha, mx, ch - alt * 0.45, 14, '#d9b45a', { 'stroke-width': 4 });
      if (o.olho) el('circle', { cx: x + larg / 2, cy: topo + alt * 0.26, r: 9, fill: '#111', stroke: '#c9a24a', 'stroke-width': 4 }, folha);
      if (o.numero) { R(folha, x + larg / 2 - 55, topo + 120, 110, 50, '#d9c9a0', { rx: 8, 'stroke-width': 4 }); texto(folha, { x: x + larg / 2, y: topo + 157, 'text-anchor': 'middle', 'font-size': 32, fill: '#2b2422' }, o.numero); }
      if (o.placa) { R(p, x + larg / 2 - 95, topo - 80, 190, 60, o.placa.cor || '#2e9b57', { rx: 6, 'stroke-width': 4 }); texto(p, { x: x + larg / 2, y: topo - 38, 'text-anchor': 'middle', 'font-size': 30, fill: o.placa.texto || '#eafff1' }, o.placa.nome); }
      const dobradica = o.macaneta === 'esq' ? x + larg - bt : x + bt;
      // fresta de baixo (o vão entre a porta e o chão, por onde passa luz ou aparece alguma coisa) e a tramela de sítio
      const fresta = o.fresta ? el('rect', { x: x + bt, y: ch - 14 * k, width: larg - 2 * bt, height: 14 * k, fill: o.fresta === true ? '#07060a' : o.fresta }, p) : null;
      const tramela = o.tramela ? el('g', {}, folha) : null;
      if (tramela) { const ty = ch - alt * 0.55, tx = o.macaneta === 'esq' ? x + bt : x + larg - bt; R(tramela, tx - 70 * k, ty - 12 * k, 140 * k, 24 * k, '#6b4a2a', { 'stroke-width': 4 }); R(tramela, tx - 18 * k, ty - 30 * k, 36 * k, 60 * k, '#5a5a62', { 'stroke-width': 4 }); }
      return { g: p, folha, vao, fresta, tramela, x, larg, alt, topo, chao: ch, meio: x + larg / 2,
        // estufa(k, tt): a porta empurrada de fora: a folha incha para dentro e treme; a tramela entorta
        estufa(kk, tt = 0) {
          kk = clamp(kk); const cx = x + larg / 2, cy = topo + alt / 2;
          folha.setAttribute('transform', `translate(${cx + Math.sin(tt * 60) * 5 * kk} ${cy}) scale(${1 + 0.05 * kk} ${1 + 0.02 * kk}) translate(${-cx} ${-cy})`);
          if (tramela) tramela.setAttribute('transform', `rotate(${-14 * kk} ${o.macaneta === 'esq' ? x + bt : x + larg - bt} ${ch - alt * 0.55})`);
        },
        abrir(k, treme = 0) { // a folha gira na dobradiça: fica mais estreita e mostra o vão escuro
          k = clamp(k);
          folha.setAttribute('transform', `translate(${dobradica + treme} 0) scale(${1 - 0.85 * k} 1) translate(${-dobradica} 0)`);
        } };
    }

    // ---------- porta vista por dentro (de perto): trancar, abrir, fresta de luz embaixo ----------
    // o: {cor, parede, listras, chao (y do chão), esc (tamanho da porta na tela), x (centro)}
    // quadro(t, {abre, tranca, luzFora, batida, vaoCor}). atras: o que se vê pelo vão (corredor); atores: quem está na frente.
    function portaPorDentro(g, o = {}) {
      const ch = o.chao ?? 1640, esc = o.esc ?? 1, cx = o.x ?? 540, cor = o.cor || '#7a4f38';
      fundo(g, o.parede || '#2c3048');
      if (o.listras !== false) parede(g, { cor: o.parede || '#2c3048', listras: { cor: o.listras || '#30344e' }, y1: ch });
      chao(g, { y: ch, cor: o.corChao || '#3b2c26', tipo: 'liso' });
      const pg = el('g', { transform: `translate(${cx} ${ch}) scale(${esc}) translate(-540 -1640)` }, g);
      R(pg, 230, 260, 620, 1390, escuro(cor, 0.28));
      const vao = el('g', {}, pg);
      const vaoFundo = el('rect', { x: 260, y: 290, width: 560, height: 1350, fill: '#120f14' }, vao);
      let corteX = 820;
      const atras = recorte(vao, cp => { corteX = el('rect', { x: 260, y: 290, width: 560, height: 1350 }, cp); });
      const folha = el('g', {}, pg);
      R(folha, 260, 290, 560, 1350, cor);
      R(folha, 310, 340, 460, 560, 'none', { stroke: escuro(cor, 0.22), 'stroke-width': 8 }); R(folha, 310, 960, 460, 620, 'none', { stroke: escuro(cor, 0.22), 'stroke-width': 8 });
      el('circle', { cx: 540, cy: 560, r: 16, fill: '#111', stroke: '#c9a24a', 'stroke-width': 6 }, folha); // olho mágico
      R(folha, 700, 900, 70, 150, '#c9a24a', { rx: 12 }); const tambor = C(folha, 735, 1000, 22, '#e2bd5c', { 'stroke-width': 5 });
      const fenda = L(folha, 735, 988, 735, 1012, TINTA, 5);
      R(folha, 700, 800, 70, 60, '#c9a24a', { rx: 10 });
      const lingueta = R(pg, 800, 820, 0, 24, '#e2bd5c', { rx: 4, 'stroke-width': 4 });
      const bordaSombra = el('rect', { x: 0, y: 290, width: 26, height: 1350, fill: escuro(cor, 0.45), stroke: TINTA, 'stroke-width': 5 }, pg);
      const fresta = el('rect', { x: 260, y: 1630, width: 560, height: 12, fill: '#ffcf8a', opacity: 0.6 }, pg);
      const atores = el('g', {}, g);
      const paraTela = (x, y) => [cx + (x - 540) * esc, ch + (y - 1640) * esc];
      return { g, folha, atras, atores, paraTela, esc,
        macaneta: paraTela(735, 1000), olho: paraTela(540, 560), alt: 1390 * esc, chao: ch,
        quadro(tt, e = {}) {
          const abre = clamp(e.abre ?? 0), bate = e.batida ?? 0, sx = 1 - 0.7 * abre, borda = 260 + 560 * sx;
          folha.setAttribute('transform', `translate(${Math.sin(tt * 60) * 4 * bate} 0) translate(260 965) scale(${sx} ${1 + 0.05 * abre}) translate(-260 -965)`);
          bordaSombra.setAttribute('x', borda - 2); bordaSombra.setAttribute('opacity', abre > 0.01 ? 1 : 0);
          corteX.setAttribute('x', borda + 10); corteX.setAttribute('width', Math.max(0, 820 - borda - 10));
          vao.setAttribute('opacity', abre > 0.005 ? 1 : 0);
          vaoFundo.setAttribute('fill', e.vaoCor || '#120f14');
          const tr = clamp(e.tranca ?? 0);
          lingueta.setAttribute('width', 46 * tr); lingueta.setAttribute('x', 806 - 46 * tr);
          fenda.setAttribute('transform', `rotate(${tr * 90} 735 1000)`);
          fresta.setAttribute('opacity', e.luzFora ?? 0.6);
        } };
    }

    // ---------- janela com cortina ----------
    // o: {x, y, w, h, vista: 'dia' | 'noite' (prédios) | 'campo' | 'campoDia' (morro, mato e, de noite, a lua), cortina: cor}.
    // vista também pode ser uma função (g, {x, y, w, h}) que desenha o que a história pede lá fora (o milharal, a casa da vizinha):
    // o desenho fica recortado na janela. Ela devolve o que precisar mexer, e isso volta em janela.vista. quadro(t, {fechada 0..1, luz}) — fechada 1 deixa só uma fresta de luz.
    function janela(g, o) {
      const p = el('g', {}, g), { x, y, w, h } = o;
      R(p, x - 16, y - 16, w + 32, h + 32, o.moldura || '#d9d2c0');
      const vista = recorte(p, cp => el('rect', { x, y, width: w, height: h }, cp));
      const propria = typeof o.vista === 'function' ? o.vista(vista, { x, y, w, h }) : null;
      const dia = o.vista === 'dia' || o.vista === 'campoDia', campo = o.vista === 'campo' || o.vista === 'campoDia' || typeof o.vista === 'function';
      if (!propria) el('rect', { x, y, width: w, height: h, fill: dia ? '#bfe0f5' : '#101633' }, vista);
      else vista.insertBefore(el('rect', { x, y, width: w, height: h, fill: '#101633' }), vista.firstChild);
      if (campo && !propria) { // o morro, a linha do mato e, de noite, a lua e estrelas
        if (!dia) { for (let i = 0; i < 14; i++) el('circle', { cx: x + hash(i * 3.1) * w, cy: y + hash(i * 7.3) * h * 0.5, r: 2 + hash(i) * 2, fill: '#e8ecff', opacity: 0.8 }, vista); el('circle', { cx: x + w * 0.72, cy: y + h * 0.22, r: Math.min(w, h) * 0.09, fill: '#f4efd8' }, vista); }
        el('path', { d: `M ${x - 10} ${y + h * 0.62} Q ${x + w * 0.3} ${y + h * 0.45} ${x + w * 0.6} ${y + h * 0.58} T ${x + w + 10} ${y + h * 0.55} L ${x + w + 10} ${y + h + 10} L ${x - 10} ${y + h + 10} Z`, fill: dia ? '#7fa36a' : '#1d2a2a' }, vista);
        for (let i = 0; i < Math.ceil(w / 22); i++) { const bx = x + i * 22, bh = h * (0.18 + hash(i * 1.7 + 3) * 0.12); el('path', { d: `M ${bx} ${y + h} L ${bx + 6} ${y + h - bh} L ${bx + 14} ${y + h}`, fill: dia ? '#5d8a4e' : '#132020' }, vista); }
      }
      if (!campo) for (let i = 0; i < Math.ceil(w / 60); i++) {
        const bx = x + i * 60, bh = h * (0.25 + hash(i + o.x) * 0.45);
        el('rect', { x: bx, y: y + h - bh, width: 54, height: bh, fill: dia ? '#8fa7bd' : '#1b2142' }, vista);
        if (!dia) for (let j = 0; j < 5; j++) if (hash(i * 9 + j) > 0.5) el('rect', { x: bx + 10 + (j % 2) * 20, y: y + h - bh + 12 + Math.floor(j / 2) * 32, width: 10, height: 16, fill: '#f0c56a', opacity: 0.8 }, vista);
      }
      L(p, x + w / 2, y, x + w / 2, y + h, TINTA, 8); L(p, x, y + h * 0.48, x + w, y + h * 0.48, TINTA, 8);
      const cor = o.cortina || '#7a3b3b';
      const esq = P(p, '', cor), dir = P(p, '', cor);
      const brilho = el('rect', { x: x + w / 2 - 6, y, width: 12, height: h, fill: '#fff3d6', opacity: 0 }, p);
      const feixe = el('path', { d: '', fill: '#fff1d0', opacity: 0, filter: u('desf24') }, g);
      return { g: p, feixe, vista: propria, quadro(tt, e = {}) {
        const f = clamp(e.fechada ?? 0), aberto = (w / 2) * (1 - f) * 0.85 + 8;
        // cada lado da cortina: preso em cima, com dobras; a borda de dentro vai até "aberto" do centro
        const lado = (s, el_) => { const xb = x + w / 2 - s * aberto, xf = s < 0 ? x + w + 40 : x - 40, onda = Math.sin(tt * 0.8) * 4;
          el_.setAttribute('d', `M ${xf} ${y - 30} L ${xb} ${y - 30} Q ${xb - s * 18 + onda} ${y + h / 2} ${xb} ${y + h + 30} L ${xf} ${y + h + 30} Z`); };
        lado(1, esq); lado(-1, dir);
        brilho.setAttribute('opacity', f > 0.9 ? 0.9 : 0);
        const l = e.luz ?? 0;
        feixe.setAttribute('opacity', l * (0.25 + 0.05 * ruido(tt)));
        feixe.setAttribute('d', `M ${x + w / 2 - 8} ${y} L ${x + w / 2 + 8} ${y} L ${x + w / 2 + 260} ${y + h + 700} L ${x + w / 2 - 120} ${y + h + 700} Z`);
      } };
    }

    // ---------- luz de teto ou abajur ----------
    function luminaria(g, o) {
      const p = el('g', {}, g);
      el('rect', { x: o.x - 50, y: o.y, width: 100, height: 22, fill: '#e9e2c8', stroke: TINTA, 'stroke-width': 4 }, p);
      const cone = el('path', { d: `M ${o.x - 50} ${o.y + 22} L ${o.x + 50} ${o.y + 22} L ${o.x + 260} ${o.chao} L ${o.x - 260} ${o.chao} Z`, fill: '#ffe2a8', opacity: 0.12 }, p);
      return { g: p, quadro(tt, l = 1) { cone.setAttribute('opacity', l * (0.1 + 0.03 * ruido(tt * 4 + o.x))); } };
    }

    // ---------- móveis ----------
    // sofá de lado, com o assento em "chao - 170" (para deitar alguém: y do corpo ≈ assento)
    function sofa(g, o) {
      const p = el('g', {}, g), x = o.x, ch = o.chao, w = o.larg || 760, cor = o.cor || '#4d6b6e';
      R(p, x, ch - 330, w, 240, cor, { rx: 36 });                               // encosto
      R(p, x, ch - 450, 150, 360, escuro(cor, 0.12), { rx: 40 });                // braço
      R(p, x + w - 130, ch - 400, 150, 310, escuro(cor, 0.12), { rx: 40 });
      const assento = R(p, x + 50, ch - 220, w - 100, 140, Boneco.mix(cor, '#ffffff', 0.12), { rx: 28 });
      R(p, x + 40, ch - 90, 40, 90, '#2a1f1b'); R(p, x + w - 80, ch - 90, 40, 90, '#2a1f1b');
      return { g: p, assento: ch - 220, x, w };
    }
    function mesa(g, o) {
      const p = el('g', {}, g), x = o.x, ch = o.chao, w = o.larg || 360, alt = o.alt || 300, cor = o.cor || '#7a5a3a';
      R(p, x, ch - alt, w, 30, cor, { rx: 6 }); R(p, x + 20, ch - alt + 30, 26, alt - 30, escuro(cor)); R(p, x + w - 46, ch - alt + 30, 26, alt - 30, escuro(cor));
      if (o.tombada) p.setAttribute('transform', `rotate(${o.tombada} ${x + w / 2} ${ch})`);
      return p;
    }
    function quadroParede(g, o) {
      const p = el('g', {}, g);
      R(p, o.x, o.y, o.w, o.h, o.moldura || '#c9a24a'); R(p, o.x + 18, o.y + 18, o.w - 36, o.h - 36, o.cor || '#8fa3b5');
      if (o.torto) p.setAttribute('transform', `rotate(${o.torto} ${o.x + o.w / 2} ${o.y})`);
      return p;
    }
    // coisas no chão (roupa, brinquedo, papel): formas soltas com sombra, para lugar revirado
    function bagunca(g, o) {
      const p = el('g', {}, g);
      for (let i = 0; i < (o.n || 6); i++) {
        const x = o.x + hash(i * 7 + 1) * o.w, cor = o.cores[i % o.cores.length], a = (hash(i * 3) - 0.5) * 60;
        el('ellipse', { cx: x, cy: o.chao + 6, rx: 50, ry: 10, fill: '#000', opacity: 0.25 }, p);
        R(p, x - 40, o.chao - 22 - hash(i) * 20, 80 + hash(i + 9) * 60, 26 + hash(i) * 20, cor, { rx: 10, transform: `rotate(${a} ${x} ${o.chao})`, 'stroke-width': 5 });
      }
      return p;
    }

    // ---------- pelo olho mágico ----------
    // O corredor de frente, em perspectiva, num círculo com a borda escura. noPiso(k): onde pisa quem está
    // a "k" do fundo (0 perto da porta, 1 no fim do corredor), com a escala certa para a distância.
    // o: {parede, chao, portas: [{lado: -1|1, de, ate, cor, aberta}], fundo: cor do fim}
    function olhoMagico(g, o = {}) {
      fundo(g, '#050507');
      const CX = W / 2, CY = 860, RAIO = 520;
      const dentro = recorte(g, cp => el('circle', { cx: CX, cy: CY, r: RAIO }, cp));
      const cena = el('g', {}, dentro);
      const fx = W / 2, fy = 760, cor = o.parede || '#4e4642';
      el('rect', { x: -200, y: -200, width: W + 400, height: 2400, fill: cor }, cena);
      el('path', { d: `M -400 1700 L ${fx - 120} ${fy + 120} L ${fx + 120} ${fy + 120} L ${W + 400} 1700 Z`, fill: o.chao || '#2a2626' }, cena);
      el('path', { d: `M -400 0 L ${fx - 120} ${fy - 150} L ${fx + 120} ${fy - 150} L ${W + 400} 0 Z`, fill: escuro(cor, 0.2) }, cena);
      el('path', { d: `M -400 0 L ${fx - 120} ${fy - 150} L ${fx - 120} ${fy + 120} L -400 1700 Z`, fill: Boneco.mix(cor, '#ffffff', 0.08) }, cena);
      el('path', { d: `M ${W + 400} 0 L ${fx + 120} ${fy - 150} L ${fx + 120} ${fy + 120} L ${W + 400} 1700 Z`, fill: escuro(cor, 0.05) }, cena);
      R(cena, fx - 120, fy - 150, 240, 270, o.fundo || '#1e1b1b');
      const portas = [];
      for (const pt of o.portas || [{ lado: -1, de: 0.15, ate: 0.45 }, { lado: 1, de: 0.15, ate: 0.45 }, { lado: -1, de: 0.6, ate: 0.78 }, { lado: 1, de: 0.6, ate: 0.78 }]) {
        const s = pt.lado, pnt = k => [lerp(s < 0 ? -400 : W + 400, s < 0 ? fx - 120 : fx + 120, k), lerp(0, fy - 150, k), lerp(1700, fy + 120, k)];
        const [x1, t1, b1] = pnt(pt.de), [x2, t2, b2] = pnt(pt.ate);
        const d = `M ${x1} ${lerp(t1, b1, 0.18)} L ${x2} ${lerp(t2, b2, 0.18)} L ${x2} ${b2} L ${x1} ${b1} Z`;
        const vaoP = P(cena, d, '#07060a', { 'stroke-width': 5 });
        const folha = P(cena, d, pt.cor || '#6d4632', { 'stroke-width': 5 });
        if (pt.placa) { const xm = (x1 + x2) / 2, ym = lerp(lerp(t1, b1, 0.18), lerp(t2, b2, 0.18), 0.5) - 40; R(cena, xm - 50, ym - 20, 100, 34, pt.placa, { rx: 5, 'stroke-width': 3 }); }
        portas.push({ folha, vao: vaoP, x1, x2, base: [x1, b1], abrir(k) { folha.setAttribute('transform', `translate(${x2} 0) scale(${1 - 0.9 * clamp(k)} 1) translate(${-x2} 0)`); } });
      }
      const luzTeto = el('ellipse', { cx: fx, cy: 260, rx: 360, ry: 120, fill: u('brilhoQuente'), opacity: 0.5 }, cena);
      const atores = el('g', {}, cena);
      const frente = el('g', {}, cena);
      const borda = el('g', {}, dentro);
      el('circle', { cx: CX, cy: CY, r: RAIO, fill: u('vinheta') }, borda);
      el('circle', { cx: CX, cy: CY, r: 500, fill: 'none', stroke: '#000', 'stroke-width': 90, opacity: 0.65, filter: u('desf24') }, borda);
      el('circle', { cx: CX, cy: CY, r: RAIO + 2, fill: 'none', stroke: '#16141a', 'stroke-width': 14 }, g);
      el('path', { d: `M ${CX - 330} 640 Q ${CX - 250} 450 ${CX - 80} 400`, fill: 'none', stroke: '#fff', 'stroke-width': 18, opacity: 0.08, 'stroke-linecap': 'round' }, g);
      const piso = k => lerp(1720, fy + 120, k), esc = k => lerp(1.15, 0.26, Math.pow(k, 0.8));
      return { g, cena, atores, frente, portas, fx, fy,
        noPiso: (k, ficha) => ({ y: pe(ficha, piso(k), esc(k)), esc: esc(k) }),
        quadro(tt, e = {}) {
          luzTeto.setAttribute('opacity', (e.luz ?? 1) * (0.45 + 0.05 * ruido(tt * 3)));
          cena.setAttribute('transform', `translate(${CX} ${CY}) scale(${e.zoom ?? 1}) translate(${-CX} ${-CY})`);
        } };
    }

    // ---------- prédio em corte (diagrama) ----------
    // Os andares empilhados, com a escada em zigue-zague do lado esquerdo. o: {andares 16, destaque: {14: cor}, x0, x1, y0, alt}
    // escada(p): o ponto na escada a "p" andares do chão (p = 13.5 é meio caminho entre o 13º e o 14º).
    function corte(g, o = {}) {
      fundo(g, '#141a26');
      for (let x = -600; x < W + 600; x += 60) L(g, x, -600, x, H + 600, '#1b2333', 2);
      for (let y = -600; y < H + 600; y += 60) L(g, -600, y, W + 600, y, '#1b2333', 2);
      const N = o.andares || 16, X0 = o.x0 ?? 230, X1 = o.x1 ?? 850, Y0 = o.y0 ?? 260, AND = o.alt || 80, YB = Y0 + N * AND;
      R(g, X0, Y0, X1 - X0, N * AND, '#263044');
      const andares = [];
      for (let k = 1; k <= N; k++) {
        const y = Y0 + (N - k) * AND, cor = (o.destaque || {})[k];
        L(g, X0, y + AND, X1, y + AND, '#5a6a8a', 4);
        texto(g, { x: X0 - 24, y: y + 54, 'text-anchor': 'end', 'font-size': 30, fill: cor || '#6d7d9e' }, k === 1 && o.terreo ? o.terreo : k + 'º');
        andares.push({ k, y, gente: el('g', {}, g) });
      }
      const esc = el('g', {}, g);
      R(esc, X0, Y0, 150, N * AND, '#1d2536');
      // os pontos da escada: um lance por meio andar, alternando os lados. O desenho e o ponto que anda usam a mesma lista.
      const pts = []; for (let h = 0; h <= 2 * N; h++) pts.push([X0 + (h % 2 ? 140 : 10), YB - h * AND / 2]);
      const d = 'M ' + pts.map(p => p.join(' ')).join(' L ');
      el('path', { d, fill: 'none', stroke: '#8796b5', 'stroke-width': 5, 'stroke-linejoin': 'round' }, esc);
      texto(g, { x: X0 + 75, y: YB + 50, 'text-anchor': 'middle', 'font-size': 26, fill: '#8796b5' }, 'ESCADA');
      // ponto na escada: a cada andar, um lance sobe da esquerda para a direita (ou o contrário)
      function escada(pAndar) {
        const h = clamp((pAndar - 1) * 2, 0, 2 * N - 1e-6), i = Math.floor(h), f = h - i;
        return [lerp(pts[i][0], pts[i + 1][0], f), lerp(pts[i][1], pts[i + 1][1], f)];
      }
      const andarY = k => Y0 + (N - k) * AND;
      return { g, andares, escada, andarY, X0, X1, Y0, YB, AND, N };
    }

    // ---------- campo: céu, morro, grama, terra, estrada, cerca, árvore e plantação ----------
    // céu de noite (lua e estrelas) ou de dia, de y0 até o horizonte y1. quadro(t): as estrelas piscam devagar.
    function ceu(g, o = {}) {
      const p = el('g', {}, g), y0 = o.y0 ?? -800, y1 = o.y1 ?? 900, x0 = o.x0 ?? -1200, x1 = o.x1 ?? W + 1200, noite = o.noite !== false;
      el('rect', { x: x0, y: y0, width: x1 - x0, height: y1 - y0, fill: noite ? '#0f1630' : '#a9d4f0' }, p);
      el('rect', { x: x0, y: lerp(y0, y1, 0.55), width: x1 - x0, height: (y1 - y0) * 0.45, fill: noite ? '#1c2647' : '#d6ecf7', opacity: 0.8, filter: u('desf50') }, p);
      const est = [];
      if (noite) for (let i = 0; i < (o.estrelas ?? 60); i++) est.push(el('circle', { cx: x0 + hash(i * 2.3) * (x1 - x0), cy: y0 + hash(i * 5.1) * (y1 - y0) * 0.75, r: 1.5 + hash(i) * 2.5, fill: '#eef1ff' }, p));
      if (o.lua !== false && noite) {
        const [lx, ly] = o.lua || [x0 + (x1 - x0) * 0.7, lerp(y0, y1, 0.3)];
        el('circle', { cx: lx, cy: ly, r: 260, fill: u('brilhoFrio'), opacity: 0.35 }, p);
        el('circle', { cx: lx, cy: ly, r: 62, fill: '#f4efd8', stroke: TINTA, 'stroke-width': 5 }, p);
        el('circle', { cx: lx - 18, cy: ly - 10, r: 12, fill: '#ddd5b8' }, p); el('circle', { cx: lx + 16, cy: ly + 18, r: 8, fill: '#ddd5b8' }, p);
      }
      return { g: p, quadro(tt) { est.forEach((e, i) => e.setAttribute('opacity', 0.5 + 0.5 * ruido(tt * 0.6 + i))); } };
    }
    // morro no horizonte (de y para baixo), numa cor só
    function morro(g, o) {
      const x0 = o.x0 ?? -1200, x1 = o.x1 ?? W + 1200, y = o.y, h = o.h ?? 160;
      let d = `M ${x0} ${y + h}`;
      for (let i = 0; i <= 8; i++) { const x = lerp(x0, x1, i / 8); d += ` Q ${x - (x1 - x0) / 16} ${y - h * (0.3 + hash(i + (o.semente || 1)) * 0.7)} ${x} ${y + h * 0.2 * hash(i * 3)}`; }
      return el('path', { d: d + ` L ${x1} ${y + 2000} L ${x0} ${y + 2000} Z`, fill: o.cor || '#1d2a2a' }, g);
    }
    // chão de terra ou grama de y para baixo, com tufos de mato na linha do chão
    function grama(g, o) {
      const p = el('g', {}, g), x0 = o.x0 ?? -1200, x1 = o.x1 ?? W + 1200, y = o.y, cor = o.cor || '#2c4a2a';
      el('rect', { x: x0, y, width: x1 - x0, height: 2000, fill: cor }, p);
      if (o.tufos !== false) for (let x = x0; x < x1; x += 34) { const h = 18 + hash(x * 0.37) * 26; el('path', { d: `M ${x} ${y + 4} Q ${x + 4} ${y - h * 0.5} ${x - 4} ${y - h} Q ${x + 10} ${y - h * 0.4} ${x + 14} ${y - h * 0.8} Q ${x + 16} ${y - h * 0.3} ${x + 26} ${y + 4} Z`, fill: escuro(cor, 0.15) }, p); }
      return p;
    }
    // estrada de terra que some no horizonte: da largura "larg" perto até um fio no ponto de fuga [fx, fy].
    // Com atravessa: true, ela cruza a tela de lado a lado, de y a y + larg ("do outro lado da estrada").
    function estrada(g, o) {
      const p = el('g', {}, g), cor = o.cor || '#6a5440';
      if (o.atravessa) {
        const y = o.y, larg = o.larg || 220, x0 = o.x0 ?? -1200, x1 = o.x1 ?? W + 1200;
        el('rect', { x: x0, y, width: x1 - x0, height: larg, fill: cor }, p);
        L(p, x0, y, x1, y, escuro(cor, 0.25), 5); L(p, x0, y + larg, x1, y + larg, escuro(cor, 0.25), 5);
        for (let i = 0; i < 40; i++) el('ellipse', { cx: x0 + hash(i * 3.7) * (x1 - x0), cy: y + 14 + hash(i * 1.9) * (larg - 28), rx: 10 + hash(i) * 16, ry: 4 + hash(i * 2) * 4, fill: escuro(cor, 0.18) }, p);
        for (const yy of [y + larg * 0.35, y + larg * 0.7]) L(p, x0, yy, x1, yy, escuro(cor, 0.1), 10);
        return p;
      }
      const { fx, fy, y } = o, larg = o.larg || 700;
      el('path', { d: `M ${fx - 6} ${fy} L ${fx + 6} ${fy} L ${fx + larg / 2} ${y} L ${fx - larg / 2} ${y} Z`, fill: cor }, p);
      for (let i = 0; i < 14; i++) { const k = hash(i * 4.3), xx = lerp(fx, fx + (hash(i) - 0.5) * larg * 0.8, k), yy = lerp(fy, y, k); el('ellipse', { cx: xx, cy: yy, rx: 4 + 14 * k, ry: 2 + 4 * k, fill: escuro(cor, 0.2) }, p); }
      return p;
    }
    // cerca de arame com mourões, de x0 a x1, com o pé em y
    function cerca(g, o) {
      const p = el('g', {}, g), alt = o.alt || 220, passo = o.passo || 260;
      for (let x = o.x0; x <= o.x1; x += passo) R(p, x - 10, o.y - alt, 20, alt + 10, o.cor || '#6b5038', { 'stroke-width': 5 });
      for (const k of [0.25, 0.55, 0.85]) L(p, o.x0, o.y - alt * k, o.x1, o.y - alt * k, '#9a9aa2', 3);
      return p;
    }
    // árvore: tronco e copa em três massas; quadro(t, vento) balança a copa
    function arvore(g, o) {
      const p = el('g', {}, g), { x, y } = o, h = o.alt || 700, cor = o.cor || '#2f4a32';
      el('path', { d: `M ${x - h * 0.05} ${y} L ${x - h * 0.03} ${y - h * 0.55} L ${x + h * 0.03} ${y - h * 0.55} L ${x + h * 0.05} ${y} Z`, fill: '#4a3626', stroke: TINTA, 'stroke-width': 6 }, p);
      const copa = el('g', {}, p);
      for (const [dx, dy, r] of [[-0.16, -0.62, 0.2], [0.15, -0.66, 0.19], [0, -0.82, 0.22]]) C(copa, x + dx * h, y + dy * h, r * h, dx === 0 ? Boneco.mix(cor, '#ffffff', 0.08) : cor);
      return { g: p, quadro(tt, vento = 1) { copa.setAttribute('transform', `rotate(${Math.sin(tt * 1.3 + x) * 1.5 * vento} ${x} ${y - h * 0.55})`); } };
    }
    // plantação (milho, cana, mato alto): fileiras de pés altos que balançam com o vento.
    // mexe(x, k) sacode os pés perto de x: alguma coisa passando no meio da plantação.
    function plantacao(g, o) {
      // escala: o tamanho das folhas, do talo e da espiga (o milho de longe, numa janela, é 0,3)
      const p = el('g', {}, g), pes = [], k = o.escala || 1, alt = o.alt || 900 * k, cor = o.cor || '#3c5a2c', passo = o.passo || 70 * k;
      for (let x = o.x0; x <= o.x1; x += passo * (0.8 + hash(x) * 0.4)) {
        const h = alt * (0.85 + hash(x * 1.3) * 0.3), gp = el('g', {}, p);
        const sw = Math.max(2, 4 * k);
        el('path', { d: `M ${x - 6 * k} ${o.y} L ${x - 3 * k} ${o.y - h} L ${x + 3 * k} ${o.y - h} L ${x + 6 * k} ${o.y} Z`, fill: escuro(cor, 0.1), stroke: TINTA, 'stroke-width': sw }, gp);
        for (let f = 0.3; f < 0.95; f += 0.17) { const s = (Math.floor(f * 10) % 2) ? 1 : -1, yy = o.y - h * f; el('path', { d: `M ${x} ${yy} Q ${x + s * 90 * k} ${yy - 60 * k} ${x + s * 170 * k} ${yy + 10 * k} Q ${x + s * 90 * k} ${yy - 30 * k} ${x} ${yy + 12 * k} Z`, fill: cor, stroke: TINTA, 'stroke-width': sw, 'stroke-linejoin': 'round' }, gp); }
        if (o.espiga !== false && hash(x * 2.1) > 0.4) R(gp, x + 6 * k, o.y - h * 0.55, 22 * k, 70 * k, '#c9a24a', { rx: 10 * k, 'stroke-width': sw });
        el('path', { d: `M ${x} ${o.y - h} l ${-16 * k} ${-40 * k} M ${x} ${o.y - h} l ${14 * k} ${-44 * k} M ${x} ${o.y - h} l ${2 * k} ${-50 * k}`, stroke: '#c9b06a', 'stroke-width': 5 * k, 'stroke-linecap': 'round' }, gp);
        pes.push({ g: gp, x, base: o.y, f: hash(x) * 6 });
      }
      let mexe = [];
      return { g: p, mexe(x, k = 1) { mexe.push([x, k]); }, quadro(tt, vento = 1) {
        for (const pe of pes) {
          let a = Math.sin(tt * 1.1 + pe.f) * 1.6 * vento;
          for (const [mx, f] of mexe) { const d = Math.abs(pe.x - mx); if (d < 160 * k) a += Math.sin(tt * 14 + pe.f) * 7 * f * (1 - d / (160 * k)); }
          pe.g.setAttribute('transform', `rotate(${a} ${pe.x} ${pe.base})`);
        }
        mexe = [];
      } };
    }

    // ---------- casa vista de fora (a do vizinho, a do sítio) ----------
    // o: {x (esquerda), chao, larg, alt (da parede), cor, telhado, porta: cor, janelas: n, varanda: true}. Devolve a porta (K.porta),
    // as janelas (cada uma com luz(k): a janela acesa) e um grupo atores, na frente da casa.
    function casa(g, o) {
      const p = el('g', {}, g), { x, chao: ch } = o, larg = o.larg || 900, alt = o.alt || 700, cor = o.cor || '#d9cdb4';
      R(p, x, ch - alt, larg, alt, cor);
      P(p, `M ${x - 60} ${ch - alt} L ${x + larg / 2} ${ch - alt - alt * 0.45} L ${x + larg + 60} ${ch - alt} Z`, o.telhado || '#8a3a2a');
      for (let i = 1; i < 6; i++) L(p, x - 60 + i * (larg + 120) / 12, ch - alt - 4, x + larg / 2, ch - alt - alt * 0.44, escuro(o.telhado || '#8a3a2a', 0.2), 3);
      const altP = alt * 0.78, pt = porta(p, { x: x + larg * 0.62, chao: ch, alt: altP, larg: altP * 0.3, cor: o.porta || '#3a5a8a' });
      const janelas = [];
      for (let i = 0; i < (o.janelas ?? 1); i++) {
        const jx = x + larg * (0.12 + i * 0.25), jy = ch - alt * 0.72, jw = larg * 0.2, jh = alt * 0.32;
        R(p, jx - 10, jy - 10, jw + 20, jh + 20, '#e8e2d6');
        const vidro = el('rect', { x: jx, y: jy, width: jw, height: jh, fill: '#1a2238' }, p);
        L(p, jx + jw / 2, jy, jx + jw / 2, jy + jh, TINTA, 5); L(p, jx, jy + jh / 2, jx + jw, jy + jh / 2, TINTA, 5);
        janelas.push({ luz: kk => vidro.setAttribute('fill', Boneco.mix('#1a2238', '#ffcf7a', clamp(kk))) });
      }
      if (o.varanda !== false) { R(p, x - 40, ch - 18, larg + 80, 26, '#9a8a72', { 'stroke-width': 4 }); for (const px of [x - 30, x + larg + 20]) R(p, px, ch - alt - 10, 16, alt - 8, '#6b5038', { 'stroke-width': 4 }); }
      const atores = el('g', {}, g);
      return { g: p, porta: pt, janelas, atores };
    }

    // ---------- facho de luz (lanterna, farol, celular) ----------
    // Um cone nítido que sai de [x, y] na direção "ang" (graus; 0 para a direita), com o círculo de luz onde bate.
    // quadro([x, y], ang, forca): a luz acompanha a mão (Boneco.ondeEsta) e para onde o personagem aponta.
    function facho(g, o = {}) {
      const p = el('g', {}, g), id = novoId('f'), cor = o.cor || '#fff2c8', alc = o.alcance || 700, ab = (o.abertura || 22) * Math.PI / 180;
      S.svg.querySelector('defs').insertAdjacentHTML('beforeend', `<linearGradient id="${id}" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="${cor}" stop-opacity="0.85"/><stop offset="100%" stop-color="${cor}" stop-opacity="0.05"/></linearGradient>`);
      const cone = el('path', { fill: `url(#${id})`, style: 'mix-blend-mode:screen' }, p);
      const borda = el('path', { fill: 'none', stroke: cor, 'stroke-width': 2, opacity: 0.35 }, p);
      const mancha = el('ellipse', { rx: alc * Math.tan(ab) * 0.9, ry: alc * Math.tan(ab) * 0.45, fill: cor, opacity: 0.35, filter: u('desf10'), style: 'mix-blend-mode:screen' }, p);
      const brilho = el('circle', { r: 22, fill: cor, opacity: 0.9, filter: u('desf4') }, p);
      return { g: p, quadro([x, y], ang, forca = 1) {
        const a = ang * Math.PI / 180, ex = x + Math.cos(a) * alc, ey = y + Math.sin(a) * alc, n = [-Math.sin(a), Math.cos(a)], r = alc * Math.tan(ab);
        const pa = [ex + n[0] * r, ey + n[1] * r], pb = [ex - n[0] * r, ey - n[1] * r];
        cone.setAttribute('d', `M ${x} ${y} L ${pa[0]} ${pa[1]} L ${pb[0]} ${pb[1]} Z`);
        borda.setAttribute('d', `M ${pa[0]} ${pa[1]} L ${x} ${y} L ${pb[0]} ${pb[1]}`);
        mancha.setAttribute('cx', ex); mancha.setAttribute('cy', ey); mancha.setAttribute('transform', `rotate(${ang + 90} ${ex} ${ey})`);
        brilho.setAttribute('cx', x); brilho.setAttribute('cy', y);
        p.setAttribute('opacity', clamp(forca));
      } };
    }

    // ---------- figura que se mexe no diagrama (um ponto com rastro) ----------
    function marcador(g, cor = '#ff5a4a') {
      const p = el('g', {}, g);
      const halo = el('circle', { r: 34, fill: cor, opacity: 0.25 }, p);
      el('circle', { r: 14, fill: cor, stroke: '#fff', 'stroke-width': 4 }, p);
      return { g: p, em(x, y, tt) { p.setAttribute('transform', `translate(${x} ${y})`); halo.setAttribute('r', 26 + 10 * Math.abs(Math.sin(tt * 4))); } };
    }

    return { L, R, C, P, escuro, recorte, escala, pe, fundo, parede, azulejo, chao, rodape, porta, portaPorDentro, janela, ceu, morro, grama, estrada, cerca, arvore, plantacao, casa, facho,
      luminaria, sofa, mesa, quadroParede, bagunca, olhoMagico, corte, marcador };
  }
  window.Cenario = { kit };
})();
