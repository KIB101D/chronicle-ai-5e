// ui.js

export function switchView(viewId) {
  document.querySelectorAll(".view").forEach((view) => {
    view.classList.remove("active");
  });
  const targetView = document.getElementById(viewId);
  if (targetView) {
    targetView.classList.add("active");
  }
}

export async function runLoadingSequence() {
  const steps = document.querySelectorAll(".loading-step");

  steps.forEach((step) => step.classList.remove("active", "done"));

  steps[0].classList.add("active");
  await new Promise((r) => setTimeout(r, 1000));
  steps[0].classList.remove("active");
  steps[0].classList.add("done");

  steps[1].classList.add("active");
  await new Promise((r) => setTimeout(r, 1200));
  steps[1].classList.remove("active");
  steps[1].classList.add("done");

  steps[2].classList.add("active");
}

export function finishLoadingSequence() {
  const steps = document.querySelectorAll(".loading-step");
  if (steps[2]) {
    steps[2].classList.remove("active");
    steps[2].classList.add("done");
  }
}

export function renderResults(data, onBuildSheetCallback) {
  const bestCardContainer = document.getElementById("best-card");
  const otherCardsContainer = document.getElementById("other-cards");

  if (!data.matches || data.matches.length === 0) {
    renderError(
      "No Matches Found",
      "AI couldn't align your description with any archetype.",
    );
    return;
  }

  function updateMainPreview(selectedClass) {
    const scorePct = (selectedClass.score * 100).toFixed(0);
    const tagsHTML = selectedClass.tags
      .map(
        (t) =>
          `<span class="tag ${t === "homebrew" ? "homebrew" : ""}">${t}</span>`,
      )
      .join("");

    // Формуємо блок варіантів-субкласів ТІЛЬКИ для головної картки прев'ю
    let mainVariantsHTML = "";
    if (selectedClass.variants && selectedClass.variants.length > 0) {
      const links = selectedClass.variants
        .map(
          (v) =>
            `<a href="${v.link}" target="_blank" style="color: #9d4edd; text-decoration: none; font-size: 13px; margin-right: 12px;">🔗 ${v.title}</a>`,
        )
        .join("");
      mainVariantsHTML = `<div class="main-variants" style="margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.05);">${links}</div>`;
    }

    bestCardContainer.innerHTML = `
      <div class="best-card">
        <div class="card-top">
          <div>
            <h2 class="card-class-name">${selectedClass.class_name}</h2>
          </div>
          <div class="card-score-block">
            <span class="card-score-num">${scorePct}%</span>
            <span class="card-score-label">match</span>
          </div>
        </div>
        
        <p class="card-desc">${selectedClass.description}</p>
        
        <div class="card-tags">${tagsHTML}</div>
        
        <div class="card-meta">
          ${selectedClass.combat_style_label ? `<div><strong>Style:</strong> ${selectedClass.combat_style_label}</div>` : ""}
          ${selectedClass.power_source_label ? `<div><strong>Source:</strong> ${selectedClass.power_source_label}</div>` : ""}
        </div>
        
        ${mainVariantsHTML}

        <div class="match-bar-wrap">
          <div class="match-bar">
            <div class="match-bar-fill" id="best-match-fill" style="width: 0%"></div>
          </div>
        </div>

        <div class="card-footer">
          <span class="card-source"><a href="${selectedClass.link}" target="_blank">Documentation ↗</a></span>
          <button class="btn-build" id="build-sheet-btn">
            <span>Build Character Sheet</span>
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
              <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
        </div>
      </div>
    `;

    setTimeout(() => {
      const fill = document.getElementById("best-match-fill");
      if (fill) fill.style.width = `${scorePct}%`;
    }, 50);

    document.getElementById("build-sheet-btn").addEventListener("click", () => {
      onBuildSheetCallback(selectedClass);
    });
  }

  updateMainPreview(data.matches[0]);

  otherCardsContainer.innerHTML = "";

  otherCardsContainer.style.scrollSnapType = "none";

  data.matches.forEach((match, index) => {
    const ocScorePct = (match.score * 100).toFixed(0);

    const card = document.createElement("div");
    card.className = `other-card ${index === 0 ? "selected" : ""}`;

    card.innerHTML = `
      <div class="oc-header" style="display: flex; justify-content: space-between; align-items: center; gap: 12px; width: 100%;">
        <h3 class="oc-name" style="margin: 0; font-size: 14px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex-grow: 1; min-width: 0;" title="${match.class_name}">${match.class_name}</h3>
        <div class="oc-score" style="font-weight: 600; color: #C9A84C; flex-shrink: 0; font-size: 15px;">${ocScorePct}%</div>
      </div>
      <p class="oc-desc" style="font-size: 12px; opacity: 0.6; line-height: 1.4; margin: 8px 0 0 0; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; text-overflow: ellipsis;">
        ${match.description}
      </p>
    `;

    let startXCoord = 0;
    let startYCoord = 0;

    card.addEventListener("mousedown", (e) => {
      startXCoord = e.pageX;
      startYCoord = e.pageY;
    });

    card.addEventListener("mouseup", (e) => {
      const dragDistanceX = Math.abs(e.pageX - startXCoord);
      const dragDistanceY = Math.abs(e.pageY - startYCoord);
      if (dragDistanceX > 6 || dragDistanceY > 6) return;

      document
        .querySelectorAll(".other-card")
        .forEach((c) => c.classList.remove("selected"));
      card.classList.add("selected");

      updateMainPreview(match);

      document
        .getElementById("best-card")
        .scrollIntoView({ behavior: "smooth", block: "nearest" });
    });

    otherCardsContainer.appendChild(card);
  });

  // ── ПЛАВНИЙ КІНЕТИЧНИЙ СКРОЛ З ІНЕРЦІЄЮ (SMOOTH KINETIC DRAG-TO-SCROLL) ──
  let isDown = false;
  let startX;
  let scrollLeft;
  let velocity = 0;
  let lastX = 0;
  let animationId = null;

  otherCardsContainer.addEventListener("mousedown", (e) => {
    if (e.button !== 0) return; // Тільки ліва кнопка миші
    isDown = true;

    cancelAnimationFrame(animationId);

    startX = e.pageX - otherCardsContainer.offsetLeft;
    scrollLeft = otherCardsContainer.scrollLeft;
    lastX = e.pageX;
    velocity = 0;
  });

  otherCardsContainer.addEventListener("mouseleave", () => {
    if (!isDown) return;
    isDown = false;
    startInertia();
  });

  otherCardsContainer.addEventListener("mouseup", () => {
    if (!isDown) return;
    isDown = false;
    startInertia();
  });

  otherCardsContainer.addEventListener("mousemove", (e) => {
    if (!isDown) return;
    e.preventDefault();

    const x = e.pageX - otherCardsContainer.offsetLeft;
    const walk = (x - startX) * 1.2;
    otherCardsContainer.scrollLeft = scrollLeft - walk;

    velocity = e.pageX - lastX;
    lastX = e.pageX;
  });

  function startInertia() {
    const step = () => {
      if (Math.abs(velocity) < 0.2) return;

      otherCardsContainer.scrollLeft -= velocity * 1.2;
      velocity *= 0.92;

      animationId = requestAnimationFrame(step);
    };
    animationId = requestAnimationFrame(step);
  }
}

