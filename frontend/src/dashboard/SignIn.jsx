import React from "react";
import { useLang } from "../i18n.jsx";
import { useAuth } from "../auth.jsx";

export function SignIn({ onApply }) {
  const { t } = useLang();
  const { login } = useAuth();
  const [form, setForm] = React.useState({ email: "", password: "" });
  const [error, setError] = React.useState(null);
  const [busy, setBusy] = React.useState(false);
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const submit = async (e) => {
    e.preventDefault();
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      await login(form.email, form.password);
    } catch {
      setError(t("form_email_invalid"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="screen signin">
      <div className="signin__card">
        <p className="apply__eyebrow">{t("nav_dashboard")}</p>
        <h1 className="apply__title">{t("md_signin_title")}</h1>
        <p className="apply__sub">{t("md_signin_sub")}</p>
        <form className="apply__form apply__form--acct" onSubmit={submit} noValidate>
          <label className="apply__field">
            <span className="apply__lbl">{t("form_email")}</span>
            <input type="email" autoComplete="email" value={form.email} onChange={(e) => set("email", e.target.value)} />
          </label>
          <label className="apply__field">
            <span className="apply__lbl">{t("acct_password")}</span>
            <input type="password" autoComplete="current-password" value={form.password} onChange={(e) => set("password", e.target.value)} />
          </label>
          {error && <span className="apply__err">{error}</span>}
          <button type="submit" className="btn btn--primary btn--lg" disabled={busy}>
            {t("md_signin_cta")}<span className="btn__arrow" aria-hidden="true">→</span>
          </button>
          <p className="apply__signin">
            <span>{t("md_no_account")}</span>{" "}
            <button type="button" className="apply__signin-link" onClick={onApply}>{t("apply_cta")}</button>
          </p>
        </form>
      </div>
    </main>
  );
}
