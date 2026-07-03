import { useEffect, useRef } from 'react';

export default function BgCanvas({ theme }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let W, H, particles = [], animId;
    const isDark = () => theme === 'dark';

    function resize() {
      W = canvas.width  = window.innerWidth;
      H = canvas.height = window.innerHeight;
    }
    resize();
    window.addEventListener('resize', resize);

    function Particle() { this.reset(); }
    Particle.prototype.reset = function () {
      this.x     = Math.random() * W;
      this.y     = Math.random() * H;
      this.z     = Math.random() * W;
      this.r     = Math.random() * 1.5 + 0.3;
      this.speed = Math.random() * 0.4 + 0.1;
      this.alpha = Math.random() * 0.6 + 0.1;
    };
    Particle.prototype.update = function () {
      this.z -= this.speed;
      if (this.z <= 0) this.reset();
    };
    Particle.prototype.draw = function () {
      const sx    = (this.x - W / 2) * (W / this.z) + W / 2;
      const sy    = (this.y - H / 2) * (W / this.z) + H / 2;
      const size  = this.r * (W / this.z);
      if (sx < 0 || sx > W || sy < 0 || sy > H) { this.reset(); return; }
      const alpha = Math.min(this.alpha * (1 - this.z / W), 0.7);
      ctx.beginPath();
      ctx.arc(sx, sy, Math.min(size, 2.5), 0, Math.PI * 2);
      ctx.fillStyle = isDark()
        ? `rgba(0,229,255,${alpha})`
        : `rgba(0,80,160,${alpha * 0.5})`;
      ctx.fill();
    };

    for (let i = 0; i < 120; i++) {
      const p = new Particle();
      p.z = Math.random() * W;
      particles.push(p);
    }

    function drawGrid() {
      const vx = W / 2, vy = H * 0.55;
      const gAlpha = isDark() ? 0.035 : 0.025;
      const gColor = isDark() ? '0,229,255' : '0,80,160';
      ctx.strokeStyle = `rgba(${gColor},${gAlpha})`;
      ctx.lineWidth = 0.5;
      for (let i = 0; i <= 14; i++) {
        const y = H * 0.55 + (i / 14) * H * 0.55;
        const t = i / 14;
        ctx.beginPath();
        ctx.moveTo(vx - vx * (1 - t * 0.3), y);
        ctx.lineTo(vx + (W - vx) * (1 - t * 0.3), y);
        ctx.stroke();
      }
      for (let j = 0; j <= 20; j++) {
        const x = (j / 20) * W;
        ctx.beginPath();
        ctx.moveTo(vx, vy);
        ctx.lineTo(x, H);
        ctx.stroke();
      }
    }

    function animate() {
      ctx.clearRect(0, 0, W, H);
      drawGrid();
      particles.forEach(p => { p.update(); p.draw(); });
      animId = requestAnimationFrame(animate);
    }
    animate();

    return () => {
      window.removeEventListener('resize', resize);
      cancelAnimationFrame(animId);
    };
  }, [theme]);

  return (
    <canvas
      ref={canvasRef}
      id="bg-canvas"
      style={{
        position: 'fixed',
        top: 0, left: 0,
        width: '100%', height: '100%',
        pointerEvents: 'none',
        zIndex: 0,
      }}
    />
  );
}
