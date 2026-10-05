"use client";

import {useEffect, useRef} from "react";

export default function CursorGlow() {
  const overlay = useRef<HTMLDivElement>(null);
  const spot = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    const layer = overlay.current;
    const light = spot.current;
    if (!layer || !light) return;

    const motion = window.matchMedia("(prefers-reduced-motion: reduce)");
    const pointer = window.matchMedia("(any-hover: hover) and (any-pointer: fine)");
    let frame: number | null = null;
    let visible = false;
    let lastTime = 0;
    let x = 0, y = 0, targetX = 0, targetY = 0;

    const paint = () => {
      light.style.transform = `translate3d(${x.toFixed(2)}px, ${y.toFixed(2)}px, 0)`;
    };
    const hide = () => {
      visible = false;
      layer.dataset.visible = "false";
      if (frame !== null) window.cancelAnimationFrame(frame);
      frame = null;
      lastTime = 0;
    };
    const animate = (time: number) => {
      const elapsed = lastTime ? Math.min(time - lastTime, 64) : 16;
      lastTime = time;
      const ease = 1 - Math.exp(-elapsed / 70);
      x += (targetX - x) * ease;
      y += (targetY - y) * ease;
      if (Math.abs(targetX - x) + Math.abs(targetY - y) < 0.3) {
        x = targetX;
        y = targetY;
        paint();
        frame = null;
        lastTime = 0;
        return;
      }
      paint();
      frame = window.requestAnimationFrame(animate);
    };
    const move = (event: PointerEvent) => {
      if (event.pointerType !== "mouse" || motion.matches || !pointer.matches) {
        hide();
        return;
      }
      targetX = event.clientX;
      targetY = event.clientY;
      if (!visible) {
        x = targetX;
        y = targetY;
        paint();
        visible = true;
        layer.dataset.visible = "true";
      }
      if (frame === null) frame = window.requestAnimationFrame(animate);
    };
    const leave = (event: PointerEvent) => {
      if (event.relatedTarget === null) hide();
    };
    const visibility = () => {
      if (document.hidden) hide();
    };

    window.addEventListener("pointermove", move, {passive: true});
    window.addEventListener("pointerout", leave, {passive: true});
    window.addEventListener("blur", hide);
    document.addEventListener("visibilitychange", visibility);
    motion.addEventListener("change", hide);
    pointer.addEventListener("change", hide);
    return () => {
      hide();
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerout", leave);
      window.removeEventListener("blur", hide);
      document.removeEventListener("visibilitychange", visibility);
      motion.removeEventListener("change", hide);
      pointer.removeEventListener("change", hide);
    };
  }, []);

  return <div ref={overlay} className="cursor-glow" data-visible="false" aria-hidden="true"><span ref={spot} className="cursor-glow__spot"/></div>;
}
