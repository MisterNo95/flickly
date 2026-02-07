const seedDreams = [
  {
    id: "dream-moon",
    title: "The Luminous Moon",
    description: "You stand beneath a moon so bright it paints the world in silver.",
    spiritual: "The moon reflects intuition calling you to honor sacred cycles.",
    psychological: "A desire for clarity and emotional stability is surfacing.",
    cultural: "Across traditions, the moon signifies mystery, femininity, and time.",
    category: "Places",
    related: ["Ocean", "Stars"],
  },
  {
    id: "dream-serpent",
    title: "Serpent in the Garden",
    description: "A serpent moves through the garden without fear.",
    spiritual: "Transformation and kundalini energy are awakening.",
    psychological: "You may be shedding an old pattern or belief.",
    cultural: "Serpents symbolize renewal, wisdom, and primal power.",
    category: "Animals",
    related: ["Water", "Temple"],
  },
  {
    id: "dream-bridge",
    title: "Crossing the Bridge",
    description: "You walk across a bridge suspended in mist.",
    spiritual: "The bridge is a rite of passage into a higher understanding.",
    psychological: "You are transitioning between life chapters.",
    cultural: "Bridges often represent connection between worlds.",
    category: "Actions",
    related: ["Journey", "Gate"],
  },
];

const reflections = [
  "When the soul is still, the cosmos speaks in symbols.",
  "The temple of wisdom opens when breath becomes prayer.",
  "Every dream is a lantern guiding you toward the unseen.",
  "Your path is written in stars, but walked by your heart.",
  "Mystery is the veil that invites the seeker deeper.",
];

const dailyQuote = [
  "May your spirit awaken to the rhythm of the heavens.",
  "The universe mirrors the silence within you.",
  "Listen to the wind; it carries the memory of the stars.",
  "Sacred knowledge is a flame best tended in stillness.",
  "Today invites you to honor the quiet voice of intuition.",
];

const dreamCategories = ["Animals", "Objects", "Emotions", "People", "Places", "Actions"];

const storageKey = "flickly-dreams";

const getStoredDreams = () => {
  const stored = localStorage.getItem(storageKey);
  if (!stored) {
    localStorage.setItem(storageKey, JSON.stringify(seedDreams));
    return [...seedDreams];
  }
  return JSON.parse(stored);
};

const setStoredDreams = (dreams) => {
  localStorage.setItem(storageKey, JSON.stringify(dreams));
};

const getDailyMessage = (collection) => {
  const index = new Date().getDate() % collection.length;
  return collection[index];
};

const renderHomepage = () => {
  const reflectionEl = document.querySelector("[data-reflection]");
  if (reflectionEl) {
    reflectionEl.textContent = getDailyMessage(reflections);
  }

  const heroQuote = document.querySelector("[data-hero-quote]");
  if (heroQuote) {
    heroQuote.textContent = getDailyMessage(dailyQuote);
  }
};

const renderDreamDictionary = () => {
  const searchInput = document.querySelector("#dream-search");
  const resultsEl = document.querySelector("#dream-results");
  const categoryWrap = document.querySelector("#dream-categories");

  if (!searchInput || !resultsEl || !categoryWrap) {
    return;
  }

  const dreams = getStoredDreams();
  let activeCategory = "All";

  const renderCategories = () => {
    categoryWrap.innerHTML = "";
    const allCategories = ["All", ...dreamCategories];

    allCategories.forEach((category) => {
      const button = document.createElement("button");
      button.className = "badge";
      button.type = "button";
      button.textContent = category;
      if (category === activeCategory) {
        button.style.background = "rgba(215, 183, 111, 0.2)";
      }
      button.addEventListener("click", () => {
        activeCategory = category;
        renderCategories();
        renderResults();
      });
      categoryWrap.appendChild(button);
    });
  };

  const renderResults = () => {
    const query = searchInput.value.toLowerCase();
    resultsEl.innerHTML = "";

    const filtered = dreams.filter((dream) => {
      const matchesQuery = dream.title.toLowerCase().includes(query);
      const matchesCategory = activeCategory === "All" || dream.category === activeCategory;
      return matchesQuery && matchesCategory;
    });

    if (filtered.length === 0) {
      resultsEl.innerHTML = "<p class=\"section-subtitle\">No dream entries match this search.</p>";
      return;
    }

    filtered.forEach((dream) => {
      const entry = document.createElement("article");
      entry.className = "dream-entry";
      entry.innerHTML = `
        <h3>${dream.title}</h3>
        <p>${dream.description}</p>
        <div class="badge-row">
          <span class="badge">${dream.category}</span>
        </div>
        <p><strong>Spiritual:</strong> ${dream.spiritual}</p>
        <p><strong>Psychological:</strong> ${dream.psychological}</p>
        <p><strong>Cultural:</strong> ${dream.cultural}</p>
        <p><strong>Related:</strong> ${dream.related.join(", ")}</p>
      `;
      resultsEl.appendChild(entry);
    });
  };

  searchInput.addEventListener("input", renderResults);
  renderCategories();
  renderResults();
};

