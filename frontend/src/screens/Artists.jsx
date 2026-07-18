import React from "react";
import { useLang, bi } from "../i18n.jsx";
import { useGo } from "../nav.js";
import { Public } from "../api.js";
import { useFetch } from "../hooks.js";
import { ArtImage, Crumbs, Loading, ErrorState, EmptyState } from "../components/primitives.jsx";
import { useSeoPage } from "../head.js";

function RosterRow({ artist, index }) {
  const { lang, t } = useLang();
  const go = useGo();
  const highlights = artist.highlights || [];
  return (
    <li className="roster__row">
      <span className="roster__num" aria-hidden="true">{String(index + 1).padStart(2, "0")}</span>

      <div className="roster__portrait" onClick={() => go({ name: "artist", id: artist.slug })}>
        <div className="roster__portrait-frame">
          <svg className="roster__portrait-stripes" viewBox="0 0 100 125" preserveAspectRatio="none" aria-hidden="true">
            <defs>
              <pattern id={`rs-${artist.slug}`} width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
                <line x1="0" y1="0" x2="0" y2="6" stroke="currentColor" strokeOpacity=".14" strokeWidth="2" />
              </pattern>
            </defs>
            <rect width="100" height="125" fill={`url(#rs-${artist.slug})`} />
          </svg>
          <span className="roster__portrait-init" aria-hidden="true">{artist.initials}</span>
          <span className="roster__portrait-tag">
            {lang === "es" ? "Retrato · por colocar" : "Portrait · to add"}
          </span>
        </div>
      </div>

      <div className="roster__body">
        <p className="roster__discipline">{bi(artist.discipline, lang)}</p>
        <h2 className="roster__name">{artist.display_name}</h2>
        <p className="roster__loc">{t("based_in")} {artist.city}, CDMX</p>
        <p className="roster__bio">{bi(artist.bio, lang)}</p>
        <dl className="roster__meta">
          <div><dt>{lang === "es" ? "Obras" : "Works"}</dt><dd>{artist.works_count}</dd></div>
          {artist.since && <div><dt>{t("since")}</dt><dd>{artist.since}</dd></div>}
          {artist.instagram && <div><dt>{t("instagram")}</dt><dd>{artist.instagram}</dd></div>}
        </dl>
        <button type="button" className="btn btn--ghost roster__cta" onClick={() => go({ name: "artist", id: artist.slug })}>
          {t("view_profile")}<span className="btn__arrow" aria-hidden="true">→</span>
        </button>
      </div>

      <div className="roster__works">
        <p className="roster__works-lbl">{lang === "es" ? "Obra destacada" : "Highlighted work"}</p>
        <ul className="roster__works-grid">
          {highlights.map((w) => (
            <li key={w.slug}>
              <button type="button" className="roster__work" onClick={() => go({ name: "artwork", id: w.slug })} aria-label={bi(w.title, lang)}>
                <ArtImage src={w.primary_image?.url} alt={bi(w.title, lang)} ratio="3 / 4" variant="thumb" />
                <span className="roster__work-meta">
                  <span className="roster__work-title"><em>{bi(w.title, lang)}</em>, {w.year}</span>
                  {w.featured && <span className="roster__work-flag">{t("featured_tag")}</span>}
                </span>
              </button>
            </li>
          ))}
          {Array.from({ length: Math.max(0, 3 - highlights.length) }).map((_, k) => (
            <li key={`ph-${k}`} className="roster__work-placeholder" aria-hidden="true" />
          ))}
        </ul>
      </div>
    </li>
  );
}

export function Artists() {
  const { lang, t } = useLang();
  const go = useGo();
  useSeoPage("artists");
  const { loading, error, data, reload } = useFetch(() => Public.artists(), []);
  const artists = data ? (data.results || data) : [];

  return (
    <main className="screen artists">
      <Crumbs items={[
        { label: t("breadcrumb_home"), onClick: () => go({ name: "home" }) },
        { label: t("nav_artists") },
      ]} />
      <header className="page-head">
        <p className="page-head__eyebrow">Roster</p>
        <h1>{t("section_artists")}</h1>
        <p className="page-head__sub">
          {lang === "es"
            ? "Artistas radicados en la Ciudad de México."
            : "Artists based in Mexico City."}
        </p>
      </header>

      {loading ? (
        <Loading />
      ) : error ? (
        <ErrorState onRetry={reload} />
      ) : artists.length === 0 ? (
        <EmptyState title={t("empty_t")} body={t("empty_b")} />
      ) : (
        <ol className="roster">
          {artists.map((a, i) => <RosterRow key={a.slug} artist={a} index={i} />)}
        </ol>
      )}
    </main>
  );
}
