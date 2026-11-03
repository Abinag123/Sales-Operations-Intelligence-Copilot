/* Landing page: hero console, KPI band, analytics previews, assistant teaser. */

(async function initHome() {
  const { fmt, bar, hbar, donut, line, gauge, animateCounters, bindTips } = Copilot;

  let analytics;
  let model;
  let knowledge;

  try {
    [analytics, model, knowledge] = await Promise.all([
      Copilot.loadJSON("assets/data/analytics.json"),
      Copilot.loadJSON("assets/data/model.json"),
      Copilot.loadJSON("assets/data/knowledge.json"),
    ]);
  } catch (error) {
    console.error(error);
    document.querySelectorAll(".chart").forEach((node) => {
      node.innerHTML = '<p class="muted" style="font-size:.85rem">Data unavailable.</p>';
    });
    return;
  }

  /* ---------------------------------------------------------------- *
   * Hero console
   * ---------------------------------------------------------------- */

  const sampleLead = {
    lead_source: "Website",
    industry: "IT",
    company_size: "Large",
    budget: 150000,
    website_visits: 40,
    emails_opened: 15,
    calls_made: 10,
    previous_interactions: 8,
    response_time_hours: 1,
  };

  const result = CopilotScoring.score(model, sampleLead);
  const percent = result.probability * 100;

  gauge(document.getElementById("heroGauge"), percent, { threshold: model.threshold * 100 });

  const verdict = document.getElementById("heroVerdict");
  if (verdict) {
    verdict.textContent = result.prediction;
    verdict.className = `verdict ${result.above ? "good" : "bad"}`;
  }

  const drivers = CopilotScoring.topDrivers(result, 4);
  const maxContribution = Math.max(...drivers.map((item) => Math.abs(item.value)), 0.001);
  const driverList = document.getElementById("heroDrivers");
  if (driverList) {
    driverList.innerHTML = drivers
      .map(
        (item) => `
        <div class="driver">
          <span class="driver-name">${Copilot.esc(item.label.replace(/:.*/, ""))}</span>
          <span class="driver-track"><span class="driver-fill${item.value < 0 ? " neg" : ""}" style="width:${(Math.abs(item.value) / maxContribution) * 100}%"></span></span>
          <span class="driver-val">${item.value >= 0 ? "+" : ""}${item.value.toFixed(2)}</span>
        </div>`
      )
      .join("");
    bindTips(driverList);
  }

  /* ---------------------------------------------------------------- *
   * KPI band + hero stats
   * ---------------------------------------------------------------- */

  const kpis = analytics.kpis;
  const assign = (id, value) => {
    const node = document.getElementById(id);
    if (node) node.textContent = value;
  };

  const counters = [
    ["kpiLeads", kpis.totalLeads, 0, ""],
    ["kpiConverted", kpis.convertedLeads, 0, ""],
    ["kpiRate", kpis.conversionRate, 2, "%"],
    ["kpiBudget", kpis.averageBudget, 0, ""],
  ];

  counters.forEach(([id, value, decimals, suffix]) => {
    const node = document.getElementById(id);
    if (!node) return;
    node.setAttribute("data-counter", String(value));
    node.setAttribute("data-decimals", String(decimals));
    node.setAttribute("data-suffix", suffix);
  });

  assign("heroLeads", fmt.int(kpis.totalLeads));
  assign("heroRate", fmt.pct(kpis.conversionRate, 2));
  assign("heroAuc", fmt.num(analytics.holdout.rocAuc, 3));
  assign("heroChunks", fmt.int(kpis.knowledgeChunks));

  animateCounters();

  /* ---------------------------------------------------------------- *
   * Charts
   * ---------------------------------------------------------------- */

  bar(
    document.getElementById("sourceChart"),
    analytics.bySource.map((row) => ({
      label: row.name,
      value: row.rate,
      tip: `<b>${row.name}</b><br>${row.rate.toFixed(2)}% conversion<br>${fmt.int(row.leads)} leads · ${fmt.int(row.converted)} converted`,
    })),
    { suffix: "%", max: 100, label: "Conversion rate by lead source" }
  );

  donut(
    document.getElementById("outcomeChart"),
    [
      { label: "Converted", value: kpis.convertedLeads, color: "#34d399" },
      { label: "Not converted", value: kpis.notConvertedLeads, color: "#475569" },
    ],
    { centerValue: fmt.pct(kpis.conversionRate, 1), centerLabel: "CONVERSION", label: "Lead outcome distribution" }
  );

  hbar(
    document.getElementById("industryChart"),
    analytics.byIndustry.map((row) => ({
      label: row.name,
      value: row.rate,
      tip: `<b>${row.name}</b><br>${row.rate.toFixed(2)}% conversion<br>${fmt.int(row.leads)} leads`,
    })),
    { suffix: "%", label: "Conversion rate by industry" }
  );

  line(
    document.getElementById("responseChart"),
    analytics.responseBuckets.map((row) => ({
      label: row.label,
      value: row.rate,
      tip: `<b>${row.label} first response</b><br>${row.rate.toFixed(2)}% conversion<br>${fmt.int(row.leads)} leads`,
    })),
    { suffix: "%", min: 65, max: 95, label: "Conversion rate by response time" }
  );

  /* Diverging correlation chart (hand-built) */
  const corrNode = document.getElementById("correlationChart");
  if (corrNode) {
    const rows = analytics.correlation;
    const width = 640;
    const rowH = 38;
    const labelW = 168;
    const height = rows.length * rowH + 26;
    const centerX = labelW + (width - labelW - 40) / 2;
    const half = (width - labelW - 40) / 2;
    const maxAbs = Math.max(...rows.map((row) => Math.abs(row.value)), 0.001);

    let inner = `
      <defs>
        <linearGradient id="corrPos" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stop-color="#0ea5e9" stop-opacity=".5"/>
          <stop offset="100%" stop-color="#38bdf8"/>
        </linearGradient>
        <linearGradient id="corrNeg" x1="1" y1="0" x2="0" y2="0">
          <stop offset="0%" stop-color="#f97316" stop-opacity=".5"/>
          <stop offset="100%" stop-color="#fb7185"/>
        </linearGradient>
      </defs>`;

    inner += `<line x1="${centerX}" y1="8" x2="${centerX}" y2="${height - 14}" stroke="rgba(148,183,224,.22)" stroke-width="1"/>`;
    inner += `<text class="axis-label" x="${centerX}" y="${height - 1}" text-anchor="middle">0</text>`;

    rows.forEach((row, index) => {
      const y = index * rowH + 10;
      const barW = (Math.abs(row.value) / maxAbs) * half;
      const positive = row.value >= 0;
      const x = positive ? centerX : centerX - barW;
      const tip = `<b>${row.feature.replace(/_/g, " ")}</b><br>Pearson r = ${row.value.toFixed(3)}`;
      inner += `<text class="axis-label" x="0" y="${y + 16}">${Copilot.esc(row.feature.replace(/_/g, " "))}</text>`;
      inner += `<rect class="bar-h" data-tip="${Copilot.esc(tip)}" x="${x}" y="${y + 6}" width="${Math.max(barW, 2)}" height="14" rx="7" fill="url(#${positive ? "corrPos" : "corrNeg"})" style="animation-delay:${index * 50}ms; transform-origin:${positive ? "left" : "right"}"/>`;
      inner += `<text class="value-label" x="${positive ? x + barW + 8 : x - 8}" y="${y + 17}" text-anchor="${positive ? "start" : "end"}">${row.value.toFixed(2)}</text>`;
    });

    corrNode.innerHTML = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Correlation of numeric features with conversion" preserveAspectRatio="xMidYMid meet">${inner}</svg>`;
    bindTips(corrNode);
  }

  bar(
    document.getElementById("budgetChart"),
    analytics.budgetQuartiles.map((row) => ({
      label: row.label,
      value: row.rate,
      tip: `<b>${row.label}</b><br>Avg budget ${fmt.money(row.avgBudget)}<br>${row.rate.toFixed(2)}% conversion<br>${fmt.int(row.leads)} leads`,
    })),
    { suffix: "%", max: 100, label: "Conversion by budget quartile" }
  );

  /* ---------------------------------------------------------------- *
   * Assistant teaser
   * ---------------------------------------------------------------- */

  const answer = document.getElementById("teaserAnswer");
  if (answer) answer.textContent = knowledge.transcript.answer;

  const chunkList = document.getElementById("teaserChunks");
  if (chunkList) {
    const citations = (knowledge.transcript.citations || []).slice(0, 3);
    chunkList.innerHTML = citations
      .map((citation, index) => {
        const match = knowledge.chunks.find(
          (item) => item.source === citation.source && item.chunkId === citation.chunkId
        );
        if (!match) return "";
        const excerpt = Copilot.truncate(match.content, 190);
        return `
          <div class="chunk">
            <div class="chunk-head">
              <span><strong style="color:#e9f1fb">Source ${index + 1}</strong> &middot; ${Copilot.esc(citation.source)} &middot; chunk ${citation.chunkId}</span>
              <span class="tag ${index === 0 ? "good" : "info"}">distance ${citation.distance.toFixed(3)}</span>
            </div>
            <p class="chunk-text">${Copilot.esc(excerpt)}</p>
          </div>
        `;
      })
      .join("");
  }
})();
