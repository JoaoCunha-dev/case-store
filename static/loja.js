const brl = n => Number(n).toLocaleString("pt-BR", {style: "currency", currency: "BRL"});
const $ = s => document.querySelector(s);
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const byId = {}; let carrinho = {};

const card = p => `<article class="card">${p.imagem ? `<img src="${esc(p.imagem)}" alt="${esc(p.nome)}">` : '<div class="ph"></div>'}
<div class="b"><strong>${esc(p.nome)}</strong><span class="mut">${esc(p.categoria)}</span><span class="preco">${brl(p.preco)}</span>
<span class="acoes"><button class="sec" data-ver="${p._id}">Detalhes</button><button data-add="${p._id}">Adicionar</button></span></div></article>`;

function registrar(lista) { lista.forEach(p => byId[p._id] = p); }

async function carregar() {
  const lista = await (await fetch("/api/produtos")).json(); registrar(lista);
  $("#status").textContent = lista.length ? "" : "Nenhum produto cadastrado ainda.";
  $("#catalogo").innerHTML = lista.map(card).join("");
}
async function carregarRecentes() {
  const lista = await (await fetch("/api/recentes")).json(); registrar(lista);
  $("#sec-rec").hidden = !lista.length; $("#recentes").innerHTML = lista.map(card).join("");
}

function renderCarrinho() {
  const itens = Object.values(carrinho);
  const total = itens.reduce((s, i) => s + i.p.preco * i.q, 0);
  $("#qtd").textContent = itens.reduce((s, i) => s + i.q, 0);
  $("#total").textContent = brl(total); $("#comprar").disabled = !itens.length;
  $("#itens").innerHTML = itens.length ? itens.map(({p, q}) => `<div class="row"><span>${esc(p.nome)}<br><span class="mut">${brl(p.preco)}</span></span>
<span style="display:flex;gap:6px;align-items:center"><button class="sec" data-dec="${p._id}">−</button>${q}<button class="sec" data-add="${p._id}">+</button>
<button class="sec" data-rem="${p._id}">Remover</button></span></div>`).join("") : '<p class="mut">Seu carrinho está vazio.</p>';
}

document.addEventListener("click", async e => {
  const t = e.target.closest("button"); if (!t) return;
  const d = t.dataset;
  if (d.add) { const p = byId[d.add]; carrinho[p._id] = {p, q: (carrinho[p._id]?.q || 0) + 1}; renderCarrinho(); $("#modal").hidden = true; }
  if (d.dec) { const i = carrinho[d.dec]; if (--i.q <= 0) delete carrinho[d.dec]; renderCarrinho(); }
  if (d.rem) { delete carrinho[d.rem]; renderCarrinho(); }
  if (d.ver) {
    const p = byId[d.ver];
    $("#detalhe").innerHTML = `${p.imagem ? `<img src="${esc(p.imagem)}" alt="" style="width:100%;max-height:280px;object-fit:cover">` : ""}
<div class="in"><h2 style="margin:0">${esc(p.nome)}</h2><p>${esc(p.descricao) || "Sem descrição."}</p><p class="preco">${brl(p.preco)}</p>
<button data-add="${p._id}">Adicionar ao carrinho</button> <button class="sec" id="x">Fechar</button></div>`;
    $("#modal").hidden = false;
    await fetch("/api/recentes", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(p)});
    carregarRecentes();
  }
  if (t.id === "x") $("#modal").hidden = true;
});
$("#modal").addEventListener("click", e => { if (e.target.id === "modal") e.target.hidden = true; });
$("#abrir").onclick = () => $("#side").hidden = false;
$("#fechar").onclick = () => $("#side").hidden = true;
$("#comprar").onclick = () => {
  const itens = Object.values(carrinho);
  const total = itens.reduce((s, i) => s + i.p.preco * i.q, 0);
  const msg = `Olá, gostaria de pedir: ${itens.map(i => `${i.q}x ${i.p.nome}`).join(", ")}. Total: ${brl(total)}`;
  window.open(`https://wa.me/${window.WHATSAPP}?text=${encodeURIComponent(msg)}`, "_blank");
};
renderCarrinho(); carregar(); carregarRecentes();
