const params = new URLSearchParams(window.location.search);
const src = params.get("src");
const title = params.get("title") || "Article";
const kind = params.get("kind") || "writeup";
const meta = params.get("meta") || "Security article";
const date = params.get("date") || "";

const titleElement = document.querySelector("#article-title");
const metaElement = document.querySelector("#article-meta");
const dateElement = document.querySelector("#article-date");
const contentElement = document.querySelector("#article-content");
const tocElement = document.querySelector("#article-toc");
const tocPanel = document.querySelector("#article-toc-panel");
const backLink = document.querySelector("#article-back");

const kindConfig = {
  writeup: { label: "Writeup", panel: "ctf", back: "Back to writeups" },
  project: { label: "Project", panel: "projects", back: "Back to projects" },
  blog: { label: "Blog", panel: "blogs", back: "Back to blogs" },
};

const currentKind = kindConfig[kind] || kindConfig.writeup;

const escapeHtml = (value) =>
  value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");

const basePath = (path) => path.split("/").slice(0, -1).join("/");

const resolveAsset = (url) => {
  if (/^(https?:|data:|#|mailto:)/i.test(url)) {
    return url;
  }

  return `${basePath(src || "")}/${url}`.replaceAll(" ", "%20");
};

const renderInline = (text) => {
  let output = escapeHtml(text);

  output = output.replace(
    /!\[([^\]]*)\]\(([^)]+)\)/g,
    (_, alt, url) =>
      `<img class="markdown-image" src="${escapeHtml(resolveAsset(url.trim()))}" alt="${escapeHtml(alt)}" />`,
  );
  output = output.replace(
    /\[([^\]]+)\]\(([^)]+)\)/g,
    (_, label, url) =>
      `<a href="${escapeHtml(resolveAsset(url.trim()))}">${label}</a>`,
  );
  output = output.replace(/`([^`]+)`/g, "<code>$1</code>");
  output = output.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  output = output.replace(/\*([^*]+)\*/g, "<em>$1</em>");
  output = output.replace(/~~(.+?)~~/g, "<del>$1</del>");

  return output;
};

const stripFrontmatter = (markdown) =>
  markdown.replace(/^---[\s\S]*?---\s*/m, "");

const languageNames = {
  bash: "Bash",
  c: "C",
  cpp: "C++",
  css: "CSS",
  html: "HTML",
  javascript: "JavaScript",
  js: "JavaScript",
  json: "JSON",
  php: "PHP",
  python: "Python",
  py: "Python",
  shell: "Shell",
  sql: "SQL",
  text: "Text",
  typescript: "TypeScript",
  ts: "TypeScript",
};

const renderCodeBlock = (codeLines, language = "") => {
  const normalizedLanguage = language.toLowerCase();
  const languageLabel =
    languageNames[normalizedLanguage] ||
    (language ? language.toUpperCase() : "Code");
  const lines = codeLines.length ? codeLines : [""];
  const renderedLines = lines
    .map(
      (line, index) =>
        `<span class="code-line" data-line="${index + 1}"><span class="code-line-content">${escapeHtml(line) || " "}</span></span>`,
    )
    .join("");

  return `
    <section class="code-block" data-language="${escapeHtml(normalizedLanguage)}">
      <div class="code-toolbar">
        <button class="code-toggle" type="button" aria-expanded="true" title="Thu gọn hoặc mở rộng code">
          <span class="code-chevron" aria-hidden="true"></span>
          <span>${language ? `Code · ${escapeHtml(languageLabel)}` : "Code"}</span>
        </button>
        <button class="code-copy" type="button" title="Sao chép code" aria-label="Sao chép code">
          <span class="copy-icon" aria-hidden="true"></span>
        </button>
      </div>
      <pre><code>${renderedLines}</code></pre>
    </section>
  `;
};

const renderMarkdown = (markdown) => {
  const lines = stripFrontmatter(markdown).split(/\r?\n/);
  const html = [];
  let inCode = false;
  let codeLanguage = "";
  let codeLines = [];
  let listType = null;
  let paragraphLines = [];

  const closeList = () => {
    if (listType) {
      html.push(`</${listType}>`);
      listType = null;
    }
  };

  const flushParagraph = () => {
    if (!paragraphLines.length) {
      return;
    }

    const content = paragraphLines
      .map(({ text, hardBreak }, index) => {
        const separator = hardBreak ? "<br>" : index < paragraphLines.length - 1 ? " " : "";
        return `${renderInline(text)}${separator}`;
      })
      .join("");

    html.push(`<p>${content}</p>`);
    paragraphLines = [];
  };

  const closeBlocks = () => {
    flushParagraph();
    closeList();
  };

  for (const line of lines) {
    const fence = line.trim().match(/^```([\w#+.-]*)/);
    if (fence) {
      if (inCode) {
        html.push(renderCodeBlock(codeLines, codeLanguage));
        codeLines = [];
        codeLanguage = "";
      } else {
        closeBlocks();
        codeLanguage = fence[1] || "";
      }
      inCode = !inCode;
      continue;
    }

    if (inCode) {
      codeLines.push(line);
      continue;
    }

    const trimmed = line.trim();

    if (!trimmed) {
      closeBlocks();
      continue;
    }

    if (/^<img\s/i.test(trimmed)) {
      closeBlocks();
      html.push(trimmed.replace("<img ", '<img class="markdown-image" '));
      continue;
    }

    if (/^([-*_])\s*(\1\s*){2,}$/.test(trimmed)) {
      closeBlocks();
      html.push("<hr>");
      continue;
    }

    const heading = trimmed.match(/^(#{1,6})\s+(.+)$/);
    if (heading) {
      closeBlocks();
      const level = heading[1].length;
      html.push(`<h${level}>${renderInline(heading[2].replace(/\s+#+$/, ""))}</h${level}>`);
      continue;
    }

    const blockquote = trimmed.match(/^>\s?(.+)$/);
    if (blockquote) {
      closeBlocks();
      html.push(`<blockquote><p>${renderInline(blockquote[1])}</p></blockquote>`);
      continue;
    }

    const unorderedItem = trimmed.match(/^[-+*]\s+(.+)$/);
    const orderedItem = trimmed.match(/^(\d+)[.)]\s+(.+)$/);
    if (unorderedItem || orderedItem) {
      flushParagraph();
      const nextListType = unorderedItem ? "ul" : "ol";

      if (listType && listType !== nextListType) {
        closeList();
      }

      if (!listType) {
        const startAttribute = orderedItem
          ? ` start="${Number.parseInt(orderedItem[1], 10)}"`
          : "";
        html.push(`<${nextListType}${startAttribute}>`);
        listType = nextListType;
      }

      const itemContent = unorderedItem ? unorderedItem[1] : orderedItem[2];
      const valueAttribute = orderedItem
        ? ` value="${Number.parseInt(orderedItem[1], 10)}"`
        : "";
      html.push(`<li${valueAttribute}>${renderInline(itemContent)}</li>`);
      continue;
    }

    closeList();
    const hardBreak = /\\\s*$/.test(line);
    paragraphLines.push({
      text: hardBreak ? trimmed.replace(/\\\s*$/, "") : trimmed,
      hardBreak,
    });
  }

  if (inCode) {
    html.push(renderCodeBlock(codeLines, codeLanguage));
  }

  closeBlocks();
  return html.join("\n");
};

const slugify = (value) =>
  value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/đ/g, "d")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "") || "section";

