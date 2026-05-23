const state = {
  lastAnswer: null,
};

const elements = {
  projectName: document.querySelector("#project-name"),
  projectVersion: document.querySelector("#project-version"),
  healthPill: document.querySelector("#health-pill"),
  redisStatus: document.querySelector("#redis-status"),
  vectorStatus: document.querySelector("#vector-status"),
  ingestForm: document.querySelector("#ingest-form"),
  fileName: document.querySelector("#file-name"),
  sourceUrl: document.querySelector("#source-url"),
  localFile: document.querySelector("#local-file"),
  ingestFeedback: document.querySelector("#ingest-feedback"),
  ingestStatus: document.querySelector("#ingest-status"),
  ingestPages: document.querySelector("#ingest-pages"),
  ingestChunks: document.querySelector("#ingest-chunks"),
  chatForm: document.querySelector("#chat-form"),
  userId: document.querySelector("#user-id"),
  topK: document.querySelector("#top-k"),
  question: document.querySelector("#question"),
  chatFeedback: document.querySelector("#chat-feedback"),
  chatLog: document.querySelector("#chat-log"),
  summary: document.querySelector("#conversation-summary"),
  sourcesList: document.querySelector("#sources-list"),
  promptChips: document.querySelectorAll(".chip[data-prompt]"),
};