const renderAdmin = () => {
  const loginForm = document.querySelector("#admin-login");
  const adminShell = document.querySelector("#admin-shell");
  const adminStatus = document.querySelector("#admin-status");

  if (!loginForm || !adminShell || !adminStatus) {
    return;
  }

  const syncShell = (isAuthenticated) => {
    loginForm.style.display = isAuthenticated ? "none" : "block";
    adminShell.style.display = isAuthenticated ? "grid" : "none";
    adminStatus.textContent = isAuthenticated
      ? "Authenticated as Keeper of Dreams"
      : "Secure access required";
  };

  const storedAuth = sessionStorage.getItem("dream-admin-auth") === "true";
  syncShell(storedAuth);

  loginForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const password = loginForm.querySelector("input").value;
    if (password === "oracle") {
      sessionStorage.setItem("dream-admin-auth", "true");
      syncShell(true);
    } else {
      adminStatus.textContent = "The temple remains closed to that key.";
    }
  });

  const dreamList = document.querySelector("#admin-dream-list");
  const dreamForm = document.querySelector("#admin-dream-form");
  const categoryForm = document.querySelector("#admin-category-form");
  const editor = document.querySelector("#dream-editor");
  const summaryField = document.querySelector("#dream-summary");

  if (!dreamList || !dreamForm || !categoryForm || !editor || !summaryField) {
    return;
  }

  const getEditorValue = () => editor.innerHTML.trim();
  const setEditorValue = (value) => {
    editor.innerHTML = value;
  };

  const renderAdminDreams = () => {
    dreamList.innerHTML = "";
    const dreams = getStoredDreams();
    dreams.forEach((dream) => {
      const item = document.createElement("div");
      item.className = "dream-entry";
      item.innerHTML = `
        <h3>${dream.title}</h3>
        <p>${dream.description}</p>
        <div class="badge-row">
          <span class="badge">${dream.category}</span>
        </div>
        <button class="button" data-edit="${dream.id}">Edit</button>
        <button class="button" data-delete="${dream.id}">Delete</button>
      `;
      dreamList.appendChild(item);
    });
  };

  dreamList.addEventListener("click", (event) => {
    const editId = event.target.getAttribute("data-edit");
    const deleteId = event.target.getAttribute("data-delete");
    const dreams = getStoredDreams();

    if (editId) {
      const dream = dreams.find((entry) => entry.id === editId);
      if (!dream) return;
      dreamForm.dataset.editing = editId;
      dreamForm.querySelector("#dream-title").value = dream.title;
      dreamForm.querySelector("#dream-description").value = dream.description;
      dreamForm.querySelector("#dream-spiritual").value = dream.spiritual;
      dreamForm.querySelector("#dream-psychological").value = dream.psychological;
      dreamForm.querySelector("#dream-cultural").value = dream.cultural;
      dreamForm.querySelector("#dream-category").value = dream.category;
      summaryField.value = dream.related.join(", ");
      setEditorValue(dream.description);
    }

    if (deleteId) {
      const updated = dreams.filter((entry) => entry.id !== deleteId);
      setStoredDreams(updated);
      renderAdminDreams();
    }
  });

  const toolbar = document.querySelectorAll("[data-command]");
  toolbar.forEach((button) => {
    button.addEventListener("click", () => {
      document.execCommand(button.dataset.command, false, null);
    });
  });

  dreamForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const dreams = getStoredDreams();
    const editing = dreamForm.dataset.editing;

    const payload = {
      id: editing || `dream-${Date.now()}`,
      title: dreamForm.querySelector("#dream-title").value.trim(),
      description: dreamForm.querySelector("#dream-description").value.trim(),
      spiritual: dreamForm.querySelector("#dream-spiritual").value.trim(),
      psychological: dreamForm.querySelector("#dream-psychological").value.trim(),
      cultural: dreamForm.querySelector("#dream-cultural").value.trim(),
      category: dreamForm.querySelector("#dream-category").value,
      related: summaryField.value.split(",").map((item) => item.trim()).filter(Boolean),
    };

    const richText = getEditorValue();
    if (richText) {
      payload.description = richText;
    }

    const updated = editing
      ? dreams.map((dream) => (dream.id === editing ? payload : dream))
      : [payload, ...dreams];

    setStoredDreams(updated);
    dreamForm.reset();
    dreamForm.dataset.editing = "";
    setEditorValue("");
    renderAdminDreams();
  });

  categoryForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const newCategory = categoryForm.querySelector("input").value.trim();
    if (!newCategory) return;
    if (!dreamCategories.includes(newCategory)) {
      dreamCategories.push(newCategory);
    }
    categoryForm.reset();
    renderAdminDreams();
  });

  renderAdminDreams();
};

const init = () => {
  renderHomepage();
  renderDreamDictionary();
  renderAdmin();
};

document.addEventListener("DOMContentLoaded", init);
