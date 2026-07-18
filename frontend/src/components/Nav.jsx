import React from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useLang } from "../i18n.jsx";
import { useAuth } from "../auth.jsx";
import { Wordmark } from "./primitives.jsx";

export function Nav({ onApply }) {
  const { lang, setLang, t } = useLang();
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const item = (to, label, end = false) => (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) => "nav__item" + (isActive ? " is-active" : "")}>
      {label}
    </NavLink>
  );

  return (
    <header className="nav">
      <div className="nav__inner">
        <button type="button" className="nav__brand" onClick={() => navigate("/")}>
          <Wordmark />
        </button>
        <nav className="nav__links" aria-label="Primary">
          {item("/gallery", t("nav_gallery"))}
          {item("/locations", t("nav_location"))}
          {item("/artists", t("nav_artists"))}
        </nav>
        <div className="nav__right">
          <div className="lang-toggle" role="group" aria-label="Language">
            <button type="button" data-on={lang === "es"} onClick={() => setLang("es")}>ES</button>
            <span aria-hidden="true">·</span>
            <button type="button" data-on={lang === "en"} onClick={() => setLang("en")}>EN</button>
          </div>
          {user ? (
            <>
              <button type="button" className="nav__signin" onClick={() => navigate("/dashboard")}>
                {t("nav_dashboard")}
              </button>
              <button type="button" className="nav__apply" onClick={logout}>
                {t("nav_logout")}
              </button>
            </>
          ) : (
            <>
              <button type="button" className="nav__signin" onClick={() => navigate("/dashboard")}>
                {t("apply_login")}
              </button>
              <button type="button" className="nav__apply" onClick={onApply}>
                {t("apply_short")}
                <span className="nav__apply-dot" aria-hidden="true" />
              </button>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
