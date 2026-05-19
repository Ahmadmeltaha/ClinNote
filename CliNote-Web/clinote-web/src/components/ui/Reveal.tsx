"use client";

import { useEffect, useRef, useState } from "react";
import { clsx } from "clsx";

interface RevealProps {
  children: React.ReactNode;
  delay?: number;
  className?: string;
  /** Starting Y offset in pixels (default 16). */
  offset?: number;
  /** If true, repeats the animation every time it enters the viewport. */
  repeat?: boolean;
}

/**
 * Wraps children in a div that fades+slides in when scrolled into view.
 * Uses IntersectionObserver — no animation library, ~30 lines, respects
 * `prefers-reduced-motion`.
 */
export function Reveal({
  children,
  delay = 0,
  className,
  offset = 16,
  repeat = false,
}: RevealProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches
    ) {
      setVisible(true);
      return;
    }
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          if (!repeat) observer.unobserve(el);
        } else if (repeat) {
          setVisible(false);
        }
      },
      { threshold: 0.05, rootMargin: "0px 0px -40px 0px" },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [repeat]);

  return (
    <div
      ref={ref}
      className={clsx(
        "transition-all duration-700 ease-out will-change-transform",
        visible ? "translate-y-0 opacity-100" : "opacity-0",
        className,
      )}
      style={{
        transitionDelay: `${delay}ms`,
        transform: visible ? "translateY(0)" : `translateY(${offset}px)`,
      }}
    >
      {children}
    </div>
  );
}
