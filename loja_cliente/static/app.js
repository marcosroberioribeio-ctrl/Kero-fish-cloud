const money = new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL'});
let products = [];
let cart = JSON.parse(localStorage.getItem('keroFishCart') || '{}');

const grid = document.querySelector('#productGrid');
const statusEl = document.querySelector('#productStatus');
const cartDrawer = document.querySelector('#cartDrawer');
const overlay = document.querySelector('#overlay');
const cartItems = document.querySelector('#cartItems');
const cartCount = document.querySelector('#cartCount');
const cartSubtotal = document.querySelector('#cartSubtotal');
const checkoutTotal = document.querySelector('#checkoutTotal');
const checkoutDialog = document.querySelector('#checkoutDialog');
const checkoutForm = document.querySelector('#checkoutForm');
const checkoutMessage = document.querySelector('#checkoutMessage');

function saveCart(){localStorage.setItem('keroFishCart',JSON.stringify(cart));renderCart()}
function cartEntries(){return Object.values(cart).filter(x=>x.quantity>0)}
function subtotal(){return cartEntries().reduce((sum,x)=>sum+x.price*x.quantity,0)}
function quantityText(q){return Number.isInteger(q)?String(q):q.toLocaleString('pt-BR',{maximumFractionDigits:3})}

function renderProducts(list=products){
  grid.innerHTML='';
  statusEl.textContent=`${list.length} produto${list.length===1?'':'s'}`;
  if(!list.length){grid.innerHTML='<div class="empty">Nenhum produto encontrado.</div>';return}
  const template=document.querySelector('#productTemplate');
  list.forEach(p=>{
    const node=template.content.cloneNode(true);
    node.querySelector('.category').textContent=p.category||'Outros';
    node.querySelector('h3').textContent=p.name;
    node.querySelector('.price').textContent=p.price>0?money.format(p.price):'Consulte';
    const button=node.querySelector('.add-button');
    button.disabled=p.price<=0;
    button.textContent=p.price>0?'Adicionar':'Indisponível';
    button.addEventListener('click',()=>addToCart(p));
    grid.appendChild(node);
  });
}

function addToCart(p){
  const current=cart[p.id]||{product_id:p.id,name:p.name,price:p.price,quantity:0};
  current.quantity=Number((current.quantity+1).toFixed(3));
  cart[p.id]=current;
  saveCart();openCart();
}

function changeQty(id,delta){
  if(!cart[id])return;
  cart[id].quantity=Number((cart[id].quantity+delta).toFixed(3));
  if(cart[id].quantity<=0)delete cart[id];
  saveCart();
}

function renderCart(){
  const items=cartEntries();
  cartCount.textContent=items.reduce((s,x)=>s+x.quantity,0).toLocaleString('pt-BR',{maximumFractionDigits:2});
  cartItems.innerHTML='';
  if(!items.length){cartItems.innerHTML='<div class="empty">Seu carrinho está vazio.</div>'}
  items.forEach(item=>{
    const row=document.createElement('div');row.className='cart-row';
    row.innerHTML=`<div><h4>${item.name}</h4><small>${money.format(item.price)} cada</small></div><div class="qty-control"><button aria-label="Diminuir">−</button><strong>${quantityText(item.quantity)}</strong><button aria-label="Aumentar">+</button></div>`;
    const [minus,plus]=row.querySelectorAll('button');
    minus.addEventListener('click',()=>changeQty(item.product_id,-1));
    plus.addEventListener('click',()=>changeQty(item.product_id,1));
    cartItems.appendChild(row);
  });
  const total=subtotal();cartSubtotal.textContent=money.format(total);checkoutTotal.textContent=money.format(total);
}

function openCart(){cartDrawer.classList.add('open');overlay.classList.add('show');cartDrawer.setAttribute('aria-hidden','false')}
function closeCart(){cartDrawer.classList.remove('open');overlay.classList.remove('show');cartDrawer.setAttribute('aria-hidden','true')}

document.querySelector('#cartButton').addEventListener('click',openCart);
document.querySelector('#closeCart').addEventListener('click',closeCart);
overlay.addEventListener('click',closeCart);
document.querySelector('#checkoutButton').addEventListener('click',()=>{
  if(!cartEntries().length)return;
  closeCart();checkoutMessage.textContent='';checkoutDialog.showModal();
});
document.querySelector('#closeCheckout').addEventListener('click',()=>checkoutDialog.close());
document.querySelector('#searchInput').addEventListener('input',e=>{
  const q=e.target.value.trim().toLowerCase();
  renderProducts(products.filter(p=>`${p.name} ${p.category}`.toLowerCase().includes(q)));
});

checkoutForm.addEventListener('submit',async e=>{
  e.preventDefault();
  const button=document.querySelector('#sendOrderButton');
  button.disabled=true;button.textContent='Enviando...';checkoutMessage.textContent='';
  const data=Object.fromEntries(new FormData(checkoutForm).entries());
  const payload={
    customer:{name:data.name,phone:data.phone,cep:data.cep,address:data.address,number:data.number,complement:data.complement||'',neighborhood:data.neighborhood,city:data.city,notes:data.notes||''},
    payment_method:data.payment_method,
    items:cartEntries().map(x=>({product_id:x.product_id,name:x.name,quantity:x.quantity,unit_price:x.price}))
  };
  try{
    const response=await fetch('/api/orders',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    const result=await response.json();
    if(!response.ok)throw new Error(result.detail||'Não foi possível enviar o pedido');
    checkoutMessage.textContent=`Pedido ${result.code} recebido com sucesso!`;
    cart={};saveCart();checkoutForm.reset();
    setTimeout(()=>checkoutDialog.close(),2600);
  }catch(err){checkoutMessage.textContent=err.message||'Erro ao enviar pedido. Tente novamente.'}
  finally{button.disabled=false;button.textContent='Enviar pedido'}
});

async function loadProducts(){
  try{
    const response=await fetch('/api/products',{headers:{'Accept':'application/json'}});
    if(!response.ok)throw new Error('Falha no catálogo');
    products=await response.json();renderProducts();
  }catch(err){statusEl.textContent='Catálogo indisponível';grid.innerHTML='<div class="empty">Não foi possível carregar os produtos agora.</div>'}
}

if('serviceWorker' in navigator){window.addEventListener('load',()=>navigator.serviceWorker.register('/sw.js').catch(()=>{}))}
renderCart();loadProducts();
