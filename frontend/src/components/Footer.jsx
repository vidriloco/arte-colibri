import React from "react";
import { useNavigate } from "react-router-dom";
import { useLang } from "../i18n.jsx";
import { Wordmark } from "./primitives.jsx";

export function Footer({ onApply }) {
  const { lang, t } = useLang();
  const navigate = useNavigate();
  return (
    <footer className="foot">
      <div className="foot__inner">
        <div className="foot__brand">
          <Wordmark large />
          <p className="foot__tag">{t("tagline")}</p>
          <button type="button" className="foot__apply" onClick={onApply}>
            <span className="foot__apply-arrow" aria-hidden="true">→</span>
            <span className="foot__apply-text">
              <span className="foot__apply-eyebrow">{t("apply_im_artist")}</span>
              <span className="foot__apply-main">{t("apply_cta")}</span>
            </span>
          </button>
        </div>
        <div className="foot__cols">
          <div className="foot__col">
            <h4>Arte Colibrí</h4>
            <button type="button" onClick={() => navigate("/gallery")}>{t("nav_gallery")}</button>
            <button type="button" onClick={() => navigate("/locations")}>{t("nav_location")}</button>
            <button type="button" onClick={() => navigate("/artists")}>{t("nav_artists")}</button>
            <button type="button">{t("footer_about")}</button>
          </div>
          <div className="foot__col">
            <h4>{lang === "es" ? "Información" : "Information"}</h4>
            <button type="button" onClick={onApply}>{t("footer_artists")}</button>
            <button type="button">{t("footer_press")}</button>
            <button type="button">{t("footer_contact")}</button>
          </div>
          <div className="foot__col foot__contact">
            <h4>{lang === "es" ? "Estudio" : "Studio"}</h4>
            <p>Tlacotalpan 128<br />Roma Sur, 06760<br />Ciudad de México</p>
            <p>hola@artecolibri.mx</p>
          </div>
        </div>
      </div>
      <div className="foot__base">
        <span>© 2026 Arte Colibrí. {t("footer_rights")}</span>
        <span className="foot__legal">
          <button type="button">Aviso de privacidad</button>
          <span aria-hidden="true">·</span>
          <button type="button">Términos</button>
        </span>
      </div>
    </footer>
  );
}
