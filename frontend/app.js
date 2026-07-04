// app.js
import { analyzeCharacterStory } from "./api.js";
import {
  switchView,
  runLoadingSequence,
  finishLoadingSequence,
  renderResults,
  renderError,
  populateCharacterSheet,
} from "./ui.js";

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("char-form");
  const backFromResults = document.getElementById("back-from-results");
  const backFromSheet = document.getElementById("back-from-sheet");

  // ── ЛОГІКА КОНТРОЛЬОВАНОГО ІНПУТУ ТА ВАРНІНГУ ──
  const storyTextarea = document.getElementById("char-story");
  const charCounter = document.getElementById("char-counter");
  const llmWarning = document.getElementById("llm-warning");

  if (storyTextarea && charCounter && llmWarning) {
    storyTextarea.addEventListener("input", () => {
      const currentLength = storyTextarea.value.length;
      charCounter.textContent = `${currentLength} / 350`;

      if (currentLength >= 350) {
        llmWarning.style.display = "block";
        charCounter.style.color = "#C9A84C"; // Твоє фірмове золото
      } else {
        llmWarning.style.display = "none";
        charCounter.style.color = ""; // Дефолтний колір з темпоральних стилів
      }
    });
  }

  // Тимчасове збереження введених даних користувача для листа персонажа
  let localCharacterState = {};

  // Сабміт форми опису
  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const name = document.getElementById("char-name").value.trim();
    const race = document.getElementById("char-race").value.trim();
    const background = document.getElementById("char-bg").value.trim();
    const story = document.getElementById("char-story").value.trim();

    // Валідація головного поля
    if (!story) {
      alert("Please weave a tale or description for your character first!");
      return;
    }

    // Зберігаємо стейт
    localCharacterState = { name, race, background, story };

    // 1. Вмикаємо екран завантаження та запускаємо візуальну чергу анімацій
    switchView("view-loading");
    const visualLoadingPromise = runLoadingSequence();

    try {
      // 2. Паралельно робимо реальний запит до сервера
      const data = await analyzeCharacterStory(story);

      // 3. Чекаємо, поки мінімальні красиві кроки анімації завантаження відпрацюють
      await visualLoadingPromise;
      finishLoadingSequence();

      // Маленька кінематографічна пауза перед показом результатів
      await new Promise((r) => setTimeout(r, 450));

      if (data.status === "success") {
        // Переходимо на результати
        switchView("view-results");

        // Рендеримо картки та передаємо колбек на випадок натискання "Build Character Sheet"
        renderResults(data, (chosenClass) => {
          populateCharacterSheet(localCharacterState, chosenClass);
          switchView("view-sheet");
        });
      } else {
        switchView("view-results");
        renderError(
          "Analysis failed",
          data.message || "An error occurred during semantic matching.",
        );
      }
    } catch (error) {
      console.error("Critical connection failure:", error);
      // Чекаємо завершення кроків, щоб інтерфейс не смикався
      await visualLoadingPromise;

      switchView("view-results");
      renderError(
        "Server is offline",
        `Could not connect to the Semantic AI backend. Ensure your Python backend (<code>app.py</code>) is running actively on <code>http://127.0.0.1:8000</code>.`,
      );
    }
  });

  // Кнопка "Start Over" (Повернутись з результатів на форму вводу)
  backFromResults.addEventListener("click", () => {
    switchView("view-input");
  });

  // Кнопка "Results" (Повернутись із листа персонажа назад до списку класів)
  backFromSheet.addEventListener("click", () => {
    switchView("view-results");
  });

  // ── ЛОГІКА ВИБОРУ ЧЕРТ (FEATS) ТА СИНХРОНІЗАЦІЯ З PDF ──
  const featCheckboxes = document.querySelectorAll('input[name="dnd-feat"]');
  const customFeatCheckbox = document.getElementById("custom-feat-checkbox");
  const customFeatInput = document.getElementById("custom-feat-input");
  const pdfFeatValue = document.getElementById("pdf-feat-value");

  function updatePdfFeatValue() {
    let selectedFeat = "None selected";

    if (
      customFeatCheckbox &&
      customFeatCheckbox.checked &&
      customFeatInput.value.trim() !== ""
    ) {
      selectedFeat = customFeatInput.value.trim();
    } else {
      featCheckboxes.forEach((cb) => {
        if (cb.checked && cb !== customFeatCheckbox) {
          selectedFeat = cb.nextElementSibling.textContent;
        }
      });
    }
    if (pdfFeatValue) pdfFeatValue.textContent = selectedFeat;
  }

  featCheckboxes.forEach((checkbox) => {
    checkbox.addEventListener("change", (e) => {
      // Обмеження: тільки один чекбокс (максимум 1 черта на 1 рівні)
      if (e.target.checked) {
        featCheckboxes.forEach((cb) => {
          if (cb !== e.target) cb.checked = false;
        });
      }

      // Керування кастомним інпутом
      if (customFeatCheckbox && customFeatCheckbox.checked) {
        customFeatInput.disabled = false;
        customFeatInput.focus();
      } else if (customFeatInput) {
        customFeatInput.disabled = true;
        customFeatInput.value = "";
      }

      updatePdfFeatValue();
    });
  });

  if (customFeatInput) {
    customFeatInput.addEventListener("input", updatePdfFeatValue);
  }
});
