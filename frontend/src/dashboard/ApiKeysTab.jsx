// Curator-only: store third-party API keys (type + secret). The secret is
// write-only server-side; we only ever see a masked preview. When an OpenRouter
// key is set, the SEO tab can generate SEO fields with the chosen model.
import React from "react";
import { useLang } from "../i18n.jsx";
import { Curation } from "../api.js";
import { useFetch } from "../hooks.js";
import { Loading, ErrorState } from "../components/primitives.jsx";
import { ApplyField } from "../components/forms.jsx";

function ApiKeyCard({ row, models, onSaved }) {
  const { t } = useLang();
  const [keyValue, setKeyValue] = React.useState("");
  const [model, setModel] = React.useState(row.model || (models[0] && models[0].id) || "");
  const [busy, setBusy] = React.useState(false);
  const [saved, setSaved] = React.useState(false);
  const [error, setError] = React.useState(null);

  const save = async () => {
    // The key is required the first time; once set, it can be left blank to
    // change only the model (the server keeps the stored secret).
    if (!row.is_set && !keyValue.trim()) {
      setError(t("apikeys_key_required"));
      return;
    }
    setBusy(true);
    setError(null);
    setSaved(false);
    try {
      const body = { api_type: row.api_type, model };
      if (keyValue.trim()) body.key_value = keyValue.trim();
      await Curation.saveApiKey(body);
      setKeyValue("");
      setSaved(true);
      onSaved && onSaved();
    } catch (e) {
      setError(e?.data?.key_value || e?.data?.detail || t("error_b"));
    } finally {
      setBusy(false);
    }
  };

  const remove = async () => {
    setBusy(true);
    setError(null);
    try {
      await Curation.deleteApiKey(row.api_type);
      onSaved && onSaved();
    } catch (e) {
      setError(e?.data?.detail || t("error_b"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <li className="apikey">
      <div className="apikey__head">
        <h3 className="apikey__name">{row.label}</h3>
        <span className={"apikey__status" + (row.is_set ? " is-set" : "")}>
          {row.is_set ? `${t("apikeys_configured")} · ${row.key_preview}` : t("apikeys_not_set")}
        </span>
      </div>
      <div className="apply__row apply__row--2">
        <ApplyField label={t("apikeys_key_label")} error={error}>
          <input
            type="password"
            autoComplete="off"
            placeholder={row.is_set ? "••••••••" : t("apikeys_key_ph")}
            value={keyValue}
            onChange={(e) => setKeyValue(e.target.value)}
          />
        </ApplyField>
        <ApplyField label={t("apikeys_model")}>
          <select value={model} onChange={(e) => setModel(e.target.value)}>
            {models.map((m) => (
              <option key={m.id} value={m.id}>{m.label}</option>
            ))}
          </select>
        </ApplyField>
      </div>
      <div className="apikey__actions">
        {saved && <span className="seo-saved">{t("apikeys_saved")}</span>}
        {row.is_set && (
          <button type="button" className="btn btn--ghost btn--sm" disabled={busy} onClick={remove}>
            {t("apikeys_delete")}
          </button>
        )}
        <button type="button" className="btn btn--primary btn--sm" disabled={busy} onClick={save}>
          {t("md_save")}
        </button>
      </div>
    </li>
  );
}

export function ApiKeysTab() {
  const { t } = useLang();
  const { loading, error, data, reload } = useFetch(() => Curation.apiKeys(), []);

  if (loading) return <div className="dash-panel"><Loading /></div>;
  if (error) return <div className="dash-panel"><ErrorState onRetry={reload} /></div>;

  const rows = data?.keys || [];
  const models = data?.models || [];

  return (
    <div className="dash-panel">
      <div className="dash-panel__head">
        <h2>{t("md_api_keys")}</h2>
      </div>
      <p className="seo-intro">{t("apikeys_intro")}</p>
      <ul className="apikey-list">
        {rows.map((row) => (
          <ApiKeyCard key={row.api_type} row={row} models={models} onSaved={reload} />
        ))}
      </ul>
    </div>
  );
}
