(() => {
  const photo = document.getElementById("photo");
  const canvas = document.getElementById("overlay");
  const ctx = canvas.getContext("2d");
  const select = document.getElementById("image-select");
  const workspace = document.querySelector(".workspace");
  const stage = document.getElementById("stage");
  const zoomSlider = document.getElementById("zoom-slider");
  const zoomValue = document.getElementById("zoom-value");
  const btnZoomOut = document.getElementById("btn-zoom-out");
  const btnZoomIn = document.getElementById("btn-zoom-in");
  const btnZoomFit = document.getElementById("btn-zoom-fit");
  const statusEl = document.getElementById("status");
  const btnSubmit = document.getElementById("btn-submit");
  const btnClear = document.getElementById("btn-clear");
  const btnDelSel = document.getElementById("btn-delete-selected");
  const hintEl = document.getElementById("hint");
  const sourceFolderLabel = document.getElementById("source-folder-label");
  const strudelCode = document.getElementById("strudel-code");
  const btnSaveTag = document.getElementById("btn-save-tag");

  const CROP_MODES = new Set([
    "page_staff",
    "staff_measure",
    "measure_note",
    "function_in_page",
    "function_in_staff",
    "function_in_measure",
    "function_in_note",
  ]);

  const TAG_MODES = new Set([
    "code_of_page",
    "code_of_staff",
    "code_of_measure",
    "code_of_note",
  ]);

  const MODES = new Set([...CROP_MODES, ...TAG_MODES]);
  /** @type {string} */
  let currentMode = "page_staff";

  const MODE_SOURCE_FOLDER = {
    page_staff: "source/pages",
    staff_measure: "source/staffs",
    measure_note: "source/measures",
    function_in_page: "source/pages",
    function_in_staff: "source/staffs",
    function_in_measure: "source/measures",
    function_in_note: "source/notes",
    code_of_page: "source/pages",
    code_of_staff: "source/staffs",
    code_of_measure: "source/measures",
    code_of_note: "source/notes",
  };

  /** @type {Record<string, string[]>} */
  const HINT_LINES = {
    page_staff: [
      "<strong>Page → Staff</strong> · 소스는 <code>source/pages</code>",
      "드래그로 사각형을 그립니다.",
      "박스를 클릭하면 선택(빨간 테두리)됩니다.",
      "<kbd>Del</kbd> 또는 「선택 삭제」로 선택 박스를 지웁니다.",
      "저장 순서: 위→아래, 같은 줄에서는 왼쪽→오른쪽.",
      "슬라이더·휠(이미지 위)로 표시 크기를 조절합니다.",
      "저장: <code>source/staffs/{악보}/{페이지stem}/staff_001.jpg</code> …",
    ],
    staff_measure: [
      "<strong>Staff → Measure</strong> · 소스는 <code>source/staffs</code>",
      "악보 한 페이지에서 잘라낸 staff 이미지를 열고, 마디(measure) 단위로 다시 박스를 그립니다.",
      "드래그·선택·삭제·줌 동작은 Page → Staff와 같습니다.",
      "저장: <code>source/measures/{악보}/{페이지}/{staff파일stem}/measure_001.jpg</code> …",
    ],
    measure_note: [
      "<strong>Measure → Note</strong> · 소스는 <code>source/measures</code>",
      "각 마디 이미지를 열고, 필요한 노트 영역만 박스로 지정합니다.",
      "저장: <code>source/notes/{악보}/{페이지}/{staffstem}/{measurestem}/note_001.jpg</code> …",
    ],
    function_in_page: [
      "<strong>Functions in Page</strong> · 소스는 <code>source/pages</code>",
      "페이지 이미지에서 function 영역을 박스로 지정합니다.",
      "이미지: <code>source/functions/pages/{악보}/{페이지}/function_001.jpg</code> …",
      "좌표: <code>data/position_data/functions_in_page/{악보}/{페이지}.json</code>",
    ],
    function_in_staff: [
      "<strong>Functions in Staff</strong> · 소스는 <code>source/staffs</code>",
      "staff 이미지에서 function 영역을 박스로 지정합니다.",
      "이미지: <code>source/functions/pages/{악보}/{페이지}/{staff}/function_001.jpg</code> …",
      "좌표: <code>data/position_data/functions_in_staff/…</code>",
    ],
    function_in_measure: [
      "<strong>Functions in Measure</strong> · 소스는 <code>source/measures</code>",
      "measure 이미지에서 function 영역을 박스로 지정합니다.",
      "이미지: <code>source/functions/pages/…/{measure}/function_001.jpg</code> …",
      "좌표: <code>data/position_data/functions_in_measure/…</code>",
    ],
    function_in_note: [
      "<strong>Functions in Note</strong> · 소스는 <code>source/notes</code>",
      "note 이미지에서 function 영역을 박스로 지정합니다.",
      "이미지: <code>source/functions/pages/…/{note}/function_001.jpg</code> …",
      "좌표: <code>data/position_data/function_in_note/…</code>",
    ],
    code_of_page: [
      "<strong>Code of Page</strong> · 소스는 <code>source/pages</code>",
      "페이지 이미지를 보며 Strudel Code를 입력합니다 (실행·검증 없음).",
      "저장: <code>data/tag_data/pages/{악보}/{페이지}.json</code>",
    ],
    code_of_staff: [
      "<strong>Code of Staff</strong> · 소스는 <code>source/staffs</code>",
      "staff 이미지마다 Strudel Code를 입력·저장합니다.",
      "저장: <code>data/tag_data/pages/{악보}/{페이지}/{staff}.json</code>",
    ],
    code_of_measure: [
      "<strong>Code of Measure</strong> · 소스는 <code>source/measures</code>",
      "measure 이미지마다 Strudel Code를 입력·저장합니다.",
      "저장: <code>data/tag_data/pages/…/{measure}.json</code>",
    ],
    code_of_note: [
      "<strong>Code of Note</strong> · 소스는 <code>source/notes</code>",
      "note 이미지마다 Strudel Code를 입력·저장합니다.",
      "저장: <code>data/tag_data/pages/…/{note}.json</code>",
    ],
  };

  function isTagMode() {
    return TAG_MODES.has(currentMode);
  }

  function renderHints() {
    const lines = HINT_LINES[currentMode] || HINT_LINES.page_staff;
    hintEl.innerHTML = "";
    for (const html of lines) {
      const li = document.createElement("li");
      li.innerHTML = html;
      hintEl.appendChild(li);
    }
  }

  function applyModeUi() {
    document.body.classList.toggle("is-tag-mode", isTagMode());
    sourceFolderLabel.textContent = MODE_SOURCE_FOLDER[currentMode];
    renderHints();
    document.querySelectorAll(".mode-nav__btn").forEach((btn) => {
      btn.classList.toggle("is-active", btn.dataset.mode === currentMode);
    });
  }

  async function loadTagForImage() {
    const rel = select.value;
    if (!rel || !isTagMode()) {
      if (strudelCode) strudelCode.value = "";
      return;
    }
    const q = new URLSearchParams({ mode: currentMode, relative_path: rel });
    const res = await fetch(`/api/tag?${q}`);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(data.detail || `오류 ${res.status}`);
    }
    strudelCode.value = data.code ?? "";
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
    if (!MODES.has(mode)) return Promise.resolve();
    currentMode = mode;
    applyModeUi();
    syncUrlMode();
    return loadImageList();
  }

  /** @type {{ x: number, y: number, w: number, h: number }[]} */
  let boxes = [];
  /** @type {number | null} */
  let selectedIndex = null;

  /** 작업 패널에 맞춤(100%)을 기준으로 한 표시 크기 비율(%) */
  let zoomPct = Number(zoomSlider?.value) || 100;

  let drawing = false;
  let startX = 0;
  let startY = 0;
  let currentX = 0;
  let currentY = 0;

  function setStatus(msg, kind = "") {
    statusEl.textContent = msg;
    statusEl.className = "status " + kind;
  }

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
    zoomSlider.value = String(zoomPct);
    zoomValue.textContent = `${Math.round(zoomPct)}%`;
  }

  /**
   * 이미지 표시 크기 적용 후 캔버스 동기화. 새 이미지 로드처럼 박스를 비운 뒤엔 rescale 스킵.
   * @param {boolean} skipBoxRescale
   */
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

  /** 화면 좌표 → 자연 이미지 픽셀 */
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
      loadTagForImage()
        .then(() => setStatus("Strudel Code를 입력한 뒤 「코드 저장」을 누르세요."))
        .catch((e) => setStatus(String(e), "err"));
      return;
    }
    boxes = [];
    selectedIndex = null;
    redraw();
    setStatus("이미지 준비됨. 드래그로 박스를 그리세요.");
  });

  zoomSlider.addEventListener("input", () => {
    zoomPct = Number(zoomSlider.value);
    zoomValue.textContent = `${zoomPct}%`;
    if (photo.naturalWidth) layoutImage(false);
  });

  btnZoomOut.addEventListener("click", () => {
    zoomPct = Math.max(25, zoomPct - 10);
    syncZoomUi();
    if (photo.naturalWidth) layoutImage(false);
  });

  btnZoomIn.addEventListener("click", () => {
    zoomPct = Math.min(400, zoomPct + 10);
    syncZoomUi();
    if (photo.naturalWidth) layoutImage(false);
  });

  btnZoomFit.addEventListener("click", () => {
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
      setStatus(`박스 ${boxes.length}개`);
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
        setStatus(`박스 ${boxes.length}개`);
      }
    }
  });

  btnDelSel.addEventListener("click", () => {
    if (selectedIndex !== null && boxes[selectedIndex]) {
      boxes.splice(selectedIndex, 1);
      selectedIndex = boxes.length ? Math.min(selectedIndex, boxes.length - 1) : null;
      redraw();
      setStatus(`박스 ${boxes.length}개`);
    }
  });

  btnClear.addEventListener("click", () => {
    boxes = [];
    selectedIndex = null;
    redraw();
    setStatus("박스를 모두 지웠습니다.");
  });

  btnSaveTag.addEventListener("click", async () => {
    const rel = select.value;
    if (!rel) {
      setStatus("이미지를 선택하세요.", "err");
      return;
    }
    btnSaveTag.disabled = true;
    setStatus("저장 중…");
    try {
      const res = await fetch("/api/tag", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          mode: currentMode,
          relative_path: rel,
          code: strudelCode.value,
        }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setStatus(data.detail || `오류 ${res.status}`, "err");
        return;
      }
      setStatus(`코드 저장 완료 → ${data.tag_path}`, "ok");
    } catch (e) {
      setStatus(String(e), "err");
    } finally {
      btnSaveTag.disabled = false;
    }
  });

  btnSubmit.addEventListener("click", async () => {
    const rel = select.value;
    if (!rel) {
      setStatus("이미지를 선택하세요.", "err");
      return;
    }
    if (!boxes.length) {
      setStatus("박스를 하나 이상 그리세요.", "err");
      return;
    }

    const naturalBoxes = [];
    for (let i = 0; i < boxes.length; i++) {
      const n = displayToNatural(boxes[i]);
      if (!n) {
        setStatus("이미지 좌표 변환 실패.", "err");
        return;
      }
      naturalBoxes.push(n);
    }

    naturalBoxes.sort((a, b) => a.y - b.y || a.x - b.x);

    btnSubmit.disabled = true;
    setStatus("저장 중…");
    try {
      const res = await fetch("/api/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode: currentMode, relative_path: rel, boxes: naturalBoxes }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setStatus(data.detail || `오류 ${res.status}`, "err");
        return;
      }
      setStatus(`저장 완료: ${data.count}개 → ${data.saved.join(", ")}`, "ok");
    } catch (e) {
      setStatus(String(e), "err");
    } finally {
      btnSubmit.disabled = false;
    }
  });

  async function loadImageList() {
    select.innerHTML = "";
    const opt0 = document.createElement("option");
    opt0.value = "";
    opt0.textContent = "— 선택 —";
    select.appendChild(opt0);

    const res = await fetch(`/api/images?mode=${encodeURIComponent(currentMode)}`);
    const data = await res.json();
    const images = data.images || [];
    if (!images.length) {
      photo.removeAttribute("src");
      if (strudelCode) strudelCode.value = "";
      boxes = [];
      selectedIndex = null;
      redraw();
      setStatus(`이미지가 없습니다 (${MODE_SOURCE_FOLDER[currentMode]}).`, "err");
      return;
    }
    for (const p of images) {
      const o = document.createElement("option");
      o.value = p;
      o.textContent = p;
      select.appendChild(o);
    }
    select.value = images[0];
    photo.src = imageApiUrl(images[0]);
    setStatus(`${images.length}개 이미지`);
  }

  select.addEventListener("change", () => {
    const v = select.value;
    if (!v) {
      photo.removeAttribute("src");
      if (strudelCode) strudelCode.value = "";
      boxes = [];
      selectedIndex = null;
      redraw();
      return;
    }
    photo.src = imageApiUrl(v);
  });

  document.querySelectorAll(".mode-nav").forEach((nav) => {
    nav.addEventListener("click", (ev) => {
      const btn = ev.target.closest("[data-mode]");
      if (!(btn instanceof HTMLElement) || btn.tagName !== "BUTTON") return;
      const m = btn.dataset.mode;
      setMode(m).catch((e) => setStatus(String(e), "err"));
    });
  });

  (function bootstrap() {
    const fromUrl = new URLSearchParams(location.search).get("mode");
    if (MODES.has(fromUrl)) currentMode = fromUrl;
    applyModeUi();
    syncUrlMode();
    loadImageList().catch((e) => setStatus(String(e), "err"));
  })();
})();
