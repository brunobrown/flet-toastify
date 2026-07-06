#!/usr/bin/env node
import { mkdir, readdir, readFile, writeFile } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const scriptPath = fileURLToPath(import.meta.url);
const projectRoot = resolve(dirname(scriptPath), "..");
const defaultNodeToolsDir =
  process.env.FLET_TOASTIFY_DOCS_NODE_TOOLS_DIR || "/tmp/flet-toastify-docs-node-tools";

const generatedTitles = {
  classes: "Generated Class Details",
  hierarchy: "Generated Module Hierarchy",
  hybrid: "Generated Hybrid Audit View",
  modules: "Generated Module Dependencies",
};

const generatedDescriptions = {
  classes:
    "Code-generated class view with public attributes, public methods and type-level relationships discovered from Python AST.",
  hierarchy:
    "Code-generated package hierarchy view. Nested groups represent filesystem/package containment, not class inheritance.",
  hybrid:
    "Code-generated audit view combining module dependencies and class details. This is intentionally denser and is better suited for review than for onboarding.",
  modules:
    "Code-generated module dependency view. Arrows show Python imports between modules, which helps reviewers understand who depends on whom.",
};

function parseArgs(argv) {
  const options = {
    nodeToolsDir: defaultNodeToolsDir,
    pageOutputDir: null,
    renderGeneratedPages: false,
    sourceDirs: [],
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    const next = argv[index + 1];

    if (arg === "--source-dir" && next) {
      options.sourceDirs.push(resolve(projectRoot, next));
      index += 1;
    } else if (arg === "--page-output-dir" && next) {
      options.pageOutputDir = resolve(projectRoot, next);
      index += 1;
    } else if (arg === "--render-generated-pages") {
      options.renderGeneratedPages = true;
    } else if (arg === "--node-tools-dir" && next) {
      options.nodeToolsDir = resolve(next);
      index += 1;
    } else {
      throw new Error(`Unknown or incomplete argument: ${arg}`);
    }
  }

  if (options.sourceDirs.length === 0) {
    throw new Error("At least one --source-dir is required.");
  }

  if (options.renderGeneratedPages && !options.pageOutputDir) {
    throw new Error("--page-output-dir is required when --render-generated-pages is used.");
  }

  return options;
}

async function listMermaidSources(sourceDir) {
  const entries = await readdir(sourceDir, { withFileTypes: true });
  return entries
    .filter((entry) => entry.isFile() && entry.name.endsWith(".mmd"))
    .map((entry) => resolve(sourceDir, entry.name))
    .sort();
}

function diagramName(sourcePath) {
  return sourcePath.split("/").at(-1).replace(/\.mmd$/, "");
}

function ensureFinalNewline(content) {
  if (content.length === 0) {
    return content;
  }

  return `${content.replace(/\n+$/u, "")}\n`;
}

async function writeGeneratedText(path, content) {
  await writeFile(path, ensureFinalNewline(content));
}

function renderGeneratedPage(name, sourceDir) {
  const title = generatedTitles[name] || `Generated ${name}`;
  const description = generatedDescriptions[name] || "Code-generated architecture diagram.";
  const sourceRelative = sourceDir.replace(`${projectRoot}/docs/`, "../../");
  const sourceDocsPath = sourceDir.replace(`${projectRoot}/`, "");

  return `---
icon: lucide/workflow
---

# ${title}

!!! info "Generated diagram"
    This page is generated from \`${sourceDocsPath}/${name}.mmd\` by \`scripts/render_mermaid_svg.mjs\`.
    Do not edit the SVG or this page manually. Run \`uv run task docs-diagrams\` and review the diff.

${description}

Source of truth: [\`${name}.mmd\`](${sourceRelative}/${name}.mmd)
Generated artifact: [\`${name}.svg\`](${sourceRelative}/${name}.svg)

<img class="beautiful-mermaid-static" src="${sourceRelative}/${name}.svg" alt="${title}" />

`;
}

function renderGeneratedIndex(names) {
  const items = names
    .map((name) => `- [${generatedTitles[name] || `Generated ${name}`}](./${name}.md)`)
    .join("\n");

  return `---
icon: lucide/workflow
---

# Generated Architecture Diagrams

!!! info "Generated documentation"
    These pages are generated from \`docs/assets/diagrams/generated/*.mmd\` source files.
    The SVG files are generated artifacts rendered with \`beautiful-mermaid\`.

The Mermaid source files are the source of truth for review. The SVG files are the rendered artifacts displayed in the documentation for better readability.

${items}
`;
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  const packageEntry = resolve(options.nodeToolsDir, "node_modules/beautiful-mermaid/dist/index.js");
  const { renderMermaidSVG, THEMES } = await import(pathToFileURL(packageEntry).href);
  const generatedPageNames = [];

  if (options.pageOutputDir) {
    await mkdir(options.pageOutputDir, { recursive: true });
  }

  for (const sourceDir of options.sourceDirs) {
    await mkdir(sourceDir, { recursive: true });
    const sources = await listMermaidSources(sourceDir);

    for (const sourcePath of sources) {
      const name = diagramName(sourcePath);
      const mermaid = await readFile(sourcePath, "utf8");
      const svg = renderMermaidSVG(mermaid, {
        ...THEMES["github-light"],
        transparent: true,
        font: "Inter, system-ui, sans-serif",
        padding: 48,
        nodeSpacing: 32,
        layerSpacing: 64,
        thoroughness: 5,
      });

      await writeGeneratedText(sourcePath.replace(/\.mmd$/, ".svg"), svg);

      if (options.renderGeneratedPages && sourceDir.endsWith("/generated")) {
        await writeGeneratedText(join(options.pageOutputDir, `${name}.md`), renderGeneratedPage(name, sourceDir));
        generatedPageNames.push(name);
      }
    }
  }

  if (options.renderGeneratedPages) {
    await writeGeneratedText(join(options.pageOutputDir, "index.md"), renderGeneratedIndex(generatedPageNames));
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
