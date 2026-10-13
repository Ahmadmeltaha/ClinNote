/**
 * Theme colours for drawing code. A canvas (2D or WebGL) cannot read var(--color-...): give it themeColor("--color-brand")
 * instead. It returns the colour the page shows for that token now, in the theme showing now, as rgb(r, g, b), whatever
 * the token is written in (hex, oklch, color-mix). themeColorRgb gives the same colour as [r, g, b] from 0 to 1, for
 * WebGL. Call it when you draw, and draw again when watchTheme says the theme changed. An unknown token gives the page's
 * text colour. Holds no colour of its own.
 */

let probe: HTMLSpanElement | null = null;
let pixel: CanvasRenderingContext2D | null = null;

function painted(token: string): [number, number, number] | null {
  if (typeof document === "undefined") return null;
  if (!probe?.isConnected) {
    probe = document.createElement("span");
    probe.setAttribute("aria-hidden", "true");
    probe.style.display = "none";
    document.documentElement.appendChild(probe);
  }
  probe.style.color = `var(${token})`;
  const computed = getComputedStyle(probe).color;
  if (!pixel) {
    const c = document.createElement("canvas");
    c.width = 1;
    c.height = 1;
    pixel = c.getContext("2d", { willReadFrequently: true });
  }
  if (!pixel) return null;
  // The computed colour may still be oklch() or color-mix(): the browser paints it, and the paint is read back.
  pixel.clearRect(0, 0, 1, 1);
  pixel.fillStyle = computed;
  pixel.fillRect(0, 0, 1, 1);
  const [r = 0, g = 0, b = 0] = pixel.getImageData(0, 0, 1, 1).data;
  return [r, g, b];
}

/** The colour of a theme token, e.g. themeColor("--color-brand"), as rgb(r, g, b) for a canvas's fillStyle or strokeStyle. */
export function themeColor(token: string): string {
  const c = painted(token);
  return c ? `rgb(${c[0]}, ${c[1]}, ${c[2]})` : "transparent";
}

/** The same colour as [r, g, b], each from 0 to 1, for WebGL. */
export function themeColorRgb(token: string): [number, number, number] {
  const c = painted(token) ?? [0, 0, 0];
  return [c[0] / 255, c[1] / 255, c[2] / 255];
}

/** Calls `redraw` whenever the theme may have changed (the system's light or dark, or a class or data-theme on <html>). Returns the unsubscribe. */
export function watchTheme(redraw: () => void): () => void {
  if (typeof window === "undefined") return () => {};
  const scheme = window.matchMedia("(prefers-color-scheme: dark)");
  scheme.addEventListener("change", redraw);
  const seen = new MutationObserver(redraw);
  seen.observe(document.documentElement, { attributes: true, attributeFilter: ["class", "data-theme", "style"] });
  return () => {
    scheme.removeEventListener("change", redraw);
    seen.disconnect();
  };
}
