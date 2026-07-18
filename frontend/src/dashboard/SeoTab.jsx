import React from "react";
import { useLang } from "../i18n.jsx";
import { Curation } from "../api.js";
import { useFetch } from "../hooks.js";
import { Loading, ErrorState, EmptyState } from "../components/primitives.jsx";
import { ApplyField } from "../components/forms.jsx";
import { DashTabs } from "./shared.jsx";

const ROBOTS = ["index,follow", "noindex,follow", "index,nofollow", "noindex,nofollow"];

function biField(pair) {
  return { es: pair?.es || "", en: pair?.en || "" };
}

// Editor for a single SEO slot. `slot` is a PageSeo payload from the API.
function SlotEditor({ slot, onSaved }) {
  const { t } = useLang();
  const [form, setForm] = React.useState(() => ({
    title: biField(slot.title),
    description: biField(slot.description),
    og_title: biField(slot.og_title),
    og_description: biField(slot.og_description),
    canonical: slot.canonical || "",
    robots: slot.robots || "index,follow",
  }));
  const [imageUrl, setImageUrl] = React.useState(slot.og_image_url || "");
  const [saving, setSaving] = React.useState(false);
  const [uploading, setUploading] = React.useState(false);
  const [saved, setSaved] = React.useState(false);
  const [errors, setErrors] = React.useState({});

  // Reset local state whenever a different slot is selected.
  React.useEffect(() => {
    setForm({
      title: biField(slot.title),
      description: biField(slot.description),
      og_title: biField(slot.og_title),
      og_description: biField(slot.og_description),
      canonical: slot.canonical || "",
      robots: slot.robots || "index,follow",
    });
    setImageUrl(slot.og_image_url || "");
    setSaved(false);
    setErrors({});
  }, [slot.key]);

  const setBi = (field, lang, value) =>
    setForm((f) => ({ ...f, [field]: { ...f[field], [lang]: value } }));
  const set = (field, value) => setForm((f) => ({ ...f, [field]: value }));

  const submit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setSaved(false);
    setErrors({});
    try {
      const updated = await Curation.saveSeo(slot.key, form);
      setSaved(true);
      onSaved && onSaved(updated);
    } catch (err) {
      setErrors(err.data && typeof err.data === "object" ? err.data : {});
    } finally {
      setSaving(false);
    }
  };

  const onFile = async (e) => {
    const file = e.target.files && e.target.files[0];
    if (!file) return;
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append("og_image", file);
      const updated = await Curation.uploadSeoImage(slot.key, fd);
      setImageUrl(updated.og_image_url || "");
      onSaved && onSaved(updated);
    } catch (err) {
      setErrors((x) => ({ ...x, og_image: err.data?.og_image || t("error_b") }));
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  return (
    <form className="apply__form seo-form" noValidate onSubmit={submit}>
      <fieldset className="apply__section">
        <legend className="apply__section-title">{t("seo_meta")}</legend>
        <div className="apply__row apply__row--2">
          <ApplyField label={t("seo_title_es")} error={errors.title}>
            <input type="text" value={form.title.es} onChange={(e) => setBi("title", "es", e.target.value)} />
          </ApplyField>
          <ApplyField label={t("seo_title_en")}>
            <input type="text" value={form.title.en} onChange={(e) => setBi("title", "en", e.target.value)} />
          </ApplyField>
        </div>
        <div className="apply__row apply__row--2">
          <ApplyField label={t("seo_desc_es")} hint={t("seo_desc_hint")}>
            <textarea rows={2} value={form.description.es} onChange={(e) => setBi("description", "es", e.target.value)} />
          </ApplyField>
          <ApplyField label={t("seo_desc_en")}>
            <textarea rows={2} value={form.description.en} onChange={(e) => setBi("description", "en", e.target.value)} />
          </ApplyField>
        </div>
      </fieldset>

      <fieldset className="apply__section">
        <legend className="apply__section-title">{t("seo_social")}</legend>
        <div className="apply__row apply__row--2">
          <ApplyField label={t("seo_og_title_es")} hint={t("seo_og_hint")}>
            <input type="text" value={form.og_title.es} onChange={(e) => setBi("og_title", "es", e.target.value)} />
          </ApplyField>
          <ApplyField label={t("seo_og_title_en")}>
            <input type="text" value={form.og_title.en} onChange={(e) => setBi("og_title", "en", e.target.value)} />
          </ApplyField>
        </div>
        <div className="apply__row apply__row--2">
          <ApplyField label={t("seo_og_desc_es")}>
            <textarea rows={2} value={form.og_description.es} onChange={(e) => setBi("og_description", "es", e.target.value)} />
          </ApplyField>
          <ApplyField label={t("seo_og_desc_en")}>
            <textarea rows={2} value={form.og_description.en} onChange={(e) => setBi("og_description", "en", e.target.value)} />
          </ApplyField>
        </div>
        <ApplyField label={t("seo_og_image")} error={errors.og_image} hint={t("seo_og_image_hint")}>
          <div className="seo-image">
            {imageUrl && <img className="seo-image__preview" src={imageUrl} alt="" />}
            <input type="file" accept="image/*" onChange={onFile} disabled={uploading} />
          </div>
        </ApplyField>
      </fieldset>

      <fieldset className="apply__section">
        <legend className="apply__section-title">{t("seo_indexing")}</legend>
        <div className="apply__row apply__row--2">
          <ApplyField label={t("seo_canonical")} hint={t("seo_canonical_hint")}>
            <input type="url" placeholder="https://" value={form.canonical} onChange={(e) => set("canonical", e.target.value)} />
          </ApplyField>
          <ApplyField label={t("seo_robots")}>
            <select value={form.robots} onChange={(e) => set("robots", e.target.value)}>
              {ROBOTS.map((r) => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>
          </ApplyField>
        </div>
      </fieldset>

      <div className="apply__actions">
        <span aria-hidden="true">{saved && <span className="seo-saved">{t("seo_saved")}</span>}</span>
        <button type="submit" className="btn btn--primary btn--lg" disabled={saving}>
          {t("md_save")}<span className="btn__arrow" aria-hidden="true">→</span>
        </button>
      </div>
    </form>
  );
}

export function SeoTab() {
  const { t } = useLang();
  const { loading, error, data, reload } = useFetch(() => Curation.seo(), []);
  const [activeKey, setActiveKey] = React.useState(null);

  if (loading) return <div className="dash-panel"><Loading /></div>;
  if (error) return <div className="dash-panel"><ErrorState onRetry={reload} /></div>;

  const slots = data || [];
  if (slots.length === 0) {
    return <div className="dash-panel"><EmptyState title={t("seo_empty")} /></div>;
  }
  const current = slots.find((s) => s.key === activeKey) || slots[0];

  return (
    <div className="dash-panel">
      <div className="dash-panel__head">
        <h2>{t("md_seo")}</h2>
      </div>
      <p className="seo-intro">{t("seo_intro")}</p>
      <DashTabs
        active={current.key}
        onChange={setActiveKey}
        tabs={slots.map((s) => ({ key: s.key, label: s.key_label }))}
      />
      <SlotEditor key={current.key} slot={current} onSaved={() => reload()} />
    </div>
  );
}
