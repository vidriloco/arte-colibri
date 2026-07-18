import React from "react";
import { useLang } from "../i18n.jsx";
import { useGo } from "../nav.js";
import { useHead } from "../head.js";

export function NotFound() {
  const { t } = useLang();
  const go = useGo();
  useHead({ title: `${t("page404_t")} · Arte Colibrí`, robots: "noindex,follow" });
  return (
    <main className="screen not-found">
      <div className="empty-state">
        <h1>{t("page404_t")}</h1>
        <p>{t("page404_b")}</p>
        <button type="button" className="btn btn--primary" onClick={() => go({ name: "home" })}>
          {t("home")}
        </button>
      </div>
    </main>
  );
}
