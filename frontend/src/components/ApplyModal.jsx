import React from "react";
import { useNavigate } from "react-router-dom";
import { useLang } from "../i18n.jsx";
import { useAuth } from "../auth.jsx";
import { Dash } from "../api.js";
import { ApplyField, ProfileForm, ArtworkForm } from "./forms.jsx";

function ApplyShell({ children, onClose }) {
  React.useEffect(() => {
    const onKey = (e) => e.key === "Escape" && onClose();
    document.addEventListener("keydown", onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = prev;
    };
  }, [onClose]);
  return (
    <div className="apply" role="dialog" aria-modal="true" aria-label="Apply">
      <div className="apply__scrim" onClick={onClose} />
      <div className="apply__panel">
        <button type="button" className="apply__close" onClick={onClose} aria-label="Close">✕</button>
        {children}
      </div>
    </div>
  );
}

function AccountPill({ user }) {
  const { t } = useLang();
  return (
    <div className="apply__pill" title={user?.email}>
      <span className="apply__pill-check" aria-hidden="true">✓</span>
      <span className="apply__pill-lbl">{t("acct_pill")}</span>
      <span className="apply__pill-sep" aria-hidden="true" />
      <span className="apply__pill-name">{user?.name}</span>
    </div>
  );
}

function AccountStep({ onDone, onClose }) {
  const { t } = useLang();
  const { signup } = useAuth();
  const [form, setForm] = React.useState({ name: "", email: "", password: "", confirm: "" });
  const [terms, setTerms] = React.useState(false);
  const [errors, setErrors] = React.useState({});
  const [busy, setBusy] = React.useState(false);
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const submit = async (e) => {
    e.preventDefault();
    const er = {};
    if (!form.name.trim()) er.name = t("form_required");
    if (!form.email.trim()) er.email = t("form_required");
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) er.email = t("form_email_invalid");
    if (!form.password) er.password = t("form_required");
    else if (form.password.length < 8) er.password = t("acct_password_short");
    if (form.confirm !== form.password) er.confirm = t("acct_password_mismatch");
    if (!terms) er.terms = t("acct_terms_required");
    setErrors(er);
    if (Object.keys(er).length || busy) return;
    setBusy(true);
    try {
      await signup({ name: form.name, email: form.email, password: form.password });
      onDone();
    } catch (err) {
      setErrors(err.data && typeof err.data === "object" ? err.data : { email: t("error_b") });
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <header className="apply__head apply__head--acct">
        <p className="apply__eyebrow">{t("acct_eyebrow")}</p>
        <h2 className="apply__title">{t("acct_title")}</h2>
        <p className="apply__sub">{t("acct_sub")}</p>
      </header>
      <form className="apply__form apply__form--acct" onSubmit={submit} noValidate>
        <ApplyField label={t("apply_full_name")} error={errors.name} required>
          <input type="text" autoFocus value={form.name} onChange={(e) => set("name", e.target.value)} />
        </ApplyField>
        <ApplyField label={t("apply_email")} error={errors.email} required>
          <input type="email" autoComplete="email" value={form.email} onChange={(e) => set("email", e.target.value)} />
        </ApplyField>
        <div className="apply__row apply__row--2">
          <ApplyField label={t("acct_password")} error={errors.password} hint={t("acct_password_hint")} required>
            <input type="password" autoComplete="new-password" value={form.password} onChange={(e) => set("password", e.target.value)} />
          </ApplyField>
          <ApplyField label={t("acct_password_confirm")} error={errors.confirm} required>
            <input type="password" autoComplete="new-password" value={form.confirm} onChange={(e) => set("confirm", e.target.value)} />
          </ApplyField>
        </div>
        <label className={"apply__terms" + (errors.terms ? " has-error" : "")}>
          <input type="checkbox" checked={terms} onChange={(e) => setTerms(e.target.checked)} />
          <span>{t("acct_terms")}</span>
        </label>
        {errors.terms && <span className="apply__err apply__err--acct">{errors.terms}</span>}
        <div className="apply__actions apply__actions--acct">
          <button type="button" className="btn btn--ghost" onClick={onClose}>{t("form_cancel")}</button>
          <button type="submit" className="btn btn--primary btn--lg" disabled={busy}>
            {t("acct_continue")}<span className="btn__arrow" aria-hidden="true">→</span>
          </button>
        </div>
      </form>
    </>
  );
}

function OnboardCard({ n, eyebrow, title, body, cta, done, onClick }) {
  const { t } = useLang();
  return (
    <li className={"dash__card" + (done ? " is-done" : "")}>
      <span className="dash__card-n" aria-hidden="true">{n}</span>
      <div className="dash__card-icon" aria-hidden="true">
        <svg viewBox="0 0 28 28" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
          <rect x="4" y="5" width="20" height="18" rx="1.5" /><circle cx="10" cy="12" r="2" /><path d="M24 19l-6-6-10 10" />
        </svg>
      </div>
      <div className="dash__card-text">
        <p className="dash__card-eyebrow">{eyebrow}{done && <span className="dash__card-flag">✓ {t("dash_card_done")}</span>}</p>
        <h3 className="dash__card-title">{title}</h3>
        <p className="dash__card-body">{body}</p>
      </div>
      <button type="button" className="dash__card-cta" onClick={onClick}>
        <span>{done ? t("dash_card_edit") : cta}</span>
        <span className="dash__card-arrow" aria-hidden="true">→</span>
      </button>
    </li>
  );
}

