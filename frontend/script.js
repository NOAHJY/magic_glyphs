const canvas    = document.getElementById('c');
const ctx       = canvas.getContext('2d');
const flash     = document.getElementById('flash');
const statusMsg = document.getElementById('statusMsg');
const brushInput = document.getElementById('brushSize');
const brushLabel = document.getElementById('brushLabel');
const clearBtn   = document.getElementById('clearBtn');

const CANVAS_SIZE = 600;
const CENTER      = CANVAS_SIZE / 2;

let isDrawing    = false;
let lastX        = 0;
let lastY        = 0;
let strokePoints = [];
let brushSize    = 3;
let cooldown     = false;

// Canvas drawing style
ctx.lineCap     = 'round';
ctx.lineJoin    = 'round';
ctx.strokeStyle = '#1a1a1a';

// ─── Brush size control ───────────────────────────────────────────
brushInput.addEventListener('input', () => {
  brushSize = parseInt(brushInput.value);
  brushLabel.textContent = brushSize;
});

// ─── Get pointer position (mouse or touch) ────────────────────────
function getPos(e) {
  const rect   = canvas.getBoundingClientRect();
  const scaleX = CANVAS_SIZE / rect.width;
  const scaleY = CANVAS_SIZE / rect.height;
  const src    = e.touches ? e.touches[0] : e;
  return {
    x: (src.clientX - rect.left) * scaleX,
    y: (src.clientY - rect.top)  * scaleY,
  };
}

// ─── Drawing events ───────────────────────────────────────────────
function startDraw(e) {
  e.preventDefault();
  isDrawing    = true;
  const { x, y } = getPos(e);
  lastX        = x;
  lastY        = y;
  strokePoints = [{ x, y }];
  ctx.lineWidth = brushSize;
}

function draw(e) {
  if (!isDrawing) return;
  e.preventDefault();
  const { x, y } = getPos(e);
  ctx.beginPath();
  ctx.moveTo(lastX, lastY);
  ctx.lineTo(x, y);
  ctx.stroke();
  lastX = x;
  lastY = y;
  strokePoints.push({ x, y });
}

function endDraw() {
  if (!isDrawing) return;
  isDrawing = false;
  if (!cooldown && strokePoints.length > 20) {
    checkCircle(strokePoints);
  }
}

// ─── Math helpers ─────────────────────────────────────────────────
function mean(arr) {
  return arr.reduce((sum, v) => sum + v, 0) / arr.length;
}

function stdDev(arr) {
  const m = mean(arr);
  return Math.sqrt(mean(arr.map(v => (v - m) ** 2)));
}

// ─── Circle detection ─────────────────────────────────────────────
function checkCircle(pts) {
  // Step 1: find center of the stroke
  const cx = mean(pts.map(p => p.x));
  const cy = mean(pts.map(p => p.y));

  // Step 2: distance from center to every point
  const distances = pts.map(p =>
    Math.sqrt((p.x - cx) ** 2 + (p.y - cy) ** 2)
  );

  // Step 3: how circle-like is it?
  const radius         = mean(distances);
  const spread         = stdDev(distances);
  const relativeSpread = spread / radius;

  // Step 4: how close is center to canvas middle?
  const distFromCenter = Math.sqrt((cx - CENTER) ** 2 + (cy - CENTER) ** 2);

  const isCircleShaped = relativeSpread < 0.18;  // consistent distances
  const isBigEnough    = radius > 180;            // large enough radius
  const isCentered     = distFromCenter < 100;    // near canvas center

  if (isCircleShaped && isBigEnough && isCentered) {
    onCircleDetected();
  }
}

// ─── Triggered when big circle is drawn ──────────────────────────
function onCircleDetected() {
  cooldown = true;

  // Visual flash
  flash.style.opacity = '1';
  setTimeout(() => { flash.style.opacity = '0'; }, 600);

  setStatus('Circle detected! Sending to detection…', 'info');

  // Send canvas image to Python backend
  const imageData = canvas.toDataURL('image/png');

  fetch('http://localhost:5000/detect', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ image: imageData }),
  })
  .then(r => r.json())
  .then(data => {
    const pct   = Math.round(data.similarity * 100);
    const match = data.similarity >= 0.75;
    setStatus(
      match
        ? `✦ Sigil recognised — ${pct}% match`
        : `✧ No match — ${pct}% similarity`,
      match ? 'success' : 'error'
    );
  })
  .catch(() => {
    setStatus('Backend not connected yet — circle detection works!', 'info');
  })
  .finally(() => {
    setTimeout(() => { cooldown = false; }, 2000);
  });
}

// ─── Status helper ────────────────────────────────────────────────
function setStatus(msg, type = 'info') {
  statusMsg.textContent  = msg;
  statusMsg.className    = `status ${type}`;
}

// ─── Clear canvas ─────────────────────────────────────────────────
clearBtn.addEventListener('click', () => {
  ctx.clearRect(0, 0, CANVAS_SIZE, CANVAS_SIZE);
  setStatus('');
  cooldown = false;
});

// ─── Event listeners ──────────────────────────────────────────────
canvas.addEventListener('mousedown',  startDraw);
canvas.addEventListener('mousemove',  draw);
canvas.addEventListener('mouseup',    endDraw);
canvas.addEventListener('mouseleave', endDraw);
canvas.addEventListener('touchstart', startDraw, { passive: false });
canvas.addEventListener('touchmove',  draw,      { passive: false });
canvas.addEventListener('touchend',   endDraw);