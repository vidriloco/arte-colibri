import React from "react";
import { useLang, bi } from "../i18n.jsx";
import { useGo } from "../nav.js";
import { Public } from "../api.js";
import { useFetch } from "../hooks.js";
import {
  ArtImage, ArtworkCard, SectionHead, Loading, ErrorState, EmptyState,
} from "../components/primitives.jsx";
import { ShowcaseCarousel } from "../components/ShowcaseCarousel.jsx";
import { useSeoPage } from "../head.js";

function Hero({ stats }) {
  const { lang, t } = useLang();
  const go = useGo();
  return (
    <section className="hero">
      <div className="hero__inner">
        <p className="hero__eyebrow">
          <span className="hero__dot" />
          {lang === "es" ? "Galería digital · CDMX" : "Digital gallery · CDMX"}
        </p>
        <h1 className="hero__title">{t("tagline")}</h1>
        <p className="hero__sub">{t("sub")}</p>
        <div className="hero__cta">
          <button type="button" className="btn btn--primary" onClick={() => go({ name: "gallery" })}>
            {t("cta_browse")}<span className="btn__arrow" aria-hidden="true">→</span>
          </button>
          <button type="button" className="btn btn--ghost" onClick={() => go({ name: "locations" })}>
            {t("cta_locations")}
          </button>
        </div>
      </div>
      <aside className="hero__meta">
        <div>
          <span className="hero__meta-num">{stats.artists}</span>
          <span className="hero__meta-lbl">{lang === "es" ? "Artistas" : "Artists"}</span>
        </div>
        <div>
          <span className="hero__meta-num">{stats.works}</span>
          <span className="hero__meta-lbl">{lang === "es" ? "Obras" : "Works"}</span>
        </div>
        <div>
          <span className="hero__meta-num">{stats.regions}</span>
          <span className="hero__meta-lbl">{lang === "es" ? "Zonas" : "Regions"}</span>
        </div>
      </aside>
    </section>
  );
}

function HomeEditorial({ featured, recent }) {
  const { lang, t } = useLang();
  const go = useGo();
  const hero = featured[0];
  if (!hero) return null;
  return (
    <>
      <SectionHead title={t("section_featured")} action={t("cta_browse")} onAction={() => go({ name: "gallery" })} />
      <section className="home-ed">
        <article className="home-ed__hero" onClick={() => go({ name: "artwork", id: hero.slug })}>
          <ArtImage src={hero.primary_image?.url} alt={bi(hero.title, lang)} ratio="4 / 5" variant="hero" />
          <span className="home-ed__hero-tag">{t("featured_tag")}</span>
        </article>
        <div className="home-ed__caption">
          <p className="caption__eyebrow">{t("featured_tag")}</p>
          <h3 className="caption__title"><em>{bi(hero.title, lang)}</em>, {hero.year}</h3>
          <p className="caption__artist">{hero.artist_name}</p>
          <p className="caption__meta">{bi(hero.medium, lang)} · {hero.dimensions}</p>
          <p className="caption__desc">{bi(hero.description, lang)}</p>
          <button type="button" className="btn btn--primary" onClick={() => go({ name: "artwork", id: hero.slug })}>
            {t("cta_view")}<span className="btn__arrow" aria-hidden="true">→</span>
          </button>
        </div>
        <div className="home-ed__grid">
          {featured.slice(1, 4).map((w) => (
            <ArtworkCard key={w.slug} work={w} variant="bare" />
          ))}
        </div>
      </section>

      <SectionHead title={t("section_recent")} action={t("cta_browse")} onAction={() => go({ name: "gallery" })} />
      <section className="grid grid--4 grid--regular">
        {recent.map((w) => <ArtworkCard key={w.slug} work={w} />)}
      </section>
    </>
  );
}

function LocationsTeaser() {
  const { lang, t } = useLang();
  const go = useGo();
  const { data } = useFetch(() => Public.locations(), []);
  if (!data || data.length === 0) return null;
  return (
    <section className="loc-teaser">
      <SectionHead title={t("section_locations")} action={t("cta_locations")} onAction={() => go({ name: "locations" })} />
      <ul className="loc-teaser__grid">
        {data.map((r) => (
          <li key={r.slug}>
            <button type="button" className="loc-teaser__card" onClick={() => go({ name: "locations", region: r.slug })}>
              <span className="loc-teaser__name">{bi(r.name, lang)}</span>
              <span className="loc-teaser__count">{r.count} {t("region_count")}</span>
              <span className="loc-teaser__arrow" aria-hidden="true">→</span>
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}

export function Home() {
  const { t } = useLang();
  useSeoPage("home");
  const { loading, error, data, reload } = useFetch(() => Public.home(), []);

  if (loading) return <main className="screen home"><Loading /></main>;
  if (error) return <main className="screen home"><ErrorState onRetry={reload} /></main>;

  const empty = data.featured.length === 0 && data.recent.length === 0;

  return (
    <main className="screen home">
      {data.carousel.length > 0 && <ShowcaseCarousel works={data.carousel} />}
      <Hero stats={data.stats} />
      {empty ? (
        <EmptyState title={t("empty_t")} body={t("empty_b")} />
      ) : (
        <>
          <HomeEditorial featured={data.featured} recent={data.recent} />
          <LocationsTeaser />
        </>
      )}
    </main>
  );
}
