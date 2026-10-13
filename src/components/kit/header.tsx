import "./kit.css";

export interface HeaderLink {
  href: string;
  label: string;
}

/**
 * The app's header from the starter kit: its name, then its links. The name wraps inside its own column and is never
 * cut, so a long name a person typed stays whole and never runs over the links; the links wrap too, and on a narrow
 * screen they go under the name. Mark the page the person is on with `current` (its href).
 */
export function SiteHeader({ name, links, current }: { name: string; links: HeaderLink[]; current?: string }) {
  return (
    <header className="kit-header">
      <div className="kit-header-bar">
        <a href="/" className="kit-header-name">
          {name}
        </a>
        <nav aria-label="Main">
          <ul className="kit-header-links">
            {links.map((l) => (
              <li key={l.href}>
                <a href={l.href} aria-current={l.href === current ? "page" : undefined}>
                  {l.label}
                </a>
              </li>
            ))}
          </ul>
        </nav>
      </div>
    </header>
  );
}
