import React from "react";
import { useLang, bi } from "../i18n.jsx";
import { useGo } from "../nav.js";
import { ArtImage } from "./primitives.jsx";

// Full-bleed landing hero: artwork image as background, brand name on top,
// current artwork title + 2 metadata fragments below.
export function ShowcaseCarousel({ works }) {
  const { lang, t } = useLang();
  const go = useGo();
  const [idx, setIdx] = React.useState(0);
  const [paused, setPaused] = React.useState(false);
  const total = works.length;

  const goTo = React.useCallback((n) => setIdx(((n % total) + total) % total), [total]);
  const next = React.useCallback(() => goTo(idx + 1), [idx, goTo]);
  const prev = React.useCallback(() => goTo(idx - 1), [idx, goTo]);

  React.useEffect(() => {
    if (paused || total <= 1) return;
    const id = window.setInterval(() => setIdx((i) => (i + 1) % total), 6500);
    return () => window.clearInterval(id);
  }, [paused, total]);

  React.useEffect(() => {
    const onKey = (e) => {
      if (e.key === "ArrowLeft") prev();
      if (e.key === "ArrowRight") next();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [next, prev]);

  if (!total) return null;
  const cur = works[idx];

  return (
    <section
      className="showcase"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      aria-roledescription="carousel"
      aria-label={lang === "es" ? "Adquisiciones recientes" : "Recent acquisitions"}>
      <div className="showcase__bg" aria-hidden="true">
        {works.map((w, i) => (
          <div key={w.slug} className={"showcase__bg-slide" + (i === idx ? " is-active" : "")}>
            <ArtImage src={w.primary_image?.url} alt="" ratio="auto" variant="bg" />
          </div>
        ))}
        <div className="showcase__scrim" />
      </div>

      <div className="showcase__brand">
        <p className="showcase__brand-eyebrow">
          <span className="showcase__dot" />
          {lang === "es" ? "Galería digital · CDMX" : "Digital gallery · CDMX"}
        </p>
        <h1 className="showcase__brand-name">Arte Colibrí</h1>
        <p className="showcase__brand-tag">{t("tagline")}</p>
      </div>

      <div className="showcase__caption">
        <div className="showcase__caption-text" key={`c-${cur.slug}`}>
          <p className="showcase__caption-eyebrow">
            {lang === "es" ? "En exhibición" : "Now showing"}
          </p>
          <button
            type="button"
            className="showcase__caption-title"
            onClick={() => go({ name: "artwork", id: cur.slug })}>
            <em>{bi(cur.title, lang)}</em>
            <span className="showcase__caption-year">, {cur.year}</span>
          </button>
          <div className="showcase__caption-frags">
            <button
              type="button"
              className="showcase__frag"
              onClick={(e) => { e.stopPropagation(); go({ name: "artist", id: cur.artist_slug }); }}>
              <span className="showcase__frag-k">{lang === "es" ? "Artista" : "Artist"}</span>
              <span className="showcase__frag-v">{cur.artist_name}</span>
            </button>
            <span className="showcase__frag-sep" aria-hidden="true" />
            <div className="showcase__frag">
              <span className="showcase__frag-k">{t("medium")}</span>
              <span className="showcase__frag-v">{bi(cur.medium, lang)}</span>
            </div>
          </div>
        </div>

        <div className="showcase__nav">
          <span className="showcase__count" aria-live="polite">
            <span className="showcase__count-cur">{String(idx + 1).padStart(2, "0")}</span>
            <span className="showcase__count-sep" aria-hidden="true">/</span>
            <span className="showcase__count-tot">{String(total).padStart(2, "0")}</span>
          </span>
          <div className="showcase__arrows">
            <button type="button" className="showcase__arrow" onClick={prev} aria-label={t("prev")}>
              <svg width="22" height="22" viewBox="0 0 22 22" aria-hidden="true">
                <path d="M14 4 L7 11 L14 18" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>
            <button type="button" className="showcase__arrow" onClick={next} aria-label={t("next")}>
              <svg width="22" height="22" viewBox="0 0 22 22" aria-hidden="true">
                <path d="M8 4 L15 11 L8 18" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      <ol className="showcase__ticks" role="tablist">
        {works.map((w, i) => (
          <li key={w.slug}>
            <button
              type="button"
              className={"showcase__tick" + (i === idx ? " is-active" : "")}
              onClick={() => goTo(i)}
              role="tab"
              aria-selected={i === idx}
              aria-label={bi(w.title, lang)}>
              <span className="showcase__tick-num">{String(i + 1).padStart(2, "0")}</span>
              <span className="showcase__tick-bar">
                {i === idx && !paused && <span className="showcase__tick-fill" />}
              </span>
            </button>
          </li>
        ))}
      </ol>
    </section>
  );
}
