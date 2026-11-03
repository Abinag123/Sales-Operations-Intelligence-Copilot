/* Interactive analytics dashboard — recomputes everything from the raw rows. */

(async function initAnalytics() {
  const { fmt, bar, donut, hbar, line, scatter } = Copilot;

  let analytics;
  try {
    analytics = await Copilot.loadJSON("assets/data/analytics.json");
  } catch (error) {
    console.error(error);
    document.getElementById("statLeads").textContent = "Unavailable";
    return;
  }

  const { columns, categories, rows } = analytics.raw;
  const col = {};
  columns.forEach((name, index) => { col[name] = index; });

  const industries = categories.industry;
  const sources = categories.lead_source;
  const selectedIndustries = new Set(industries);
  const selectedSources = new Set(sources);

  const $ = (id) => document.getElementById(id);

  /* ---------------------------------------------------------------- *
   * Filter chips
   * ---------------------------------------------------------------- */

  function buildChips(container, values, selection) {
    container.innerHTML = values
      .map(
        (value) =>
          `<button class="chip" type="button" data-value="${Copilot.esc(value)}" aria-pressed="true">${Copilot.esc(value)}</button>`
      )
      .join("");

    container.querySelectorAll("button").forEach((button) => {
      button.addEventListener("click", () => {
        const value = button.dataset.value;
        if (selection.has(value)) {
          if (selection.size === 1) return;
          selection.delete(value);
        } else {
          selection.add(value);
        }
        button.setAttribute("aria-pressed", String(selection.has(value)));
        render();
      });
    });
  }

  buildChips($("industryFilters"), industries, selectedIndustries);
  buildChips($("sourceFilters"), sources, selectedSources);

  $("resetFilters").addEventListener("click", () => {
    industries.forEach((value) => selectedIndustries.add(value));
    sources.forEach((value) => selectedSources.add(value));
    document.querySelectorAll(".filter-bar .chip").forEach((chip) =>
      chip.setAttribute("aria-pressed", "true")
    );
    render();
  });

  /* ---------------------------------------------------------------- *
   * Aggregation helpers
   * ---------------------------------------------------------------- */

  function rateTable(list, index, names) {
    const buckets = new Map(names.map((name) => [name, { leads: 0, converted: 0 }]));
    list.forEach((row) => {
      const name = names[row[index]];
      const bucket = buckets.get(name);
      if (!bucket) return;
      bucket.leads += 1;
      bucket.converted += row[col.converted];
    });
    return [...buckets.entries()]
      .map(([name, bucket]) => ({
        name,
        leads: bucket.leads,
        converted: bucket.converted,
        rate: bucket.leads ? (bucket.converted / bucket.leads) * 100 : 0,
      }))
      .filter((row) => row.leads > 0)
      .sort((a, b) => b.rate - a.rate);
  }

  const RESPONSE_EDGES = [0, 6, 12, 24, 36, 48, 60, 72.01];
  const RESPONSE_LABELS = ["0-6h", "6-12h", "12-24h", "24-36h", "36-48h", "48-60h", "60-72h"];

  function responseBuckets(list) {
    const buckets = RESPONSE_LABELS.map((label) => ({ label, leads: 0, converted: 0 }));
    list.forEach((row) => {
      const value = row[col.response_time_hours];
      for (let i = 0; i < RESPONSE_EDGES.length - 1; i += 1) {
        if (value >= RESPONSE_EDGES[i] && value < RESPONSE_EDGES[i + 1]) {
          buckets[i].leads += 1;
          buckets[i].converted += row[col.converted];
          break;
        }
      }
    });
    return buckets
      .filter((bucket) => bucket.leads > 0)
      .map((bucket) => ({
        label: bucket.label,
        leads: bucket.leads,
        rate: (bucket.converted / bucket.leads) * 100,
      }));
  }

  const ENGAGEMENT_EDGES = [0, 20, 35, 50, 65, 80, 1000];
  const ENGAGEMENT_LABELS = ["0-20", "21-35", "36-50", "51-65", "66-80", "80+"];

  function engagementBuckets(list) {
    const buckets = ENGAGEMENT_LABELS.map((label) => ({ label, leads: 0, converted: 0 }));
    list.forEach((row) => {
      const score =
        row[col.website_visits] +
        row[col.emails_opened] +
        row[col.calls_made] +
        row[col.previous_interactions];
      for (let i = 0; i < ENGAGEMENT_EDGES.length - 1; i += 1) {
        if (score >= ENGAGEMENT_EDGES[i] && score < ENGAGEMENT_EDGES[i + 1]) {
          buckets[i].leads += 1;
          buckets[i].converted += row[col.converted];
          break;
        }
      }
    });
    return buckets
      .filter((bucket) => bucket.leads > 0)
      .map((bucket) => ({
        label: bucket.label,
        leads: bucket.leads,
        rate: (bucket.converted / bucket.leads) * 100,
      }));
  }

  function budgetQuartiles(list) {
    const budgets = list.map((row) => row[col.budget]).sort((a, b) => a - b);
    if (!budgets.length) return [];
    const quantile = (p) => budgets[Math.min(budgets.length - 1, Math.floor(p * (budgets.length - 1)))];
    const bounds = [quantile(0.25), quantile(0.5), quantile(0.75)];
    const labels = ["Q1 lowest", "Q2", "Q3", "Q4 highest"];
    const buckets = labels.map((label) => ({ label, leads: 0, converted: 0, budgetTotal: 0 }));

    list.forEach((row) => {
      const value = row[col.budget];
      const band = value <= bounds[0] ? 0 : value <= bounds[1] ? 1 : value <= bounds[2] ? 2 : 3;
      buckets[band].leads += 1;
      buckets[band].budgetTotal += value;
      buckets[band].converted += row[col.converted];
    });

    return buckets
      .filter((bucket) => bucket.leads > 0)
      .map((bucket) => ({
        label: bucket.label,
        leads: bucket.leads,
        rate: (bucket.converted / bucket.leads) * 100,
        avgBudget: bucket.budgetTotal / bucket.leads,
      }));
  }

  /* ---------------------------------------------------------------- *
   * Render
   * ---------------------------------------------------------------- */

  let currentRows = [];

  function render() {
    currentRows = rows.filter(
      (row) =>
        selectedIndustries.has(industries[row[col.industry]]) &&
        selectedSources.has(sources[row[col.lead_source]])
    );

    const total = currentRows.length;
    const converted = currentRows.reduce((sum, row) => sum + row[col.converted], 0);
    const rate = total ? (converted / total) * 100 : 0;
    const budgetTotal = currentRows.reduce((sum, row) => sum + row[col.budget], 0);
    const avgBudget = total ? budgetTotal / total : 0;
    const responseTotal = currentRows.reduce((sum, row) => sum + row[col.response_time_hours], 0);
    const avgResponse = total ? responseTotal / total : 0;

    $("statLeads").textContent = fmt.int(total);
    $("statLeadsFoot").textContent = `of ${fmt.int(rows.length)} total leads`;
    $("statConverted").textContent = fmt.int(converted);
    $("statConvertedFoot").textContent = `${fmt.int(total - converted)} did not convert`;
    $("statRate").textContent = fmt.pct(rate, 2);
    $("statRateFoot").textContent = `Baseline ${fmt.pct(analytics.kpis.conversionRate, 2)}`;
    $("statBudget").textContent = fmt.money(avgBudget);
    $("statBudgetFoot").textContent = `Avg response ${avgResponse.toFixed(1)}h`;

    const industryCount = currentRows.length
      ? new Set(currentRows.map((row) => row[col.industry])).size
      : 0;
    const sourceCount = currentRows.length
      ? new Set(currentRows.map((row) => row[col.lead_source])).size
      : 0;
    $("viewTag").textContent = `${industryCount} industries · ${sourceCount} channels`;

    const bySource = rateTable(currentRows, col.lead_source, sources);
    const byIndustry = rateTable(currentRows, col.industry, industries);
    const outcomes = [
      { label: "Converted", value: converted, color: "#34d399" },
      { label: "Not converted", value: total - converted, color: "#475569" },
    ];

    if (total === 0) {
      ["chSource", "chIndustry", "chResponse", "chEngagement", "chBudget", "chOutcome", "chScatter"].forEach((id) => {
        $(id).innerHTML = '<p class="muted" style="font-size:.85rem;padding:24px 0">No leads match the current filters.</p>';
      });
      document.querySelector("#leadTable tbody").innerHTML = "";
      $("tableCount").textContent = "0 rows";
      return;
    }

    bar(
      $("chSource"),
      bySource.map((row) => ({
        label: row.name,
        value: row.rate,
        tip: `<b>${row.name}</b><br>${row.rate.toFixed(2)}% conversion<br>${fmt.int(row.leads)} leads`,
      })),
      { suffix: "%", max: 100, label: "Conversion by channel" }
    );

    // Donut adds its own centre labels
    donut($("chOutcome"), outcomes, {
      centerValue: fmt.pct(rate, 1),
      centerLabel: "CONVERSION",
      label: "Outcome mix",
    });

    hbar(
      $("chIndustry"),
      byIndustry.map((row) => ({
        label: row.name,
        value: row.rate,
        tip: `<b>${row.name}</b><br>${row.rate.toFixed(2)}% conversion<br>${fmt.int(row.leads)} leads`,
      })),
      { suffix: "%", label: "Conversion by industry" }
    );

    const responses = responseBuckets(currentRows);
    line(
      $("chResponse"),
      responses.map((row) => ({
        label: row.label,
        value: row.rate,
        tip: `<b>${row.label} response</b><br>${row.rate.toFixed(2)}% conversion<br>${fmt.int(row.leads)} leads`,
      })),
      { suffix: "%", min: 60, max: 100, label: "Conversion by response window" }
    );

    bar(
      $("chEngagement"),
      engagementBuckets(currentRows).map((row) => ({
        label: row.label,
        value: row.rate,
        tip: `<b>Engagement ${row.label}</b><br>${row.rate.toFixed(2)}% conversion<br>${fmt.int(row.leads)} leads`,
      })),
      { suffix: "%", max: 100, label: "Conversion by engagement volume" }
    );

    bar(
      $("chBudget"),
      budgetQuartiles(currentRows).map((row) => ({
        label: row.label,
        value: row.rate,
        tip: `<b>${row.label}</b><br>Avg budget ${fmt.money(row.avgBudget)}<br>${row.rate.toFixed(2)}% conversion<br>${fmt.int(row.leads)} leads`,
      })),
      { suffix: "%", max: 100, label: "Conversion by budget quartile" }
    );

    const step = Math.max(1, Math.ceil(currentRows.length / 320));
    const sampled = currentRows
      .filter((_, index) => index % step === 0)
      .slice(0, 320)
      .map((row) => ({
        x: row[col.website_visits],
        y: row[col.budget],
        converted: row[col.converted],
      }));

    scatter($("chScatter"), sampled, {
      xMax: 50,
      yMax: 200000,
      xLabel: "website visits",
      label: "Website visits versus budget, coloured by outcome",
    });

    /* Quality + table */
    $("qualityGrid").innerHTML = [
      ["Rows", fmt.int(analytics.dataset.rows)],
      ["Missing values", fmt.int(analytics.dataset.missingValues)],
      ["Duplicate rows", fmt.int(analytics.dataset.duplicateRows)],
      ["Target rate", fmt.pct(analytics.dataset.targetPositiveRate, 2)],
    ]
      .map(
        ([label, value]) =>
          `<div class="metric"><div class="m-label">${label}</div><div class="m-value">${value}</div></div>`
      )
      .join("");

    const preview = currentRows.slice(0, 12);
    document.querySelector("#leadTable tbody").innerHTML = preview
      .map((row) => {
        const convertedFlag = row[col.converted] === 1;
        return `<tr>
          <td class="strong">${Copilot.esc(sources[row[col.lead_source]])}</td>
          <td>${Copilot.esc(industries[row[col.industry]])}</td>
          <td>${Copilot.esc(categories.company_size[row[col.company_size]])}</td>
          <td class="right">${fmt.money(row[col.budget])}</td>
          <td class="right">${row[col.website_visits]}</td>
          <td class="right">${row[col.emails_opened]}</td>
          <td class="right">${row[col.calls_made]}</td>
          <td class="right">${row[col.previous_interactions]}</td>
          <td class="right">${row[col.response_time_hours].toFixed(1)}</td>
          <td><span class="tag ${convertedFlag ? "good" : ""}">${convertedFlag ? "Converted" : "No"}</span></td>
        </tr>`;
      })
      .join("");

    $("tableCount").textContent = `${fmt.int(currentRows.length)} rows`;
    $("tableCaption").textContent = `Showing ${preview.length} of ${fmt.int(currentRows.length)} matching records`;
  }

  render();
})();