export function renderError(title, message) {
  const bestCardContainer = document.getElementById("best-card");
  bestCardContainer.innerHTML = `
    <div class="error-card">
      <div class="error-icon">⚠️</div>
      <h3 class="error-title">${title}</h3>
      <p class="error-body">${message}</p>
    </div>
  `;
}

/**
 * Заповнює фінальний пергамент листа персонажа даними
 */
export function populateCharacterSheet(user, matchedClass) {
  const sheetContent = document.getElementById("sheet-content");
  const scorePct = (matchedClass.score * 100).toFixed(0);

  sheetContent.innerHTML = `
    <h1 class="sheet-char-name">${user.name || "Unnamed Hero"}</h1>
    <div class="sheet-class-line">${user.race || "Mysterious Race"} · Level 1 · ${matchedClass.class_name}</div>
    
    <hr class="sheet-divider" />
    
    <div class="sheet-grid">
      <div>
        <span class="sf-label">Race</span>
        <span class="sf-value">${user.race || "Not specified"}</span>
      </div>
      <div>
        <span class="sf-label">Matched Class</span>
        <span class="sf-value">${matchedClass.class_name}</span>
      </div>
      <div>
        <span class="sf-label">Background</span>
        <span class="sf-value ${!user.background ? "empty" : ""}">${user.background || "Unknown Background"}</span>
      </div>
    </div>

    <hr class="sheet-divider" />

    <div class="sheet-section-label">AI Analysis Match Profile</div>
    <div class="sheet-match-row" style="margin-bottom: 28px;">
      <div class="sheet-match-num">${scorePct}%</div>
      <div style="flex-grow: 1;">
        <div class="match-bar">
          <div class="match-bar-fill" style="width: ${scorePct}%"></div>
        </div>
      </div>
    </div>

    <div style="margin-bottom: 28px;">
      <div class="sheet-section-label">Class Description</div>
      <p class="sheet-class-desc">${matchedClass.description}</p>
      <div class="sheet-tags-row" style="margin-top: 10px;">
        ${matchedClass.tags.map((t) => `<span class="tag">${t}</span>`).join("")}
      </div>
    </div>

    <div>
      <div class="sheet-section-label">Character Backstory & Profile</div>
      <p class="sheet-story">${user.story}</p>
    </div>
    
    <div class="sheet-source">
      Generated via ClassFinder Semantic AI Engine · <a href="${matchedClass.link}" target="_blank">Documentation Source</a>
    </div>
  `;
}
