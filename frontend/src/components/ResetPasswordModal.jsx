// Curator-only: reset an artist account's password by typing a new password
// and its confirmation. Mounted from AccountsTab's ResetPasswordControl.
import React from "react";
import { useLang } from "../i18n.jsx";
import { Curation } from "../api.js";

export function ResetPasswordModal({ artist, onClose, onDone }) {
  const { lang, t } = useLang();
  const [pw, setPw] = React.useState("");
  const [pw2, setPw2] = React.useState("");
  const [busy, setBusy] = React.useState(false);
  const [error, setError] = React.useState(null);
  const [submitted, setSubmitted] = React.useState(false);

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

  const tooShort = pw.length < 8;
  const mismatch = pw !== pw2;
  const showHint = (tooShort || mismatch) && (pw || pw2);

  const submit = async (ev) => {
    ev.preventDefault();
    if (busy || tooShort || mismatch) return;
    setBusy(true);
    setError(null);
    try {
      await Curation.resetArtistPassword(artist.id, pw);
      setSubmitted(true);
    } catch (e) {
      const d = e?.data;
      const msg =
        (d && (Array.isArray(d.password) ? d.password.join(" ") : d.password || d.detail)) ||
        t("error_t");
      setError(msg);
      setBusy(false);
    }
  };

  return (
    <div className="modal" role="dialog" aria-modal="true">
      <div className="modal__scrim" onClick={onClose} />
      <div className="modal__panel">
        <button type="button" className="modal__close" onClick={onClose} aria-label="Close">✕</button>
        {!submitted ? (
          <>
            <header className="modal__head">
              <p className="modal__eyebrow">{t("md_acct_reset_pw")}</p>
              <h2>{artist.display_name}</h2>
              {artist.email && <p className="modal__sub">{artist.email}</p>}
            </header>
            <form className="form" onSubmit={submit} noValidate>
              <label className="form__row">
                <span className="form__lbl">{t("md_acct_new_pw")}</span>
                <input
                  type="password"
                  autoComplete="new-password"
                  value={pw}
                  onChange={(e) => setPw(e.target.value)}
                />
              </label>
              <label className={"form__row" + (mismatch && pw2 ? " has-error" : "")}>
                <span className="form__lbl">{t("acct_password_confirm")}</span>
                <input
                  type="password"
                  autoComplete="new-password"
                  value={pw2}
                  onChange={(e) => setPw2(e.target.value)}
                />
              </label>
              {showHint ? (
                <p className="form__err">
                  {tooShort ? t("acct_password_short") : t("acct_password_mismatch")}
                </p>
              ) : (
                <p className="modal__hint">{t("acct_password_hint")}</p>
              )}
              {error && <p className="form__err">{error}</p>}
              <div className="form__actions">
                <button type="button" className="btn btn--ghost" onClick={onClose}>
                  {t("form_cancel")}
                </button>
                <button
                  type="submit"
                  className="btn btn--primary"
                  disabled={busy || tooShort || mismatch}>
                  {t("md_acct_reset_pw")}
                </button>
              </div>
            </form>
          </>
        ) : (
          <div className="modal__success">
            <div className="success-mark" aria-hidden="true">
              <svg viewBox="0 0 32 32" width="32" height="32">
                <circle cx="16" cy="16" r="15" fill="none" stroke="currentColor" strokeWidth="1.2" />
                <path d="M10 16.5 14.5 21 22 12.5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
            <h2>{t("md_acct_pw_done")}</h2>
            <button type="button" className="btn btn--primary" onClick={onDone || onClose}>
              {lang === "es" ? "Cerrar" : "Close"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
