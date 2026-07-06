(function () {
  const MIN_SCALE = 0.1;
  const MAX_SCALE = 3;
  const SCALE_STEP = 0.2;
  const RENDER_DELAY_MS = 250;
  const MAX_RENDER_ATTEMPTS = 40;

  function clamp(value, min, max) {
    return Math.min(Math.max(value, min), max);
  }

  function percent(scale) {
    return `${Math.round(scale * 100)}%`;
  }

  function applyTransform(state) {
    state.canvas.style.transform = `translate(${state.x}px, ${state.y}px) scale(${state.scale})`;
    state.scaleLabel.textContent = percent(state.scale);
  }

  function diagramSize(state) {
    const rect = state.element.getBoundingClientRect();
    return {
      height: rect.height / state.scale,
      width: rect.width / state.scale,
    };
  }

  function fitToViewport(state) {
    const size = diagramSize(state);
    const horizontalPadding = 48;
    const verticalPadding = 48;
    const availableWidth = Math.max(state.viewport.clientWidth - horizontalPadding, 1);
    const availableHeight = Math.max(state.viewport.clientHeight - verticalPadding, 1);
    const widthScale = availableWidth / Math.max(size.width, 1);
    const heightScale = availableHeight / Math.max(size.height, 1);

    state.scale = clamp(Math.min(widthScale, heightScale, 1), MIN_SCALE, MAX_SCALE);
    state.x = 0;
    state.y = 0;
    applyTransform(state);
  }

  function zoom(state, delta) {
    state.scale = clamp(state.scale + delta, MIN_SCALE, MAX_SCALE);
    applyTransform(state);
  }

  function reset(state) {
    fitToViewport(state);
  }

  function makeButton(label, title, onClick) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "mermaid-viewer-button";
    button.textContent = label;
    button.title = title;
    button.setAttribute("aria-label", title);
    button.addEventListener("click", onClick);
    return button;
  }

  function createToolbar(wrapper, state) {
    const toolbar = document.createElement("div");
    toolbar.className = "mermaid-viewer-toolbar";

    const zoomOut = makeButton("−", "Zoom out", () => zoom(state, -SCALE_STEP));
    const zoomIn = makeButton("+", "Zoom in", () => zoom(state, SCALE_STEP));
    const resetButton = makeButton("100%", "Reset zoom", () => reset(state));
    const fullscreen = makeButton("⛶", "Fullscreen", () => {
      if (document.fullscreenElement) {
        document.exitFullscreen();
      } else {
        wrapper.requestFullscreen();
      }
    });
    const drag = makeButton("✋", "Toggle drag", () => {
      state.panEnabled = !state.panEnabled;
      drag.classList.toggle("is-active", state.panEnabled);
      state.viewport.classList.toggle("is-pan-enabled", state.panEnabled);
    });
    drag.classList.add("is-active");

    state.scaleLabel = resetButton;
    toolbar.append(zoomOut, resetButton, zoomIn, fullscreen, drag);
    return toolbar;
  }

  function bindDrag(viewport, state) {
    viewport.addEventListener("pointerdown", (event) => {
      if (!state.panEnabled) {
        return;
      }
      event.preventDefault();
      state.dragging = true;
      state.startX = event.clientX - state.x;
      state.startY = event.clientY - state.y;
      viewport.setPointerCapture(event.pointerId);
      viewport.classList.add("is-dragging");
    });

    viewport.addEventListener("pointermove", (event) => {
      if (!state.dragging) {
        return;
      }
      if ((event.buttons & 1) !== 1) {
        state.dragging = false;
        viewport.classList.remove("is-dragging");
        return;
      }
      event.preventDefault();
      state.x = event.clientX - state.startX;
      state.y = event.clientY - state.startY;
      applyTransform(state);
    });

    viewport.addEventListener("pointerup", (event) => {
      state.dragging = false;
      if (viewport.hasPointerCapture(event.pointerId)) {
        viewport.releasePointerCapture(event.pointerId);
      }
      viewport.classList.remove("is-dragging");
    });

    viewport.addEventListener("pointercancel", () => {
      state.dragging = false;
      viewport.classList.remove("is-dragging");
    });

    viewport.addEventListener(
      "wheel",
      (event) => {
        if (!event.ctrlKey && !event.metaKey) {
          return;
        }
        event.preventDefault();
        zoom(state, event.deltaY > 0 ? -SCALE_STEP : SCALE_STEP);
      },
      { passive: false }
    );
  }

  function enhanceElement(element) {
    if (element.dataset.viewerEnhanced === "true") {
      return;
    }

    const wrapper = document.createElement("div");
    wrapper.className = "mermaid-viewer";

    const viewport = document.createElement("div");
    viewport.className = "mermaid-viewer-viewport";

    const canvas = document.createElement("div");
    canvas.className = "mermaid-viewer-canvas";

    element.dataset.viewerEnhanced = "true";
    element.draggable = false;
    element.addEventListener("dragstart", (event) => event.preventDefault());
    element.parentNode.insertBefore(wrapper, element);
    canvas.appendChild(element);
    viewport.appendChild(canvas);

    const state = {
      canvas,
      dragging: false,
      element,
      panEnabled: true,
      scale: 1,
      scaleLabel: null,
      startX: 0,
      startY: 0,
      viewport,
      x: 0,
      y: 0,
    };

    wrapper.append(createToolbar(wrapper, state), viewport);
    bindDrag(viewport, state);
    applyTransform(state);
    if (element.tagName === "IMG" && !element.complete) {
      element.addEventListener("load", () => fitToViewport(state), { once: true });
    } else {
      window.setTimeout(() => fitToViewport(state), 0);
    }
    window.addEventListener("resize", () => fitToViewport(state));
  }

  function enhanceDiagrams() {
    document
      .querySelectorAll(
        ".mermaid:not([data-viewer-enhanced='true']), .beautiful-mermaid-static:not([data-viewer-enhanced='true'])"
      )
      .forEach(enhanceElement);
  }

  function scheduleEnhancement(attempt = 1) {
    window.setTimeout(() => {
      enhanceDiagrams();
      const pending = document.querySelector(
        ".mermaid:not([data-viewer-enhanced='true']), .beautiful-mermaid-static:not([data-viewer-enhanced='true'])"
      );
      if (pending && attempt < MAX_RENDER_ATTEMPTS) {
        scheduleEnhancement(attempt + 1);
      }
    }, RENDER_DELAY_MS);
  }

  function observeMermaidRendering() {
    const content = document.querySelector(".md-content");
    if (!content) {
      return;
    }

    const observer = new MutationObserver(() => scheduleEnhancement());
    observer.observe(content, { childList: true, subtree: true });
  }

  function bootstrap() {
    observeMermaidRendering();
    scheduleEnhancement();
  }

  if (window.document$) {
    window.document$.subscribe(bootstrap);
    bootstrap();
  } else {
    document.addEventListener("DOMContentLoaded", bootstrap);
  }
})();
