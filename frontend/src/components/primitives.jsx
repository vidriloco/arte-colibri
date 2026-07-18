import React from "react";
import { useLang, formatPrice, bi } from "../i18n.jsx";
import { useGo } from "../nav.js";

// ── Hummingbird logo placeholder ────────────────────────────────────────────
export function LogoSlot({ size = 36, accent = "#117360" }) {
  return (
    <span className="logo-slot" style={{ width: size, height: size, "--accent": accent }}>
      <svg viewBox="0 0 36 36" width={size} height={size} aria-hidden="true">
        <rect x="1" y="1" width="34" height="34" rx="6" fill="none" stroke="currentColor"
              strokeOpacity=".22" strokeWidth="1" strokeDasharray="3 3" />
        <path d="M9 22 Q17 14 25 12 L23 17 L28 19 L20 21 L17 26 Z" fill="var(--accent)" opacity=".9" />
        <circle cx="26" cy="11.5" r="1.3" fill="var(--accent)" />
      </svg>
    </span>
  );
}

export function Wordmark({ large = false }) {
  return (
    <span className={"wordmark" + (large ? " wordmark--lg" : "")}>
      <LogoSlot size={large ? 44 : 30} />
      <span className="wordmark__text">
        <span className="wordmark__name">Arte Colibrí</span>
        {large && <span className="wordmark__sub">Galería · Ciudad de México</span>}
      </span>
    </span>
  );
}

// ── Artwork image with striped fallback ─────────────────────────────────────
export function ArtImage({ src, alt, ratio = "4 / 5", variant = "card" }) {
  const [err, setErr] = React.useState(false);
  return (
    <div className={"art-img art-img--" + variant} style={{ aspectRatio: ratio }}>
      {src && !err ? (
        <img src={src} alt={alt} loading="lazy" onError={() => setErr(true)} />
      ) : (
        <div className="art-img__fallback" aria-label={alt}>
          <svg viewBox="0 0 100 125" preserveAspectRatio="none">
            <defs>
              <pattern id="stripe" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
                <line x1="0" y1="0" x2="0" y2="6" stroke="currentColor" strokeOpacity=".12" strokeWidth="2" />
              </pattern>
            </defs>
            <rect width="100" height="125" fill="url(#stripe)" />
          </svg>
          <span className="art-img__label">{alt}</span>
        </div>
      )}
    </div>
  );
}

// ── Availability badge (public) ──────────────────────────────────────────────
export function AvailabilityBadge({ availability }) {
  const { t } = useLang();
  if (availability === "sold") return <span className="badge badge--sold">{t("avail_sold")}</span>;
  if (availability === "nfs") return <span className="badge badge--nfs">{t("avail_nfs")}</span>;
  return <span className="badge badge--avail">{t("avail_available")}</span>;
}

// ── Artwork card ─────────────────────────────────────────────────────────────
export function ArtworkCard({ work, variant = "frame", density = "regular" }) {
  const { lang, t } = useLang();
  const go = useGo();
  const sold = work.availability === "sold";
  const nfs = work.availability === "nfs";
  return (
    <article
      className={`card card--${variant} card--${density}`}
      onClick={() => go({ name: "artwork", id: work.slug })}>
      <div className="card__media">
        <ArtImage src={work.primary_image?.url} alt={bi(work.title, lang)} />
        {work.featured && variant !== "plate" && (
          <span className="card__featured">{t("featured_tag")}</span>
        )}
        {sold && <div className="card__overlay">{t("avail_sold")}</div>}
      </div>
      <div className="card__meta">
        <div className="card__title-row">
          <h3 className="card__title">
            <span className="card__title-name">{bi(work.title, lang)}</span>
            <span className="card__title-year">, {work.year}</span>
          </h3>
        </div>
        <p className="card__artist">{work.artist_name}</p>
        <div className="card__foot">
          <span className="card__price">
            {nfs ? t("avail_nfs") : formatPrice(work.price, lang, work.currency)}
          </span>
        </div>
      </div>
    </article>
  );
}

// ── Filter chips ─────────────────────────────────────────────────────────────
export function FilterChips({ tags, active, onToggle, onClear }) {
  const { lang, t } = useLang();
  return (
    <div className="chips">
      <button type="button" className={"chip" + (active.length === 0 ? " is-active" : "")} onClick={onClear}>
        {lang === "es" ? "Todas" : "All"}
      </button>
      {tags.map((tag) => (
        <button
          key={tag.slug}
          type="button"
          className={"chip" + (active.includes(tag.slug) ? " is-active" : "")}
          onClick={() => onToggle(tag.slug)}>
          {bi(tag.label, lang)}
        </button>
      ))}
      {active.length > 0 && (
        <button type="button" className="chip chip--clear" onClick={onClear}>
          ✕ {t("clear")}
        </button>
      )}
    </div>
  );
}

// ── Section head ─────────────────────────────────────────────────────────────
export function SectionHead({ title, action, onAction }) {
  return (
    <div className="section-head">
      <h2>{title}</h2>
      {action && (
        <button type="button" className="section-head__action" onClick={onAction}>
          {action} <span aria-hidden="true">→</span>
        </button>
      )}
    </div>
  );
}

// ── Breadcrumb ───────────────────────────────────────────────────────────────
export function Crumbs({ items }) {
  return (
    <nav className="crumbs" aria-label="Breadcrumb">
      {items.map((it, i) => (
        <React.Fragment key={i}>
          {i > 0 && <span className="crumbs__sep" aria-hidden="true">/</span>}
          {it.onClick ? (
            <button type="button" onClick={it.onClick}>{it.label}</button>
          ) : (
            <span className="crumbs__current">{it.label}</span>
          )}
        </React.Fragment>
      ))}
    </nav>
  );
}

// ── Shared states ────────────────────────────────────────────────────────────
export function Loading() {
  const { t } = useLang();
  return (
    <div className="state state--loading" role="status">
      <span className="state__spinner" aria-hidden="true" />
      <p>{t("loading")}</p>
    </div>
  );
}

export function ErrorState({ onRetry }) {
  const { t } = useLang();
  return (
    <div className="empty-state">
      <h2>{t("error_t")}</h2>
      <p>{t("error_b")}</p>
      {onRetry && (
        <button type="button" className="btn btn--ghost" onClick={onRetry}>{t("retry")}</button>
      )}
    </div>
  );
}

export function EmptyState({ title, body, children }) {
  return (
    <div className="empty-state">
      <h2>{title}</h2>
      {body && <p>{body}</p>}
      {children}
    </div>
  );
}
