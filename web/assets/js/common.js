/* ==========================================================================
   Sales & Operations Intelligence Copilot — shared UI + chart toolkit
   Zero dependencies. All charts are generated SVG.
   ========================================================================== */

const Copilot = (() => {
  const nf0 = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });
  const nf1 = new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 });

  const fmt = {
    int: (value) => nf0.format(Math.round(Number(value) || 0)),
    pct: (value, digits = 1) => `${(Number(value) || 0).toFixed(digits)}%`,
    num: (value, digits = 2) => (Number(value) || 0).toFixed(digits),
    money: (value) => nf0.format(Math.round(Number(value) || 0)),
    compact: (value) => {
      const n = Number(value) || 0;
      if (Math.abs(n) >= 1e6) return `${nf1.format(n / 1e6)}M`;
      if (Math.abs(n) >= 1e3) return `${nf0.format(n / 1e3)}k`;
      return nf0.format(n);
    },
  };

  const esc = (value) =>
    String(value).replace(/[&<>"']/g, (char) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    }[char]));

  async function loadJSON(path) {
    const response = await fetch(path, { cache: "no-cache" });
    if (!response.ok) throw new Error(`Failed to load ${path} (${response.status})`);
    return response.json();
  }

  /* ------------------------------------------------------------------ *
   * Tooltip
   * ------------------------------------------------------------------ */

  let tipEl = null;

  function tip() {
    if (!tipEl) {
      tipEl = document.createElement("div");
      tipEl.className = "chart-tip";
      tipEl.setAttribute("role", "status");
      document.body.appendChild(tipEl);
    }
    return tipEl;
  }

  function showTip(event, html) {
    const element = tip();
    element.innerHTML = html;
    element.classList.add("is-on");
    element.style.left = `${event.clientX}px`;
    element.style.top = `${event.clientY - 12}px`;
  }

  function hideTip() {
    if (tipEl) tipEl.classList.remove("is-on");
  }

  function bindTips(root) {
    root.querySelectorAll("[data-tip]").forEach((node) => {
      node.addEventListener("pointermove", (event) =>
        showTip(event, node.getAttribute("data-tip"))
      );
      node.addEventListener("pointerleave", hideTip);
      node.addEventListener("focus", (event) => {
        const box = event.target.getBoundingClientRect();
        showTip({ clientX: box.left + box.width / 2, clientY: box.top }, node.getAttribute("data-tip"));
      });
      node.addEventListener("blur", hideTip);
    });
  }

  /* ------------------------------------------------------------------ *
   * SVG helpers
   * ------------------------------------------------------------------ */

  const svg = (width, height, inner, label) =>
    `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc(label)}" preserveAspectRatio="xMidYMid meet">${inner}</svg>`;

  const defs = () => `
    <defs>
      <linearGradient id="barGrad" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#7dd3fc"/>
        <stop offset="100%" stop-color="#0ea5e9" stop-opacity="0.55"/>
      </linearGradient>
      <linearGradient id="barGradWarm" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#fda4af"/>
        <stop offset="100%" stop-color="#f97316" stop-opacity="0.55"/>
      </linearGradient>
      <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#38bdf8" stop-opacity="0.35"/>
        <stop offset="100%" stop-color="#38bdf8" stop-opacity="0"/>
      </linearGradient>
      <linearGradient id="gaugeGrad" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0%" stop-color="#fbbf24"/>
        <stop offset="55%" stop-color="#38bdf8"/>
        <stop offset="100%" stop-color="#34d399"/>
      </linearGradient>
    </defs>`;

  function truncate(text, limit) {
    const value = String(text);
    return value.length > limit ? `${value.slice(0, limit - 1)}…` : value;
  }

  /* ------------------------------------------------------------------ *
   * Vertical bar chart
   * ------------------------------------------------------------------ */

  function bar(container, data, options = {}) {
    if (!container) return;
    const width = 640;
    const height = options.height || 300;
    const pad = { top: 26, right: 14, bottom: 46, left: 46 };
    const plotW = width - pad.left - pad.right;
    const plotH = height - pad.top - pad.bottom;
    const max = options.max || Math.max(...data.map((d) => d.value)) * 1.18 || 1;
    const suffix = options.suffix ?? "%";
    const digits = options.digits ?? 1;
    const showValues = options.showValues !== false;

    let content = defs();

    for (let i = 0; i <= 4; i += 1) {
      const y = pad.top + (plotH / 4) * i;
      const value = max - (max / 4) * i;
      content += `<line class="grid-line" x1="${pad.left}" y1="${y}" x2="${width - pad.right}" y2="${y}"/>`;
      content += `<text class="axis-label" x="${pad.left - 10}" y="${y + 4}" text-anchor="end">${fmt.compact(value)}${suffix === "%" ? "%" : ""}</text>`;
    }

    const slot = plotW / data.length;
    const barW = Math.min(options.barWidth || 52, slot * 0.58);

    data.forEach((item, index) => {
      const value = Math.max(0, Number(item.value) || 0);
      const barH = (value / max) * plotH;
      const x = pad.left + slot * index + (slot - barW) / 2;
      const y = pad.top + plotH - barH;
      const delay = index * 55;
      const tipText = item.tip || `<b>${esc(item.label)}</b><br>${value.toFixed(digits)}${suffix}${item.meta ? `<br>${esc(item.meta)}` : ""}`;

      content += `<rect class="bar" data-tip="${esc(tipText)}" x="${x}" y="${y}" width="${barW}" height="${Math.max(barH, 2)}" rx="6" fill="${options.warm ? "url(#barGradWarm)" : "url(#barGrad)"}" style="animation-delay:${delay}ms"/>`;

      if (showValues) {
        content += `<text class="value-label" x="${x + barW / 2}" y="${y - 8}" text-anchor="middle">${value.toFixed(digits)}${suffix}</text>`;
      }

      const label = String(item.label);
      const words = label.split(" ");
      if (words.length > 1 && label.length > 10) {
        content += `<text class="axis-label" x="${x + barW / 2}" y="${height - 32}" text-anchor="middle">${esc(words[0])}</text>`;
        content += `<text class="axis-label" x="${x + barW / 2}" y="${height - 18}" text-anchor="middle">${esc(words.slice(1).join(" "))}</text>`;
      } else {
        content += `<text class="axis-label" x="${x + barW / 2}" y="${height - 20}" text-anchor="middle">${esc(truncate(label, options.labelLimit || 18))}</text>`;
      }
    });

    container.innerHTML = svg(width, height, content, options.label || "Bar chart");
    bindTips(container);
  }

  /* ------------------------------------------------------------------ *
   * Horizontal bars
   * ------------------------------------------------------------------ */

  function hbar(container, data, options = {}) {
    if (!container) return;
    const rowH = options.rowHeight || 40;
    const width = 640;
    const labelW = options.labelWidth || 130;
    const valueW = 62;
    const height = data.length * rowH + 18;
    const max = Math.max(...data.map((d) => d.value)) || 1;
    const suffix = options.suffix ?? "%";
    const digits = options.digits ?? 1;
    let content = defs();

    data.forEach((item, index) => {
      const y = index * rowH + 10;
      const barMax = width - labelW - valueW - 16;
      const barW = Math.max(3, (item.value / max) * barMax);
      const tipText = item.tip || `<b>${esc(item.label)}</b><br>${Number(item.value).toFixed(digits)}${suffix}`;
      content += `<text class="axis-label" x="0" y="${y + 16}">${esc(truncate(item.label, 18))}</text>`;
      content += `<rect class="bar-h" data-tip="${esc(tipText)}" x="${labelW}" y="${y + 6}" width="${barW}" height="14" rx="7" fill="${options.warm ? "url(#barGradWarm)" : "url(#barGrad)"}" style="animation-delay:${index * 55}ms"/>`;
      content += `<text class="value-label" x="${width - 4}" y="${y + 17}" text-anchor="end">${Number(item.value).toFixed(digits)}${suffix}</text>`;
    });

    container.innerHTML = svg(width, height, content, options.label || "Horizontal bar chart");
    bindTips(container);
  }

  /* ------------------------------------------------------------------ *
   * Donut
   * ------------------------------------------------------------------ */

  function donut(container, segments, options = {}) {
    if (!container) return;
    container.style.maxWidth = "320px";
    container.style.marginInline = "auto";
    const size = 280;
    const radius = 100;
    const stroke = 26;
    const center = size / 2;
    const total = segments.reduce((sum, s) => sum + s.value, 0) || 1;
    const circumference = 2 * Math.PI * radius;
    let offset = 0;
    let content = defs();

    segments.forEach((segment) => {
      const fraction = segment.value / total;
      const length = Math.max(fraction * circumference - 4, 0);
      content += `<circle cx="${center}" cy="${center}" r="${radius}" fill="none" stroke="${segment.color}" stroke-width="${stroke}" stroke-linecap="butt" stroke-dasharray="${length} ${circumference - length}" stroke-dashoffset="${-offset}" transform="rotate(-90 ${center} ${center})" data-tip="${esc(`<b>${esc(segment.label)}</b><br>${fmt.int(segment.value)} leads · ${fmt.pct(fraction * 100, 2)}`)}"/>`;
      offset += fraction * circumference;
    });

    content += `<text x="${center}" y="${center - 2}" text-anchor="middle" fill="#e9f1fb" font-family="Sora, sans-serif" font-size="38" font-weight="600">${esc(options.centerValue || "")}</text>`;
    content += `<text x="${center}" y="${center + 24}" text-anchor="middle" fill="#7c8fac" font-size="12" letter-spacing="1.6">${esc(options.centerLabel || "")}</text>`;

    container.innerHTML = svg(size, size, content, options.label || "Donut chart");
    bindTips(container);
  }

  /* ------------------------------------------------------------------ *
   * Line / area chart
   * ------------------------------------------------------------------ */

  function line(container, points, options = {}) {
    if (!container) return;
    const width = 640;
    const height = options.height || 280;
    const pad = { top: 24, right: 20, bottom: 44, left: 46 };
    const plotW = width - pad.left - pad.right;
    const plotH = height - pad.top - pad.bottom;
    const suffix = options.suffix ?? "%";
    const digits = options.digits ?? 1;
    const values = points.map((p) => p.value);
    const min = options.min ?? Math.max(0, Math.min(...values) - 8);
    const max = options.max ?? Math.max(...values) + 6;
    const span = max - min || 1;

    const xAt = (index) => pad.left + (plotW / (points.length - 1 || 1)) * index;
    const yAt = (value) => pad.top + plotH - ((value - min) / span) * plotH;

    let content = defs();

    for (let i = 0; i <= 4; i += 1) {
      const y = pad.top + (plotH / 4) * i;
      const value = max - (span / 4) * i;
      content += `<line class="grid-line" x1="${pad.left}" y1="${y}" x2="${width - pad.right}" y2="${y}"/>`;
      content += `<text class="axis-label" x="${pad.left - 10}" y="${y + 4}" text-anchor="end">${value.toFixed(0)}${suffix === "%" ? "%" : ""}</text>`;
    }

    const linePath = points.map((p, i) => `${i === 0 ? "M" : "L"}${xAt(i)},${yAt(p.value)}`).join(" ");
    const areaPath = `${linePath} L${xAt(points.length - 1)},${pad.top + plotH} L${pad.left},${pad.top + plotH} Z`;

    content += `<path d="${areaPath}" fill="url(#areaGrad)"/>`;
    content += `<path d="${linePath}" fill="none" stroke="#38bdf8" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>`;

    points.forEach((point, index) => {
      const x = xAt(index);
      const y = yAt(point.value);
      const tipText = point.tip || `<b>${esc(point.label)}</b><br>${Number(point.value).toFixed(digits)}${suffix}`;
      content += `<circle class="point" data-tip="${esc(tipText)}" cx="${x}" cy="${y}" r="5" fill="#04121d" stroke="#38bdf8" stroke-width="2.5"/>`;
      content += `<text class="axis-label" x="${x}" y="${height - 18}" text-anchor="middle">${esc(point.label)}</text>`;
    });

    container.innerHTML = svg(width, height, content, options.label || "Line chart");
    bindTips(container);
  }

  /* ------------------------------------------------------------------ *
   * Scatter
   * ------------------------------------------------------------------ */

  function scatter(container, points, options = {}) {
    if (!container) return;
    const width = 640;
    const height = options.height || 330;
    const pad = { top: 24, right: 20, bottom: 46, left: 56 };
    const plotW = width - pad.left - pad.right;
    const plotH = height - pad.top - pad.bottom;
    const xMax = options.xMax || 50;
    const yMax = options.yMax || 200000;

    let content = defs();

    for (let i = 0; i <= 4; i += 1) {
      const y = pad.top + (plotH / 4) * i;
      const value = yMax - (yMax / 4) * i;
      content += `<line class="grid-line" x1="${pad.left}" y1="${y}" x2="${width - pad.right}" y2="${y}"/>`;
      content += `<text class="axis-label" x="${pad.left - 10}" y="${y + 4}" text-anchor="end">${fmt.compact(value)}</text>`;
    }

    for (let i = 0; i <= 5; i += 1) {
      const x = pad.left + (plotW / 5) * i;
      content += `<text class="axis-label" x="${x}" y="${height - 20}" text-anchor="middle">${Math.round((xMax / 5) * i)}</text>`;
    }

    content += `<text class="axis-label" x="${pad.left + plotW / 2}" y="${height - 2}" text-anchor="middle">${esc(options.xLabel || "")}</text>`;

    points.forEach((point) => {
      const x = pad.left + (Math.min(point.x, xMax) / xMax) * plotW;
      const y = pad.top + plotH - (Math.min(point.y, yMax) / yMax) * plotH;
      const color = point.converted ? "#34d399" : "#fb923c";
      const tipText = `<b>${point.converted ? "Converted" : "Not converted"}</b><br>Visits: ${point.x}<br>Budget: ${fmt.money(point.y)}`;
      content += `<circle class="point" data-tip="${esc(tipText)}" cx="${x}" cy="${y}" r="4.6" fill="${color}" fill-opacity="0.72" stroke="${color}" stroke-opacity="0.9" stroke-width="1"/>`;
    });

    container.innerHTML = svg(width, height, content, options.label || "Scatter chart");
    bindTips(container);
  }

  /* ------------------------------------------------------------------ *
   * Gauge (semi-circular)
   * ------------------------------------------------------------------ */

  function polar(cx, cy, r, angle) {
    const rad = ((angle - 180) * Math.PI) / 180;
    return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
  }

  function arc(cx, cy, r, startAngle, endAngle) {
    const start = polar(cx, cy, r, endAngle);
    const end = polar(cx, cy, r, startAngle);
    const largeArc = endAngle - startAngle <= 180 ? 0 : 1;
    return `M ${start.x} ${start.y} A ${r} ${r} 0 ${largeArc} 0 ${end.x} ${end.y}`;
  }

  function gauge(container, value, options = {}) {
    if (!container) return;
    const percent = Math.max(0, Math.min(100, Number(value) || 0));
    const cx = 150;
    const cy = 130;
    const r = 100;
    const endAngle = (percent / 100) * 180;
    const track = arc(cx, cy, r, 0, 180);
    const progress = percent > 0 ? arc(cx, cy, r, 0, Math.max(endAngle, 0.4)) : "";
    const threshold = options.threshold != null ? Number(options.threshold) : null;
    const thresholdAngle = threshold != null ? (threshold / 100) * 180 : null;

    let content = defs();
    content += `<path d="${track}" fill="none" stroke="rgba(148,183,224,0.14)" stroke-width="18" stroke-linecap="round"/>`;
    if (progress) {
      content += `<path d="${progress}" fill="none" stroke="url(#gaugeGrad)" stroke-width="18" stroke-linecap="round"/>`;
    }

    if (thresholdAngle != null) {
      const inner = polar(cx, cy, r - 16, thresholdAngle);
      const outer = polar(cx, cy, r + 16, thresholdAngle);
      content += `<line x1="${inner.x}" y1="${inner.y}" x2="${outer.x}" y2="${outer.y}" stroke="#e9f1fb" stroke-width="2" stroke-dasharray="3 3" opacity="0.75"/>`;
    }

    content += `<text x="${cx}" y="${cy - 24}" text-anchor="middle" class="gauge-value">${percent.toFixed(1)}%</text>`;
    content += `<text x="${cx}" y="${cy + 38}" text-anchor="middle" class="gauge-caption">conversion probability</text>`;

    container.innerHTML = svg(300, 192, content, `Conversion probability gauge: ${percent.toFixed(1)}%`);
  }

  /* ------------------------------------------------------------------ *
   * Counters, reveal, nav, copy
   * ------------------------------------------------------------------ */

  function animateCounters(root = document) {
    const nodes = root.querySelectorAll("[data-counter]");
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    nodes.forEach((node) => {
      const target = Number(node.getAttribute("data-counter"));
      const digits = Number(node.getAttribute("data-decimals") || 0);
      const prefix = node.getAttribute("data-prefix") || "";
      const suffix = node.getAttribute("data-suffix") || "";
      const formatter = new Intl.NumberFormat("en-US", {
        minimumFractionDigits: digits,
        maximumFractionDigits: digits,
      });

      if (reduce) {
        node.textContent = `${prefix}${formatter.format(target)}${suffix}`;
        return;
      }

      const duration = 1000;
      const start = performance.now();
      const tick = (now) => {
        const progress = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        node.textContent = `${prefix}${formatter.format(target * eased)}${suffix}`;
        if (progress < 1) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    });
  }

  function initReveal() {
    const items = document.querySelectorAll(".reveal");
    if (!("IntersectionObserver" in window)) {
      items.forEach((item) => item.classList.add("is-visible"));
      return;
    }
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
    );
    items.forEach((item) => observer.observe(item));
  }

  function initNav() {
    const nav = document.querySelector(".site-nav");
    const toggle = document.querySelector(".nav-toggle");
    const links = document.querySelector(".nav-links");

    if (nav) {
      const onScroll = () => nav.classList.toggle("is-scrolled", window.scrollY > 12);
      onScroll();
      window.addEventListener("scroll", onScroll, { passive: true });
    }

    if (toggle && links) {
      toggle.addEventListener("click", () => {
        const open = links.classList.toggle("is-open");
        toggle.setAttribute("aria-expanded", String(open));
      });
      links.querySelectorAll("a").forEach((link) =>
        link.addEventListener("click", () => {
          links.classList.remove("is-open");
          toggle.setAttribute("aria-expanded", "false");
        })
      );
    }

    const page = document.body.getAttribute("data-page");
    document.querySelectorAll(".nav-links a[data-nav]").forEach((link) => {
      if (link.getAttribute("data-nav") === page) link.setAttribute("aria-current", "page");
    });
  }

  function initCopy() {
    document.querySelectorAll("[data-copy]").forEach((button) => {
      button.addEventListener("click", async () => {
        const target = document.querySelector(button.getAttribute("data-copy"));
        if (!target) return;
        try {
          await navigator.clipboard.writeText(target.textContent);
          const previous = button.textContent;
          button.textContent = "Copied";
          setTimeout(() => { button.textContent = previous; }, 1600);
        } catch {
          button.textContent = "Press Ctrl+C";
        }
      });
    });
  }

  function boot() {
    initNav();
    initReveal();
    initCopy();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }

  return { fmt, esc, loadJSON, bar, hbar, donut, line, scatter, gauge, animateCounters, initReveal, bindTips, truncate };
})();
