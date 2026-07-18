import React from "react";
import { useLang, bi, formatPrice } from "../i18n.jsx";
import { useAuth } from "../auth.jsx";
import { Curation } from "../api.js";
import { useFetch } from "../hooks.js";
import { ArtImage, Loading, ErrorState, EmptyState } from "../components/primitives.jsx";
import { ModStatusBadge, DashTabs, RejectControl } from "./shared.jsx";
import { SeoTab } from "./SeoTab.jsx";

function ReviewRow({ work, onApprove, onReject }) {
  const { lang, t } = useLang();
  return (
    <li className="dash-work">
      <div className="dash-work__thumb">
        <ArtImage src={work.images?.[0]?.thumb} alt={bi(work.title, lang)} ratio="1 / 1" variant="thumb" />
      </div>
      <div className="dash-work__meta">
        <h3 className="dash-work__title"><em>{bi(work.title, lang)}</em>, {work.year}</h3>
        <p className="dash-work__sub">{work.artist_name} · {formatPrice(work.price, lang, work.currency)}</p>
      </div>
      <ModStatusBadge status={work.status} />
      <div className="dash-work__actions">
        <button type="button" className="btn btn--primary btn--sm" onClick={() => onApprove(work)}>{t("md_approve")}</button>
        <RejectControl onReject={(notes) => onReject(work, notes)} />
      </div>
    </li>
  );
}

function QueueTab() {
  const { t } = useLang();
  const { loading, error, data, reload } = useFetch(() => Curation.queue(), []);
  if (loading) return <Loading />;
  if (error) return <ErrorState onRetry={reload} />;
  const arts = data.artworks || [];
  const profiles = data.artists || [];
  if (arts.length === 0 && profiles.length === 0) {
    return <div className="dash-panel"><EmptyState title={t("md_queue_empty")} /></div>;
  }
  return (
    <div className="dash-panel">
      <h2>{t("md_review_queue")}</h2>
      <ul className="dash-works">
        {arts.map((w) => (
          <ReviewRow key={w.slug} work={w}
            onApprove={async (work) => { await Curation.approveArtwork(work.id); reload(); }}
            onReject={async (work, notes) => { await Curation.rejectArtwork(work.id, notes); reload(); }}
          />
        ))}
      </ul>
      {profiles.length > 0 && (
        <>
          <h2 style={{ marginTop: 32 }}>{t("nav_artists")}</h2>
          <ul className="dash-works">
            {profiles.map((a) => (
              <li key={a.slug} className="dash-work">
                <div className="dash-work__meta">
                  <h3 className="dash-work__title">{a.display_name}</h3>
                  <p className="dash-work__sub">{bi(a.bio, "es")?.slice(0, 90)}</p>
                </div>
                <ModStatusBadge status={a.status} />
                <div className="dash-work__actions">
                  <button type="button" className="btn btn--primary btn--sm" onClick={async () => { await Curation.approveArtist(a.id); reload(); }}>{t("md_approve")}</button>
                  <RejectControl onReject={async (notes) => { await Curation.rejectArtist(a.id, notes); reload(); }} />
                </div>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}

function AllWorksTab() {
  const { lang, t } = useLang();
  const { loading, error, data, reload } = useFetch(() => Curation.allArtworks(), []);
  if (loading) return <Loading />;
  if (error) return <ErrorState onRetry={reload} />;
  if (data.length === 0) return <div className="dash-panel"><EmptyState title={t("md_no_works")} /></div>;
  return (
    <div className="dash-panel">
      <h2>{t("md_all_works")}</h2>
      <ul className="dash-works">
        {data.map((w) => (
          <li key={w.slug} className="dash-work">
            <div className="dash-work__thumb">
              <ArtImage src={w.images?.[0]?.thumb} alt={bi(w.title, lang)} ratio="1 / 1" variant="thumb" />
            </div>
            <div className="dash-work__meta">
              <h3 className="dash-work__title"><em>{bi(w.title, lang)}</em>, {w.year}</h3>
              <p className="dash-work__sub">{w.artist_name}</p>
            </div>
            <ModStatusBadge status={w.status} />
            <div className="dash-work__actions">
              {w.status === "published" && (
                <button type="button" className={"btn btn--sm " + (w.featured ? "btn--primary" : "btn--ghost")}
                        onClick={async () => { await Curation.featureArtwork(w.id); reload(); }}>
                  {w.featured ? t("md_unfeature") : t("md_feature")}
                </button>
              )}
              {w.status === "submitted" && (
                <button type="button" className="btn btn--primary btn--sm"
                        onClick={async () => { await Curation.approveArtwork(w.id); reload(); }}>
                  {t("md_approve")}
                </button>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

function InquiriesTab() {
  const { lang, t } = useLang();
  const { loading, error, data, reload } = useFetch(() => Curation.inquiries(), []);
  if (loading) return <Loading />;
  if (error) return <ErrorState onRetry={reload} />;
  if (data.length === 0) return <div className="dash-panel"><EmptyState title={t("md_no_inquiries")} /></div>;
  return (
    <div className="dash-panel">
      <h2>{t("md_inquiries")}</h2>
      <ul className="inbox">
        {data.map((q) => (
          <li key={q.id} className="inbox__item">
            <div className="inbox__top">
              <span className="inbox__work">{bi(q.artwork_title, lang)}</span>
              <span className="inbox__date">{new Date(q.created_at).toLocaleDateString()}</span>
            </div>
            <p className="inbox__from">{q.name} · <a href={`mailto:${q.email}`}>{q.email}</a></p>
            <p className="inbox__msg">{q.message}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function CuratorDashboard() {
  const { t } = useLang();
  const { user } = useAuth();
  const [tab, setTab] = React.useState("queue");
  return (
    <main className="screen dash-screen">
      <header className="dash-header">
        <p className="page-head__eyebrow">{t("md_curator_panel")}</p>
        <h1>{user?.name}</h1>
      </header>
      <DashTabs
        active={tab}
        onChange={setTab}
        tabs={[
          { key: "queue", label: t("md_review_queue") },
          { key: "works", label: t("md_all_works") },
          { key: "inquiries", label: t("md_inquiries") },
          { key: "seo", label: t("md_seo") },
        ]}
      />
      {tab === "queue" && <QueueTab />}
      {tab === "works" && <AllWorksTab />}
      {tab === "inquiries" && <InquiriesTab />}
      {tab === "seo" && <SeoTab />}
    </main>
  );
}
