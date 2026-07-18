import React from "react";
import { useLang, bi } from "../i18n.jsx";
import { useGo } from "../nav.js";
import { Public } from "../api.js";
import { useFetch } from "../hooks.js";
import { ArtworkCard, Crumbs, Loading, ErrorState, EmptyState } from "../components/primitives.jsx";
import { MiniMap } from "../components/MiniMap.jsx";
import { useSeoPage } from "../head.js";

export function Locations() {
  const { lang, t } = useLang();
  const go = useGo();
  useSeoPage("locations");
  const { loading, error, data, reload } = useFetch(() => Public.locations(), []);
  const artists = useFetch(() => Public.artists(), []);

  const artistMarkers = ((artists.data?.results || artists.data || []) || [])
    .filter((a) => a.location)
    .map((a) => ({
      ...a.location,
      label: `${a.display_name}${a.city ? ` · ${a.city}` : ""}`,
      onClick: () => go({ name: "artist", slug: a.slug }),
    }));

  // Deep-link support: scroll to #region-<slug> once data is in.
  React.useEffect(() => {
    if (!data) return;
    const hash = window.location.hash;
    if (hash) {
      const el = document.querySelector(hash);
      if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [data]);

  return (
    <main className="screen locations">
      <Crumbs items={[
        { label: t("breadcrumb_home"), onClick: () => go({ name: "home" }) },
        { label: t("nav_location") },
      ]} />
      <header className="page-head">
        <p className="page-head__eyebrow">{lang === "es" ? "Geografía" : "Geography"}</p>
        <h1>{t("section_locations")}</h1>
        <p className="page-head__sub">
          {lang === "es"
            ? "La colección agrupada por la colonia donde reside el artista."
            : "The collection grouped by the neighborhood where the artist resides."}
        </p>
      </header>

      {artistMarkers.length > 0 && (
        <div className="locations__map">
          <MiniMap markers={artistMarkers} height={380} />
        </div>
      )}

      {loading ? (
        <Loading />
      ) : error ? (
        <ErrorState onRetry={reload} />
      ) : data.length === 0 ? (
        <EmptyState title={t("empty_t")} body={t("empty_b")} />
      ) : (
        data.map((g) => {
          const names = Array.from(new Set(g.works.map((w) => w.artist_name))).join(" · ");
          return (
            <section key={g.slug} className="loc-group" id={`region-${g.slug}`}>
              <div className="loc-group__head">
                <div>
                  <h2>{bi(g.name, lang)}</h2>
                  <p>{g.count} {t("region_count")} · {names}</p>
                </div>
                <button type="button" className="section-head__action" onClick={() => go({ name: "gallery" })}>
                  {lang === "es" ? "Ver todas" : "View all"} <span aria-hidden="true">→</span>
                </button>
              </div>
              <div className="grid grid--3 grid--regular">
                {g.works.map((w) => <ArtworkCard key={w.slug} work={w} />)}
              </div>
            </section>
          );
        })
      )}
    </main>
  );
}
