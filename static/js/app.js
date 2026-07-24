(() => {
  "use strict";

  const APP_BASE = (window.APP_BASE || "").replace(/\/$/, "");
  const withBase = (path) => `${APP_BASE}${path.startsWith("/") ? path : `/${path}`}`;
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
  const state = { products: [], result: null, name: "" };
  const accents = { red: "#96321e", teal: "#287871", blue: "#326c84", gold: "#b47a22", green: "#47784c", sand: "#8c694d" };

  async function getJSON(url, options) {
    const response = await fetch(url, options);
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.error || "网络连接失败，请稍后重试");
    return data;
  }

  function setText(id, value) {
    const node = document.getElementById(id);
    if (node) node.textContent = value ?? "";
  }

  function localDateGodUrl(product, size = "icon") {
    return withBase(`/static/img/date-gods/${size}/${product.sign_key}.png`);
  }

  function dateGodUrl(product, size = "icon") {
    return product.date_god_image || localDateGodUrl(product, size);
  }

  function wireImageFallback(image, product, size = "icon") {
    image.dataset.fallbackSrc = localDateGodUrl(product, size);
    image.addEventListener("error", () => {
      if (image.src.endsWith(image.dataset.fallbackSrc)) return;
      image.src = image.dataset.fallbackSrc;
    });
  }

  function wireFallbackImages(root = document) {
    $$("img[data-fallback-src]", root).forEach((image) => {
      image.addEventListener("error", () => {
        if (image.src.endsWith(image.dataset.fallbackSrc)) return;
        image.src = image.dataset.fallbackSrc;
      });
    });
  }

  function setDateGodImage(id, product, size = "full") {
    const image = document.getElementById(id);
    if (!image) return;
    image.src = dateGodUrl(product, size);
    image.alt = `${product.name_zh} · ${product.name_transliteration} · ${product.name_nahuatl} 日期守护神`;
    wireImageFallback(image, product, size);
  }

  function showToast(message) {
    const toast = $("#toast");
    toast.textContent = message;
    toast.hidden = false;
    clearTimeout(showToast.timer);
    showToast.timer = setTimeout(() => { toast.hidden = true; }, 2400);
  }

  function route(name, updateHash = true) {
    const protectedViews = new Set(["result", "product", "share", "calendar"]);
    if (protectedViews.has(name) && !state.result) name = "birthday";
    const target = $(`[data-view="${name}"]`);
    if (!target) name = "home";
    $$(".view").forEach((view) => {
      const active = view.dataset.view === name;
      view.hidden = !active;
      view.classList.toggle("is-active", active);
    });
    if (updateHash && location.hash !== `#${name}`) history.pushState(null, "", `#${name}`);
    scrollTo({ top: 0, behavior: "smooth" });
  }

  function buildOrbit(root) {
    if (!root || root.querySelector(".orbit-chip")) return;
    const ring = root.querySelector(".orbit-ring");
    state.products.slice().sort((a, b) => a.symbol_index - b.symbol_index).forEach((product, index) => {
      const chip = document.createElement("span");
      chip.className = "orbit-chip";
      chip.style.setProperty("--angle", `${index * 18}deg`);
      chip.style.setProperty("--chip", accents[product.accent] || accents.red);
      const image = document.createElement("img");
      image.src = dateGodUrl(product);
      wireImageFallback(image, product);
      image.alt = "";
      chip.appendChild(image);
      chip.title = `${product.product_no}号 ${product.name_zh} · ${product.name_transliteration} · ${product.name_nahuatl}`;
      ring.after(chip);
    });
  }

  function buildMobileHero() {
    const root = $("#mobile-hero-art");
    if (!root || !state.products.length) return;
    const ordered = state.products.slice().sort((a, b) => a.symbol_index - b.symbol_index);
    const featured = [ordered[16], ordered[17], ordered[18], ordered[19], ordered[0]].filter(Boolean);
    root.innerHTML = `
      <div class="mobile-hero-core">
        <img src="${dateGodUrl(ordered[16] || ordered[0], "full")}" data-fallback-src="${localDateGodUrl(ordered[16] || ordered[0], "full")}" alt="奥林日期守护神">
      </div>
      ${featured.map((product, index) => `
        <span class="mobile-hero-satellite satellite-${index + 1}">
          <img src="${dateGodUrl(product)}" data-fallback-src="${localDateGodUrl(product)}" alt="${product.name_zh}日期守护神">
        </span>`).join("")}`;
    wireFallbackImages(root);
  }

  function initDatePicker() {
    const year = $("#birth-year"), month = $("#birth-month"), day = $("#birth-day");
    const today = new Date();
    // 由早到晚：滚轮上方是较早年份，下方是较晚年份。
    for (let y = 1900; y <= today.getFullYear(); y++) year.add(new Option(y, y));
    for (let m = 1; m <= 12; m++) month.add(new Option(String(m).padStart(2, "0"), m));
    const demoDate = new Date(Math.min(today.getTime(), new Date(2026, 6, 15).getTime()));
    year.value = demoDate.getFullYear();
    month.value = demoDate.getMonth() + 1;

    function fillDays(preferred = Number(day.value) || demoDate.getDate()) {
      const count = new Date(Number(year.value), Number(month.value), 0).getDate();
      day.replaceChildren();
      for (let d = 1; d <= count; d++) day.add(new Option(String(d).padStart(2, "0"), d));
      day.value = Math.min(preferred, count);
    }
    year.addEventListener("change", () => fillDays());
    month.addEventListener("change", () => fillDays());
    fillDays();
  }

  function mayanNumber(value) {
    if (value === 0) return "◉";
    const dots = "●".repeat(value % 5);
    const bars = "━\n".repeat(Math.floor(value / 5)).trim();
    return [dots, bars].filter(Boolean).join("\n");
  }

  function formatPrice(product) {
    return product.price == null ? "请咨询" : `¥${Number(product.price).toFixed(0)}`;
  }

  function stockLabel(status) {
    return { in_stock: "□ 状态：现货", low_stock: "△ 状态：少量", sold_out: "× 状态：售罄" }[status] || status;
  }

  function renderResult(data) {
    state.result = data;
    state.name = data.display_name || "";
    const p = data.product;
    renderGuardianCrowd(p);
    document.documentElement.style.setProperty("--active-accent", accents[p.accent] || accents.red);
    ["result-icon-image", "product-icon-image", "share-icon-image", "loading-symbol-image"].forEach((id) => setDateGodImage(id, p, "full"));
    setDateGodImage("calendar-mini-image", p, "icon");
    const resultDisplayName = $("#result-display-name");
    resultDisplayName.textContent = state.name;
    resultDisplayName.hidden = !state.name;
    setText("result-personal-copy", state.name ? "，你的生日守护图腾" : "你的生日守护图腾");
    ["result-name-zh", "product-name-zh", "share-name-zh"].forEach((id) => setText(id, p.name_zh));
    ["result-name-nahuatl", "product-name-nahuatl", "share-name-nahuatl"].forEach((id) => setText(id, p.name_nahuatl));
    ["result-name-transliteration", "product-name-transliteration", "share-name-transliteration", "calendar-name-transliteration"].forEach((id) => setText(id, p.name_transliteration));
    ["result-product-no", "result-button-no", "product-title-no", "product-medallion-no", "clerk-product-no", "clerk-big-no", "share-product-no", "calendar-product-no", "calendar-button-no"].forEach((id) => setText(id, p.product_no));
    setText("result-keywords", p.keywords.replace("/", "·"));
    setText("share-keywords", p.keywords);
    setText("result-signature", `${data.tzolkin_number} ${p.name_nahuatl}`);
    setText("share-signature", `${data.tzolkin_number} ${p.name_nahuatl}`);
    setText("calendar-signature", `${data.tzolkin_number} ${p.name_nahuatl}`);
    setText("share-long-count-text", data.long_count.join(" · "));
    setText("share-tzolkin-text", `${data.tzolkin_number} ${data.tzolkin_maya_name}`);
    setText("share-haab-text", `${data.haab_day} ${data.haab_month}`);
    setText("share-night-lord-text", `G${data.night_lord}`);
    setText("product-story", p.story);
    setText("product-material", p.material);
    setText("product-stock", stockLabel(p.stock_status));
    setText("product-price", formatPrice(p));
    setText("clerk-big-name", `${p.name_zh} · ${p.name_transliteration} · ${p.name_nahuatl}`);
    setText("calendar-product-name", `${p.name_zh}款`);
    setText("long-count-text", data.long_count.join(" · "));
    setText("tzolkin-text", `${data.tzolkin_number} ${data.tzolkin_maya_name}`);
    setText("haab-text", `${data.haab_day} ${data.haab_month}`);
    setText("night-lord-text", `G${data.night_lord}`);
    setText("share-date", formatShareDate(data.birth_date));

    const units = ["Baktun", "Katun", "Tun", "Winal", "Kin"];
    const glyphMarkup = data.long_count.map((n, i) => `<div class="maya-number"><b>${units[i]}</b><i>${mayanNumber(n)}</i></div>`).join("");
    $("#long-count-glyphs").innerHTML = glyphMarkup;
    $("#share-long-count-glyphs").innerHTML = glyphMarkup;
    renderGallery();
  }

  function seededShuffle(items, seed) {
    const result = items.slice();
    let value = seed || 1;
    for (let i = result.length - 1; i > 0; i--) {
      value = (value * 9301 + 49297) % 233280;
      const j = Math.floor((value / 233280) * (i + 1));
      [result[i], result[j]] = [result[j], result[i]];
    }
    return result;
  }

  function renderGuardianCrowd(currentProduct) {
    const crowd = $("#guardian-crowd");
    if (!crowd) return;
    const others = seededShuffle(
      state.products.filter((product) => product.product_no !== currentProduct.product_no),
      state.result?.total_days || currentProduct.product_no
    );
    crowd.replaceChildren();
    others.forEach((product, index) => {
      const item = document.createElement("span");
      const innerRing = index < 7;
      const ringIndex = innerRing ? index : index - 7;
      const ringCount = innerRing ? 7 : 12;
      const offset = innerRing ? 7 : -5;
      item.className = `guardian-bg-item ${innerRing ? "ring-inner" : "ring-outer"}`;
      item.style.setProperty("--angle", `${offset + (360 / ringCount) * ringIndex}deg`);
      item.style.setProperty("--delay", `${70 + index * 25}ms`);
      item.style.setProperty("--float-x", `${((index * 7) % 15) - 7}px`);
      item.style.setProperty("--float-y", `${-5 - ((index * 5) % 10)}px`);
      item.style.setProperty("--float-duration", `${3.8 + (index % 6) * 0.42}s`);
      item.style.setProperty("--guardian-color", accents[product.accent] || accents.red);
      const image = document.createElement("img");
      image.src = dateGodUrl(product);
      image.alt = "";
      item.appendChild(image);
      item.title = `${product.name_zh} · ${product.name_nahuatl}`;
      crowd.appendChild(item);
    });
    crowd.classList.remove("is-revealing");
    void crowd.offsetWidth;
    crowd.classList.add("is-revealing");
    const medallion = $("#result-medallion");
    medallion.classList.remove("is-arriving");
    void medallion.offsetWidth;
    medallion.classList.add("is-arriving");
  }

  function formatShareDate(iso) {
    const [year, month, day] = iso.split("-");
    return $("#hide-year")?.checked ? `${month}.${day}` : `${year}.${month}.${day}`;
  }

  function renderGallery() {
    const grid = $("#product-grid");
    if (!grid) return;
    const current = state.result?.product?.product_no;
    grid.innerHTML = state.products.map((p) => `
      <article class="product-card ${p.product_no === current ? "is-current" : ""}" title="${p.keywords}">
        <b>${p.product_no}</b><div class="grid-icon"><img src="${dateGodUrl(p)}" data-fallback-src="${localDateGodUrl(p)}" alt="${p.name_zh}日期守护神"></div>
        <span>${p.name_zh}</span><small class="transliteration">${p.name_transliteration}</small><small class="latin-name">${p.name_nahuatl}</small>
      </article>`).join("");
    wireFallbackImages(grid);
  }

  async function calculate(event) {
    event.preventDefault();
    const error = $("#date-error");
    error.textContent = "";
    const y = $("#birth-year").value, m = $("#birth-month").value.padStart(2, "0"), d = $("#birth-day").value.padStart(2, "0");
    const birthDate = `${y}-${m}-${d}`;
    const name = $("#display-name").value.trim();
    route("loading");
    try {
      const started = performance.now();
      const data = await getJSON(withBase("/api/calculate"), {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ birthDate, name })
      });
      await new Promise((resolve) => setTimeout(resolve, Math.max(0, 1100 - (performance.now() - started))));
      renderResult(data);
      route("result");
    } catch (err) {
      error.textContent = err.message;
      route("birthday");
    }
  }

  function roundedRect(ctx, x, y, width, height, radius, fill) {
    ctx.beginPath();
    ctx.roundRect(x, y, width, height, radius);
    ctx.fillStyle = fill;
    ctx.fill();
  }

  function loadImage(src, fallbackSrc) {
    return new Promise((resolve, reject) => {
      const image = new Image();
      image.crossOrigin = "anonymous";
      image.onload = () => resolve(image);
      image.onerror = () => {
        if (fallbackSrc && image.src !== new URL(fallbackSrc, location.href).href) {
          image.crossOrigin = null;
          image.src = fallbackSrc;
          return;
        }
        reject(new Error("日期守护神图片加载失败"));
      };
      image.src = src;
    });
  }

  function drawImageContain(ctx, image, centerX, centerY, maxWidth, maxHeight) {
    const scale = Math.min(maxWidth / image.naturalWidth, maxHeight / image.naturalHeight);
    const width = image.naturalWidth * scale;
    const height = image.naturalHeight * scale;
    ctx.drawImage(image, centerX - width / 2, centerY - height / 2, width, height);
  }

  function drawCanvasMayanNumber(ctx, value, centerX, topY) {
    ctx.save();
    ctx.fillStyle = "#7b2418";
    if (value === 0) {
      ctx.lineWidth = 6;
      ctx.strokeStyle = "#7b2418";
      ctx.beginPath();
      ctx.ellipse(centerX, topY + 52, 35, 18, 0, 0, Math.PI * 2);
      ctx.stroke();
      ctx.restore();
      return;
    }
    const bars = Math.floor(value / 5);
    const dots = value % 5;
    const dotGap = 22;
    const dotStart = centerX - ((dots - 1) * dotGap) / 2;
    for (let i = 0; i < dots; i += 1) {
      ctx.beginPath();
      ctx.arc(dotStart + i * dotGap, topY + 24, 7, 0, Math.PI * 2);
      ctx.fill();
    }
    for (let i = 0; i < bars; i += 1) {
      roundedRect(ctx, centerX - 43, topY + 48 + i * 22, 86, 12, 6, "#7b2418");
    }
    ctx.restore();
  }

  function drawCanvasInfoRow(ctx, label, value, y) {
    roundedRect(ctx, 120, y, 840, 82, 14, "rgba(73, 17, 12, .28)");
    ctx.strokeStyle = "rgba(255, 231, 174, .38)";
    ctx.lineWidth = 2;
    ctx.strokeRect(120, y, 840, 82);
    ctx.textAlign = "left";
    ctx.fillStyle = "rgba(255, 231, 174, .75)";
    ctx.font = "24px sans-serif";
    ctx.fillText(label, 148, y + 51);
    ctx.textAlign = "right";
    ctx.fillStyle = "#ffe7ae";
    ctx.font = "bold 27px sans-serif";
    ctx.fillText(value, 932, y + 52);
  }

  async function downloadCard() {
    if (!state.result) return;
    const canvas = $("#share-canvas"), ctx = canvas.getContext("2d"), data = state.result, p = data.product;
    let guardianImage;
    try {
      guardianImage = await loadImage(dateGodUrl(p, "full"), localDateGodUrl(p, "full"));
    } catch (error) {
      showToast(error.message);
      return;
    }
    const W = canvas.width, H = canvas.height;
    const gradient = ctx.createLinearGradient(0, 0, 0, H);
    gradient.addColorStop(0, "#a74125"); gradient.addColorStop(1, "#6f2115");
    ctx.fillStyle = gradient; ctx.fillRect(0, 0, W, H);
    ctx.strokeStyle = "#d9a24c"; ctx.lineWidth = 12; ctx.strokeRect(34, 34, W - 68, H - 68);
    ctx.strokeStyle = "#f2c879"; ctx.lineWidth = 3; ctx.strokeRect(54, 54, W - 108, H - 108);
    ctx.textAlign = "center"; ctx.fillStyle = "#ffe7ae";
    ctx.font = "28px sans-serif"; ctx.fillText("BIRTH TOTEM · 20", W / 2, 120);
    ctx.beginPath(); ctx.arc(W / 2, 390, 205, 0, Math.PI * 2); ctx.fillStyle = "#d5a33e"; ctx.fill();
    ctx.beginPath(); ctx.arc(W / 2, 390, 180, 0, Math.PI * 2); ctx.fillStyle = "#163d3b"; ctx.fill();
    ctx.beginPath(); ctx.arc(W / 2, 390, 143, 0, Math.PI * 2); ctx.fillStyle = "#782418"; ctx.fill();
    drawImageContain(ctx, guardianImage, W / 2, 386, 270, 270);
    ctx.fillStyle = "#ffe7ae";
    ctx.font = "34px serif"; ctx.fillText(state.name ? `${state.name} 的生日图腾` : "我的生日图腾是", W / 2, 640);
    ctx.font = "bold 68px serif"; ctx.fillText(`${p.name_zh} · ${p.name_nahuatl}`, W / 2, 725);
    ctx.font = "bold 28px sans-serif"; ctx.fillStyle = "rgba(255,231,174,.82)"; ctx.fillText(p.name_transliteration, W / 2, 775);
    roundedRect(ctx, 260, 810, 560, 72, 36, "#ffe8b8");
    ctx.fillStyle = "#781f14"; ctx.font = "bold 30px sans-serif"; ctx.fillText(`${p.product_no}号产品 · ${data.tzolkin_number} ${p.name_nahuatl}`, W / 2, 857);
    ctx.fillStyle = "#ffe7ae"; ctx.font = "bold 31px serif"; ctx.fillText(p.keywords, W / 2, 950);

    ctx.textAlign = "left";
    ctx.font = "bold 34px serif";
    ctx.fillText("完整生日历法", 120, 1035);
    ctx.strokeStyle = "rgba(255, 231, 174, .45)";
    ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(348, 1025); ctx.lineTo(960, 1025); ctx.stroke();

    roundedRect(ctx, 120, 1075, 840, 300, 16, "rgba(73, 17, 12, .28)");
    ctx.strokeStyle = "rgba(255, 231, 174, .38)";
    ctx.strokeRect(120, 1075, 840, 300);
    ctx.textAlign = "center";
    ctx.fillStyle = "rgba(255, 231, 174, .76)";
    ctx.font = "23px sans-serif";
    ctx.fillText("长纪历 Long Count", W / 2, 1120);
    ctx.fillStyle = "#ffe7ae";
    ctx.font = "bold 31px sans-serif";
    ctx.fillText(data.long_count.join(" · "), W / 2, 1167);
    const units = ["Baktun", "Katun", "Tun", "Winal", "Kin"];
    data.long_count.forEach((value, index) => {
      const cardX = 148 + index * 160;
      roundedRect(ctx, cardX, 1200, 138, 130, 12, "#f3dfb5");
      ctx.fillStyle = "#7b2418";
      ctx.font = "bold 18px sans-serif";
      ctx.fillText(units[index], cardX + 69, 1230);
      drawCanvasMayanNumber(ctx, value, cardX + 69, 1237);
    });
    ctx.fillStyle = "rgba(255, 231, 174, .68)";
    ctx.font = "17px sans-serif";
    ctx.fillText("Baktun · Katun · Tun · Winal · Kin", W / 2, 1360);

    drawCanvasInfoRow(ctx, "卓尔金历 Tzolk'in", `${data.tzolkin_number} ${data.tzolkin_maya_name}`, 1410);
    drawCanvasInfoRow(ctx, "Haab 历", `${data.haab_day} ${data.haab_month}`, 1510);
    drawCanvasInfoRow(ctx, "夜神 Night Lord", `G${data.night_lord}`, 1610);
    drawCanvasInfoRow(ctx, "计算口径", "GMT 584283", 1710);

    ctx.textAlign = "left";
    ctx.fillStyle = "#ffe7ae";
    ctx.font = "26px sans-serif";
    ctx.fillText(formatShareDate(data.birth_date), 92, 2070);
    ctx.setLineDash([12, 8]);
    ctx.strokeStyle = "#3b1d17";
    ctx.lineWidth = 6;
    ctx.fillStyle = "#fff";
    ctx.fillRect(W - 222, 1930, 130, 130);
    ctx.strokeRect(W - 222, 1930, 130, 130);
    ctx.setLineDash([]);
    ctx.textAlign = "center";
    ctx.fillStyle = "#3b1d17";
    ctx.font = "64px sans-serif";
    ctx.fillText("⌗", W - 157, 2017);
    const link = document.createElement("a");
    link.download = `生日图腾-${p.product_no}号-${p.name_nahuatl}.png`;
    link.href = canvas.toDataURL("image/png"); link.click();
    showToast("生日卡已生成并保存");
  }

  async function init() {
    initDatePicker();
    try {
      state.products = (await getJSON(withBase("/api/products"))).items;
      buildOrbit($("#home-orbit")); buildOrbit($("#loading-orbit")); buildMobileHero(); renderGallery();
    } catch (err) { showToast(err.message); }

    document.addEventListener("click", (event) => {
      const trigger = event.target.closest("[data-go]");
      if (trigger) route(trigger.dataset.go);
    });
    $("#birthday-form").addEventListener("submit", calculate);
    $("#download-card").addEventListener("click", downloadCard);
    $("#hide-year").addEventListener("change", () => state.result && setText("share-date", formatShareDate(state.result.birth_date)));

    const dialog = $("#clerk-dialog");
    $("#show-clerk-button").addEventListener("click", () => dialog.showModal());
    $$(".dialog-close, .dialog-close-action", dialog).forEach((button) => button.addEventListener("click", () => dialog.close()));
    window.addEventListener("popstate", () => route(location.hash.slice(1) || "home", false));
    route(location.hash.slice(1) || "home", false);
  }

  document.addEventListener("DOMContentLoaded", init);
})();
