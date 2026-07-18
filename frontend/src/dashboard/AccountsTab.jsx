// Curator accounts admin: every artist account, their submitted artwork, and
// a per-account password reset. Curator-only (mounted from CuratorDashboard).
import React from "react";
import { useLang, bi } from "../i18n.jsx";
import { Curation } from "../api.js";
import { useFetch } from "../hooks.js";
import { ArtImage, Loading, ErrorState, EmptyState } from "../components/primitives.jsx";
import { ResetPasswordModal } from "../components/ResetPasswordModal.jsx";
import { ModStatusBadge } from "./shared.jsx";

const FILTERS = ["all", "submitted", "published", "draft", "rejected"];
const STATUS_LABEL = {
  submitted: "md_status_submitted",
  published: "md_status_published",
  draft: "md_status_draft",
  rejected: "md_status_rejected",
};

// Password reset: the button opens a modal where the curator types the new
// password and its confirmation; a ✓ replaces it once the reset succeeds.
function ResetPasswordControl({ artist }) {
  const { t } = useLang();
  const [open, setOpen] = React.useState(false);
  const [done, setDone] = React.useState(false);

  if (!artist.has_account) {
    return <span className="acct__noacct">{t("md_acct_no_account")}</span>;
  }
  if (done) {
    return <span className="acct__pwok">✓ {t("md_acct_pw_done")}</span>;
  }
  return (
    <>
      <button type="button" className="btn btn--ghost btn--sm" onClick={() => setOpen(true)}>
        {t("md_acct_reset_pw")}
      </button>
      {open && (
        <ResetPasswordModal
          artist={artist}
          onClose={() => setOpen(false)}
          onDone={() => { setDone(true); setOpen(false); }}
        />
      )}
    </>
  );
}

function AccountCard({ artist }) {
  const { lang, t } = useLang();
  const [openWorks, setOpenWorks] = React.useState(false);
  const works = artist.works || [];
  return (
    <li className="acct">
      <div className="acct__head">
        <div className="acct__avatar" aria-hidden="true">
          {artist.avatar ? <img src={artist.avatar} alt="" /> : <span>{artist.initials}</span>}
        </div>
        <div className="acct__id">
          <h3 className="acct__name">{artist.display_name}</h3>
          <p className="acct__email">
            {artist.email ? (
              <a href={`mailto:${artist.email}`}>{artist.email}</a>
            ) : (
              <span className="acct__noacct">{t("md_acct_no_account")}</span>
            )}
          </p>
          <p className="acct__meta">
            {artist.date_joined && (
              <span>{t("md_acct_joined")} {new Date(artist.date_joined).toLocaleDateString()}</span>
            )}
            <span>· {artist.works_count} {t("works")}</span>
          </p>
        </div>
        <ModStatusBadge status={artist.status} />
        <div className="acct__actions">
          <ResetPasswordControl artist={artist} />
        </div>
      </div>

      {works.length > 0 && (
        <div className="acct__works-wrap">
          <button type="button" className="acct__toggle" onClick={() => setOpenWorks((v) => !v)}>
            {openWorks
              ? t("md_acct_hide_works")
              : `${t("md_acct_view_works")} (${works.length})`}
          </button>
          {openWorks && (
            <ul className="acct__works">
              {works.map((w) => (
                <li key={w.slug} className="acct__work">
                  <ArtImage
                    src={w.images?.[0]?.thumb}
                    alt={bi(w.title, lang)}
                    ratio="1 / 1"
                    variant="thumb"
                  />
                  <span className="acct__work-title"><em>{bi(w.title, lang)}</em></span>
                  <ModStatusBadge status={w.status} />
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </li>
  );
}

export function AccountsTab() {
  const { t } = useLang();
  const [filter, setFilter] = React.useState("all");
  const { loading, error, data, reload } = useFetch(
    () => Curation.artistsAdmin(filter === "all" ? null : filter),
    [filter]
  );

  return (
    <div className="dash-panel">
      <div className="dash-panel__head">
        <h2>{t("md_accounts")}</h2>
      </div>
      <div className="acct-filters">
        {FILTERS.map((f) => (
          <button
            key={f}
            type="button"
            className={"chip" + (filter === f ? " is-active" : "")}
            onClick={() => setFilter(f)}>
            {f === "all" ? t("md_acct_all") : t(STATUS_LABEL[f])}
          </button>
        ))}
      </div>
      {loading ? (
        <Loading />
      ) : error ? (
        <ErrorState onRetry={reload} />
      ) : (data || []).length === 0 ? (
        <EmptyState title={t("md_acct_empty")} />
      ) : (
        <ul className="acct-list">
          {data.map((a) => <AccountCard key={a.id} artist={a} />)}
        </ul>
      )}
    </div>
  );
}
