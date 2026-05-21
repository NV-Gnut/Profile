const navButtons = document.querySelectorAll(".nav-button");
const panels = document.querySelectorAll("[data-panel-content]");
const panelTitle = document.querySelector("#panel-title");
const appShell = document.querySelector("#app-shell");
const profileToggle = document.querySelector(".profile-toggle");
const profileClose = document.querySelector(".profile-close");
const profileBackdrop = document.querySelector(".profile-backdrop");
const cvPanel = document.querySelector("#cv-panel");
const filterContainer = document.querySelector("#tournament-filter");
const writeupGrid = document.querySelector("#writeup-grid");
const projectList = document.querySelector("#project-list");
const achievementRows = document.querySelector("#achievement-rows");
const achievementTabs = document.querySelectorAll("[data-achievement-year]");
const achievementUpdated = document.querySelector("#achievement-updated");
const rankWorld = document.querySelector("#rank-world");
const rankVietnam = document.querySelector("#rank-vietnam");

const titles = {
  ctf: "Writeups",
  projects: "Project",
  team: "Our team",
};

const setProfileOpen = (isOpen) => {
  if (!appShell || !profileToggle || !cvPanel) {
    return;
  }

  appShell.classList.toggle("profile-open", isOpen);
  profileToggle.setAttribute("aria-expanded", String(isOpen));
  cvPanel.setAttribute("aria-hidden", String(!isOpen));
  cvPanel.inert = !isOpen;
};

navButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const panelName = button.dataset.panel;

    navButtons.forEach((item) => item.classList.remove("active"));
    button.classList.add("active");

    panels.forEach((panel) => {
      const isActive = panel.dataset.panelContent === panelName;
      panel.hidden = !isActive;
      panel.classList.toggle("active", isActive);
    });

    if (panelTitle) {
      const title = titles[panelName] || "Learning profile";
      panelTitle.textContent = title;
    }
  });
});

profileToggle?.addEventListener("click", () => {
  const isOpen = appShell?.classList.contains("profile-open") ?? false;
  setProfileOpen(!isOpen);
});

profileClose?.addEventListener("click", () => setProfileOpen(false));
profileBackdrop?.addEventListener("click", () => setProfileOpen(false));

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    setProfileOpen(false);
  }
});

const formatDate = (date) =>
  new Date(`${date}T00:00:00`).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });

const categoryClass = (category) => {
  const normalized = category.toLowerCase();

  if (normalized.includes("rev")) {
    return "reversing";
  }

  if (normalized.includes("pwn")) {
    return "pwn";
  }

  return "web";
};

const writeupHref = (item) => {
  const query = new URLSearchParams({
    src: item.src,
    title: item.title,
    event: item.event,
    category: item.category,
    date: item.date,
  });

  return `writeup.html?${query.toString()}`;
};

const renderWriteupCards = (items, filter = "all") => {
  if (!writeupGrid) {
    return;
  }

  const visibleItems =
    filter === "all" ? items : items.filter((item) => item.eventKey === filter);

  writeupGrid.innerHTML = visibleItems
    .map(
      (item) => `
        <a class="writeup-card" href="${writeupHref(item)}" data-event="${item.eventKey}">
          <div class="writeup-meta">
            <span class="category ${categoryClass(item.category)}">${item.category}</span>
            <span>${item.event}</span>
          </div>
          <h4>${item.title}</h4>
          <time datetime="${item.date}">${formatDate(item.date)}</time>
        </a>
      `,
    )
    .join("");
};

const renderWriteupFilters = (items) => {
  if (!filterContainer) {
    return;
  }

  const events = [...new Map(items.map((item) => [item.eventKey, item.event])).entries()];

  filterContainer.innerHTML = [
    `<button class="filter-chip active" data-event-filter="all" type="button">All</button>`,
    ...events.map(
      ([eventKey, event]) =>
        `<button class="filter-chip" data-event-filter="${eventKey}" type="button">${event}</button>`,
    ),
  ].join("");

  filterContainer.querySelectorAll("[data-event-filter]").forEach((button) => {
    button.addEventListener("click", () => {
      const filter = button.dataset.eventFilter;

      filterContainer
        .querySelectorAll("[data-event-filter]")
        .forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
      renderWriteupCards(items, filter);
    });
  });
};

