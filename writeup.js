const params = new URLSearchParams(window.location.search);
const src = params.get("src");
const title = params.get("title") || "Writeup";
const eventName = params.get("event") || "CTF";
const category = params.get("category") || "Writeup";
const date = params.get("date") || "";

const titleElement = document.querySelector("#writeup-title");
const metaElement = document.querySelector("#writeup-meta");
const dateElement = document.querySelector("#writeup-date");
const contentElement = document.querySelector("#writeup-content");

const escapeHtml = (value) =>
  value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");

const basePath = (path) => {
  return path.split("/").slice(0, -1).join("/");
};

const resolveAsset = (url) => {
  if (/^(https?:|data:|#|mailto:)/i.test(url)) {
    return url;
  }

  return `${basePath(src)}/${url}`.replaceAll(" ", "%20");
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
  output = output.replace(/~~(.+?)~~/g, "<del>$1</del>");

  return output;
};

const stripFrontmatter = (markdown) =>
  markdown.replace(/^---[\s\S]*?---\s*/m, "");

const renderMarkdown = (markdown) => {
  const lines = stripFrontmatter(markdown).split(/\r?\n/);
  const html = [];
  let inCode = false;
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
    if (line.trim().startsWith("```")) {
      if (inCode) {
        html.push(`<pre><code>${escapeHtml(codeLines.join("\n"))}</code></pre>`);
        codeLines = [];
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
      html.push(`<h${level}>${renderInline(heading[2])}</h${level}>`);
      continue;
    }

    const blockquote = trimmed.match(/^>\s?(.+)$/);
    if (blockquote) {
      closeBlocks();
      html.push(`<blockquote><p>${renderInline(blockquote[1])}</p></blockquote>`);
      continue;
    }

    const unorderedItem = trimmed.match(/^[-+*]\s+(.+)$/);
    const orderedItem = trimmed.match(/^\d+[.)]\s+(.+)$/);
    if (unorderedItem || orderedItem) {
      flushParagraph();
      const nextListType = unorderedItem ? "ul" : "ol";

      if (listType && listType !== nextListType) {
        closeList();
      }

      if (!listType) {
        html.push(`<${nextListType}>`);
        listType = nextListType;
      }

      html.push(`<li>${renderInline((unorderedItem || orderedItem)[1])}</li>`);
      continue;
    }

    closeList();
    const hardBreak = /\\\s*$/.test(line);
    paragraphLines.push({
      text: hardBreak ? trimmed.replace(/\\\s*$/, "") : trimmed,
      hardBreak,
    });
  }

  closeBlocks();
  return html.join("\n");
};

const loadWriteup = async () => {
  titleElement.textContent = title;
  metaElement.textContent = `${eventName} / ${category}`;
  document.title = `${title} | Writeup`;

  if (date) {
    dateElement.dateTime = date;
    dateElement.textContent = new Date(`${date}T00:00:00`).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  }

  if (!src) {
    contentElement.innerHTML = "<p>Missing writeup source.</p>";
    return;
  }

  try {
    const response = await fetch(src);

    if (!response.ok) {
      throw new Error(`Cannot load ${src}`);
    }

    const markdown = await response.text();
    contentElement.innerHTML = renderMarkdown(markdown);
  } catch (error) {
    contentElement.innerHTML =
      "<p>Cannot load this writeup. Please check the Markdown file path.</p>";
    console.error(error);
  }
};

loadWriteup();