async function requestJson(url, options = {}) {
  const { allowHttpError = false, ...fetchOptions } = options;
  const headers = { ...(fetchOptions.headers || {}) };
  if (!(fetchOptions.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(url, {
    ...fetchOptions,
    headers,
  });

  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json")
    ? await response.json()
    : { error: `Unexpected response from ${url}` };

  if (!response.ok && !allowHttpError) {
    const rawDetails = payload.details ?? payload.detail;
    const details = Array.isArray(rawDetails)
      ? rawDetails.map((item) => item.msg || item.message || "Validation error").join(", ")
      : rawDetails?.reason || rawDetails || payload.error || "Request failed";
    throw new Error(details);
  }

  return payload;
}

function setFeedback(node, message, tone = "neutral") {
  node.className = `feedback ${tone}`;
  node.textContent = message;
}

function setHealthBadge(status) {
  elements.healthPill.className =
    status === "ok" ? "pill pill-ok" : "pill pill-bad";
  elements.healthPill.textContent = status === "ok" ? "Healthy" : "Degraded";
}

function deriveFileNameFromValue(value) {
  const trimmed = value.trim();
  if (!trimmed) {
    return "";
  }

  try {
    const pathname = trimmed.includes("://") ? new URL(trimmed).pathname : trimmed;
    const lastSegment = pathname.split("/").filter(Boolean).pop() || "";
    return lastSegment.replace(/\.[^.]+$/, "") || "";
  } catch (error) {
    return trimmed.replace(/\.[^.]+$/, "");
  }
}

function appendMessage(role, content) {
  const article = document.createElement("article");
  article.className = `message ${role}`;

  const meta = document.createElement("div");
  meta.className = "message-meta";
  meta.textContent = role === "user" ? "You" : "Assistant";

  const body = document.createElement("p");
  body.textContent = content;

  article.append(meta, body);
  elements.chatLog.append(article);
  elements.chatLog.scrollTop = elements.chatLog.scrollHeight;
}

function renderSources(sources) {
  elements.sourcesList.innerHTML = "";

  if (!sources || sources.length === 0) {
    const emptyCard = document.createElement("article");
    emptyCard.className = "source-card empty-state";
    emptyCard.innerHTML = "<p>No source snippets returned for this answer.</p>";
    elements.sourcesList.append(emptyCard);
    return;
  }

  sources.forEach((source, index) => {
    const card = document.createElement("article");
    card.className = "source-card";
    card.innerHTML = `
      <div class="meta">
        <span>Source ${index + 1}</span>
        <span>${source.source_file || "Unknown file"}</span>
        <span>${source.page_number ? `Page ${source.page_number}` : "Page unknown"}</span>
      </div>
      <h3>${source.source_file || "Retrieved context"}</h3>
      <p>${source.excerpt || "No excerpt available."}</p>
    `;
    elements.sourcesList.append(card);
  });
}

async function loadProjectMeta() {
  try {
    const about = await requestJson("/about");
    elements.projectName.textContent = about.project;
    elements.projectVersion.textContent = about.version;
  } catch (error) {
    elements.projectName.textContent = "Unavailable";
    elements.projectVersion.textContent = "--";
  }
}

async function loadHealth() {
  try {
    const health = await requestJson("/health", { allowHttpError: true });
    setHealthBadge(health.status || "degraded");

    const redisData = health.data?.redis || {};
    const vectorData = health.data?.vectorstore || {};

    elements.redisStatus.textContent =
      redisData.status === "error"
        ? redisData.message || "Unavailable"
        : redisData.status || "Unknown";

    const count = typeof vectorData.documents === "number"
      ? ` (${vectorData.documents} docs)`
      : "";
    elements.vectorStatus.textContent =
      vectorData.status === "error"
        ? vectorData.message || "Unavailable"
        : `${vectorData.status || "Unknown"}${count}`;
  } catch (error) {
    setHealthBadge("degraded");
    elements.redisStatus.textContent = "Unavailable";
    elements.vectorStatus.textContent = error.message;
  }
}

async function handleIngestSubmit(event) {
  event.preventDefault();
  setFeedback(elements.ingestFeedback, "Ingesting file...", "neutral");

  try {
    const selectedFile = elements.localFile.files?.[0] || null;
    const sourceUrl = elements.sourceUrl.value.trim();
    const resolvedFileName =
      elements.fileName.value.trim() ||
      deriveFileNameFromValue(selectedFile?.name || sourceUrl);

    if (!selectedFile && !sourceUrl) {
      throw new Error("Choose a local supported file or enter a supported file URL.");
    }

    if (!resolvedFileName) {
      throw new Error("Add a file name or choose a file with a readable name.");
    }

    let payload;
    if (selectedFile) {
      const formData = new FormData();
      formData.append("file", selectedFile);
      formData.append("file_name", resolvedFileName);

      payload = await requestJson("/api/ingest/upload", {
        method: "POST",
        body: formData,
      });
    } else {
      payload = await requestJson("/api/ingest", {
        method: "POST",
        body: JSON.stringify({
          file_name: resolvedFileName,
          source_url: sourceUrl,
        }),
      });
    }

    const result = payload.data;
    const tone = result.status === "ingested" ? "success" : "neutral";
    const message =
      result.status === "ingested"
        ? `Stored ${result.num_chunks} chunks from ${result.file_name} via ${result.input_type || "ingest"}.`
        : `Skipped ${result.file_name} because the content already exists.`;

    setFeedback(elements.ingestFeedback, message, tone);
    elements.ingestStatus.textContent = result.status;
    elements.ingestPages.textContent = String(result.num_pages);
    elements.ingestChunks.textContent = String(result.num_chunks);
    if (selectedFile) {
      elements.localFile.value = "";
    }
    await loadHealth();
  } catch (error) {
    setFeedback(elements.ingestFeedback, error.message, "error");
    elements.ingestStatus.textContent = "failed";
    elements.ingestPages.textContent = "0";
    elements.ingestChunks.textContent = "0";
  }
}

function handleLocalFileChange() {
  const selectedFile = elements.localFile.files?.[0];
  if (selectedFile && !elements.fileName.value.trim()) {
    elements.fileName.value = deriveFileNameFromValue(selectedFile.name);
  }
}

function handleSourceUrlBlur() {
  if (!elements.fileName.value.trim() && elements.sourceUrl.value.trim()) {
    elements.fileName.value = deriveFileNameFromValue(elements.sourceUrl.value);
  }
}

async function handleChatSubmit(event) {
  event.preventDefault();

  const question = elements.question.value.trim();
  if (!question) {
    setFeedback(elements.chatFeedback, "Enter a question first.", "error");
    return;
  }

  appendMessage("user", question);
  elements.question.value = "";
  setFeedback(elements.chatFeedback, "Thinking through the retrieved context...", "neutral");

  try {
    const payload = await requestJson("/api/chat", {
      method: "POST",
      body: JSON.stringify({
        user_id: elements.userId.value.trim(),
        q: question,
        top_k: Number(elements.topK.value),
      }),
    });

    const result = payload.data;
    state.lastAnswer = result;
    appendMessage("assistant", result.answer);
    elements.summary.textContent = result.summary || "No summary available yet.";
    renderSources(result.sources || []);
    setFeedback(elements.chatFeedback, "Answer ready. Source evidence updated on the right.", "success");
  } catch (error) {
    appendMessage("assistant", "I couldn’t generate an answer right now.");
    setFeedback(elements.chatFeedback, error.message, "error");
  }
}

function bindPromptChips() {
  elements.promptChips.forEach((chip) => {
    chip.addEventListener("click", () => {
      elements.question.value = chip.dataset.prompt || "";
      elements.question.focus();
    });
  });
}

function init() {
  bindPromptChips();
  elements.ingestForm.addEventListener("submit", handleIngestSubmit);
  elements.localFile.addEventListener("change", handleLocalFileChange);
  elements.sourceUrl.addEventListener("blur", handleSourceUrlBlur);
  elements.chatForm.addEventListener("submit", handleChatSubmit);
  loadProjectMeta();
  loadHealth();
}

init();
