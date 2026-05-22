(() => {
  const photo = document.getElementById("photo");
  const canvas = document.getElementById("overlay");
  const ctx = canvas.getContext("2d");
  const imageTreeList = document.getElementById("image-tree-list");
  const imageTreeBreadcrumb = document.getElementById("image-tree-breadcrumb");
  const imageListEmpty = document.getElementById("image-list-empty");
  const sidebarTitle = document.querySelector(".sidebar-title");
  const workspace = document.querySelector(".workspace");
  const stage = document.getElementById("stage");
  const zoomSlider = document.getElementById("zoom-slider");
  const zoomValue = document.getElementById("zoom-value");
  const btnZoomOut = document.getElementById("btn-zoom-out");
  const btnZoomIn = document.getElementById("btn-zoom-in");
  const btnZoomFit = document.getElementById("btn-zoom-fit");
  const logPanel = document.getElementById("log-panel");
  const tagLogPanel = document.getElementById("tag-log-panel");
  const btnSubmit = document.getElementById("btn-submit");
  const btnClear = document.getElementById("btn-clear");
  const btnDelSel = document.getElementById("btn-delete-selected");
  const sourceFolderLabel = document.getElementById("source-folder-label");
  const strudelCode = document.getElementById("strudel-code");
  const btnSaveTag = document.getElementById("btn-save-tag");
  const tagInputLabel = document.getElementById("tag-input-label");
  const pdfViewer = document.getElementById("pdf-viewer");
  const catalogForm = document.getElementById("catalog-form");
  const catTitle = document.getElementById("cat-title");
  const catSubtitle = document.getElementById("cat-subtitle");
  const catDisplayTitle = document.getElementById("cat-display-title");
  const catComposer = document.getElementById("cat-composer");
  const catDisplayComposer = document.getElementById("cat-display-composer");
  const catAnalysis = document.getElementById("cat-analysis");
  const uploadWorkId = document.getElementById("upload-work-id");
  const uploadPdfFile = document.getElementById("upload-pdf-file");
  const btnUploadPdf = document.getElementById("btn-upload-pdf");

  const CROP_MODES = new Set([
    "page_staff",
    "staff_measure",
    "measure_note",
    "function_in_page",
    "function_in_staff",
    "function_in_measure",
    "function_in_note",
  ]);

  const CODE_TAG_MODES = new Set([
    "code_of_page",
    "code_of_staff",
    "code_of_measure",
    "code_of_note",
  ]);

  const FUNCTION_TAG_MODES = new Set([
    "tag_of_page_function",
    "tag_of_staff_function",
    "tag_of_measure_function",
    "tag_of_note_function",
  ]);

  const CATALOG_TAG_MODES = new Set(["meta_of_work"]);

  const TAG_MODES = new Set([...CODE_TAG_MODES, ...FUNCTION_TAG_MODES, ...CATALOG_TAG_MODES]);
  const MODES = new Set([...CROP_MODES, ...TAG_MODES]);

  const GROUP_DEFAULT_MODE = {
    crop: "page_staff",
    tag: "code_of_page",
  };

  const MODE_SOURCE_FOLDER = {
    page_staff: "works/{id}/images/pages",
    staff_measure: "works/{id}/images/staffs",
    measure_note: "works/{id}/images/measures",
    function_in_page: "works/{id}/images/pages",
    function_in_staff: "works/{id}/images/staffs",
    function_in_measure: "works/{id}/images/measures",
    function_in_note: "works/{id}/images/notes",
    code_of_page: "works/{id}/images/pages",
    code_of_staff: "works/{id}/images/staffs",
    code_of_measure: "works/{id}/images/measures",
    code_of_note: "works/{id}/images/notes",
    tag_of_page_function: "works/{id}/images/functions",
    tag_of_staff_function: "works/{id}/images/functions",
    tag_of_measure_function: "works/{id}/images/functions",
    tag_of_note_function: "works/{id}/images/functions",
    meta_of_work: "works/{id}/assets + catalog.json",
  };

  const TAG_INPUT_UI = {
    code_of_page: {
      label: "Strudel Code",
      placeholder: "Strudel 코드를 입력하세요…",
      saveLabel: "코드 저장",
      readyStatus: "Strudel Code를 입력한 뒤 저장하세요.",
      savedStatus: "코드 저장 완료",
    },
    code_of_staff: {
      label: "Strudel Code",
      placeholder: "Strudel 코드를 입력하세요…",
      saveLabel: "코드 저장",
      readyStatus: "Strudel Code를 입력한 뒤 저장하세요.",
      savedStatus: "코드 저장 완료",
    },
    code_of_measure: {
      label: "Strudel Code",
      placeholder: "Strudel 코드를 입력하세요…",
      saveLabel: "코드 저장",
      readyStatus: "Strudel Code를 입력한 뒤 저장하세요.",
      savedStatus: "코드 저장 완료",
    },
    code_of_note: {
      label: "Strudel Code",
      placeholder: "Strudel 코드를 입력하세요…",
      saveLabel: "코드 저장",
      readyStatus: "Strudel Code를 입력한 뒤 저장하세요.",
      savedStatus: "코드 저장 완료",
    },
    tag_of_page_function: {
      label: "Tag",
      placeholder: "태그를 입력하세요…",
      saveLabel: "태그 저장",
      readyStatus: "태그를 입력한 뒤 저장하세요.",
      savedStatus: "태그 저장 완료",
    },
    tag_of_staff_function: {
      label: "Tag",
      placeholder: "태그를 입력하세요…",
      saveLabel: "태그 저장",
      readyStatus: "태그를 입력한 뒤 저장하세요.",
      savedStatus: "태그 저장 완료",
    },
    tag_of_measure_function: {
      label: "Tag",
      placeholder: "태그를 입력하세요…",
      saveLabel: "태그 저장",
      readyStatus: "태그를 입력한 뒤 저장하세요.",
      savedStatus: "태그 저장 완료",
    },
    tag_of_note_function: {
      label: "Tag",
      placeholder: "태그를 입력하세요…",
      saveLabel: "태그 저장",
      readyStatus: "태그를 입력한 뒤 저장하세요.",
      savedStatus: "태그 저장 완료",
    },
  };

  /** @type {string} */
  let currentMode = "page_staff";
  /** @type {"crop" | "tag"} */
  let currentGroup = "crop";
  /** @type {string[]} */
  let allImages = [];
  /** @type {string | null} */
  let selectedImagePath = null;
  /** @type {string[]} */
  let treePath = [];
  /** @type {{ x: number, y: number, w: number, h: number }[]} */
  let boxes = [];
  /** @type {number | null} */
  let selectedIndex = null;
  let zoomPct = Number(zoomSlider?.value) || 100;
  let drawing = false;
  let startX = 0;
  let startY = 0;
  let currentX = 0;
  let currentY = 0;

  function isCatalogMode() {
    return CATALOG_TAG_MODES.has(currentMode);
  }

  function isFunctionTagMode() {
    return FUNCTION_TAG_MODES.has(currentMode);
  }

  function isTagMode() {
    return TAG_MODES.has(currentMode);
  }

  function isCropMode() {
    return CROP_MODES.has(currentMode);
  }

  function tagInputUi() {
    return TAG_INPUT_UI[currentMode] || TAG_INPUT_UI.code_of_page;
  }

  function activeLogPanel() {
    return isTagMode() ? tagLogPanel : logPanel;
  }

  const LOG_SAVE_OK = "저장에 성공했습니다.";
  const LOG_SAVE_FAIL = "저장에 실패했습니다.";
  const LOG_LOAD_FAIL = "이미지 로드에 실패했습니다.";

  function appendLog(msg, kind = "") {
    const panel = activeLogPanel();
    if (!panel) return;
    const entry = document.createElement("div");
    entry.className = "log-entry" + (kind ? ` log-entry--${kind}` : "");
    const time = document.createElement("time");
    time.textContent = new Date().toLocaleTimeString("ko-KR", { hour12: false });
    entry.appendChild(time);
    entry.appendChild(document.createTextNode(msg));
    panel.prepend(entry);
    while (panel.childElementCount > 100) {
      panel.lastElementChild?.remove();
    }
  }

  function logSuccess(msg = LOG_SAVE_OK) {
    appendLog(msg, "ok");
  }

  function logFailure(msg) {
    appendLog(msg, "err");
  }

  function storageKey(mode) {
    return `annotator:lastImage:${mode}`;
  }

  function rememberSelection(path) {
    if (!path) return;
    try {
      localStorage.setItem(storageKey(currentMode), path);
    } catch {
      /* ignore */
    }
  }

  function recalledSelection() {
    try {
      return localStorage.getItem(storageKey(currentMode));
    } catch {
      return null;
    }
  }

  function workStateStorageKey(mode) {
    return `annotator:workState:${mode}`;
  }

  /** @returns {Record<string, "active" | "done">} */
  function loadWorkStates(mode = currentMode) {
    try {
      const raw = localStorage.getItem(workStateStorageKey(mode));
      if (!raw) return {};
      const parsed = JSON.parse(raw);
      return typeof parsed === "object" && parsed !== null ? parsed : {};
    } catch {
      return {};
    }
  }

  function saveWorkStates(states, mode = currentMode) {
    try {
      localStorage.setItem(workStateStorageKey(mode), JSON.stringify(states));
    } catch {
      /* ignore */
    }
  }

  function getWorkState(path, mode = currentMode) {
    const states = loadWorkStates(mode);
    return states[path] === "done" ? "done" : "active";
  }

  function syncWorkStates(images) {
    const states = loadWorkStates();
    let changed = false;
    for (const path of images) {
      if (!(path in states)) {
        states[path] = "active";
        changed = true;
      }
    }
    for (const path of Object.keys(states)) {
      if (!images.includes(path)) {
        delete states[path];
        changed = true;
      }
    }
    if (changed) saveWorkStates(states);
  }

  function markWorkDone(path) {
    updateWorkState(path, true);
  }

  function updateWorkState(path, done) {
    if (!path) return;
    const states = loadWorkStates();
    states[path] = done ? "done" : "active";
    saveWorkStates(states);
    renderImageTree();
  }

  function syncCatalogWorkStates(completeMap) {
    const states = loadWorkStates();
    let changed = false;
    for (const work of allImages) {
      const next = completeMap?.[work] ? "done" : "active";
      if (states[work] !== next) {
        states[work] = next;
        changed = true;
      }
    }
    for (const path of Object.keys(states)) {
      if (!allImages.includes(path)) {
        delete states[path];
        changed = true;
      }
    }
    if (changed) saveWorkStates(states);
  }

  function displayName(filename) {
    return filename.replace(/\.[^.]+$/, "");
  }

  /** @returns {{ name: string, kind: "folder" | "leaf", path?: string }[]} */
  function listChildrenAtPath(prefixParts) {
    /** @type {Map<string, { kind: "folder" | "leaf", path?: string }>} */
    const map = new Map();

    for (const imgPath of allImages) {
      const parts = imgPath.split("/");
      if (prefixParts.length && !prefixParts.every((part, i) => parts[i] === part)) {
        continue;
      }
      const depth = prefixParts.length;
      if (parts.length <= depth) continue;

      const name = parts[depth];
      if (parts.length === depth + 1) {
        map.set(name, { kind: "leaf", path: imgPath });
      } else if (!map.has(name)) {
        map.set(name, { kind: "folder" });
      }
    }

    return [...map.entries()]
      .sort((a, b) => {
        const aFolder = a[1].kind === "folder" ? 0 : 1;
        const bFolder = b[1].kind === "folder" ? 0 : 1;
        if (aFolder !== bFolder) return aFolder - bFolder;
        return a[0].localeCompare(b[0], undefined, { numeric: true });
      })
      .map(([name, info]) => ({ name, ...info }));
  }

  function isPrefixDone(prefixParts) {
    const prefix = prefixParts.join("/");
    const matching = allImages.filter((path) => {
      if (!prefix) return true;
      return path === prefix || path.startsWith(`${prefix}/`);
    });
    return matching.length > 0 && matching.every((path) => getWorkState(path) === "done");
  }

  function treePathForImage(path) {
    return path.split("/").slice(0, -1);
  }

  function renderImageTreeBreadcrumb() {
    if (!imageTreeBreadcrumb) return;
    imageTreeBreadcrumb.innerHTML = "";

    if (!allImages.length || isCatalogMode()) {
      imageTreeBreadcrumb.hidden = true;
      return;
    }

    imageTreeBreadcrumb.hidden = false;

    const rootBtn = document.createElement("button");
    rootBtn.type = "button";
    rootBtn.className = "image-tree-breadcrumb__item" + (treePath.length === 0 ? " is-current" : "");
    rootBtn.textContent = "루트";
    rootBtn.dataset.crumbIdx = "0";
    imageTreeBreadcrumb.appendChild(rootBtn);

    treePath.forEach((segment, i) => {
      const sep = document.createElement("span");
      sep.className = "image-tree-breadcrumb__sep";
      sep.textContent = "›";
      sep.setAttribute("aria-hidden", "true");
      imageTreeBreadcrumb.appendChild(sep);

      const btn = document.createElement("button");
      btn.type = "button";
      const isCurrent = i === treePath.length - 1;
      btn.className = "image-tree-breadcrumb__item" + (isCurrent ? " is-current" : "");
      btn.textContent = displayName(segment);
      btn.dataset.crumbIdx = String(i + 1);
      imageTreeBreadcrumb.appendChild(btn);
    });
  }

  function renderImageTree() {
    if (!imageTreeList) return;
    imageTreeList.innerHTML = "";
    renderImageTreeBreadcrumb();

    if (!allImages.length) {
      imageListEmpty?.removeAttribute("hidden");
      if (imageListEmpty) {
        imageListEmpty.textContent = isCatalogMode()
          ? "Work가 없습니다. PDF를 업로드하세요."
          : "이미지가 없습니다.";
      }
      return;
    }
    imageListEmpty?.setAttribute("hidden", "");

    const children = listChildrenAtPath(treePath);
    for (const child of children) {
      const li = document.createElement("li");
      li.className = "image-tree-item";
      li.dataset.treeKind = child.kind;
      li.dataset.treeName = child.name;
      if (child.path) li.dataset.path = child.path;

      const done =
        child.kind === "leaf"
          ? getWorkState(child.path) === "done"
          : isPrefixDone([...treePath, child.name]);
      if (done) li.classList.add("is-done");
      if (child.kind === "leaf" && child.path === selectedImagePath) {
        li.classList.add("is-selected");
      }

      const icon = document.createElement("span");
      icon.className = "image-tree-item__icon";
      icon.textContent = child.kind === "folder" ? "▸" : "•";
      icon.setAttribute("aria-hidden", "true");

      const label = document.createElement("span");
      label.className = "image-tree-item__label";
      label.textContent = displayName(child.name);

      li.appendChild(icon);
      li.appendChild(label);
      imageTreeList.appendChild(li);
    }
  }

  function selectImage(path, { remember = true } = {}) {
    if (!path || !allImages.includes(path)) return;
    selectedImagePath = path;
    if (isCatalogMode()) {
      if (remember) rememberSelection(path);
      if (uploadWorkId) uploadWorkId.value = path;
      renderImageTree();
      if (pdfViewer) {
        pdfViewer.hidden = false;
        pdfViewer.src = `/api/work-pdf/${encodeURIComponent(path)}`;
      }
      photo.removeAttribute("src");
      loadCatalogForWork(path).catch(() => logFailure(LOG_LOAD_FAIL));
      return;
    }
    treePath = treePathForImage(path);
    if (remember) rememberSelection(path);
    renderImageTree();
    if (pdfViewer) {
      pdfViewer.hidden = true;
      pdfViewer.removeAttribute("src");
    }
    photo.src = imageApiUrl(path);
  }

  function clearCatalogForm() {
    if (catTitle) catTitle.value = "";
    if (catSubtitle) catSubtitle.value = "";
    if (catDisplayTitle) catDisplayTitle.value = "";
    if (catComposer) catComposer.value = "";
    if (catDisplayComposer) catDisplayComposer.value = "";
    if (catAnalysis) catAnalysis.value = "";
    catalogForm?.querySelectorAll('input[name="copyright_free"]').forEach((el) => {
      el.checked = false;
    });
  }

  function fillCatalogForm(data) {
    if (catTitle) catTitle.value = data.title ?? "";
    if (catSubtitle) catSubtitle.value = data.subtitle ?? "";
    if (catDisplayTitle) catDisplayTitle.value = data.display_title ?? "";
    if (catComposer) catComposer.value = data.composer ?? "";
    if (catDisplayComposer) catDisplayComposer.value = data.display_composer ?? "";
    if (catAnalysis) catAnalysis.value = data.analysis ?? "";
    catalogForm?.querySelectorAll('input[name="copyright_free"]').forEach((el) => {
      if (data.copyright_free === true) el.checked = el.value === "true";
      else if (data.copyright_free === false) el.checked = el.value === "false";
      else el.checked = false;
    });
  }

  function readCatalogForm() {
    const copyrightEl = catalogForm?.querySelector('input[name="copyright_free"]:checked');
    return {
      work: selectedImagePath,
      title: catTitle?.value ?? "",
      subtitle: catSubtitle?.value ?? "",
      display_title: catDisplayTitle?.value ?? "",
      composer: catComposer?.value ?? "",
      display_composer: catDisplayComposer?.value ?? "",
      analysis: catAnalysis?.value ?? "",
      copyright_free: copyrightEl ? copyrightEl.value === "true" : null,
    };
  }

  async function loadCatalogForWork(work) {
    if (!work || !isCatalogMode()) {
      clearCatalogForm();
      return;
    }
    const q = new URLSearchParams({ work });
    const res = await fetch(`/api/catalog?${q}`);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(data.detail || `오류 ${res.status}`);
    }
    fillCatalogForm(data);
    updateWorkState(work, !!data.complete);
  }

  function clearWorkspace() {
    photo.removeAttribute("src");
    if (pdfViewer) {
      pdfViewer.hidden = true;
      pdfViewer.removeAttribute("src");
    }
    selectedImagePath = null;
    if (strudelCode) strudelCode.value = "";
    clearCatalogForm();
    boxes = [];
    selectedIndex = null;
    redraw();
    renderImageTree();
  }

  function navigateTreeTo(index) {
    treePath = treePath.slice(0, index);
    renderImageTree();
  }

  function navigateTreeInto(name) {
    treePath = [...treePath, name];
    renderImageTree();
  }

  function applyModeUi() {
    currentGroup = isTagMode() ? "tag" : "crop";
    document.body.classList.toggle("is-tag-mode", isTagMode());
    document.body.classList.toggle("is-tag-group", currentGroup === "tag");
    document.body.classList.toggle("is-catalog-mode", isCatalogMode());

    if (sourceFolderLabel) {
      sourceFolderLabel.textContent = MODE_SOURCE_FOLDER[currentMode] || "";
    }

    if (sidebarTitle) {
      sidebarTitle.textContent = isCatalogMode() ? "Work 목록" : "이미지 목록";
    }

    if (isCatalogMode()) {
      if (btnSaveTag) btnSaveTag.textContent = "메타 저장";
    } else {
      const ui = tagInputUi();
      if (tagInputLabel) tagInputLabel.textContent = ui.label;
      if (strudelCode) strudelCode.placeholder = ui.placeholder;
      if (btnSaveTag) btnSaveTag.textContent = ui.saveLabel;
    }

    document.querySelectorAll(".mode-group-nav__btn").forEach((btn) => {
      btn.classList.toggle("is-active", btn.dataset.group === currentGroup);
    });

    document.querySelectorAll(".mode-nav__btn").forEach((btn) => {
      btn.classList.toggle("is-active", btn.dataset.mode === currentMode);
    });

    const cropNav = document.querySelector(".mode-nav.crop-group-only");
    const tagNav = document.querySelector(".mode-nav.tag-group-only");
    if (cropNav) cropNav.hidden = currentGroup !== "crop";
    if (tagNav) tagNav.hidden = currentGroup !== "tag";
  }

  async function loadTagForImage() {
    if (!selectedImagePath || !isTagMode() || isCatalogMode()) {
      if (strudelCode) strudelCode.value = "";
      return;
    }
    const q = new URLSearchParams({ mode: currentMode, relative_path: selectedImagePath });
    const res = await fetch(`/api/tag?${q}`);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(data.detail || `오류 ${res.status}`);
    }
    const field = data.field || (isFunctionTagMode() ? "tag" : "code");
    strudelCode.value = data[field] ?? "";
  }

  function syncUrlMode() {
    const u = new URL(location.href);
    u.searchParams.set("mode", currentMode);
    history.replaceState(null, "", u);
  }

  function imageApiUrl(relPath) {
    const q = new URLSearchParams({ mode: currentMode });
    return `/api/image/${encodeURI(relPath)}?${q}`;
  }

  function setMode(mode) {
    if (!MODES.has(mode)) {
      return Promise.resolve();
    }
    currentMode = mode;
    applyModeUi();
    syncUrlMode();
    return loadImageList().catch(() => logFailure(LOG_LOAD_FAIL));
  }

  function setGroup(group) {
    if (group !== "crop" && group !== "tag") return;
    const modes = group === "crop" ? CROP_MODES : TAG_MODES;
    if (!modes.has(currentMode)) {
      setMode(GROUP_DEFAULT_MODE[group]);
      return;
    }
    currentGroup = group;
    applyModeUi();
  }

  document.addEventListener("click", (ev) => {
    const groupBtn = ev.target.closest(".mode-group-nav__btn[data-group]");
    if (groupBtn) {
      setGroup(groupBtn.dataset.group);
      return;
    }

    const modeBtn = ev.target.closest(".mode-nav__btn[data-mode]");
    if (modeBtn) {
      setMode(modeBtn.getAttribute("data-mode"));
      return;
    }

    const crumb = ev.target.closest(".image-tree-breadcrumb__item[data-crumb-idx]");
    if (crumb && !crumb.classList.contains("is-current")) {
      navigateTreeTo(Number(crumb.dataset.crumbIdx));
      return;
    }

    const item = ev.target.closest(".image-tree-item[data-tree-kind]");
    if (item) {
      if (item.dataset.treeKind === "folder") {
        navigateTreeInto(item.dataset.treeName);
      } else if (item.dataset.path) {
        selectImage(item.dataset.path);
      }
    }
  });

  function availWidthForImage() {
    return Math.max(80, workspace.clientWidth - 32);
  }

  function fittedBaseWidth() {
    const nw = photo.naturalWidth;
    if (!nw) return 1;
    return Math.min(nw, availWidthForImage());
  }

  function rescaleBoxesBy(factor) {
    if (!(factor > 0) || factor === 1 || boxes.length === 0) return;
    for (const b of boxes) {
      b.x *= factor;
      b.y *= factor;
      b.w *= factor;
      b.h *= factor;
    }
  }

  function syncZoomUi() {
    if (zoomSlider) zoomSlider.value = String(zoomPct);
    if (zoomValue) zoomValue.textContent = `${Math.round(zoomPct)}%`;
  }

  function layoutImage(skipBoxRescale = false) {
    const nw = photo.naturalWidth;
    const nh = photo.naturalHeight;
    if (!nw || !nh || !photo.src) return;

    const prevW = photo.clientWidth;
    const base = fittedBaseWidth();
    const displayW = Math.max(16, Math.round((base * zoomPct) / 100));

    photo.style.maxWidth = "none";
    photo.style.width = displayW + "px";

    const newW = photo.clientWidth;
    const factor = prevW > 0 ? newW / prevW : 1;
    if (!skipBoxRescale && prevW > 0 && boxes.length && Math.abs(factor - 1) > 0.001) {
      rescaleBoxesBy(factor);
    }

    syncCanvasSize();
  }

  function syncCanvasSize() {
    const rect = photo.getBoundingClientRect();
    const w = Math.round(rect.width);
    const h = Math.round(rect.height);
    if (w <= 0 || h <= 0) return;
    const dpr = window.devicePixelRatio || 1;
    canvas.width = Math.round(w * dpr);
    canvas.height = Math.round(h * dpr);
    canvas.style.width = w + "px";
    canvas.style.height = h + "px";
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    redraw();
  }

  function redraw() {
    const w = photo.clientWidth;
    const h = photo.clientHeight;
    ctx.clearRect(0, 0, w, h);

    boxes.forEach((b, i) => {
      const sel = i === selectedIndex;
      ctx.strokeStyle = sel ? "#ef4444" : "#22c55e";
      ctx.lineWidth = 2;
      ctx.strokeRect(b.x, b.y, b.w, b.h);
      ctx.fillStyle = sel ? "rgba(239,68,68,0.12)" : "rgba(34,197,94,0.12)";
      ctx.fillRect(b.x, b.y, b.w, b.h);
    });

    if (drawing) {
      const x = Math.min(startX, currentX);
      const y = Math.min(startY, currentY);
      const ww = Math.abs(currentX - startX);
      const hh = Math.abs(currentY - startY);
      ctx.strokeStyle = "#3b82f6";
      ctx.lineWidth = 2;
      ctx.setLineDash([6, 4]);
      ctx.strokeRect(x, y, ww, hh);
      ctx.setLineDash([]);
    }
  }

  function displayToNatural(box) {
    const nw = photo.naturalWidth;
    const nh = photo.naturalHeight;
    const cw = photo.clientWidth;
    const ch = photo.clientHeight;
    if (!nw || !nh || !cw || !ch) return null;
    const sx = nw / cw;
    const sy = nh / ch;
    let x = Math.round(box.x * sx);
    let y = Math.round(box.y * sy);
    let w = Math.round(box.w * sx);
    let h = Math.round(box.h * sy);
    w = Math.max(1, w);
    h = Math.max(1, h);
    x = Math.max(0, Math.min(x, nw - 1));
    y = Math.max(0, Math.min(y, nh - 1));
    return { x, y, w, h };
  }

  function hitTest(px, py) {
    for (let i = boxes.length - 1; i >= 0; i--) {
      const b = boxes[i];
      if (px >= b.x && py >= b.y && px <= b.x + b.w && py <= b.y + b.h) return i;
    }
    return null;
  }

  function canvasCoords(ev) {
    const r = canvas.getBoundingClientRect();
    return { x: ev.clientX - r.left, y: ev.clientY - r.top };
  }

  photo.addEventListener("load", () => {
    syncZoomUi();
    layoutImage(true);
    if (isTagMode()) {
      loadTagForImage().catch(() => logFailure(LOG_LOAD_FAIL));
      return;
    }
    boxes = [];
    selectedIndex = null;
    redraw();
  });

  photo.addEventListener("error", () => {
    logFailure(LOG_LOAD_FAIL);
  });

  zoomSlider?.addEventListener("input", () => {
    zoomPct = Number(zoomSlider.value);
    if (zoomValue) zoomValue.textContent = `${zoomPct}%`;
    if (photo.naturalWidth) layoutImage(false);
  });

  btnZoomOut?.addEventListener("click", () => {
    zoomPct = Math.max(25, zoomPct - 10);
    syncZoomUi();
    if (photo.naturalWidth) layoutImage(false);
  });

  btnZoomIn?.addEventListener("click", () => {
    zoomPct = Math.min(400, zoomPct + 10);
    syncZoomUi();
    if (photo.naturalWidth) layoutImage(false);
  });

  btnZoomFit?.addEventListener("click", () => {
    zoomPct = 100;
    syncZoomUi();
    if (photo.naturalWidth) layoutImage(false);
  });

  stage.addEventListener(
    "wheel",
    (e) => {
      if (!photo.naturalWidth || !photo.src) return;
      e.preventDefault();
      const step = e.shiftKey ? 20 : 5;
      zoomPct += e.deltaY > 0 ? -step : step;
      zoomPct = Math.round(Math.min(400, Math.max(25, zoomPct)) / 5) * 5;
      syncZoomUi();
      layoutImage(false);
    },
    { passive: false }
  );

  window.addEventListener("resize", () => {
    if (photo.complete && photo.naturalWidth) layoutImage(false);
  });

  canvas.addEventListener("mousedown", (ev) => {
    if (isTagMode() || !photo.src || !photo.naturalWidth) return;
    const { x, y } = canvasCoords(ev);
    const hit = hitTest(x, y);
    if (hit !== null && !ev.shiftKey) {
      selectedIndex = hit;
      redraw();
      return;
    }
    drawing = true;
    startX = currentX = x;
    startY = currentY = y;
    selectedIndex = null;
    redraw();
  });

  canvas.addEventListener("mousemove", (ev) => {
    if (!drawing) return;
    const { x, y } = canvasCoords(ev);
    currentX = x;
    currentY = y;
    redraw();
  });

  canvas.addEventListener("mouseup", () => {
    if (!drawing) return;
    drawing = false;
    const x = Math.min(startX, currentX);
    const y = Math.min(startY, currentY);
    const w = Math.abs(currentX - startX);
    const h = Math.abs(currentY - startY);
    if (w > 4 && h > 4) {
      boxes.push({ x, y, w, h });
      selectedIndex = boxes.length - 1;
    }
    redraw();
  });

  canvas.addEventListener("mouseleave", () => {
    if (drawing) {
      drawing = false;
      redraw();
    }
  });

  document.addEventListener("keydown", (ev) => {
    if (isTagMode()) return;
    if (ev.key === "Delete" || ev.key === "Backspace") {
      if (selectedIndex !== null && boxes[selectedIndex]) {
        boxes.splice(selectedIndex, 1);
        selectedIndex = boxes.length ? Math.min(selectedIndex, boxes.length - 1) : null;
        redraw();
      }
    }
  });

  btnDelSel?.addEventListener("click", () => {
    if (selectedIndex !== null && boxes[selectedIndex]) {
      boxes.splice(selectedIndex, 1);
      selectedIndex = boxes.length ? Math.min(selectedIndex, boxes.length - 1) : null;
      redraw();
    }
  });

  btnClear?.addEventListener("click", () => {
    boxes = [];
    selectedIndex = null;
    redraw();
  });

  btnUploadPdf?.addEventListener("click", async () => {
    const work = uploadWorkId?.value?.trim();
    const file = uploadPdfFile?.files?.[0];
    if (!work) {
      logFailure(LOG_SAVE_FAIL);
      return;
    }
    if (!file) {
      logFailure(LOG_SAVE_FAIL);
      return;
    }
    btnUploadPdf.disabled = true;
    try {
      const form = new FormData();
      form.append("work", work);
      form.append("file", file);
      const res = await fetch("/api/work-upload", { method: "POST", body: form });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        logFailure(LOG_SAVE_FAIL);
        return;
      }
      logSuccess();
      if (uploadPdfFile) uploadPdfFile.value = "";
      await loadImageList();
      if (allImages.includes(work)) {
        selectImage(work, { remember: false });
      }
    } catch {
      logFailure(LOG_SAVE_FAIL);
    } finally {
      btnUploadPdf.disabled = false;
    }
  });

  btnSaveTag?.addEventListener("click", async () => {
    if (!selectedImagePath) return;
    btnSaveTag.disabled = true;
    try {
      if (isCatalogMode()) {
        const res = await fetch("/api/catalog", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(readCatalogForm()),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          logFailure(LOG_SAVE_FAIL);
          return;
        }
        logSuccess();
        updateWorkState(selectedImagePath, !!data.complete);
        return;
      }

      const body = {
        mode: currentMode,
        relative_path: selectedImagePath,
      };
      if (isFunctionTagMode()) {
        body.tag = strudelCode.value;
      } else {
        body.code = strudelCode.value;
      }
      const res = await fetch("/api/tag", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        logFailure(LOG_SAVE_FAIL);
        return;
      }
      logSuccess();
      markWorkDone(selectedImagePath);
    } catch {
      logFailure(LOG_SAVE_FAIL);
    } finally {
      btnSaveTag.disabled = false;
    }
  });

  btnSubmit?.addEventListener("click", async () => {
    if (!selectedImagePath) return;

    const naturalBoxes = [];
    for (let i = 0; i < boxes.length; i++) {
      const n = displayToNatural(boxes[i]);
      if (!n) return;
      naturalBoxes.push(n);
    }
    naturalBoxes.sort((a, b) => a.y - b.y || a.x - b.x);

    btnSubmit.disabled = true;
    try {
      const res = await fetch("/api/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          mode: currentMode,
          relative_path: selectedImagePath,
          boxes: naturalBoxes,
        }),
      });
      if (!res.ok) {
        logFailure(LOG_SAVE_FAIL);
        return;
      }
      logSuccess();
      markWorkDone(selectedImagePath);
    } catch {
      logFailure(LOG_SAVE_FAIL);
    } finally {
      btnSubmit.disabled = false;
    }
  });

  async function loadImageList() {
    allImages = [];
    treePath = [];
    selectedImagePath = null;

    const res = await fetch(`/api/images?mode=${encodeURIComponent(currentMode)}`);
    if (!res.ok) {
      clearWorkspace();
      renderImageTree();
      logFailure(LOG_LOAD_FAIL);
      return;
    }
    const data = await res.json();
    allImages = data.images || [];

    if (!allImages.length) {
      clearWorkspace();
      renderImageTree();
      if (!isCatalogMode()) {
        logFailure(LOG_LOAD_FAIL);
      }
      return;
    }

    if (sourceFolderLabel) {
      sourceFolderLabel.textContent =
        data.source_label || MODE_SOURCE_FOLDER[currentMode] || "";
    }

    if (isCatalogMode()) {
      syncCatalogWorkStates(data.catalog_complete || {});
    } else {
      syncWorkStates(allImages);
    }

    const recalled = recalledSelection();
    const initial = recalled && allImages.includes(recalled) ? recalled : allImages[0];
    selectImage(initial, { remember: false });
  }

  (function bootstrap() {
    const fromUrl = new URLSearchParams(location.search).get("mode");
    if (fromUrl && MODES.has(fromUrl)) currentMode = fromUrl;
    applyModeUi();
    syncUrlMode();
    loadImageList().catch(() => logFailure(LOG_LOAD_FAIL));
  })();
})();
