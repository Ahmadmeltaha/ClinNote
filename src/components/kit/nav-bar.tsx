import type { ReactNode } from "react";
import "./kit.css";

type NavLinkProps = { href: string; className: string; "aria-current"?: "page"; children: ReactNode };

/**
 * The app's navigation bar from the starter kit: the app's name and a link to each page, the current page marked for
 * screen readers and on screen. It carries the starter's `site-header` class, so the starter's header styles still
 * apply, and its links wrap onto more rows on a phone. In a Next app pass `link` to render each with next/link (a
 * raw root link breaks under the preview's sub-path); otherwise plain anchors are used.
 */
export function NavBar({
  appName,
  links,
  current,
  link,
}: {
  appName: ReactNode;
  links: { href: string; label: string }[];
  current?: string;
  link?: (props: NavLinkProps) => ReactNode;
}) {
  return (
    <header className="site-header kit-nav">
      <div className="kit-nav-inner">
        <span className="kit-nav-name">{appName}</span>
        <nav aria-label="Main">
          <ul className="kit-nav-links">
            {links.map((l) => {
              const here = l.href === current;
              return (
                <li key={l.href}>
                  {link ? (
                    link({ href: l.href, className: "kit-nav-link", "aria-current": here ? "page" : undefined, children: l.label })
                  ) : (
                    <a href={l.href} className="kit-nav-link" aria-current={here ? "page" : undefined}>
                      {l.label}
                    </a>
                  )}
                </li>
              );
            })}
          </ul>
        </nav>
      </div>
    </header>
  );
}