export function ApplyModal({ onClose }) {
  const { t } = useLang();
  const { user, refresh } = useAuth();
  const navigate = useNavigate();
  const [phase, setPhase] = React.useState("account");
  const [done, setDone] = React.useState({ profile: false, artwork: false });
  const [artworkId, setArtworkId] = React.useState(null);
  const [busy, setBusy] = React.useState(false);

  const canSubmit = done.profile && done.artwork;
  const total = (done.profile ? 1 : 0) + (done.artwork ? 1 : 0);

  const finish = async () => {
    if (!canSubmit || busy) return;
    setBusy(true);
    try {
      await Dash.submitProfile();
      if (artworkId) await Dash.submitArtwork(artworkId);
      await refresh();
      setPhase("success");
    } finally {
      setBusy(false);
    }
  };

  if (phase === "account") {
    return (
      <ApplyShell onClose={onClose}>
        <AccountStep onDone={() => setPhase("dashboard")} onClose={onClose} />
      </ApplyShell>
    );
  }

  if (phase === "profile") {
    return (
      <ApplyShell onClose={onClose}>
        <header className="apply__head apply__head--task">
          <button type="button" className="apply__back" onClick={() => setPhase("dashboard")}>
            <span aria-hidden="true">←</span><span>{t("apply_back")}</span>
          </button>
          <AccountPill user={user} />
          <p className="apply__eyebrow">{t("dash_card_profile_eyebrow")}</p>
          <h2 className="apply__title">{t("dash_card_profile_title")}</h2>
          <p className="apply__sub">{t("dash_card_profile_body")}</p>
        </header>
        <ProfileForm
          artist={user?.artist}
          submitLabel={t("apply_next")}
          onBack={() => setPhase("dashboard")}
          onSaved={() => { setDone((d) => ({ ...d, profile: true })); setPhase("dashboard"); }}
        />
      </ApplyShell>
    );
  }

  if (phase === "artwork") {
    return (
      <ApplyShell onClose={onClose}>
        <header className="apply__head apply__head--task">
          <button type="button" className="apply__back" onClick={() => setPhase("dashboard")}>
            <span aria-hidden="true">←</span><span>{t("apply_back")}</span>
          </button>
          <AccountPill user={user} />
          <p className="apply__eyebrow">{t("dash_card_artwork_eyebrow")}</p>
          <h2 className="apply__title">{t("dash_card_artwork_title")}</h2>
          <p className="apply__sub">{t("dash_card_artwork_body")}</p>
        </header>
        <ArtworkForm
          submitLabel={t("apply_next")}
          onBack={() => setPhase("dashboard")}
          onSaved={(saved) => { setArtworkId(saved.id); setDone((d) => ({ ...d, artwork: true })); setPhase("dashboard"); }}
        />
      </ApplyShell>
    );
  }

  if (phase === "success") {
    return (
      <ApplyShell onClose={onClose}>
        <div className="apply__success">
          <div className="apply__success-mark" aria-hidden="true">
            <svg viewBox="0 0 48 48" width="48" height="48">
              <circle cx="24" cy="24" r="22" fill="none" stroke="currentColor" strokeWidth="1.4" />
              <path d="M14 24.5 21 31 34 18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          <h2 className="apply__success-t">{t("apply_success_t")}</h2>
          <p className="apply__success-b">{t("apply_success_b")}</p>
          <div className="apply__success-cta">
            <button type="button" className="btn btn--primary btn--lg" onClick={() => { onClose(); navigate("/dashboard"); }}>
              {t("apply_success_done")}<span className="btn__arrow" aria-hidden="true">→</span>
            </button>
            <button type="button" className="btn btn--ghost" onClick={() => { setDone((d) => ({ ...d, artwork: false })); setArtworkId(null); setPhase("artwork"); }}>
              {t("apply_success_again")}
            </button>
          </div>
        </div>
      </ApplyShell>
    );
  }

  // dashboard (onboarding)
  return (
    <ApplyShell onClose={onClose}>
      <header className="apply__head apply__head--dash">
        <AccountPill user={user} />
        <p className="apply__eyebrow">{t("dash_eyebrow")}</p>
        <h2 className="apply__title">{t("dash_title")}</h2>
        <p className="apply__sub">{t("dash_sub")}</p>
      </header>
      <div className="dash__progress">
        <div className="dash__progress-row">
          <span className="dash__progress-lbl">{t("dash_progress")}</span>
          <span className="dash__progress-count">
            <span className="dash__progress-cur">{String(total).padStart(2, "0")}</span>
            <span className="dash__progress-sep" aria-hidden="true"> / </span>
            <span className="dash__progress-tot">02</span>
          </span>
        </div>
        <div className="dash__progress-bar" aria-hidden="true">
          <span style={{ width: `${(total / 2) * 100}%` }} />
        </div>
      </div>
      <ol className="dash__cards">
        <OnboardCard n="01" eyebrow={t("dash_card_artwork_eyebrow")} title={t("dash_card_artwork_title")}
                     body={t("dash_card_artwork_body")} cta={t("dash_card_artwork_cta")}
                     done={done.artwork} onClick={() => setPhase("artwork")} />
        <OnboardCard n="02" eyebrow={t("dash_card_profile_eyebrow")} title={t("dash_card_profile_title")}
                     body={t("dash_card_profile_body")} cta={t("dash_card_profile_cta")}
                     done={done.profile} onClick={() => setPhase("profile")} />
      </ol>
      <div className="dash__finish">
        <button type="button" className="btn btn--primary btn--lg dash__finish-btn" disabled={!canSubmit || busy} onClick={finish}>
          {t("dash_finish")}<span className="btn__arrow" aria-hidden="true">→</span>
        </button>
        {!canSubmit && <span className="dash__finish-hint">{t("dash_finish_locked")}</span>}
      </div>
    </ApplyShell>
  );
}
