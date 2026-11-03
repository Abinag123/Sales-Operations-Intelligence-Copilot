/* Knowledge assistant — browser-side BM25 over the indexed ChromaDB chunks. */

(async function initKnowledge() {
  const { esc } = Copilot;

  let knowledge;
  try {
    knowledge = await Copilot.loadJSON("assets/data/knowledge.json");
  } catch (error) {
    console.error(error);
    return;
  }

  const $ = (id) => document.getElementById(id);
  const chunks = knowledge.chunks;
  const transcript = knowledge.transcript;

  $("chunkCount").textContent = `${chunks.length} chunks`;

  /* ---------------------------------------------------------------- *
   * BM25 index
   * ---------------------------------------------------------------- */

  const K1 = 1.5;
  const B = 0.75;

  const tokenize = (text) =>
    text
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, " ")
      .trim()
      .split(/\s+/)
      .filter(Boolean);

  const documents = chunks.map((chunk) => tokenize(chunk.content));
  const lengths = documents.map((tokens) => tokens.length);
  const averageLength = lengths.reduce((sum, value) => sum + value, 0) / (lengths.length || 1);
  const documentFrequency = new Map();

  documents.forEach((tokens) => {
    new Set(tokens).forEach((token) => {
      documentFrequency.set(token, (documentFrequency.get(token) || 0) + 1);
    });
  });

  const total = documents.length;

  function idf(term) {
    const frequency = documentFrequency.get(term) || 0;
    return Math.log(1 + (total - frequency + 0.5) / (frequency + 0.5));
  }

  function search(query, topK = 3) {
    const terms = tokenize(query);
    if (!terms.length) return [];

    return chunks
      .map((chunk, index) => {
        const tokens = documents[index];
        const counts = new Map();
        tokens.forEach((token) => counts.set(token, (counts.get(token) || 0) + 1));

        let score = 0;
        terms.forEach((term) => {
          const frequency = counts.get(term) || 0;
          if (!frequency) return;
          const denominator =
            frequency + K1 * (1 - B + (B * tokens.length) / averageLength);
          score += idf(term) * ((frequency * (K1 + 1)) / denominator);
        });

        return { chunk, score };
      })
      .filter((row) => row.score > 0)
      .sort((a, b) => b.score - a.score)
      .slice(0, topK);
  }

  /* ---------------------------------------------------------------- *
   * Highlighting
   * ---------------------------------------------------------------- */

  function highlight(text, query) {
    const terms = [...new Set(tokenize(query))].filter((term) => term.length > 2);
    let html = esc(text);
    if (!terms.length) return html;
    const pattern = new RegExp(`\\b(${terms.map((term) => term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|")})\\b`, "gi");
    html = html.replace(pattern, "<mark>$1</mark>");
    return html;
  }

  /* ---------------------------------------------------------------- *
   * Render results
   * ---------------------------------------------------------------- */

  const normalize = (text) => text.toLowerCase().replace(/[^a-z0-9 ]+/g, " ").trim();

  function renderResults(query) {
    const results = search(query);
    const matchesTranscript =
      normalize(query).includes("discount") ||
      normalize(query) === normalize(transcript.question);

    const parts = [];

    if (matchesTranscript) {
      parts.push(`
        <div class="answer-card">
          <span class="answer-label">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>
            Grounded answer · recorded from POST /ask
          </span>
          <p class="answer-text">${esc(transcript.answer)}</p>
        </div>
      `);
    } else {
      parts.push(`
        <div class="note warn">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 8h.01M11 12h1v4h1"/></svg>
          <span>
            <strong>Retrieval only.</strong> The static site cannot call Llama, so no
            generated answer is produced here. Run the FastAPI service locally and
            <span class="mono">POST /ask</span> to generate one from these passages.
          </span>
        </div>
      `);
    }

    if (!results.length) {
      parts.push(
        '<p class="card-sub" style="margin-top:14px;">No keyword overlap with the indexed chunks. The semantic retriever in the API would still return its nearest neighbours.</p>'
      );
    } else {
      const maxScore = results[0].score;
      parts.push('<div class="chunk-list">');
      results.forEach((result, index) => {
        const chunk = result.chunk;
        parts.push(`
          <div class="chunk">
            <div class="chunk-head">
              <span><strong style="color:#e9f1fb">Source ${index + 1}</strong> · ${esc(chunk.source)} · chunk ${chunk.chunkId}</span>
              <span style="display:flex;align-items:center;gap:10px;">
                <span class="mono">BM25 ${result.score.toFixed(3)}</span>
                <span class="chunk-score"><span style="width:${Math.max(8, (result.score / maxScore) * 100)}%"></span></span>
              </span>
            </div>
            <p class="chunk-text">${highlight(chunk.content, query)}</p>
          </div>
        `);
      });
      parts.push("</div>");
    }

    $("results").innerHTML = parts.join("");
  }

  /* ---------------------------------------------------------------- *
   * Wiring
   * ---------------------------------------------------------------- */

  const input = $("question");
  const form = $("searchForm");

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const query = input.value.trim();
    if (query.length < 3) {
      $("results").innerHTML =
        '<p class="card-sub">Enter a question with at least 3 characters.</p>';
      return;
    }
    renderResults(query);
  });

  $("sampleQuestions").innerHTML = knowledge.sampleQuestions
    .map(
      (question) =>
        `<button class="chip" type="button" data-question="${esc(question)}">${esc(question)}</button>`
    )
    .join("");

  $("sampleQuestions").querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => {
      input.value = button.dataset.question;
      renderResults(button.dataset.question);
      $("results").scrollIntoView({ behavior: "smooth", block: "nearest" });
    });
  });

  /* Documents */
  $("documentList").innerHTML = knowledge.documents
    .map(
      (doc) => `
      <details class="doc">
        <summary>
          <span>${esc(doc.title)} <span class="mono" style="color:var(--faint);font-size:.76rem;">· ${esc(doc.name)}</span></span>
          <span style="color:var(--faint);font-size:.76rem;margin-left:auto;">${doc.chars} chars</span>
        </summary>
        <div class="doc-body">${esc(doc.text)}</div>
      </details>`
    )
    .join("");

  /* Transcript */
  $("transcriptAnswer").textContent = transcript.answer;

  $("transcriptCitations").innerHTML = (transcript.citations || [])
    .map((citation, index) => {
      const chunk = chunks.find(
        (item) => item.source === citation.source && item.chunkId === citation.chunkId
      );
      return `
        <div class="chunk">
          <div class="chunk-head">
            <span>Source ${index + 1} · ${esc(citation.source)} · chunk ${citation.chunkId}</span>
            <span class="tag good">distance ${citation.distance.toFixed(3)}</span>
          </div>
          <p class="chunk-text">${esc(chunk ? chunk.content : "")}</p>
        </div>`;
    })
    .join("");

  /* First paint */
  input.value = transcript.question;
  renderResults(transcript.question);
})();
