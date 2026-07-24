(() => {
  const grid = document.querySelector("#admin-grid");
  const status = document.querySelector("#admin-status");
  const token = document.querySelector("#admin-token");

  function moneyToCents(value) { return value === "" ? null : Math.round(Number(value) * 100); }
  async function request(url, options) {
    const response = await fetch(url, options);
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "操作失败");
    return data;
  }
  function card(product) {
    const el = document.createElement("form");
    el.className = "admin-card";
    el.dataset.product = product.product_no;
    el.innerHTML = `
      <h3>${product.product_no}号 · ${product.name_zh} · ${product.name_transliteration} · ${product.name_nahuatl}</h3>
      <label>寓意关键词<input name="keywords" value="${product.keywords}"></label>
      <label>产品故事<textarea name="story">${product.story}</textarea></label>
      <label>材质<input name="material" value="${product.material}"></label>
      <label>价格（元，留空为请咨询）<input name="price" type="number" min="0" step="1" value="${product.price ?? ""}"></label>
      <label>库存<select name="stock_status"><option value="in_stock">现货</option><option value="low_stock">少量</option><option value="sold_out">售罄</option></select></label>
      <label>产品图地址<input name="product_image" value="${product.product_image ?? ""}"></label>
      <button class="primary-button" type="submit">保存这款产品</button>`;
    el.elements.stock_status.value = product.stock_status;
    el.addEventListener("submit", save);
    return el;
  }
  async function load() {
    status.textContent = "正在读取产品……";
    try {
      const data = await request("/api/products");
      grid.replaceChildren(...data.items.map(card)); status.textContent = `已载入 ${data.items.length} 款产品`;
    } catch (err) { status.textContent = err.message; }
  }
  async function save(event) {
    event.preventDefault();
    const form = event.currentTarget, no = form.dataset.product;
    status.textContent = `正在保存 ${no} 号……`;
    const body = {
      keywords: form.elements.keywords.value.trim(), story: form.elements.story.value.trim(),
      material: form.elements.material.value.trim(), price_cents: moneyToCents(form.elements.price.value),
      stock_status: form.elements.stock_status.value, product_image: form.elements.product_image.value.trim() || null
    };
    try {
      await request(`/api/admin/products/${no}`, { method: "PUT", headers: { "Content-Type": "application/json", "X-Admin-Token": token.value }, body: JSON.stringify(body) });
      status.textContent = `${no} 号已保存`;
    } catch (err) { status.textContent = err.message; }
  }
  document.querySelector("#load-products").addEventListener("click", load);
  load();
})();