const loadWriteupManifest = async () => {
  if (!filterContainer || !writeupGrid) {
    return;
  }

  try {
    const response = await fetch("writeups/manifest.json");

    if (!response.ok) {
      throw new Error("Cannot load writeups/manifest.json");
    }

    const items = await response.json();
    renderWriteupFilters(items);
    renderWriteupCards(items);
  } catch (error) {
    writeupGrid.innerHTML = `<p class="load-error">Cannot load writeup list.</p>`;
    console.error(error);
  }
};

loadWriteupManifest();

const renderProjects = (items) => {
  if (!projectList) {
    return;
  }

  if (!items.length) {
    projectList.innerHTML = `<p class="load-error">No projects yet.</p>`;
    return;
  }

  projectList.innerHTML = items
    .map(
      (item) => `
        <article class="project-item">
          <div>
            <p class="card-kicker">${item.type}</p>
            <h4>
              ${
                item.url
                  ? `<a href="${item.url}" target="_blank" rel="noreferrer">${item.title}</a>`
                  : item.title
              }
            </h4>
            <p>${item.description}</p>
          </div>
          <div class="tag-list">
            ${(item.tags || []).map((tag) => `<span>${tag}</span>`).join("")}
          </div>
        </article>
      `,
    )
    .join("");
};

const loadProjectManifest = async () => {
  if (!projectList) {
    return;
  }

  try {
    const response = await fetch("projects/manifest.json");

    if (!response.ok) {
      throw new Error("Cannot load projects/manifest.json");
    }

    const items = await response.json();
    renderProjects(items);
  } catch (error) {
    projectList.innerHTML = `<p class="load-error">Cannot load project list.</p>`;
    console.error(error);
  }
};

loadProjectManifest();

const renderAchievements = (data, year = "2026") => {
  if (!achievementRows) {
    return;
  }

  const rows = (data.years?.[year] || [])
    .filter((item) => Number(item.place) <= 150)
    .sort((a, b) => Number(a.place) - Number(b.place));

  if (!rows.length) {
    achievementRows.innerHTML = `
      <tr>
        <td colspan="3">No top 150 results for ${year} yet.</td>
      </tr>
    `;
    return;
  }

  achievementRows.innerHTML = rows
    .map(
      (item) => `
        <tr>
          <td>#${item.place}</td>
          <td>
            ${
              item.url
                ? `<a href="${item.url}" target="_blank" rel="noreferrer">${item.event}</a>`
                : item.event
            }
          </td>
          <td>${item.ratingPoints ?? "-"}</td>
        </tr>
      `,
    )
    .join("");
};

const loadAchievements = async () => {
  if (!achievementRows) {
    return;
  }

  try {
    const response = await fetch("data/ctftime-results.json");

    if (!response.ok) {
      throw new Error("Cannot load data/ctftime-results.json");
    }

    const data = await response.json();
    let currentYear = "2026";

    if (rankWorld) {
      rankWorld.textContent = data.rankings?.world ? `#${data.rankings.world}` : "--";
    }

    if (rankVietnam) {
      rankVietnam.textContent = data.rankings?.vietnam ? `#${data.rankings.vietnam}` : "--";
    }

    renderAchievements(data, currentYear);

    if (achievementUpdated) {
      achievementUpdated.textContent = data.updatedAt
        ? `Updated ${new Date(data.updatedAt).toLocaleString("en-US")}`
        : "Waiting for first automated update.";
    }

    achievementTabs.forEach((button) => {
      button.addEventListener("click", () => {
        currentYear = button.dataset.achievementYear;
        achievementTabs.forEach((item) => item.classList.remove("active"));
        button.classList.add("active");
        renderAchievements(data, currentYear);
      });
    });
  } catch (error) {
    achievementRows.innerHTML = `
      <tr>
        <td colspan="3">Cannot load CTFtime results.</td>
      </tr>
    `;
    console.error(error);
  }
};

loadAchievements();
