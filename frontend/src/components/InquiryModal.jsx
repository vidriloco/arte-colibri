import React from "react";
import { useLang, bi } from "../i18n.jsx";
import { Public } from "../api.js";

export function InquiryModal({ work, onClose }) {
  const { lang, t } = useLang();
  const [form, setForm] = React.useState({ name: "", email: "", message: "" });
  const [errors, setErrors] = React.useState({});
  const [submitted, setSubmitted] = React.useState(false);
  const [sending, setSending] = React.useState(false);

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

  const validate = () => {
    const e = {};
    if (!form.name.trim()) e.name = t("form_required");
    if (!form.email.trim()) e.email = t("form_required");
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) e.email = t("form_email_invalid");
    if (!form.message.trim()) e.message = t("form_required");
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const submit = async (ev) => {
    ev.preventDefault();
    if (!validate() || sending) return;
    setSending(true);
    try {
      await Public.inquire(work.slug, form);
      setSubmitted(true);
    } catch (err) {
      setErrors(err.data && typeof err.data === "object" ? err.data : { message: t("error_b") });
    } finally {
      setSending(false);
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
              <p className="modal__eyebrow">{t("cta_inquire")}</p>
              <h2>{bi(work.title, lang)}, {work.year}</h2>
              <p className="modal__sub">
                {work.artist_name} · {bi(work.medium, lang)} · {work.dimensions}
              </p>
              <p className="modal__hint">{t("inquire_sub")}</p>
            </header>
            <form className="form" onSubmit={submit} noValidate>
              <label className={"form__row" + (errors.name ? " has-error" : "")}>
                <span className="form__lbl">{t("form_name")}</span>
                <input type="text" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
                {errors.name && <span className="form__err">{errors.name}</span>}
              </label>
              <label className={"form__row" + (errors.email ? " has-error" : "")}>
                <span className="form__lbl">{t("form_email")}</span>
                <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
                {errors.email && <span className="form__err">{errors.email}</span>}
              </label>
              <label className={"form__row" + (errors.message ? " has-error" : "")}>
                <span className="form__lbl">{t("form_msg")}</span>
                <textarea rows={4} placeholder={t("form_msg_ph")} value={form.message}
                          onChange={(e) => setForm({ ...form, message: e.target.value })} />
                {errors.message && <span className="form__err">{errors.message}</span>}
              </label>
              <div className="form__actions">
                <button type="button" className="btn btn--ghost" onClick={onClose}>{t("form_cancel")}</button>
                <button type="submit" className="btn btn--primary" disabled={sending}>{t("form_send")}</button>
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
            <h2>{t("form_success_t")}</h2>
            <p>{t("form_success_b")}</p>
            <button type="button" className="btn btn--primary" onClick={onClose}>
              {lang === "es" ? "Cerrar" : "Close"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
