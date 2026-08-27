const navButtons = document.querySelectorAll(".nav-button");
const panels = document.querySelectorAll("[data-panel-content]");
const panelTitle = document.querySelector("#panel-title");
const appShell = document.querySelector("#app-shell");
const profileToggle = document.querySelector(".profile-toggle");
const profileClose = document.querySelector(".profile-close");
const profileBackdrop = document.querySelector(".profile-backdrop");
const cvPanel = document.querySelector("#cv-panel");
const panelFrame = document.querySelector(".panel-frame");
const filterContainer = document.querySelector("#tournament-filter");
const writeupGrid = document.querySelector("#writeup-grid");
const writeupCount = document.querySelector("#writeup-count");
const writeupSearch = document.querySelector("#writeup-search");
const projectList = document.querySelector("#project-list");
const labList = document.querySelector("#lab-list");
const labCount = document.querySelector("#lab-count");
const blogList = document.querySelector("#blog-list");
const achievementRows = document.querySelector("#achievement-rows");
const achievementTabs = document.querySelectorAll("[data-achievement-year]");
const achievementUpdated = document.querySelector("#achievement-updated");
const rankWorld = document.querySelector("#rank-world");
const rankVietnam = document.querySelector("#rank-vietnam");

const titles = {
  ctf: "Writeups",
  projects: "Projects",
  labs: "Labs",
  blogs: "Blogs",
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

const panelOrder = [...navButtons].map((button) => button.dataset.panel);
let panelTransitionActive = false;

const finishAnimation = async (animation) => {
  try {
    await animation.finished;
  } catch {
    // A canceled animation should not block navigation state updates.
  }
};

const switchPanel = async (button) => {
  const panelName = button.dataset.panel;
  const currentPanel = document.querySelector("[data-panel-content].active");
  const nextPanel = document.querySelector(`[data-panel-content="${panelName}"]`);

  if (!nextPanel || nextPanel === currentPanel || panelTransitionActive) {
    return;
  }

  panelTransitionActive = true;
  if (panelFrame) {
    panelFrame.dataset.activePanel = panelName;
  }
  const currentName = currentPanel?.dataset.panelContent;
  const direction = panelOrder.indexOf(panelName) > panelOrder.indexOf(currentName) ? 1 : -1;
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  navButtons.forEach((item) => item.classList.toggle("active", item === button));

  if (panelTitle) {
    panelTitle.textContent = titles[panelName] || "Learning profile";
  }

  if (currentPanel && !reduceMotion) {
    await finishAnimation(
      currentPanel.animate(
        [
          { opacity: 1, transform: "translateX(0)" },
          { opacity: 0, transform: `translateX(${-direction * 5}rem)` },
        ],
        { duration: 180, easing: "cubic-bezier(0.4, 0, 1, 1)" },
      ),
    );
  }

  currentPanel?.classList.remove("active");
  if (currentPanel) {
    currentPanel.hidden = true;
  }

  nextPanel.hidden = false;
  nextPanel.classList.add("active");
  nextPanel.scrollTop = 0;

  if (!reduceMotion) {
    await finishAnimation(
      nextPanel.animate(
        [
          { opacity: 0, transform: `translateX(${direction * 6}rem)` },
          { opacity: 1, transform: "translateX(0)" },
        ],
        { duration: 360, easing: "cubic-bezier(0.16, 1, 0.3, 1)" },
      ),
    );
  }

  panelTransitionActive = false;
};

navButtons.forEach((button) => {
  button.addEventListener("click", () => switchPanel(button));
});

const requestedPanel = window.location.hash.slice(1);
const requestedButton = document.querySelector(`[data-panel="${requestedPanel}"]`);
if (requestedButton && !requestedButton.classList.contains("active")) {
  requestedButton.click();
}

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

const articleHref = (item, kind) => {
  const metaByKind = {
    writeup: `${item.event} / ${item.category}`,
    project: `${item.type} / Project`,
    lab: `${item.platform} / ${item.category} / Lab`,
    blog: `${item.category} / Blog`,
  };
  const query = new URLSearchParams();

  [
    ["src", item.src],
    ["title", item.title],
    ["kind", kind],
    ["meta", metaByKind[kind]],
    ["date", item.date],
  ].forEach(([key, value]) => {
    if (value) {
      query.set(key, value);
    }
  });

  return `article.html?${query.toString()}`;
};

const normalizeSearchText = (value) =>
  value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();

const renderWriteupCards = (items, filter = "all", query = "") => {
  if (!writeupGrid) {
    return;
  }

  const normalizedQuery = normalizeSearchText(query.trim());
  const visibleItems = items.filter((item) => {
    const matchesFilter = filter === "all" || item.eventKey === filter;
    const searchableText = normalizeSearchText(`${item.title} ${item.event}`);
    return matchesFilter && (!normalizedQuery || searchableText.includes(normalizedQuery));
  });

  if (writeupCount) {
    writeupCount.textContent = String(visibleItems.length).padStart(2, "0");
  }

  if (!visibleItems.length) {
    writeupGrid.innerHTML = `
      <div class="empty-search">
        <strong>No matching writeups</strong>
        <p>Try another title, event name, or filter.</p>
      </div>
    `;
    return;
  }

  writeupGrid.innerHTML = visibleItems
    .map(
      (item) => `
        <a class="writeup-card" href="${articleHref(item, "writeup")}" data-event="${item.eventKey}">
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

  let activeFilter = "all";

  const refreshWriteups = () => {
    renderWriteupCards(items, activeFilter, writeupSearch?.value || "");
  };

  filterContainer.querySelectorAll("[data-event-filter]").forEach((button) => {
    button.addEventListener("click", () => {
      activeFilter = button.dataset.eventFilter;

      filterContainer
        .querySelectorAll("[data-event-filter]")
        .forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
      refreshWriteups();
    });
  });

  writeupSearch?.addEventListener("input", refreshWriteups);
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
    .map((item) => {
      const href = item.src ? articleHref(item, "project") : item.url;
      const externalAttributes =
        item.url && !item.src ? ' target="_blank" rel="noreferrer"' : "";

      return `
        <article class="project-item">
          <div>
            <p class="card-kicker">${item.type}</p>
            <h4>
              ${
                href
                  ? `<a href="${href}"${externalAttributes}>${item.title}</a>`
                  : item.title
              }
            </h4>
            <p>${item.description}</p>
          </div>
          <div class="project-aside">
            <div class="tag-list">
              ${(item.tags || []).map((tag) => `<span>${tag}</span>`).join("")}
            </div>
            ${
              href
                ? `<a class="project-read" href="${href}"${externalAttributes}>${
                    item.src ? "Read notes" : "View project"
                  }</a>`
                : ""
            }
          </div>
        </article>
      `;
    })
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

const normalizeClassName = (value) =>
  String(value || "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");

const renderCertificateLinks = (certificate) => {
  if (!certificate) {
    return "-";
  }

  const href = encodeURI(certificate);

  return `
    <div class="certificate-actions">
      <a href="${href}" target="_blank" rel="noreferrer">View</a>
    </div>
  `;
};

const renderLabs = (items) => {
  if (!labList) {
    return;
  }

  if (labCount) {
    labCount.textContent = String(items.length).padStart(2, "0");
  }

  if (!items.length) {
    labList.innerHTML = `
      <div class="lab-empty">
        <strong>No labs published yet.</strong>
      </div>
    `;
    return;
  }

  labList.innerHTML = items
    .map((item) => {
      const href = item.src ? articleHref(item, "lab") : item.url;
      const externalAttributes =
        item.url && !item.src ? ' target="_blank" rel="noreferrer"' : "";
      const content = `
        <div class="lab-meta">
          <span>${item.platform}</span>
          <span class="lab-difficulty ${normalizeClassName(item.difficulty)}">
            ${item.difficulty}
          </span>
        </div>
        <div class="lab-copy">
          <p class="card-kicker">${item.category}</p>
          <h4>${item.title}</h4>
          <p>${item.description}</p>
        </div>
        <div class="lab-footer">
          ${
            item.status
              ? `<span class="lab-status ${normalizeClassName(item.status)}">${item.status}</span>`
              : ""
          }
          <div class="tag-list">
            ${(item.tags || []).map((tag) => `<span>${tag}</span>`).join("")}
          </div>
        </div>
      `;

      return href
        ? `<a class="lab-card" href="${href}"${externalAttributes}>${content}</a>`
        : `<article class="lab-card">${content}</article>`;
    })
    .join("");
};

const loadLabManifest = async () => {
  if (!labList) {
    return;
  }

  try {
    const response = await fetch("labs/manifest.json");

    if (!response.ok) {
      throw new Error("Cannot load labs/manifest.json");
    }

    renderLabs(await response.json());
  } catch (error) {
    labList.innerHTML = `<p class="load-error">Cannot load lab list.</p>`;
    console.error(error);
  }
};

loadLabManifest();

const renderBlogs = (items) => {
  if (!blogList) {
    return;
  }

  if (!items.length) {
    blogList.innerHTML = `<p class="load-error">No blog posts yet.</p>`;
    return;
  }

  blogList.innerHTML = items
    .map(
      (item) => `
        <a class="blog-card" href="${articleHref(item, "blog")}">
          <div class="blog-meta">
            <span>${item.category}</span>
            <time datetime="${item.date}">${formatDate(item.date)}</time>
          </div>
          <h4>${item.title}</h4>
          <p>${item.description}</p>
          <div class="tag-list">
            ${(item.tags || []).map((tag) => `<span>${tag}</span>`).join("")}
          </div>
        </a>
      `,
    )
    .join("");
};

const loadBlogManifest = async () => {
  if (!blogList) {
    return;
  }

  try {
    const response = await fetch("blogs/manifest.json");

    if (!response.ok) {
      throw new Error("Cannot load blogs/manifest.json");
    }

    renderBlogs(await response.json());
  } catch (error) {
    blogList.innerHTML = `<p class="load-error">Cannot load blog list.</p>`;
    console.error(error);
  }
};

loadBlogManifest();

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
        <td colspan="4">No top 150 results for ${year} yet.</td>
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
          <td>${renderCertificateLinks(item.certificate)}</td>
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
        <td colspan="4">Cannot load CTFtime results.</td>
      </tr>
    `;
    console.error(error);
  }
};

loadAchievements();
