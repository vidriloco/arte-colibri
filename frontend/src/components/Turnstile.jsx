import React from "react";
import { Public } from "../api.js";
import { useLang } from "../i18n.jsx";

// Cloudflare Turnstile widget. The site key comes from /api/meta/ so the SPA
// needs no build-time config; when the backend has no key configured the
// component renders nothing and forms submit without a token.

const SCRIPT_SRC =
  "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit";

let scriptPromise = null;
function loadScript() {
  if (window.turnstile) return Promise.resolve();
  if (!scriptPromise) {
    scriptPromise = new Promise((resolve, reject) => {
      const s = document.createElement("script");
      s.src = SCRIPT_SRC;
      s.async = true;
      s.onload = resolve;
      s.onerror = () => {
        scriptPromise = null; // allow a retry on the next mount
        reject(new Error("turnstile script failed to load"));
      };
      document.head.appendChild(s);
    });
  }
  return scriptPromise;
}

let cachedSiteKey = null; // null = unknown yet, "" = disabled
export function useTurnstileSiteKey() {
  const [siteKey, setSiteKey] = React.useState(cachedSiteKey);
  React.useEffect(() => {
    if (cachedSiteKey !== null) return;
    let alive = true;
    Public.meta()
      .then((m) => {
        cachedSiteKey = m?.turnstile_site_key || "";
        if (alive) setSiteKey(cachedSiteKey);
      })
      .catch(() => alive && setSiteKey(""));
    return () => {
      alive = false;
    };
  }, []);
  return siteKey;
}

export function Turnstile({ siteKey, onToken, error }) {
  const { lang } = useLang();
  const ref = React.useRef(null);

  React.useEffect(() => {
    if (!siteKey || !ref.current) return undefined;
    let widgetId = null;
    let alive = true;
    loadScript()
      .then(() => {
        if (!alive || !ref.current) return;
        widgetId = window.turnstile.render(ref.current, {
          sitekey: siteKey,
          language: lang,
          callback: (token) => onToken(token),
          "expired-callback": () => onToken(""),
          "error-callback": () => onToken(""),
        });
      })
      .catch(() => {});
    return () => {
      alive = false;
      if (widgetId !== null) window.turnstile?.remove(widgetId);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [siteKey, lang]);

  if (!siteKey) return null;
  return (
    <div className={"form__row" + (error ? " has-error" : "")}>
      <div ref={ref} />
      {error && <span className="form__err">{error}</span>}
    </div>
  );
}
