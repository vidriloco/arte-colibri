import React from "react";
import { useParams } from "react-router-dom";
import { useLang, bi } from "../i18n.jsx";
import { useGo } from "../nav.js";
import { Public } from "../api.js";
import { useFetch } from "../hooks.js";
import { ArtworkCard, SectionHead, Crumbs, Loading } from "../components/primitives.jsx";
import { useHead } from "../head.js";

export function Artist() {
  const { slug } = useParams();
  const { lang, t } = useLang();
  const go = useGo();
  const { loading, error, data: artist } = useFetch(() => Public.artist(slug), [slug]);

  useHead(
    artist
      ? {
          title: `${artist.display_name} · Arte Colibrí`,
          description: bi(artist.bio, lang),
          image: artist.avatar || "",
        }
      : null
  );

  if (loading) return <main className="screen artist"><Loading /></main>;
  if (error || !artist) {
    return (
      <main className="screen not-found">
        <div className="empty-state">
          <h1>404</h1>
          <button type="button" className="btn btn--primary" onClick={() => go({ name: "artists" })}>
            {t("nav_artists")}
          </button>
        </div>
      </main>
    );
  }

  const works = artist.works || [];
  const firstName = artist.display_name.split(" ")[0];

  return (
    <main className="screen artist">
      <Crumbs items={[
        { label: t("breadcrumb_home"), onClick: () => go({ name: "home" }) },
        { label: t("nav_artists"), onClick: () => go({ name: "artists" }) },
        { label: artist.display_name },
      ]} />

      <section className="artist__head">
        <div className="artist__avatar" aria-hidden="true"><span>{artist.initials}</span></div>
        <div className="artist__id">
          <p className="artist__eyebrow">{bi(artist.discipline, lang)}</p>
          <h1>{artist.display_name}</h1>
          <p className="artist__loc">{t("based_in")} {artist.city}, CDMX</p>
        </div>
        <div className="artist__stats">
          <div>
            <span className="stat__n">{works.length}</span>
            <span className="stat__l">{lang === "es" ? "obras publicadas" : "published works"}</span>
          </div>
          {artist.since && (
            <div>
              <span className="stat__n">{artist.since}</span>
              <span className="stat__l">{t("since")}</span>
            </div>
          )}
        </div>
      </section>

      <section className="artist__body">
        <div className="artist__statement">
          <h2>{t("statement")}</h2>
          <p>{bi(artist.bio, lang)}</p>
        </div>
        <aside className="artist__links">
          <h3>{t("links")}</h3>
          <ul>
            {artist.web && (
              <li>
                <span className="artist__link-k">{t("web")}</span>
                <a href="#" onClick={(e) => e.preventDefault()}>{artist.web}</a>
              </li>
            )}
            {artist.instagram && (
              <li>
                <span className="artist__link-k">{t("instagram")}</span>
                <a href="#" onClick={(e) => e.preventDefault()}>{artist.instagram}</a>
              </li>
            )}
          </ul>
        </aside>
      </section>

      <SectionHead title={`${t("works_by")} ${firstName}`} />
      <section className="grid grid--3 grid--regular">
        {works.map((w) => <ArtworkCard key={w.slug} work={w} />)}
      </section>
    </main>
  );
}
