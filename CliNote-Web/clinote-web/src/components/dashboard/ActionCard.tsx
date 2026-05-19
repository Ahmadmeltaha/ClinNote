import Link from "next/link";
import { ArrowRight, type LucideIcon } from "lucide-react";
import { clsx } from "clsx";

type Accent = "emerald" | "blue" | "amber";

interface ActionCardProps {
  accent: Accent;
  icon: LucideIcon;
  /** Optional small label above the icon (e.g. "Case 1"). Omit for a cleaner card. */
  eyebrow?: string;
  title: string;
  description: string;
  cta: string;
  href: string;
}

const ACCENTS: Record<
  Accent,
  {
    glow: string;
    border: string;
    accentBar: string;
    iconBg: string;
    eyebrow: string;
    cta: string;
    ctaUnderline: string;
    blob: string;
    blobSm: string;
    ring: string;
  }
> = {
  emerald: {
    glow: "hover:shadow-[0_30px_70px_-20px_rgba(16,185,129,0.55)] dark:hover:shadow-[0_30px_70px_-20px_rgba(16,185,129,0.45)]",
    border: "hover:border-emerald-300 dark:hover:border-emerald-700/60",
    accentBar: "bg-gradient-to-r from-emerald-400 via-emerald-500 to-emerald-600",
    iconBg:
      "bg-gradient-to-br from-emerald-400 to-emerald-600 shadow-lg shadow-emerald-500/40",
    eyebrow: "text-emerald-600 dark:text-emerald-400",
    cta: "text-emerald-700 dark:text-emerald-400",
    ctaUnderline: "bg-emerald-500",
    blob: "from-emerald-300/40 to-emerald-500/20 dark:from-emerald-700/30 dark:to-emerald-900/10",
    blobSm: "bg-emerald-400/20 dark:bg-emerald-600/15",
    ring: "ring-emerald-500/30",
  },
  blue: {
    glow: "hover:shadow-[0_30px_70px_-20px_rgba(59,130,246,0.55)] dark:hover:shadow-[0_30px_70px_-20px_rgba(59,130,246,0.45)]",
    border: "hover:border-blue-300 dark:hover:border-blue-700/60",
    accentBar: "bg-gradient-to-r from-blue-400 via-blue-500 to-blue-600",
    iconBg:
      "bg-gradient-to-br from-blue-400 to-blue-600 shadow-lg shadow-blue-500/40",
    eyebrow: "text-blue-600 dark:text-blue-400",
    cta: "text-blue-700 dark:text-blue-400",
    ctaUnderline: "bg-blue-500",
    blob: "from-blue-300/40 to-blue-500/20 dark:from-blue-700/30 dark:to-blue-900/10",
    blobSm: "bg-blue-400/20 dark:bg-blue-600/15",
    ring: "ring-blue-500/30",
  },
  amber: {
    glow: "hover:shadow-[0_30px_70px_-20px_rgba(245,158,11,0.55)] dark:hover:shadow-[0_30px_70px_-20px_rgba(245,158,11,0.45)]",
    border: "hover:border-amber-300 dark:hover:border-amber-700/60",
    accentBar: "bg-gradient-to-r from-amber-400 via-amber-500 to-amber-600",
    iconBg:
      "bg-gradient-to-br from-amber-400 to-amber-600 shadow-lg shadow-amber-500/40",
    eyebrow: "text-amber-600 dark:text-amber-500",
    cta: "text-amber-700 dark:text-amber-400",
    ctaUnderline: "bg-amber-500",
    blob: "from-amber-300/40 to-amber-500/20 dark:from-amber-700/30 dark:to-amber-900/10",
    blobSm: "bg-amber-400/20 dark:bg-amber-600/15",
    ring: "ring-amber-500/30",
  },
};

export function ActionCard({
  accent,
  icon: Icon,
  eyebrow,
  title,
  description,
  cta,
  href,
}: ActionCardProps) {
  const a = ACCENTS[accent];

  return (
    <Link
      href={href}
      className={clsx(
        "group relative flex h-full min-h-[460px] flex-col overflow-hidden rounded-3xl border border-slate-200 bg-white p-8 shadow-lg transition-all duration-500 dark:border-slate-700 dark:bg-slate-800",
        "hover:-translate-y-2 hover:scale-[1.015]",
        a.border,
        a.glow,
      )}
    >
      {/* Top accent bar */}
      <div
        aria-hidden="true"
        className={clsx(
          "absolute inset-x-0 top-0 h-1.5 transition-all duration-300 group-hover:h-2",
          a.accentBar,
        )}
      />

      {/* Decorative gradient blob — corner */}
      <div
        aria-hidden="true"
        className={clsx(
          "pointer-events-none absolute -right-24 -top-24 h-64 w-64 rounded-full bg-gradient-to-br opacity-60 blur-3xl transition-all duration-700 group-hover:scale-110 group-hover:opacity-100",
          a.blob,
        )}
      />

      {/* Smaller corner blob */}
      <div
        aria-hidden="true"
        className={clsx(
          "pointer-events-none absolute -bottom-16 -left-16 h-40 w-40 rounded-full opacity-50 blur-2xl transition-all duration-500 group-hover:scale-110",
          a.blobSm,
        )}
      />

      {/* Glass shine on hover */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -inset-x-4 -top-40 h-32 -rotate-12 bg-gradient-to-r from-transparent via-white/30 to-transparent opacity-0 transition-all duration-700 group-hover:top-[110%] group-hover:opacity-100 dark:via-white/5"
      />

      {/* Eyebrow (optional) */}
      {eyebrow && (
        <p
          className={clsx(
            "relative text-[11px] font-bold uppercase tracking-[0.25em]",
            a.eyebrow,
          )}
        >
          {eyebrow}
        </p>
      )}

      {/* Icon */}
      <div
        className={clsx(
          "relative inline-flex h-16 w-16 items-center justify-center rounded-2xl transition-all duration-500 group-hover:scale-110 group-hover:-rotate-6 group-hover:ring-4",
          eyebrow ? "mt-5" : "",
          a.iconBg,
          a.ring,
        )}
      >
        <Icon className="h-8 w-8 text-white" strokeWidth={2.5} />
      </div>

      {/* Title */}
      <h3 className="relative mt-6 text-2xl font-extrabold tracking-tight text-slate-900 dark:text-slate-50">
        {title}
      </h3>

      {/* Description */}
      <p className="relative mt-3 flex-1 text-sm leading-relaxed text-slate-600 dark:text-slate-300">
        {description}
      </p>

      {/* CTA */}
      <div
        className={clsx(
          "relative mt-6 inline-flex items-center gap-2 text-sm font-bold",
          a.cta,
        )}
      >
        <span className="relative">
          {cta}
          <span
            className={clsx(
              "absolute -bottom-0.5 left-0 h-0.5 w-0 transition-all duration-300 group-hover:w-full",
              a.ctaUnderline,
            )}
          />
        </span>
        <ArrowRight className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-1.5" />
      </div>
    </Link>
  );
}
