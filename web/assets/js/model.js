/* Model Lab — live scoring, driver attribution and model reporting. */

(async function initModelLab() {
  const { fmt, gauge, line, esc } = Copilot;

  let model;
  let analytics;

  try {
    [model, analytics] = await Promise.all([
      Copilot.loadJSON("assets/data/model.json"),
      Copilot.loadJSON("assets/data/analytics.json"),
    ]);
  } catch (error) {
    console.error(error);
    return;
  }

  const form = document.getElementById("leadForm");
  const $ = (id) => document.getElementById(id);
  const fields = [
    "lead_source",
    "industry",
    "company_size",
    "budget",
    "website_visits",
    "emails_opened",
    "calls_made",
    "previous_interactions",
    "response_time_hours",
  ];

  /* ---------------------------------------------------------------- *
   * Populate categorical selects from the exported encoder categories
   * ---------------------------------------------------------------- */

  model.categorical.forEach((feature) => {
    const select = $(feature.name);
    if (!select) return;
    select.innerHTML = feature.options
      .map((option) => `<option value="${esc(option.value)}">${esc(option.value)}</option>`)
      .join("");
  });

  const presets = {
    hot: {
      lead_source: "Website",
      industry: "IT",
      company_size: "Large",
      budget: 150000,
      website_visits: 40,
      emails_opened: 15,
      calls_made: 10,
      previous_interactions: 8,
      response_time_hours: 1,
    },
    warm: {
      lead_source: "Referral",
      industry: "Healthcare",
      company_size: "Medium",
      budget: 30000,
      website_visits: 8,
      emails_opened: 3,
      calls_made: 2,
      previous_interactions: 1,
      response_time_hours: 6,
    },
    cold: {
      lead_source: "Social Media",
      industry: "Retail",
      company_size: "Small",
      budget: 5000,
      website_visits: 1,
      emails_opened: 0,
      calls_made: 0,
      previous_interactions: 0,
      response_time_hours: 48,
    },
    median: {
      lead_source: "Email",
      industry: "Healthcare",
      company_size: "Medium",
      budget: Math.round(model.numeric.find((f) => f.name === "budget").median),
      website_visits: Math.round(model.numeric.find((f) => f.name === "website_visits").median),
      emails_opened: Math.round(model.numeric.find((f) => f.name === "emails_opened").median),
      calls_made: Math.round(model.numeric.find((f) => f.name === "calls_made").median),
      previous_interactions: Math.round(model.numeric.find((f) => f.name === "previous_interactions").median),
      response_time_hours: Math.round(model.numeric.find((f) => f.name === "response_time_hours").median * 10) / 10,
    },
  };

  function applyPreset(values) {
    fields.forEach((field) => {
      const input = $(field);
      if (input && values[field] != null) input.value = values[field];
    });
    render();
  }

  document.querySelectorAll("[data-preset]").forEach((button) => {
    button.addEventListener("click", () => {
      const key = button.dataset.preset;
      document.querySelectorAll("[data-preset]").forEach((other) =>
        other.setAttribute("aria-pressed", "false")
      );
      button.setAttribute("aria-pressed", "true");
      applyPreset(presets[key]);
    });
  });

  /* ---------------------------------------------------------------- *
   * Read + score
   * ---------------------------------------------------------------- */

  function readLead() {
    const lead = {};
    fields.forEach((field) => {
      const input = $(field);
      lead[field] = input.value;
    });
    return lead;
  }

  function render() {
    const lead = readLead();
    const result = CopilotScoring.score(model, lead);
    const percent = result.probability * 100;

    gauge($("labGauge"), percent, { threshold: model.threshold * 100 });

    const verdict = $("labVerdict");
    verdict.textContent = result.prediction;
    verdict.className = `verdict ${result.above ? "good" : "bad"}`;

    $("labThreshold").textContent = `cut-off ${(model.threshold * 100).toFixed(0)}%`;
    $("resultLogit").textContent = `logit ${result.logit.toFixed(2)}`;
    $("resultLeadLine").textContent = `${lead.lead_source} · ${lead.industry} · ${lead.company_size}`;

    const contributions = [...result.contributions].sort(
      (a, b) => Math.abs(b.value) - Math.abs(a.value)
    );
    const maxAbs = Math.max(...contributions.map((item) => Math.abs(item.value)), 0.001);

    $("contributionList").innerHTML = contributions
      .slice(0, 8)
      .map((item) => {
        const magnitude = (Math.abs(item.value) / maxAbs) * 50;
        const positive = item.value >= 0;
        const left = positive ? 50 : 50 - magnitude;
        const label = item.kind === "categorical"
          ? item.label.replace(":", " ·")
          : item.label;
        return `<div class="contribution">
          <span class="name">${esc(label)}</span>
          <span class="track">
            <span class="fill${positive ? "" : " neg"}" style="left:${left}%; width:${Math.max(magnitude, 0.6)}%"></span>
          </span>
          <span class="value">${positive ? "+" : ""}${item.value.toFixed(2)}</span>
        </div>`;
      })
      .join("");
  }

  form.addEventListener("input", render);
  form.addEventListener("change", render);
  form.addEventListener("submit", (event) => event.preventDefault());

  // The <select> elements select their first option on populate, so restore the
  // documented high-intent example explicitly.
  applyPreset(presets.hot);
  document.querySelector('[data-preset="hot"]').setAttribute("aria-pressed", "true");

  /* ---------------------------------------------------------------- *
   * Model card
   * ---------------------------------------------------------------- */

  const holdout = analytics.holdout;
  const rate = (value) => `${(value * 100).toFixed(1)}%`;

  $("holdoutNote").textContent = `${fmt.int(holdout.rows)} held-out leads · threshold ${(holdout.threshold * 100).toFixed(0)}%`;
  $("modelBadge").textContent = `pipeline v${model.modelVersion}`;

  const metrics = [
    ["Accuracy", rate(holdout.accuracy)],
    ["Macro F1", rate(holdout.macroF1)],
    ["ROC-AUC", fmt.num(holdout.rocAuc, 3)],
    ["Recall (converted)", rate(holdout.recall)],
    ["Precision (converted)", rate(holdout.precision)],
    ["Hold-out rows", fmt.int(holdout.rows)],
  ];

  $("metricGrid").innerHTML = metrics
    .map(
      ([label, value]) =>
        `<div class="metric"><div class="m-label">${label}</div><div class="m-value">${value}</div></div>`
    )
    .join("");

  const confusion = holdout.confusion;
  $("confusionGrid").innerHTML = `
    <div class="head"></div>
    <div class="head">Predicted no</div>
    <div class="head">Predicted yes</div>

    <div class="head" style="justify-items: start;">Actual no</div>
    <div class="cell hit"><b>${fmt.int(confusion.trueNegative)}</b>true negative</div>
    <div class="cell miss"><b>${fmt.int(confusion.falsePositive)}</b>false positive</div>

    <div class="head" style="justify-items: start;">Actual yes</div>
    <div class="cell miss"><b>${fmt.int(confusion.falseNegative)}</b>false negative</div>
    <div class="cell hit"><b>${fmt.int(confusion.truePositive)}</b>true positive</div>
  `;

  line(
    $("thresholdChart"),
    analytics.thresholdSweep.map((row) => ({
      label: row.threshold.toFixed(2),
      value: row.accuracy * 100,
      tip: `<b>Threshold ${row.threshold.toFixed(2)}</b><br>Accuracy ${(row.accuracy * 100).toFixed(1)}%<br>Macro F1 ${row.macroF1.toFixed(3)}<br>${fmt.int(row.predictedConversions)} conversions predicted`,
    })),
    {
      suffix: "%",
      min: 60,
      max: 90,
      label: "Hold-out accuracy across decision thresholds",
    }
  );

  $("thresholdBody").innerHTML = analytics.thresholdSweep
    .map(
      (row) => `<tr>
        <td class="strong">${row.threshold.toFixed(2)}${row.threshold === holdout.threshold ? ' <span class="tag info">deployed</span>' : ""}</td>
        <td class="right">${(row.accuracy * 100).toFixed(1)}%</td>
        <td class="right">${row.macroF1.toFixed(3)}</td>
        <td class="right">${fmt.int(row.predictedConversions)}</td>
      </tr>`
    )
    .join("");

  $("comparisonBody").innerHTML = analytics.modelComparison
    .map(
      (row) => `<tr>
        <td class="strong">${esc(row.model)}</td>
        <td class="right">${row.threshold.toFixed(2)}</td>
        <td class="right">${(row.accuracy * 100).toFixed(1)}%</td>
        <td class="right">${row.macroF1.toFixed(3)}</td>
        <td class="right">${row.rocAuc.toFixed(3)}</td>
      </tr>`
    )
    .join("");

  $("scenarioBody").innerHTML = analytics.scenarios
    .map((row) => {
      const hot = row.probability >= row.threshold;
      return `<tr>
        <td class="strong">${esc(row.leadId)}</td>
        <td>${esc(row.leadSource)} · ${esc(row.industry)} · ${esc(row.companySize)}</td>
        <td class="right">${(row.probability * 100).toFixed(2)}%</td>
        <td><span class="tag ${hot ? "good" : ""}">${esc(row.prediction)}</span></td>
      </tr>`;
    })
    .join("");
})();
