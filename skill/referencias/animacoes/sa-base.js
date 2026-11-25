// Série Animada: as ferramentas da cena. Entra no <script> com <!--#inclui sa-base.js-->, depois do sa-personagem.js.
// const S = SA.cena(svg, PALAVRAS) dá: o tempo das palavras (S.t("@abre")), as curvas, a câmera, a boca e o piscar,
// o acabamento (granulado, vinheta, desfoques, brilhos, fumaça, poeira), os planos com dissolve e corte seco,
// e as peças fixas da série (legenda, etiqueta de quem fala, selo, contador, cartão, botões da escolha).
// No fim: S.ligar(S.filme(planos)). Cada quadro é desenhado só a partir do tempo: nada de Math.random, relógio ou loop.
(function () {
  const NS = 'http://www.w3.org/2000/svg';
  const W = 1080, H = 1920;
  const TINTA = (window.Boneco && window.Boneco.TINTA) || '#17121c';
  function el(tag, attrs, parent) {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }

  // ---------- curvas ----------
  const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
  const lerp = (a, b, k) => a + (b - a) * k;
  const suave = k => { k = clamp(k); return k * k * (3 - 2 * k); };
  const suave2 = k => { k = clamp(k); return k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2; };
  const sai = k => 1 - Math.pow(1 - clamp(k), 3);
  const entra = k => Math.pow(clamp(k), 3);
  const prog = (t, a, b) => clamp((t - a) / (b - a));
  // chaves: [[t, valor], ...] com curva suave entre elas (câmera, posição, luz)
  function chave(t, ks, curva = suave2) {
    if (t <= ks[0][0]) return ks[0][1];
    for (let i = 1; i < ks.length; i++) if (t <= ks[i][0]) return lerp(ks[i - 1][1], ks[i][1], curva((t - ks[i - 1][0]) / (ks[i][0] - ks[i - 1][0])));
    return ks[ks.length - 1][1];
  }
  // ruído determinístico: o mesmo t dá o mesmo valor (o render desenha cada quadro sozinho, fora de ordem)
  const hash = n => { const s = Math.sin(n * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); };
  const ruido = x => { const i = Math.floor(x), f = x - i; return lerp(hash(i), hash(i + 1), f * f * (3 - 2 * f)); };

  // ---------- poses de movimento (para o Boneco.posar) ----------
  const andar = (ph, amp = 1) => ({ pernaF: { a: -22 * amp * Math.sin(ph), b: Math.max(0, 34 * Math.sin(ph + 1.3)) * amp }, pernaT: { a: 22 * amp * Math.sin(ph), b: Math.max(0, -34 * Math.sin(ph + 1.3)) * amp }, bracoF: { a: 16 * amp * Math.sin(ph), b: -18 }, bracoT: { a: -16 * amp * Math.sin(ph), b: -18 }, quadrilY: -Math.abs(Math.cos(ph)) * 8 * amp });
  const correr = ph => ({ tronco: 14, pernaF: { a: -40 * Math.sin(ph) - 10, b: 20 + 60 * Math.max(0, Math.sin(ph + 1.4)) }, pernaT: { a: 40 * Math.sin(ph) - 10, b: 20 + 60 * Math.max(0, -Math.sin(ph + 1.4)) }, bracoF: { a: 40 * Math.sin(ph), b: -90 }, bracoT: { a: -40 * Math.sin(ph), b: -90 }, quadrilY: -Math.abs(Math.cos(ph)) * 22 });
  const parado = { pernaF: { a: -3, b: 2 }, pernaT: { a: 4, b: 2 }, bracoF: { a: -4, b: -6 }, bracoT: { a: 6, b: -10 } };
  const respira = t => Math.sin(t * 1.8) * 1.6;
  // ---------- andar sem patinar ----------
  // A perna anda o que o corpo anda: a fase do passo sai da distância percorrida, e a amplitude, da velocidade.
  // Assim a perna não dispara quando a velocidade muda, e não fica andando parada quando o corpo para (Vitório, 2026-11-20).
  // posDe(t): onde a pessoa está ([x, y] ou só x). passada: o comprimento de um passo, em px da tela (uns 0,6 da perna).
  // Devolve {ph, amp, x}: use andar(ph, amp) (ou o andar do personagem) e passo(ph) * amp no "achata".
  function caminhada(posDe, t, de, passada, vNormal) {
    const P = tt => { const v = posDe(tt); return Array.isArray(v) ? v : [v, 0]; };
    let dist = 0, [x0, y0] = P(de);
    const n = Math.max(2, Math.ceil((t - de) * 30));
    for (let i = 1; i <= n; i++) { const [x1, y1] = P(de + (t - de) * i / n); dist += Math.hypot(x1 - x0, y1 - y0); x0 = x1; y0 = y1; }
    const [a0, b0] = P(t - 0.04), [a1, b1] = P(t + 0.04), vel = Math.hypot(a1 - a0, b1 - b0) / 0.08;
    return { ph: dist / passada * Math.PI, amp: clamp(vel / (vNormal || passada * 1.6)), x: P(t)[0] };
  }
  const passo = ph => Math.max(0, Math.cos(2 * ph)) * 0.22; // o achatar de cada passo, quando o pé bate no chão
  // ---------- princípios de personagem (ver animacoes.md, "Princípios de movimento") ----------
  // antes(k, recuo): curva com antecipação: recua um pouco no sentido contrário e depois vai, assentando com um passo além.
  // Use no lugar do suave() em todo movimento grande (levantar, virar, correr, girar a chave).
  const antes = (k, recuo = 1.4) => { k = clamp(k); const c = recuo * 1.525; return k < 0.5 ? (Math.pow(2 * k, 2) * ((c + 1) * 2 * k - c)) / 2 : (Math.pow(2 * k - 2, 2) * ((c + 1) * (k * 2 - 2) + c) + 2) / 2; };
  // arco(k, [x0, y0], [x1, y1], altura): o ponto no caminho em curva (nada se desloca em linha reta). altura > 0 sobe no meio.
  const arco = (k, a, b, altura = 80) => { k = clamp(k); return [lerp(a[0], b[0], k), lerp(a[1], b[1], k) - Math.sin(k * Math.PI) * altura]; };
  // impacto(t, em, forca): o achatar que volta, para o "achata" da pose: no instante "em" comprime e assenta com um balanço curto.
  const impacto = (t, em, forca = 1) => { const d = t - em; if (d < 0 || d > 0.45) return 0; return forca * Math.exp(-d * 9) * Math.cos(d * 22); };
  // susto(t, em): estica (achata negativo) e volta, com o tranco do corpo
  const susto = (t, em, forca = 1) => -impacto(t, em, forca);
  // segue(t, atraso, fn): ação secundária: a mesma curva um pouco depois (cabelo, roupa, a cabeça que acompanha o tronco)
  const segue = (t, atraso, fn) => fn(t - atraso);
  const mistura = (a, b) => Object.assign({}, a, b, ...['pernaF', 'pernaT', 'bracoF', 'bracoT'].map(k => ({ [k]: Object.assign({}, a[k], b[k]) })));

  // ---------- luzes: toda luz sai de algum lugar da cena (lâmpada, lua, tela do celular, fogo) ----------
  const LUZ = {
    lampada: { ang: -50, recorte: '#ffd7a1', forca: 0.9 },
    lua: { ang: -130, recorte: '#a9c3ff', forca: 0.8 },
    celular: { ang: 10, recorte: '#9fd0ff', forca: 1 },
    fogo: { ang: 60, recorte: '#ffa24a', forca: 1 },
  };
  // a cor da luz da cena, que tinge tudo (pele, roupa, cabelo, estampa)
  const AMBIENTE = { noite: '#7b84b4', noiteEscura: '#59628f', sala: '#d8c7b5', lampada: '#efe0c8', fogo: '#ffc79a', dia: '#ffffff' };

  // ---------- palavras da fala ----------
  const normal = s => String(s).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/[^a-z0-9%]/g, '');

  // cor e fonte da marca da pessoa (variáveis do montar), com um padrão se faltar
  function cssVar(nome, padrao) {
    const v = getComputedStyle(document.documentElement).getPropertyValue(nome).trim();
    return v || padrao;
  }

  function cena(svg, palavras) {
    const pal = (palavras || []).map((p, i) => Object.assign({ quem: 'narrador' }, p, { i }));
    // falas: as palavras seguidas de quem fala (o "voz" com personagens grava o número da fala em cada palavra)
    const falas = [];
    pal.forEach((p, i) => {
      const ant = pal[i - 1];
      const nova = !ant || (p.fala != null ? p.fala !== ant.fala : (p.quem !== ant.quem || /[.!?]$/.test(ant.texto)));
      if (nova) falas.push({ quem: p.quem, inicio: p.inicio, fim: p.fim, palavras: [] });
      const f = falas[falas.length - 1]; f.palavras.push(p); f.fim = p.fim;
    });
    // "@abre", "@abre#2" (a segunda vez), "@abre+0.3" (0,3 s depois), "@abre#2-0.2": a mesma regra do roteiro.json
    function achar(ref) {
      const m = String(ref).match(/^@(.+?)(?:#(\d+))?([+-]\d+(?:\.\d+)?)?$/);
      if (!m) throw new Error('tempo inválido: ' + ref);
      const alvo = normal(m[1]), vez = +(m[2] || 1);
      const iguais = pal.filter(p => normal(p.texto) === alvo);
      if (iguais.length < vez) throw new Error(`a palavra ${ref} não está na fala`);
      return [iguais[vez - 1], +(m[3] || 0)];
    }
    const t = ref => typeof ref === 'number' ? ref : (([p, d]) => p.inicio + d)(achar(ref));
    const f = ref => typeof ref === 'number' ? ref : (([p, d]) => p.fim + d)(achar(ref));
    const fala = ref => { const [p] = achar(ref); return falas.find(x => x.palavras.includes(p)); };
    // em(i, 'palavra', n): quando a palavra começa na fala i (a n-ésima vez, dentro dela); ate(...): quando ela acaba.
    // A palavra igual vale antes da que só começa igual: em(3, 'é') acha "É", e não "estrada". Sem palavra, o começo e o fim da fala.
    function naFala(i, tr, n = 1) {
      const fl = falas[i]; if (!fl) throw new Error(`não há a fala ${i}`);
      const alvo = normal(tr), iguais = fl.palavras.filter(p => normal(p.texto) === alvo), comeca = fl.palavras.filter(p => normal(p.texto).startsWith(alvo));
      const p = (iguais.length >= n ? iguais : comeca)[n - 1];
      if (!p) throw new Error(`"${tr}" não está na fala ${i}: ${fl.palavras.map(x => x.texto).join(' ')}`);
      return p;
    }
    const em = (i, tr, n) => tr ? naFala(i, tr, n).inicio : falas[i].inicio;
    const ate = (i, tr, n) => tr ? naFala(i, tr, n).fim : falas[i].fim;
    const duracao = pal.length ? pal[pal.length - 1].fim + 1.0 : 1; // fim seco: 1 s depois da última fala

    // boca de quem fala: abre em cada palavra dele
    function boca(tt, quem) {
      for (const p of pal) if (p.quem === quem && tt >= p.inicio && tt <= p.fim) {
        const k = (tt - p.inicio) / Math.max(0.08, p.fim - p.inicio);
        return 0.35 + 0.55 * Math.abs(Math.sin(k * Math.PI * Math.max(1, Math.round((p.fim - p.inicio) / 0.13))));
      }
      return 0.05;
    }
    // piscar a cada 2 a 5 s, fechado por uns 0,12 s; a semente muda o ritmo de cada personagem
    function pisca(tt, semente = 1) {
      let x = 0.7 * semente, i = 0;
      while (x < tt + 1) { const dur = 0.12; if (tt >= x && tt < x + dur) return Math.sin((tt - x) / dur * Math.PI); x += 2 + 3 * hash(semente * 13 + i++); }
      return 0;
    }

    // ---------- definições (gradientes e desfoques), com id próprio deste desenho ----------
    const pre = (svg.id || 'sa') + '-';
    const u = nome => `url(#${pre}${nome})`;
    let defs = svg.querySelector('defs') || el('defs', {}, svg);
    const grad = (id, cor, a0, a1 = 0, raio = '50%', meio) => `<radialGradient id="${pre}${id}" cx="50%" cy="50%" r="${raio}"><stop offset="0%" stop-color="${cor}" stop-opacity="${a0}"/>${meio || ''}<stop offset="100%" stop-color="${cor}" stop-opacity="${a1}"/></radialGradient>`;
    defs.insertAdjacentHTML('beforeend', [
      `<radialGradient id="${pre}vinheta" cx="50%" cy="48%" r="70%"><stop offset="50%" stop-color="#000" stop-opacity="0"/><stop offset="100%" stop-color="#000" stop-opacity="0.82"/></radialGradient>`,
      grad('brilhoQuente', '#ffbf6b', 0.85), grad('brilhoFrio', '#9fc7ff', 0.75), grad('brilhoVermelho', '#ff4a3d', 0.9),
      grad('brilhoFogo', '#ff5a1f', 1, 0, '50%', '<stop offset="45%" stop-color="#ff6a2a" stop-opacity="0.55"/>'),
      grad('brilhoTela', '#cfe6ff', 0.9),
      `<linearGradient id="${pre}feixe" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="#ffe9c4" stop-opacity="0.6"/><stop offset="100%" stop-color="#ffe9c4" stop-opacity="0"/></linearGradient>`,
      `<linearGradient id="${pre}feixeFrio" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="#d6e8ff" stop-opacity="0.55"/><stop offset="100%" stop-color="#d6e8ff" stop-opacity="0"/></linearGradient>`,
      ...[4, 10, 24, 50].map(s => `<filter id="${pre}desf${s}" x="-${20 + s}%" y="-${20 + s}%" width="${140 + 2 * s}%" height="${140 + 2 * s}%"><feGaussianBlur stdDeviation="${s}"/></filter>`),
    ].join(''));

    // camadas: o mundo (os planos), as peças da série por cima e o acabamento por cima de tudo
    const mundo = el('g', {}, svg), sobre = el('g', {}, svg), topo = el('g', {}, svg);
    const FONTE = cssVar('--f-forte', 'Inter').replace(/"/g, '');
    const COR = cssVar('--c-serie', '#ffa53a');
    function texto(parent, attrs, conteudo) {
      const e = el('text', Object.assign({ 'font-family': `${FONTE}, sans-serif`, 'font-weight': 800, 'paint-order': 'stroke', 'stroke-linejoin': 'round' }, attrs), parent);
      if (conteudo != null) e.textContent = conteudo;
      return e;
    }

    // câmera: centro (cx, cy) e escala s, com um tremor de mão leve. A câmera sempre anda.
    function camera(g, cx, cy, s, tt, tremor = 1) {
      const dx = (ruido(tt * 0.7) - 0.5) * 10 * tremor, dy = (ruido(tt * 0.6 + 40) - 0.5) * 10 * tremor;
      g.setAttribute('transform', `translate(${W / 2 + dx} ${H / 2 + dy}) scale(${s}) translate(${-cx} ${-cy})`);
    }

    // granulado: 6 telas de ruído feitas uma vez e trocadas 24 vezes por segundo (todas no DOM: troca sem esperar imagem carregar)
    function granulado(parent = topo, forca = 0.55) {
      const g = el('g', { style: 'mix-blend-mode:overlay', opacity: forca }, parent), ims = [];
      for (let s = 0; s < 6; s++) {
        const c = document.createElement('canvas'); c.width = 540; c.height = 960;
        const x = c.getContext('2d'), img = x.createImageData(540, 960);
        let seed = 1234 + s * 999;
        const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
        for (let i = 0; i < img.data.length; i += 4) { const v = 128 + (rnd() - 0.5) * 255; img.data[i] = img.data[i + 1] = img.data[i + 2] = v; img.data[i + 3] = 34; }
        x.putImageData(img, 0, 0);
        ims.push(el('image', { x: 0, y: 0, width: W, height: H, preserveAspectRatio: 'none', href: c.toDataURL(), display: s ? 'none' : '' }, g));
      }
      return tt => { const k = Math.floor(tt * 24) % ims.length; ims.forEach((im, i) => im.setAttribute('display', i === k ? '' : 'none')); };
    }
    // fumaça: bolhas desfocadas que sobem e se espalham. area: {x, y, w, h, vento, r}
    function fumaca(parent, n, area, cor = '#5b5a63', semente = 1) {
      const g = el('g', { filter: u('desf24') }, parent), bolhas = [];
      for (let i = 0; i < n; i++) bolhas.push({ e: el('ellipse', { fill: cor }, g), s: hash(semente * 31 + i * 7.3), v: 0.4 + hash(semente + i * 3.1) * 0.6 });
      return (tt, densidade = 1, sobe = 1) => {
        for (const b of bolhas) {
          const vida = (tt * 0.12 * b.v * sobe + b.s) % 1;
          const x = area.x + area.w * (b.s + Math.sin(tt * 0.3 + b.s * 9) * 0.06) + vida * (area.vento || 0);
          const y = area.y + area.h - vida * area.h, r = (area.r || 70) * (0.6 + vida * 1.4);
          b.e.setAttribute('cx', x); b.e.setAttribute('cy', y); b.e.setAttribute('rx', r * 1.3); b.e.setAttribute('ry', r);
          b.e.setAttribute('opacity', densidade * Math.sin(vida * Math.PI) * 0.75);
        }
      };
    }
    // poeira flutuando dentro de um feixe de luz
    function poeira(parent, n, area, semente = 2) {
      const g = el('g', {}, parent), ps = [];
      for (let i = 0; i < n; i++) ps.push({ e: el('circle', { r: 1.5 + hash(i * 5 + semente) * 2.5, fill: '#fff4dc' }, g), a: hash(i * 9.1 + semente), b: hash(i * 3.7 + semente * 2) });
      return (tt, forca = 1) => { for (const p of ps) {
        const x = area.x + area.w * (((p.a + Math.sin(tt * 0.21 + p.b * 6) * 0.04 + tt * 0.006 * (p.b - 0.5)) % 1 + 1) % 1);
        const y = area.y + area.h * ((p.b + tt * 0.012 * (0.3 + p.a)) % 1);
        p.e.setAttribute('cx', x); p.e.setAttribute('cy', y); p.e.setAttribute('opacity', forca * (0.25 + 0.5 * Math.abs(Math.sin(tt * 0.8 + p.a * 20))));
      } };
    }

    // ---------- planos ----------
    // planos: [{ini, fim, corte (entra com corte seco, só no susto), montar(g) -> (t, tl) => {...}}], em ordem.
    // Troca por dissolve de 0,45 s com desfoque; no corte seco, um clarão. Devolve render(t), que desenha tudo.
    const extras = []; // as peças da série e o acabamento, desenhados depois dos planos
    function filme(planos, o = {}) {
      const TR = o.dissolve ?? 0.45;
      const clarao = el('rect', { x: 0, y: 0, width: W, height: H, fill: '#fff', opacity: 0 }, topo);
      el('rect', { x: 0, y: 0, width: W, height: H, fill: u('vinheta') }, topo);
      const grao = granulado(topo, o.granulado ?? 0.55);
      for (const p of planos) { p.g = el('g', { display: 'none' }, mundo); p.q = p.montar(p.g); }
      planos.forEach((p, i) => { p.prox = planos[i + 1]; });
      return function render(tt) {
        for (const p of planos) {
          const entrando = p.corte ? 0 : TR / 2, saindo = p.prox && !p.prox.corte ? TR / 2 : 0;
          const ativo = tt >= p.ini - entrando && tt < p.fim + saindo;
          p.g.setAttribute('display', ativo ? '' : 'none');
          if (!ativo) continue;
          // um plano com erro não apaga o vídeo inteiro: o erro aparece uma vez no console, com o plano
          try { p.q(tt, tt - p.ini); } catch (err) { if (!p.erro) { p.erro = true; console.error(`Série Animada, plano ${planos.indexOf(p)} (${p.ini.toFixed(2)} s): ${err.message}`); } }
          const kOut = saindo ? prog(tt, p.fim - saindo, p.fim + saindo) : 0;
          const kIn = entrando ? prog(tt, p.ini - entrando, p.ini + entrando) : 1;
          p.g.setAttribute('opacity', Math.min(kIn, 1));
          p.g.setAttribute('filter', kOut > 0.05 ? (kOut > 0.5 ? u('desf24') : u('desf10')) : '');
        }
        for (const x of extras) x(tt);
        const susto = planos.find(p => p.corte && tt >= p.ini && tt < p.ini + 0.12);
        clarao.setAttribute('opacity', susto ? (o.clarao ?? 0.55) * (1 - (tt - susto.ini) / 0.12) : 0);
        grao(tt);
      };
    }
    // liga o desenho ao relógio do vídeo: um tween vazio do tamanho da cena chama o desenho a cada quadro,
    // inclusive quando o render pula direto para um tempo (o tl.call não dispara nesse pulo; o onUpdate dispara).
    // Uso, no fim do script: S.ligar(S.filme(planos), tl, t0, D)
    function ligar(render, tl, t0, D) {
      const relogio = { k: 0 };
      tl.fromTo(relogio, { k: 0 }, { k: 1, duration: D, ease: 'none', immediateRender: false, onUpdate: () => render(t0 + relogio.k * D) }, t0);
      render(t0);
      return render;
    }

    // ---------- peças da série (margem de 150 px nas laterais; nada acima de 220 px) ----------
    // legenda de 2 ou 3 palavras, em caixa alta, branca com contorno preto, palavra-chave na cor da série;
    // fala de personagem em itálico, com a etiqueta de quem fala. o: {y, chave: [palavras], nomes: {quem: {nome, cor}}, ate}
    function legenda(o = {}) {
      const y = o.y ?? 1470, CH = new Set((o.chave || []).map(normal)), nomes = o.nomes || {};
      const etq = el('g', { opacity: 0 }, sobre);
      const etqFundo = el('rect', { x: 0, y: y - 152, width: 400, height: 58, rx: 29, fill: '#c9506f' }, etq);
      const etqTxt = texto(etq, { x: 540, y: y - 112, 'text-anchor': 'middle', 'font-size': 30, fill: '#fff' });
      const lg = texto(sobre, { x: 540, y, 'text-anchor': 'middle', 'font-size': o.tamanho || 70, fill: '#fff', stroke: '#0b0b10', 'stroke-width': 14 });
      // trocas: [["catorze zero cinco", "1405"]]: o que a voz fala por extenso aparece escrito como número
      const trocas = (o.trocas || []).map(([de, para]) => [de.split(/\s+/).map(normal), para]);
      const junta = lista => {
        const out = [];
        for (let i = 0; i < lista.length; i++) {
          const tr = trocas.find(([seq]) => seq.every((w, k) => lista[i + k] && normal(lista[i + k].texto) === w));
          if (!tr) { out.push(lista[i]); continue; }
          const ult = lista[i + tr[0].length - 1], pont = (ult.texto.match(/[.,!?:;]$/) || [''])[0];
          out.push(Object.assign({}, lista[i], { texto: tr[1] + pont, fim: ult.fim }));
          i += tr[0].length - 1;
        }
        return out;
      };
      const blocos = [];
      for (const fl of falas) {
        let atual = [];
        junta(fl.palavras).forEach((p, i, arr) => {
          atual.push(p);
          if (/[.,!?:;]$/.test(p.texto) || atual.length === 3 || i === arr.length - 1) { blocos.push({ palavras: atual, ini: atual[0].inicio, quem: fl.quem }); atual = []; }
        });
      }
      blocos.forEach((b, i) => { const prox = blocos[i + 1], ult = b.palavras[b.palavras.length - 1].fim; b.fim = prox && prox.ini - ult < 0.6 ? prox.ini : ult + 0.25; });
      const ate = o.ate != null ? t(o.ate) : 1e9;
      extras.push(tt => {
        const b = tt < ate ? blocos.find(x => tt >= x.ini && tt < x.fim) : null;
        while (lg.firstChild) lg.removeChild(lg.firstChild);
        etq.setAttribute('opacity', 0);
        if (!b) return;
        const personagem = b.quem !== 'narrador';
        b.palavras.forEach((p, i) => {
          const ts = el('tspan', { fill: CH.has(normal(p.texto)) ? COR : (personagem ? '#ffe7ef' : '#ffffff') }, lg);
          ts.textContent = (i ? ' ' : '') + p.texto.replace(/[.,:;]$/, '').toUpperCase();
        });
        lg.setAttribute('font-style', personagem ? 'italic' : 'normal');
        const k = sai(prog(tt, b.ini, b.ini + 0.12)); // entra com um pulo pequeno
        const cabe = Math.min(1, 780 / Math.max(1, lg.getComputedTextLength())); // encolhe se passar de 780 px
        lg.setAttribute('transform', `translate(540 ${y}) scale(${(0.86 + 0.14 * k) * cabe}) translate(-540 ${-y})`);
        if (personagem && nomes[b.quem]) {
          const n = nomes[b.quem];
          etqTxt.textContent = n.nome || n; etqFundo.setAttribute('fill', n.cor || '#c9506f');
          const larg = etqTxt.getComputedTextLength() + 60;
          etqFundo.setAttribute('x', 540 - larg / 2); etqFundo.setAttribute('width', larg);
          etq.setAttribute('opacity', 1);
        }
      });
      return lg;
    }
    // selo no alto: "NOME · DIA N" e o relógio da história. O fundo acompanha o texto mais largo, medido com a fonte carregada.
    // o: {nome, horas: [[tempo, "21:40"], ...]}
    function selo(o) {
      const g = el('g', {}, sobre);
      const fundo = el('rect', { x: 150, y: 236, width: 420, height: 118, rx: 18, fill: '#0b0c12', opacity: 0.72 }, g);
      const nome = texto(g, { x: 174, y: 278, 'font-size': 26, fill: COR, 'letter-spacing': 1 }, o.nome);
      const hora = texto(g, { x: 172, y: 336, 'font-size': 54, fill: '#f2f2f6' }, '');
      const horas = (o.horas || []).map(([a, h]) => [t(a), h]);
      extras.push(tt => {
        let h = horas.length ? horas[0][1] : ''; for (const [a, v] of horas) if (tt >= a) h = v;
        hora.textContent = h;
        fundo.setAttribute('width', Math.max(nome.getBBox().width, hora.getBBox().width) + 48);
        g.setAttribute('opacity', o.ate != null ? 1 - prog(tt, t(o.ate), t(o.ate) + 0.3) : 1);
      });
      return g;
    }
    // contador do recurso da série (no alto, à direita do selo). o: {icone(g) desenha em volta de (730, 300), valor(t) -> texto, de, ate}
    function contador(o) {
      const g = el('g', { opacity: 0 }, sobre);
      const fundo = el('rect', { x: 690, y: 236, width: 240, height: 92, rx: 18, fill: '#0b0c12', opacity: 0.72 }, g);
      const dentro = el('g', {}, g);
      if (o.icone) o.icone(el('g', {}, dentro));
      const txt = texto(dentro, { x: 774, y: 306, 'font-size': 50, fill: '#f2f2f6' }, '');
      let ultimo = null, mudou = -9;
      extras.push(tt => {
        const v = o.valor(tt);
        // quando o valor muda (a bateria caiu, a água baixou), o número pula e assenta
        if (ultimo !== null && v !== ultimo) mudou = tt; ultimo = v;
        const pulo = tt - mudou >= 0 && tt - mudou < 0.4 ? Math.exp(-(tt - mudou) * 8) * Math.cos((tt - mudou) * 20) : 0;
        txt.setAttribute('transform', `translate(774 290) scale(${1 + 0.25 * pulo}) translate(-774 -290)`);
        txt.textContent = v;
        const larg = Math.max(240, txt.getBBox().width + 110); // cresce para a esquerda: a margem da direita fica em 150 px
        fundo.setAttribute('x', 930 - larg); fundo.setAttribute('width', larg);
        dentro.setAttribute('transform', `translate(${240 - larg} 0)`);
        const de = o.de != null ? t(o.de) : -1, ate = o.ate != null ? t(o.ate) : 1e9;
        g.setAttribute('opacity', Math.min(prog(tt, de, de + 0.3), 1 - prog(tt, ate, ate + 0.3)));
      });
      return g;
    }
    // cartão "PROBLEMA Nº 1 / A ÁGUA". itens: [[de, ate, "PROBLEMA Nº 1", "A ÁGUA"], ...]
    function cartao(itens, o = {}) {
      const g = el('g', { opacity: 0 }, sobre), y = o.y ?? 470;
      el('rect', { x: 150, y, width: 780, height: 230, rx: 26, fill: '#101119', stroke: '#2a2c3a', 'stroke-width': 4, opacity: 0.94 }, g);
      const faixa = el('rect', { x: 380, y: y - 24, width: 320, height: 58, rx: 29, fill: cssVar('--c-alerta', '#d6261c') }, g);
      const num = texto(g, { x: 540, y: y + 17, 'text-anchor': 'middle', 'font-size': 32, fill: '#fff' }, '');
      const txt = texto(g, { x: 540, y: y + 160, 'text-anchor': 'middle', 'font-size': 96, fill: '#fff' }, '');
      const lista = itens.map(([a, b, n, s]) => [t(a), t(b), n, s]);
      extras.push(tt => {
        let k = 0;
        for (const [a, b, n, s] of lista) if (tt >= a - 0.05 && tt < b) { k = Math.min(prog(tt, a - 0.05, a + 0.2), 1 - prog(tt, b - 0.3, b)); num.textContent = n; txt.textContent = s; }
        const larg = Math.max(320, num.getComputedTextLength() + 80);
        faixa.setAttribute('x', 540 - larg / 2); faixa.setAttribute('width', larg);
        txt.setAttribute('transform', `translate(540 0) scale(${Math.min(1, 700 / Math.max(1, txt.getComputedTextLength()))} 1) translate(-540 0)`);
        // bate na tela: chega grande, achata e assenta; a faixa vermelha entra 0,1 s depois, de cima
        let em = -9; for (const [a] of lista) if (tt >= a - 0.05) em = a;
        const ac = impacto(tt, em + 0.12, 1) * 0.08, ent = sai(prog(tt, em - 0.05, em + 0.15));
        g.setAttribute('opacity', k);
        g.setAttribute('transform', `translate(540 ${y + 115}) scale(${(1.25 - 0.25 * ent) * (1 + ac)} ${(1.25 - 0.25 * ent) * (1 - ac)}) translate(-540 ${-(y + 115)})`);
        faixa.setAttribute('transform', `translate(0 ${(1 - sai(prog(tt, em + 0.1, em + 0.35))) * -60})`);
      });
      return g;
    }
    // o fim: os botões da escolha, com o risco de cada uma embaixo, e o fecho ("A MAIORIA DECIDE O DIA 2").
    // o: {opcoes: [{em, n: "1", titulo, risco, cor}], fecho: {em, cima, botao, baixo}}
    function escolha(o) {
      const g = el('g', {}, sobre), bts = [];
      (o.opcoes || []).forEach((op, i) => {
        const y = (o.y ?? 1540) + i * 170;
        const b = el('g', { opacity: 0 }, g), cor = op.cor || (i ? '#f2f2f6' : '#f6c343');
        el('rect', { x: 150, y, width: 780, height: 150, rx: 30, fill: cor, stroke: '#0b0b10', 'stroke-width': 6 }, b);
        el('circle', { cx: 222, cy: y + 75, r: 44, fill: '#0b0b10' }, b);
        texto(b, { x: 222, y: y + 93, 'text-anchor': 'middle', 'font-size': 50, fill: cor }, op.n || String(i + 1));
        const tit = texto(b, { x: 288, y: y + 70, 'font-size': 42, fill: '#0b0b10' }, op.titulo);
        const ris = texto(b, { x: 288, y: y + 118, 'font-size': 25, fill: '#3a2a20', 'font-weight': 700 }, op.risco || '');
        bts.push([b, t(op.em), tit, ris]);
      });
      const fe = o.fecho, fg = el('g', { opacity: 0 }, g);
      if (fe) {
        el('rect', { x: 170, y: 520, width: 740, height: 230, rx: 34, fill: '#0b0c12', opacity: 0.85 }, fg);
        texto(fg, { x: 540, y: 600, 'text-anchor': 'middle', 'font-size': 44, fill: '#f2f2f6' }, fe.cima);
        el('rect', { x: 300, y: 630, width: 480, height: 92, rx: 46, fill: fe.cor || cssVar('--c-serie', '#f07a2a') }, fg);
        texto(fg, { x: 540, y: 694, 'text-anchor': 'middle', 'font-size': 56, fill: '#fff' }, fe.botao);
        if (fe.baixo) texto(fg, { x: 540, y: 820, 'text-anchor': 'middle', 'font-size': 48, fill: '#ffd36b', stroke: '#0b0b10', 'stroke-width': 10 }, fe.baixo);
      }
      extras.push(tt => {
        for (const [b, em, tit, ris] of bts) {
          // interface: entra de baixo com um pulo (back.out) e achata ao chegar; o selo do número chega 0,08 s depois
          const k = prog(tt, em, em + 0.35), y = (1 - sai(k)) * 90 - Math.sin(clamp(k * 1.4) * Math.PI) * 8;
          const ac = impacto(tt, em + 0.3, 0.6) * 0.05;
          const yb = +b.firstChild.getAttribute('y') + 75;
          b.setAttribute('opacity', Math.min(1, k * 2.5));
          b.setAttribute('transform', `translate(540 ${yb + y}) scale(${1 + ac} ${1 - ac}) translate(-540 ${-yb})`);
          for (const x of [tit, ris]) x.setAttribute('transform', `translate(288 0) scale(${Math.min(1, 600 / Math.max(1, x.getComputedTextLength()))} 1) translate(-288 0)`);
        }
        if (fe) { // o fecho cresce do centro com um pulo e achata ao assentar
          const e0 = t(fe.em), k = prog(tt, e0, e0 + 0.4), sc = 0.7 + 0.3 * (1 - Math.pow(1 - k, 3)) + Math.sin(clamp(k * 1.3) * Math.PI) * 0.06, ac = impacto(tt, e0 + 0.35, 0.6) * 0.05;
          fg.setAttribute('opacity', Math.min(1, k * 3));
          fg.setAttribute('transform', `translate(540 640) scale(${sc * (1 + ac)} ${sc * (1 - ac)}) translate(-540 -640)`);
        }
      });
      return g;
    }
    // qualquer outra peça por cima dos planos, desenhada a cada quadro: S.sobrepor(t => {...})
    const sobrepor = fn => extras.push(fn);

    return { W, H, el, TINTA, svg, mundo, sobre, topo, u, texto, cor: COR, fonte: FONTE, cssVar,
      clamp, lerp, suave, suave2, sai, entra, prog, chave, hash, ruido,
      palavras: pal, falas, t, f, fala, em, ate, duracao, boca, pisca,
      camera, granulado, fumaca, poeira, filme, ligar, legenda, selo, contador, cartao, escolha, sobrepor,
      andar, correr, parado, respira, mistura, caminhada, passo, antes, arco, impacto, susto, segue, LUZ, AMBIENTE };
  }

  window.SA = { cena, normal };
})();
