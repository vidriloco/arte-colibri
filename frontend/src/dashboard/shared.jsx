import React from "react";
import { useLang } from "../i18n.jsx";

const STATUS_KEY = {
  draft: "md_status_draft",
  submitted: "md_status_submitted",
  published: "md_status_published",
  rejected: "md_status_rejected",
};

export function ModStatusBadge({ status }) {
  const { t } = useLang();
  return <span className={`mod-badge mod-badge--${status}`}>{t(STATUS_KEY[status] || status)}</span>;
}

export function DashTabs({ tabs, active, onChange }) {
  return (
    <nav className="dash-tabs" aria-label="Dashboard sections">
      {tabs.map((tab) => (
        <button
          key={tab.key}
          type="button"
          className={"dash-tab" + (active === tab.key ? " is-active" : "")}
          onClick={() => onChange(tab.key)}>
          {tab.label}
          {typeof tab.count === "number" && <span className="dash-tab__count">{tab.count}</span>}
        </button>
      ))}
    </nav>
  );
}

// Inline reject control: reveals a notes field, requires notes to confirm.
export function RejectControl({ onReject }) {
  const { t } = useLang();
  const [open, setOpen] = React.useState(false);
  const [notes, setNotes] = React.useState("");
  if (!open) {
    return (
      <button type="button" className="btn btn--ghost btn--sm" onClick={() => setOpen(true)}>
        {t("md_reject")}
      </button>
    );
  }
  return (
    <div className="reject-box">
      <textarea rows={2} placeholder={t("md_reject_notes")} value={notes} onChange={(e) => setNotes(e.target.value)} />
      <div className="reject-box__actions">
        <button type="button" className="btn btn--ghost btn--sm" onClick={() => { setOpen(false); setNotes(""); }}>
          {t("form_cancel")}
        </button>
        <button type="button" className="btn btn--primary btn--sm" disabled={!notes.trim()}
                onClick={() => onReject(notes.trim())}>
          {t("md_reject")}
        </button>
      </div>
    </div>
  );
}
