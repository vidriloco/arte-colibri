import React from "react";
import { useParams } from "react-router-dom";
import { useLang, bi, formatPrice, tagLabel } from "../i18n.jsx";
import { useGo } from "../nav.js";
import { Public } from "../api.js";
import { useFetch } from "../hooks.js";
import {
  ArtImage, AvailabilityBadge, ArtworkCard, SectionHead, Crumbs, Loading,
} from "../components/primitives.jsx";
import { InquiryModal } from "../components/InquiryModal.jsx";
import { useHead } from "../head.js";

export function ArtworkDetail() {
  const { slug } = useParams();
  const { lang, t } = useLang();
  const go = useGo();
  const [idx, setIdx] = React.useState(0);
  const [modal, setModal] = React.useState(false);

  const { loading, error, data: work } = useFetch(() => Public.artwork(slug), [slug]);
  React.useEffect(() => { setIdx(0); }, [slug]);

  // Other works by the same artist (fetched once the artwork is known).
  const others = useFetch(
    () => (work ? Public.artist(work.artist.slug) : Promise.resolve(null)),
    [work?.artist?.slug]
  );

  useHead(
    work
      ? {
          title: `${bi(work.title, lang)} · ${work.artist.display_name} · Arte Colibrí`,
          description: bi(work.description, lang),
          image: work.images?.[0]?.url || "",
          robots: "index,follow",
        }
      : null
  );

  if (loading) return <main className="screen detail"><Loading /></main>;

  if (error || !work) {
    return (
      <main className="screen not-found">
        <Crumbs items={[
          { label: t("breadcrumb_home"), onClick: () => go({ name: "home" }) },
          { label: "404" },
        ]} />
        <div className="empty-state">
          <h1>{t("not_found_t")}</h1>
          <p>{t("not_found_b")}</p>
          <button type="button" className="btn btn--primary" onClick={() => go({ name: "gallery" })}>
            {t("back_gallery")}
          </button>
        </div>
      </main>
    );
  }

  const artist = work.artist;
  const sold = work.availability === "sold";
  const otherWorks = (others.data?.works || []).filter((w) => w.slug !== work.slug).slice(0, 4);

  return (
    <main className="screen detail">
      <Crumbs items={[
        { label: t("breadcrumb_home"), onClick: () => go({ name: "home" }) },
        { label: t("nav_gallery"), onClick: () => go({ name: "gallery" }) },
        { label: bi(work.title, lang) },
      ]} />

      <section className="detail__top">
        <div className="detail__images">
          <div className="detail__primary">
            <ArtImage key={idx} src={work.images[idx]?.url} alt={bi(work.title, lang)} ratio="4 / 5" variant="primary" />
            {work.featured && <span className="card__featured detail__featured">{t("featured_tag")}</span>}
          </div>
          {work.images.length > 1 && (
            <ol className="detail__thumbs">
              {work.images.map((img, i) => (
                <li key={img.id}>
                  <button type="button" className={"detail__thumb" + (i === idx ? " is-active" : "")}
                          onClick={() => setIdx(i)} aria-label={`Image ${i + 1}`}>
                    <ArtImage src={img.thumb} alt={`${bi(work.title, lang)} (${i + 1})`} ratio="1 / 1" variant="thumb" />
                  </button>
                </li>
              ))}
            </ol>
          )}
        </div>

        <aside className="detail__info">
          <p className="detail__eyebrow">{bi(artist.discipline, lang)}</p>
          <h1 className="detail__title">
            <em>{bi(work.title, lang)}</em>
            <span className="detail__year">, {work.year}</span>
          </h1>
          <button type="button" className="detail__artist-link" onClick={() => go({ name: "artist", id: artist.slug })}>
            {artist.display_name}<span aria-hidden="true">→</span>
          </button>

          <dl className="detail__specs">
            <div><dt>{t("medium")}</dt><dd>{bi(work.medium, lang)}</dd></div>
            <div><dt>{t("dimensions")}</dt><dd>{work.dimensions}</dd></div>
            <div><dt>{t("year")}</dt><dd>{work.year}</dd></div>
            <div><dt>{t("location")}</dt><dd>{artist.city}, CDMX</dd></div>
          </dl>

          <div className="detail__price-row">
            <div>
              <p className="detail__price-lbl">{t("price")}</p>
              <p className="detail__price">
                {work.availability === "nfs" ? t("avail_nfs") : formatPrice(work.price, lang, work.currency)}
              </p>
            </div>
            <AvailabilityBadge availability={work.availability} />
          </div>

          <p className="detail__desc">{bi(work.description, lang)}</p>

          <div className="detail__cta">
            <button type="button" className="btn btn--primary btn--lg" disabled={sold} onClick={() => setModal(true)}>
              {sold ? t("avail_sold") : t("cta_inquire")}
            </button>
            <button type="button" className="btn btn--ghost btn--lg" onClick={() => go({ name: "artist", id: artist.slug })}>
              {t("view_profile")}
            </button>
          </div>

          {work.tags.length > 0 && (
            <ul className="detail__tags">
              {work.tags.map((tg) => (
                <li key={tg}>
                  <button type="button" onClick={() => go({ name: "gallery" })}>{tagLabel(tg, lang)}</button>
                </li>
              ))}
            </ul>
          )}
        </aside>
      </section>

      {otherWorks.length > 0 && (
        <>
          <SectionHead title={`${t("other_works")} ${artist.display_name}`}
                       action={t("view_profile")} onAction={() => go({ name: "artist", id: artist.slug })} />
          <section className="grid grid--4 grid--regular">
            {otherWorks.map((w) => <ArtworkCard key={w.slug} work={w} />)}
          </section>
        </>
      )}

      {modal && <InquiryModal work={work} onClose={() => setModal(false)} />}
    </main>
  );
}
