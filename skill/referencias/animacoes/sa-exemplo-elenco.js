// Exemplo do Estilo Série Animada: o elenco da série do prédio (você, o Marcos, a síndica, o neto). Só para ver como uma ficha é feita.
// Condomínio Fechado: o elenco. Cada personagem é uma ficha para o Boneco do kit (sa-personagem.js): cores, medidas e a marca dele.
// Vem do dia 2 sem mudança, para os personagens continuarem iguais de um dia para o outro.
const ELENCO = (function () {
  const { cabelo, par, liga, mix, mul } = Boneco;
  const E = {
    // VOCÊ, do 1402: camiseta lisa de manga curta, jeans, tênis branco, cabelo crespo curto e volumoso
    voce: {
      pele: '#b9774c', peleSombra: '#8a5232', sobrancelha: '#1c1513',
      camisa: '#2f7a80', camisaSombra: '#1f5559', calca: '#2b3a55', calcaSombra: '#1c2639',
      sapato: '#eeeae0', sapatoSombra: '#b9b2a4',
      detalhes({ el, pecas, M, TINTA }) {
        const c = pecas.cabeca, r = M.cabeca, t = pecas.tronco;
        const cor = '#2a1f1b', luz = '#5a463d';
        // crespo curto: contorno de fora em cachos, passando da cabeça; de perfil cobre o alto e a nuca
        const cachos = [[0.18, -0.98, 0.26, -1.06, 0.34, -0.98], [-0.18, -1.04, -0.1, -1.12, -0.02, -1.04], [-0.55, -0.88, -0.47, -0.96, -0.39, -0.88], [-0.86, -0.5, -0.78, -0.58, -0.7, -0.5], [-0.82, -0.1, -0.74, -0.18, -0.66, -0.1], [-0.3, -0.7, -0.22, -0.78, -0.14, -0.7]];
        const cp = cabelo(el, c.frente, TINTA, r,
          [[0.6, -0.62], [0.68, -0.88], [0.48, -1.1], [0.18, -1.24], [-0.16, -1.26], [-0.5, -1.15], [-0.82, -0.94], [-1.08, -0.6], [-1.18, -0.22], [-1.1, 0.14], [-0.86, 0.36]],
          [[-0.62, 0.2], [-0.48, -0.1], [-0.18, -0.38], [0.2, -0.52], [0.6, -0.62]], 0.62, cor, cachos, luz);
        const cf = cabelo(el, c.frente, TINTA, r,
          [[-0.86, -0.16], [-1.06, -0.5], [-0.94, -0.92], [-0.62, -1.18], [-0.2, -1.28], [0.2, -1.28], [0.62, -1.18], [0.94, -0.92], [1.06, -0.5], [0.86, -0.16]],
          [[0.72, -0.42], [0.36, -0.58], [0, -0.6], [-0.36, -0.58], [-0.72, -0.42], [-0.86, -0.16]], 0.62, cor,
          [[-0.5, -0.92, -0.42, -1.0, -0.34, -0.92], [0.0, -1.02, 0.08, -1.1, 0.16, -1.02], [0.46, -0.9, 0.54, -0.98, 0.62, -0.9], [-0.22, -0.78, -0.14, -0.86, -0.06, -0.78], [0.24, -0.76, 0.32, -0.84, 0.4, -0.76]], luz);
        // manga curta: do meio do braço para baixo é pele; barra da manga marcada
        for (const n of ['bracoF', 'bracoT']) {
          el('rect', { x: -40, y: M.braco * 0.62, width: 80, height: M.braco, fill: '#b9774c' }, pecas[n].p1.extra);
          el('path', { d: `M -30 ${M.braco * 0.62} L 30 ${M.braco * 0.62}`, stroke: TINTA, 'stroke-width': 6 }, pecas[n].p1.extra);
        }
        // gola redonda
        el('path', { d: `M ${-M.ombro * 0.22} ${-M.tronco + 2} Q 0 ${-M.tronco + 30} ${M.ombro * 0.22} ${-M.tronco + 2}`, fill: 'none', stroke: TINTA, 'stroke-width': 6 }, t.pF.extra);
        el('path', { d: `M ${-M.prof * 0.1} ${-M.tronco + 2} Q ${M.prof * 0.25} ${-M.tronco + 22} ${M.prof * 0.42} ${-M.tronco + 4}`, fill: 'none', stroke: TINTA, 'stroke-width': 6 }, t.p1.extra);
        pecas.pares = [par(cp, cf)];
      },
      atualiza({ pecas, frente }) { liga(pecas.pares, frente); }
    },

    // MARCOS, do 1403: camisa amarela da seleção (gola e punhos verdes), bermuda azul, chinelo de dedo, barba por fazer, curativo
    marcos: {
      pele: '#d39a6a', peleSombra: '#a46e45', sobrancelha: '#2b1d16',
      camisa: '#f2c624', camisaSombra: '#c99a12', calca: '#2d5aa0', calcaSombra: '#1f3f73',
      canela: '#d39a6a', canelaSombra: '#a46e45', sapato: '#d39a6a', sapatoSombra: '#a46e45',
      medidas: { tronco: 310, ombro: 186, prof: 132, cintura: 130 }, barriga: 10,
      detalhes({ el, pecas, M, P, TINTA }) {
        const c = pecas.cabeca, r = M.cabeca, t = pecas.tronco;
        const cab = '#2b1d16';
        // cabelo volumoso e arredondado, com um topete cheio na frente, e costeleta fina
        const cor = '#2b1d16', luz = '#6a4a36';
        const fios = [[0.42, -0.9, 0.2, -1.12, -0.12, -1.16], [0.1, -0.86, -0.18, -1.02, -0.5, -1.02], [-0.4, -0.78, -0.7, -0.84, -0.9, -0.6]];
        const cp = cabelo(el, c.frente, TINTA, r,
          [[0.5, -0.64], [0.78, -0.86], [0.7, -1.14], [0.3, -1.32], [-0.22, -1.32], [-0.7, -1.16], [-1.04, -0.84], [-1.14, -0.42], [-1.06, -0.02], [-0.9, 0.2]],
          [[-0.68, 0.1], [-0.46, -0.22], [-0.12, -0.44], [0.2, -0.54], [0.5, -0.64]], -1, cor, fios, luz);
        const cf = cabelo(el, c.frente, TINTA, r,
          [[-0.98, -0.16], [-1.14, -0.58], [-1.0, -1.0], [-0.6, -1.3], [0.02, -1.38], [0.6, -1.3], [1.0, -1.0], [1.14, -0.58], [0.98, -0.16]],
          [[0.86, -0.36], [0.5, -0.56], [0.1, -0.62], [-0.14, -0.52], [-0.5, -0.58], [-0.86, -0.36], [-0.98, -0.16]], -1, cor,
          [[-0.14, -0.6, -0.3, -0.95, -0.7, -1.05], [0.1, -0.66, 0.35, -1.0, 0.75, -1.02], [-0.6, -0.55, -0.85, -0.75, -0.95, -0.55]], luz);
        // barba por fazer: textura de pontinhos no queixo e na mandíbula
        const bp = el('g', {}, c.frente), bf = el('g', {}, c.frente);
        for (let i = 0; i < 46; i++) {
          const a = (i * 137.5) % 360 * Math.PI / 180, rr = 0.25 + ((i * 53) % 100) / 140;
          const x = r * (0.15 + rr * 0.75 * Math.cos(a) * 0.9), y = r * (0.55 + Math.abs(Math.sin(a)) * 0.32 * rr);
          if (x > -r * 0.55 && x < r * 0.9) el('circle', { cx: x, cy: y, r: 2.2, fill: '#3a2618', opacity: 0.55 }, bp);
          el('circle', { cx: r * (rr * 1.3 * Math.cos(a)) * 0.7, cy: r * (0.6 + Math.abs(Math.sin(a)) * 0.3 * rr), r: 2.2, fill: '#3a2618', opacity: 0.55 }, bf);
        }
        const or = el('g', {}, c.frente); // sem orelha, como no traço do Edu
        // camisa da seleção: gola verde em V, faixas verdes nos punhos da manga
        const golaP = el('path', { d: `M ${-M.prof * 0.22} ${-M.tronco + 2} Q ${M.prof * 0.2} ${-M.tronco + 30} ${M.prof * 0.46} ${-M.tronco + 8}`, fill: 'none', stroke: '#1d8a4a', 'stroke-width': 12, 'stroke-linecap': 'round' }, t.p1.fora);
        const golaF = el('path', { d: `M ${-M.ombro * 0.24} ${-M.tronco + 2} L 0 ${-M.tronco + 46} L ${M.ombro * 0.24} ${-M.tronco + 2}`, fill: 'none', stroke: '#1d8a4a', 'stroke-width': 12, 'stroke-linejoin': 'round', 'stroke-linecap': 'round' }, t.pF.fora);
        el('path', { d: `M ${-M.ombro} ${-M.tronco * 0.55} L ${M.ombro} ${-M.tronco * 0.55}`, stroke: '#1d8a4a', 'stroke-width': 0 }, t.pF.extra);
        // escudo genérico (sem marca): um losango verde pequeno no peito
        el('path', { d: `M ${M.ombro * 0.22} ${-M.tronco + 70} l 14 14 l -14 14 l -14 -14 Z`, fill: '#1d8a4a', stroke: TINTA, 'stroke-width': 3 }, t.pF.extra);
        for (const n of ['bracoF', 'bracoT']) el('rect', { x: -40, y: M.braco - 26, width: 80, height: 12, fill: '#1d8a4a' }, pecas[n].p1.extra);
        // a manga é curta: o braço do ombro até a manga é camisa, e dali para baixo é pele
        for (const n of ['bracoF', 'bracoT']) el('rect', { x: -40, y: M.braco - 14, width: 80, height: 40, fill: P.pele }, pecas[n].p1.extra);
        // barra da bermuda
        for (const n of ['pernaF', 'pernaT']) el('path', { d: `M -40 ${M.coxa - 6} L 40 ${M.coxa - 6}`, stroke: TINTA, 'stroke-width': 6 }, pecas[n].p1.extra);
        // chinelo de dedo: sola azul e a tira
        for (const n of ['pernaF', 'pernaT']) {
          const p = pecas[n];
          el('path', { d: `M ${-M.wk * 0.6} ${M.canela + 20} L ${M.wk * 1.95} ${M.canela + 20} L ${M.wk * 1.95} ${M.canela + 28} L ${-M.wk * 0.6} ${M.canela + 28} Z`, fill: '#2f64b5', stroke: TINTA, 'stroke-width': 4 }, p.p3.fora);
          el('path', { d: `M ${M.wk * 1.2} ${M.canela + 14} L ${M.wk * 0.3} ${M.canela - 6}`, stroke: '#2f64b5', 'stroke-width': 7, 'stroke-linecap': 'round' }, p.p3.fora);
        }
        // curativo no antebraço da frente: gaze branca com mancha de sangue
        const a = pecas.bracoF.p2;
        el('path', { d: `M -26 26 L 26 26 L 24 92 L -24 92 Z`, fill: '#efe9dc', stroke: TINTA, 'stroke-width': 5, 'stroke-linejoin': 'round' }, a.fora);
        el('path', { d: `M -12 44 C 4 34 20 48 12 62 C 6 76 -14 70 -14 58 C -18 54 -16 48 -12 44 Z`, fill: '#a5232c' }, a.fora);
        el('path', { d: `M -24 50 L 24 48 M -22 72 L 22 70`, stroke: '#bdb4a2', 'stroke-width': 3 }, a.fora);
        pecas.pares = [par(cp, cf), par(bp, bf), par(or, el('g', {}, c.frente)), par(golaP, golaF)];
      },
      atualiza({ pecas, frente }) { liga(pecas.pares, frente); }
    },

    // DONA ROSÂNGELA, a síndica: bobes coloridos no cabelo acaju, óculos na cordinha, robe florido, chinelo
    rosangela: {
      pele: '#e8bf9c', peleSombra: '#b98e6c', sobrancelha: '#5a2a1e',
      camisa: '#cf6f86', camisaSombra: '#9e4c61', calca: '#cf6f86', calcaSombra: '#9e4c61',
      canela: '#e8bf9c', canelaSombra: '#b98e6c', sapato: '#e8bf9c', sapatoSombra: '#b98e6c',
      manga: '#cf6f86', mangaSombra: '#9e4c61', antebraco: '#cf6f86', antebracoSombra: '#9e4c61',
      medidas: { tronco: 290, ombro: 160, prof: 128, cintura: 150, coxa: 176, canela: 178 }, barriga: 14,
      detalhes({ el, pecas, M, TINTA }) {
        const c = pecas.cabeca, r = M.cabeca, t = pecas.tronco;
        const cor = '#8e3a26', luz = '#c4684a';
        const ondas = [[-1.1, -0.5, -1.0, -0.3, -1.12, -0.1], [-0.95, -0.85, -0.78, -0.72, -0.82, -0.5], [-0.6, -0.98, -0.42, -0.9, -0.48, -0.7], [-1.05, 0.15, -0.92, 0.32, -0.98, 0.45]];
        const cp = cabelo(el, c.frente, TINTA, r,
          [[0.55, -0.66], [0.66, -0.98], [0.36, -1.2], [-0.04, -1.32], [-0.5, -1.28], [-0.92, -1.05], [-1.26, -0.66], [-1.38, -0.2], [-1.3, 0.26], [-1.04, 0.58], [-0.68, 0.62]],
          [[-0.5, 0.26], [-0.42, -0.14], [-0.15, -0.48], [0.2, -0.6], [0.55, -0.66]], 0.58, cor, ondas, luz);
        const cf = cabelo(el, c.frente, TINTA, r,
          [[-0.9, 0.18], [-1.26, -0.14], [-1.34, -0.6], [-1.1, -1.02], [-0.7, -1.28], [-0.2, -1.4], [0.3, -1.38], [0.76, -1.24], [1.12, -0.98], [1.34, -0.58], [1.26, -0.14], [0.9, 0.18]],
          [[0.84, -0.24], [0.56, -0.54], [0.16, -0.62], [-0.24, -0.6], [-0.6, -0.5], [-0.86, -0.2], [-0.9, 0.18]], 0.58, cor,
          [[-1.1, -0.4, -0.98, -0.2, -1.1, 0.0], [1.1, -0.4, 0.98, -0.2, 1.1, 0.0], [-0.7, -0.9, -0.55, -0.8, -0.6, -0.62], [0.7, -0.9, 0.55, -0.8, 0.6, -0.62]], luz);
        // bobes: cilindros coloridos presos no cabelo armado
        const cores = ['#f08aa8', '#7cc3e8', '#f4d36b', '#9be08a', '#c9a0f0'];
        const bobe = (g, x, y, ang, cor) => {
          const b = el('g', { transform: `translate(${x} ${y}) rotate(${ang})` }, g);
          el('rect', { x: -27, y: -16, width: 54, height: 32, rx: 13, fill: cor, stroke: TINTA, 'stroke-width': 5 }, b);
          for (const k of [-12, 0, 12]) el('path', { d: `M ${k} -14 L ${k} 14`, stroke: TINTA, 'stroke-width': 3, opacity: 0.5 }, b);
        };
        const bp = el('g', {}, c.frente), bf = el('g', {}, c.frente);
        [[0.3, -1.18, 15], [-0.12, -1.3, -5], [-0.56, -1.2, -30], [-0.96, -0.95, -55], [-1.24, -0.5, -80]].forEach(([x, y, a], i) => bobe(bp, x * r, y * r, a, cores[i]));
        [[-0.72, -1.22, -30], [-0.22, -1.38, -8], [0.3, -1.36, 8], [0.78, -1.2, 30], [-1.16, -0.86, -60], [1.18, -0.86, 60]].forEach(([x, y, a], i) => bobe(bf, x * r, y * r, a, cores[i % 5]));
        // óculos: de perfil, uma lente e a haste; de frente, as duas lentes. A cordinha cai pelo pescoço.
        const op = el('g', {}, c.frente);
        el('rect', { x: r * 0.46 - 24, y: -r * 0.08 - 20, width: 46, height: 38, rx: 12, fill: 'rgba(220,235,255,0.14)', stroke: TINTA, 'stroke-width': 5 }, op);
        el('path', { d: `M ${r * 0.46 - 24} ${-r * 0.1} L ${-r * 0.2} ${-r * 0.16}`, stroke: TINTA, 'stroke-width': 5 }, op);
        el('path', { d: `M ${-r * 0.2} ${-r * 0.16} Q ${-r * 0.35} ${r * 0.6} ${-r * 0.1} ${r * 1.15}`, fill: 'none', stroke: '#c9a24a', 'stroke-width': 3 }, op);
        const of = el('g', {}, c.frente);
        for (const s of [-1, 1]) el('rect', { x: s * r * 0.36 - 24, y: -r * 0.06 - 20, width: 48, height: 38, rx: 12, fill: 'rgba(220,235,255,0.14)', stroke: TINTA, 'stroke-width': 5 }, of);
        el('path', { d: `M ${-r * 0.36 + 24} ${-r * 0.06} L ${r * 0.36 - 24} ${-r * 0.06}`, stroke: TINTA, 'stroke-width': 5 }, of);
        for (const s of [-1, 1]) el('path', { d: `M ${s * (r * 0.36 + 24)} ${-r * 0.04} Q ${s * r * 1.0} ${r * 0.7} ${s * r * 0.5} ${r * 1.2}`, fill: 'none', stroke: '#c9a24a', 'stroke-width': 3 }, of);
        // robe florido com faixa amarrada na cintura
        for (const p of [t.p1, t.pF]) {
          for (const [x, y] of [[-30, -230], [30, -170], [-20, -100], [36, -60], [-40, -30], [6, -260]]) {
            el('circle', { cx: x, cy: y, r: 7, fill: '#f4d36b' }, p.extra);
            for (let k = 0; k < 5; k++) { const a = k * 72 * Math.PI / 180; el('circle', { cx: x + Math.cos(a) * 13, cy: y + Math.sin(a) * 13, r: 7, fill: '#f8e8ee', opacity: 0.9 }, p.extra); }
          }
          el('path', { d: `M -90 -86 L 90 -86`, stroke: '#9e4c61', 'stroke-width': 14 }, p.extra);
        }
        // robe comprido: a coxa e o antebraço também são de pano; barra do robe no joelho
        for (const n of ['pernaF', 'pernaT']) el('path', { d: `M -40 ${M.coxa - 6} Q 0 ${M.coxa + 8} 40 ${M.coxa - 6}`, fill: 'none', stroke: TINTA, 'stroke-width': 6 }, pecas[n].p1.extra);
        for (const n of ['bracoF', 'bracoT']) el('path', { d: `M -30 ${M.ante - 30} L 30 ${M.ante - 30} L 30 ${M.ante + 20} L -30 ${M.ante + 20} Z`, fill: '#e8bf9c' }, pecas[n].p2.extra);
        // chinelo
        for (const n of ['pernaF', 'pernaT']) {
          const p = pecas[n];
          el('path', { d: `M ${-M.wk * 0.6} ${M.canela + 20} L ${M.wk * 1.95} ${M.canela + 20} L ${M.wk * 1.95} ${M.canela + 28} L ${-M.wk * 0.6} ${M.canela + 28} Z`, fill: '#f08aa8', stroke: TINTA, 'stroke-width': 4 }, p.p3.fora);
          el('path', { d: `M ${M.wk * 1.2} ${M.canela + 14} L ${M.wk * 0.3} ${M.canela - 6}`, stroke: '#f08aa8', 'stroke-width': 7, 'stroke-linecap': 'round' }, p.p3.fora);
        }
        pecas.pares = [par(cp, cf), par(bp, bf), par(op, of)];
      },
      atualiza({ pecas, frente }) { liga(pecas.pares, frente); }
    },


    // O NETO, uns 5 anos: pijama de dinossauro verde, com capuz e espinhos laranja
    neto: {
      pele: '#a8693f', peleSombra: '#7a4727', semBochecha: false,
      camisa: '#58b05a', camisaSombra: '#3d8740', calca: '#58b05a', calcaSombra: '#3d8740',
      manga: '#58b05a', mangaSombra: '#3d8740', sapato: '#58b05a', sapatoSombra: '#3d8740',
      escala: 0.6,
      medidas: { tronco: 220, ombro: 150, prof: 120, cintura: 130, braco: 118, ante: 106, coxa: 136, canela: 124, cabeca: 104, wb: 52, wa: 46, wc: 64, wk: 56 },
      detalhes({ el, pecas, M, TINTA }) {
        const c = pecas.cabeca, r = M.cabeca, t = pecas.tronco;
        // capuz de dinossauro: cobre o alto e as costas da cabeça, com espinhos e dois olhinhos
        const espinhos = (g, pts) => { for (const [x, y, a] of pts) el('path', { d: `M -14 0 L 0 -26 L 14 0 Z`, transform: `translate(${x} ${y}) rotate(${a})`, fill: '#f08a3c', stroke: TINTA, 'stroke-width': 4, 'stroke-linejoin': 'round' }, g); };
        const hp = el('g', {}, c.frente);
        espinhos(hp, [[-r * 0.2, -r * 1.12, -10], [-r * 0.68, -r * 0.9, -45], [-r * 1.0, -r * 0.4, -80], [r * 0.28, -r * 1.06, 15]]);
        el('path', { d: `M ${r * 0.62} ${-r * 0.82} C ${r * 0.1} ${-r * 1.22} ${-r * 1.0} ${-r * 1.1} ${-r * 1.1} ${-r * 0.1} C ${-r * 1.12} ${r * 0.4} ${-r * 0.9} ${r * 0.8} ${-r * 0.6} ${r * 0.95} L ${-r * 0.48} ${r * 0.2} C ${-r * 0.4} ${-r * 0.4} ${r * 0.1} ${-r * 0.62} ${r * 0.62} ${-r * 0.82} Z`, fill: '#58b05a', stroke: TINTA, 'stroke-width': 6, 'stroke-linejoin': 'round' }, hp);
        el('circle', { cx: r * 0.1, cy: -r * 0.9, r: 7, fill: '#fff', stroke: TINTA, 'stroke-width': 3 }, hp);
        const hf = el('g', {}, c.frente);
        espinhos(hf, [[0, -r * 1.16, 0], [-r * 0.62, -r * 0.96, -35], [r * 0.62, -r * 0.96, 35]]);
        el('path', { d: `M ${-r * 1.1} ${r * 0.5} C ${-r * 1.2} ${-r * 1.15} ${r * 1.2} ${-r * 1.15} ${r * 1.1} ${r * 0.5} L ${r * 0.85} ${r * 0.3} C ${r * 0.85} ${-r * 0.5} ${-r * 0.85} ${-r * 0.5} ${-r * 0.85} ${r * 0.3} Z`, fill: '#58b05a', stroke: TINTA, 'stroke-width': 6, 'stroke-linejoin': 'round' }, hf);
        for (const s of [-1, 1]) el('circle', { cx: s * r * 0.35, cy: -r * 0.78, r: 8, fill: '#fff', stroke: TINTA, 'stroke-width': 3 }, hf);
        // espinhos nas costas do pijama (perfil) e barriga mais clara (frente)
        espinhos(t.atras, [[-M.prof * 0.5, -M.tronco * 0.75, -90], [-M.prof * 0.5, -M.tronco * 0.45, -90], [-M.prof * 0.5, -M.tronco * 0.15, -90]]);
        el('ellipse', { cx: 0, cy: -M.tronco * 0.4, rx: M.ombro * 0.28, ry: M.tronco * 0.3, fill: '#c9e8a6' }, t.pF.extra);
        el('ellipse', { cx: M.prof * 0.3, cy: -M.tronco * 0.4, rx: M.prof * 0.22, ry: M.tronco * 0.3, fill: '#c9e8a6' }, t.p1.extra);
        // mãos de fora do pijama
        pecas.pares = [par(hp, hf)];
      },
      atualiza({ pecas, frente }) { liga(pecas.pares, frente); }
    }
  };
  // o Marcos se transformando: a pele puxando para o verde (Vitório, 2026-11-18)
  E.marcosZ = Object.assign({}, E.marcos, { pele: '#b3a676', peleSombra: '#857a50', canela: '#b3a676', canelaSombra: '#857a50', sapato: '#b3a676', sapatoSombra: '#857a50' });
  return E;
})();
