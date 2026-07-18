import React from "react";
import { useLang, bi, formatPrice } from "../i18n.jsx";
import { useAuth } from "../auth.jsx";
import { Dash } from "../api.js";
import { useFetch } from "../hooks.js";
import { ArtImage, Loading, ErrorState, EmptyState } from "../components/primitives.jsx";
import { ArtworkForm, ProfileForm } from "../components/forms.jsx";
import { ModStatusBadge, DashTabs } from "./shared.jsx";

function WorkRow({ work, onEdit, onSubmit, onDelete }) {
  const { lang, t } = useLang();
  const canSubmit = work.status === "draft" || work.status === "rejected";
  return (
    <li className="dash-work">
      <div className="dash-work__thumb">
        <ArtImage src={work.images?.[0]?.thumb} alt={bi(work.title, lang)} ratio="1 / 1" variant="thumb" />
      </div>
      <div className="dash-work__meta">
        <h3 className="dash-work__title"><em>{bi(work.title, lang)}</em>, {work.year}</h3>
        <p className="dash-work__sub">
          {formatPrice(work.price, lang, work.currency)} · {work.dimensions}
        </p>
        {work.status === "rejected" && work.review_notes && (
          <p className="dash-work__notes">{t("md_review_notes_label")}: {work.review_notes}</p>
        )}
      </div>
      <ModStatusBadge status={work.status} />
      <div className="dash-work__actions">
        <button type="button" className="btn btn--ghost btn--sm" onClick={() => onEdit(work)}>{t("md_edit")}</button>
        {canSubmit && (
          <button type="button" className="btn btn--primary btn--sm" onClick={() => onSubmit(work)}>{t("md_submit_review")}</button>
        )}
        <button type="button" className="dash-work__del" onClick={() => onDelete(work)} aria-label={t("md_delete")}>✕</button>
      </div>
    </li>
  );
}

function WorksTab() {
  const { t } = useLang();
  const { loading, error, data, reload } = useFetch(() => Dash.artworks(), []);
  const [editing, setEditing] = React.useState(null); // 'new' | work | null

  if (editing) {
    return (
      <div className="dash-panel">
        <button type="button" className="apply__back" onClick={() => setEditing(null)}>
          <span aria-hidden="true">←</span><span>{t("apply_back")}</span>
        </button>
        <ArtworkForm
          artwork={editing === "new" ? null : editing}
          submitLabel={t("md_save")}
          onSaved={() => { setEditing(null); reload(); }}
        />
      </div>
    );
  }

  if (loading) return <Loading />;
  if (error) return <ErrorState onRetry={reload} />;
  const works = data.results || data;

  return (
    <div className="dash-panel">
      <div className="dash-panel__head">
        <h2>{t("md_my_works")}</h2>
        <button type="button" className="btn btn--primary btn--sm" onClick={() => setEditing("new")}>
          + {t("md_new_work")}
        </button>
      </div>
      {works.length === 0 ? (
        <EmptyState title={t("md_no_works")}>
          <button type="button" className="btn btn--primary" onClick={() => setEditing("new")}>{t("md_new_work")}</button>
        </EmptyState>
      ) : (
        <ul className="dash-works">
          {works.map((w) => (
            <WorkRow key={w.id} work={w}
              onEdit={setEditing}
              onSubmit={async (work) => { await Dash.submitArtwork(work.id); reload(); }}
              onDelete={async (work) => { await Dash.deleteArtwork(work.id); reload(); }}
            />
          ))}
        </ul>
      )}
    </div>
  );
}

function ProfileTab() {
  const { t } = useLang();
  const { user, refresh } = useAuth();
  const { loading, error, data, reload } = useFetch(() => Dash.profile(), []);
  if (loading) return <Loading />;
  if (error) return <ErrorState onRetry={reload} />;
  return (
    <div className="dash-panel">
      <div className="dash-panel__head">
        <h2>{t("md_profile")}</h2>
        <ModStatusBadge status={data.status} />
      </div>
      <ProfileForm
        artist={data}
        submitLabel={t("md_save")}
        onSaved={async () => { await Dash.submitProfile(); await refresh(); reload(); }}
      />
    </div>
  );
}

function InquiriesTab() {
  const { lang, t } = useLang();
  const { loading, error, data, reload } = useFetch(() => Dash.inquiries(), []);
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

export function ArtistDashboard() {
  const { t } = useLang();
  const { user } = useAuth();
  const [tab, setTab] = React.useState("works");
  return (
    <main className="screen dash-screen">
      <header className="dash-header">
        <p className="page-head__eyebrow">{t("md_artist_panel")}</p>
        <h1>{user?.name}</h1>
      </header>
      <DashTabs
        active={tab}
        onChange={setTab}
        tabs={[
          { key: "works", label: t("md_my_works") },
          { key: "profile", label: t("md_profile") },
          { key: "inquiries", label: t("md_inquiries") },
        ]}
      />
      {tab === "works" && <WorksTab />}
      {tab === "profile" && <ProfileTab />}
      {tab === "inquiries" && <InquiriesTab />}
    </main>
  );
}