const buildTableOfContents = () => {
  if (!contentElement || !tocElement || !tocPanel) {
    return;
  }

  const headings = [...contentElement.querySelectorAll("h1, h2, h3, h4")];
  if (!headings.length) {
    tocPanel.hidden = true;
    document.querySelector(".article-layout")?.classList.add("without-toc");
    return;
  }

  const slugCounts = new Map();
  const minimumLevel = Math.min(
    ...headings.map((heading) => Number(heading.tagName.slice(1))),
  );

  tocElement.innerHTML = headings
    .map((heading) => {
      const baseSlug = slugify(heading.textContent);
      const count = slugCounts.get(baseSlug) || 0;
      const slug = count ? `${baseSlug}-${count + 1}` : baseSlug;
      const level = Number(heading.tagName.slice(1));

      slugCounts.set(baseSlug, count + 1);
      heading.id = slug;
      return `
        <a class="toc-link toc-level-${Math.min(level - minimumLevel, 3)}" href="#${slug}" data-toc-id="${slug}">
          ${escapeHtml(heading.textContent)}
        </a>
      `;
    })
    .join("");

  const tocLinks = [...tocElement.querySelectorAll(".toc-link")];
  const setActiveLink = (id) => {
    tocLinks.forEach((link) => {
      const isActive = link.dataset.tocId === id;
      link.classList.toggle("active", isActive);
      if (isActive) {
        link.setAttribute("aria-current", "location");
      } else {
        link.removeAttribute("aria-current");
      }
    });
  };

  setActiveLink(headings[0].id);

  const observer = new IntersectionObserver(
    (entries) => {
      const visibleHeading = entries
        .filter((entry) => entry.isIntersecting)
        .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0];

      if (visibleHeading) {
        setActiveLink(visibleHeading.target.id);
      }
    },
    { rootMargin: "-15% 0px -72% 0px", threshold: 0 },
  );

  headings.forEach((heading) => observer.observe(heading));
};

const initializeCodeBlocks = () => {
  contentElement?.addEventListener("click", async (event) => {
    const toggle = event.target.closest(".code-toggle");
    const copyButton = event.target.closest(".code-copy");
    const codeBlock = event.target.closest(".code-block");

    if (!codeBlock) {
      return;
    }

    if (toggle) {
      const isCollapsed = codeBlock.classList.toggle("is-collapsed");
      toggle.setAttribute("aria-expanded", String(!isCollapsed));
      codeBlock.querySelector("pre").hidden = isCollapsed;
      return;
    }

    if (copyButton) {
      const code = [...codeBlock.querySelectorAll(".code-line-content")]
        .map((line) => line.textContent)
        .join("\n");

      try {
        await navigator.clipboard.writeText(code);
        copyButton.classList.add("is-copied");
        copyButton.title = "Đã sao chép";
        setTimeout(() => {
          copyButton.classList.remove("is-copied");
          copyButton.title = "Sao chép code";
        }, 1400);
      } catch (error) {
        console.error("Cannot copy code", error);
      }
    }
  });
};

const loadArticle = async () => {
  titleElement.textContent = title;
  metaElement.textContent = meta;
  backLink.textContent = currentKind.back;
  backLink.href = `index.html#${currentKind.panel}`;
  document.title = `${title} | ${currentKind.label}`;

  if (date) {
    dateElement.dateTime = date;
    dateElement.textContent = new Date(`${date}T00:00:00`).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  }

  if (!src) {
    contentElement.innerHTML = "<p>Missing article source.</p>";
    tocPanel.hidden = true;
    return;
  }

  try {
    const response = await fetch(src);

    if (!response.ok) {
      throw new Error(`Cannot load ${src}`);
    }

    const markdown = await response.text();
    contentElement.innerHTML = renderMarkdown(markdown);
    buildTableOfContents();
    initializeCodeBlocks();
  } catch (error) {
    contentElement.innerHTML =
      "<p>Cannot load this article. Please check the Markdown file path.</p>";
    tocPanel.hidden = true;
    console.error(error);
  }
};

loadArticle();
