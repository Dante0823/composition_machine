(() => {
  const photo = document.getElementById("photo");
  const canvas = document.getElementById("overlay");
  const ctx = canvas.getContext("2d");
  const select = document.getElementById("image-select");
  const statusEl = document.getElementById("status");
  const btnSubmit = document.getElementById("btn-submit");
  const btnClear = document.getElementById("btn-clear");
  const btnDelSel = document.getElementById("btn-delete-selected");

  /** @type {{ x: number, y: number, w: number, h: number }[]} */
  let boxes = [];
  /** @type {number | null} */
  let selectedIndex = null;

  let drawing = false;
  let startX = 0;
  let startY = 0;
  let currentX = 0;
  let currentY = 0;

  function setStatus(msg, kind = "") {
    statusEl.textContent = msg;
    statusEl.className = "status " + kind;
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
    boxes = [];
    selectedIndex = null;
    syncCanvasSize();
    setStatus("이미지 준비됨. 드래그로 박스를 그리세요.");
  });

  window.addEventListener("resize", () => {
    if (photo.complete && photo.naturalWidth) syncCanvasSize();
  });

  canvas.addEventListener("mousedown", (ev) => {
    if (!photo.src || !photo.naturalWidth) return;
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
        body: JSON.stringify({ relative_path: rel, boxes: naturalBoxes }),
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

    const res = await fetch("/api/images");
    const data = await res.json();
    const images = data.images || [];
    if (!images.length) {
      setStatus(`폴더에 이미지가 없습니다: source/pages`, "err");
      return;
    }
    for (const p of images) {
      const o = document.createElement("option");
      o.value = p;
      o.textContent = p;
      select.appendChild(o);
    }
    select.value = images[0];
    photo.src = "/api/image/" + encodeURI(images[0]);
    setStatus(`${images.length}개 이미지`);
  }

  select.addEventListener("change", () => {
    const v = select.value;
    if (!v) {
      photo.removeAttribute("src");
      boxes = [];
      selectedIndex = null;
      redraw();
      return;
    }
    photo.src = "/api/image/" + encodeURI(v);
  });

  loadImageList().catch((e) => setStatus(String(e), "err"));
})();
