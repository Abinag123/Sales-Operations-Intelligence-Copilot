/* ==========================================================================
   Browser-exact inference for the exported scikit-learn pipeline.

   The JSON mirrors every preprocessing step that sklearn applies:
     numeric  -> median imputation, then (x - mean) / scale
     category -> one-hot encoding, unseen categories contribute zero
     logit    -> intercept + sum(coef_i * x_i), probability = sigmoid(logit)
   ========================================================================== */

window.CopilotScoring = (() => {
  function toNumber(value, fallback) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
  }

  function score(model, lead) {
    let logit = model.intercept;
    const contributions = [];

    model.numeric.forEach((feature) => {
      const raw = toNumber(lead[feature.name], feature.median);
      const standardized = (raw - feature.mean) / feature.scale;
      const contribution = feature.coef * standardized;
      logit += contribution;
      contributions.push({
        key: feature.name,
        label: feature.name.replace(/_/g, " "),
        value: contribution,
        raw,
        kind: "numeric",
      });
    });

    model.categorical.forEach((feature) => {
      const chosen = String(lead[feature.name] ?? "");
      const option = feature.options.find((item) => item.value === chosen);
      const contribution = option ? option.coef : 0;
      logit += contribution;
      contributions.push({
        key: feature.name,
        label: `${feature.name.replace(/_/g, " ")}: ${chosen || "unknown"}`,
        value: contribution,
        kind: "categorical",
        matched: Boolean(option),
      });
    });

    const probability = 1 / (1 + Math.exp(-logit));
    const above = probability >= model.threshold;

    return {
      probability,
      logit,
      contributions,
      above,
      prediction: above ? "Likely to Convert" : "Unlikely to Convert",
      threshold: model.threshold,
    };
  }

  function topDrivers(result, limit = 4) {
    return [...result.contributions]
      .filter((item) => Math.abs(item.value) > 1e-6)
      .sort((a, b) => Math.abs(b.value) - Math.abs(a.value))
      .slice(0, limit);
  }

  return { score, topDrivers };
})();
