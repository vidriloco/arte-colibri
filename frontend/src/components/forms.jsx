import React from "react";
import { useLang, bi } from "../i18n.jsx";
import { Public, Dash } from "../api.js";
import { useFetch } from "../hooks.js";

export const DISCIPLINES = [
  { value: "pintura", es: "Pintura", en: "Painting" },
  { value: "escultura", es: "Escultura", en: "Sculpture" },
  { value: "fotografia", es: "Fotografía", en: "Photography" },
  { value: "ceramica", es: "Cerámica", en: "Ceramics" },
  { value: "textil", es: "Textil", en: "Textile" },
  { value: "grabado", es: "Grabado", en: "Printmaking" },
  { value: "otra", es: "Otra", en: "Other" },
];

export function ApplyField({ label, error, hint, required, children }) {
  return (
    <label className={"apply__field" + (error ? " has-error" : "")}>
      <span className="apply__lbl">
        {label}
        {required && <span className="apply__lbl-req" aria-hidden="true">*</span>}
      </span>
      {children}
      {error && <span className="apply__err">{error}</span>}
      {hint && !error && <span className="apply__hint">{hint}</span>}
    </label>
  );
}

// ── Profile form ─────────────────────────────────────────────────────────────
const emptyProfile = (artist) => ({
  city: artist?.city || "",
  disciplineValue:
    DISCIPLINES.find((d) => d.es === bi(artist?.discipline, "es"))?.value || "",
  instagram: artist?.instagram || "",
  web: artist?.web || "",
  statement: bi(artist?.bio, "es") || "",
});

export function ProfileForm({ artist, onSaved, submitLabel, onBack }) {
  const { lang, t } = useLang();
  const [form, setForm] = React.useState(() => emptyProfile(artist));
  const [errors, setErrors] = React.useState({});
  const [saving, setSaving] = React.useState(false);
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const submit = async (e) => {
    e.preventDefault();
    const er = {};
    if (!form.city.trim()) er.city = t("form_required");
    if (!form.disciplineValue) er.discipline = t("form_required");
    if (!form.statement.trim()) er.statement = t("form_required");
    setErrors(er);
    if (Object.keys(er).length || saving) return;
    setSaving(true);
    const disc = DISCIPLINES.find((d) => d.value === form.disciplineValue);
    try {
      const saved = await Dash.saveProfile({
        city: form.city,
        discipline: { es: disc.es, en: disc.en },
        bio: { es: form.statement, en: form.statement },
        instagram: form.instagram,
        web: form.web,
      });
      onSaved && onSaved(saved);
    } catch (err) {
      setErrors(err.data && typeof err.data === "object" ? err.data : { city: t("error_b") });
    } finally {
      setSaving(false);
    }
  };

  return (
    <form className="apply__form" noValidate onSubmit={submit}>
      <fieldset className="apply__section">
        <legend className="apply__section-title">{t("apply_section_profile")}</legend>
        <div className="apply__row apply__row--2">
          <ApplyField label={t("apply_city")} error={errors.city} required>
            <input type="text" value={form.city} onChange={(e) => set("city", e.target.value)} />
          </ApplyField>
          <ApplyField label={t("apply_discipline")} error={errors.discipline} required>
            <select value={form.disciplineValue} onChange={(e) => set("disciplineValue", e.target.value)}>
              <option value="">{lang === "es" ? "Seleccionar…" : "Select…"}</option>
              {DISCIPLINES.map((d) => (
                <option key={d.value} value={d.value}>{lang === "es" ? d.es : d.en}</option>
              ))}
            </select>
          </ApplyField>
        </div>
        <div className="apply__row apply__row--2">
          <ApplyField label={t("apply_instagram")}>
            <input type="text" placeholder="@usuario" value={form.instagram} onChange={(e) => set("instagram", e.target.value)} />
          </ApplyField>
          <ApplyField label={t("apply_web")}>
            <input type="url" placeholder="https://" value={form.web} onChange={(e) => set("web", e.target.value)} />
          </ApplyField>
        </div>
        <ApplyField label={t("apply_statement")} error={errors.statement} required hint={t("apply_statement_ph")}>
          <textarea rows={3} value={form.statement} onChange={(e) => set("statement", e.target.value)} />
        </ApplyField>
      </fieldset>
      <div className="apply__actions">
        {onBack ? (
          <button type="button" className="btn btn--ghost" onClick={onBack}>← {t("apply_back")}</button>
        ) : <span aria-hidden="true" />}
        <button type="submit" className="btn btn--primary btn--lg" disabled={saving}>
          {submitLabel || t("md_save")}<span className="btn__arrow" aria-hidden="true">→</span>
        </button>
      </div>
    </form>
  );
}

// ── Artwork form (create/edit + image management) ───────────────────────────
const emptyArtwork = (a) => ({
  titleEs: bi(a?.title, "es") || "",
  titleEn: bi(a?.title, "en") || "",
  medium: bi(a?.medium, "es") || "",
  dimensions: a?.dimensions || "",
  year: a?.year || new Date().getFullYear(),
  price: a?.price ? String(parseFloat(a.price)) : "",
  nfs: a?.availability === "nfs",
  availability: a?.availability || "available",
  tags: a?.tags || [],
  description: bi(a?.description, "es") || "",
});

export function ArtworkForm({ artwork, onSaved, submitLabel, onBack }) {
  const { lang, t } = useLang();
  const meta = useFetch(() => Public.meta(), []);
  const [current, setCurrent] = React.useState(artwork || null);
  const [form, setForm] = React.useState(() => emptyArtwork(artwork));
  const [errors, setErrors] = React.useState({});
  const [saving, setSaving] = React.useState(false);
  const [images, setImages] = React.useState(artwork?.images || []);
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const toggleTag = (slug) =>
    setForm((f) => {
      if (f.tags.includes(slug)) return { ...f, tags: f.tags.filter((x) => x !== slug) };
      if (f.tags.length >= 4) return f;
      return { ...f, tags: [...f.tags, slug] };
    });

  const persist = async () => {
    const er = {};
    if (!form.titleEs.trim()) er.titleEs = t("form_required");
    if (!form.titleEn.trim()) er.titleEn = t("form_required");
    if (!form.medium.trim()) er.medium = t("form_required");
    if (!form.dimensions.trim()) er.dimensions = t("form_required");
    if (!form.nfs && !String(form.price).trim()) er.price = t("form_required");
    if (!form.description.trim()) er.description = t("form_required");
    setErrors(er);
    if (Object.keys(er).length) return null;
    const payload = {
      title: { es: form.titleEs, en: form.titleEn },
      medium: { es: form.medium, en: form.medium },
      description: { es: form.description, en: form.description },
      dimensions: form.dimensions,
      year: Number(form.year),
      price: form.nfs ? null : form.price,
      availability: form.nfs ? "nfs" : form.availability,
      tags: form.tags,
    };
    const saved = current?.id
      ? await Dash.updateArtwork(current.id, payload)
      : await Dash.createArtwork(payload);
    setCurrent(saved);
    setImages(saved.images || []);
    return saved;
  };

  const onSavePhase = async (e) => {
    e.preventDefault();
    if (saving) return;
    setSaving(true);
    try {
      const saved = await persist();
      if (saved && onSaved) onSaved(saved);
    } catch (err) {
      setErrors(err.data && typeof err.data === "object" ? err.data : { titleEs: t("error_b") });
    } finally {
      setSaving(false);
    }
  };

  const ensureSaved = async () => {
    if (current?.id) return current;
    return await persist();
  };

  const onUpload = async (e) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    setSaving(true);
    try {
      const saved = await ensureSaved();
      if (!saved?.id) return;
      const fd = new FormData();
      fd.append("image", file);
      const img = await Dash.addImage(saved.id, fd);
      setImages((prev) => [...prev, img]);
    } catch (err) {
      setErrors(err.data && typeof err.data === "object" ? err.data : { image: t("error_b") });
    } finally {
      setSaving(false);
    }
  };

  const removeImage = async (imageId) => {
    await Dash.deleteImage(current.id, imageId);
    setImages((prev) => prev.filter((i) => i.id !== imageId));
  };
  const makePrimary = async (imageId) => {
    const order = images.map((i) => i.id);
    await Dash.reorderImages(current.id, { order, primary: imageId });
    setImages((prev) => prev.map((i) => ({ ...i, is_primary: i.id === imageId })));
  };

  const tags = meta.data?.tags || [];

  return (
    <form className="apply__form" noValidate onSubmit={onSavePhase}>
      <fieldset className="apply__section">
        <legend className="apply__section-title">{t("apply_section_artwork")}</legend>
        <div className="apply__row apply__row--2">
          <ApplyField label={t("apply_title_es")} error={errors.titleEs} required>
            <input type="text" value={form.titleEs} onChange={(e) => set("titleEs", e.target.value)} />
          </ApplyField>
          <ApplyField label={t("apply_title_en")} error={errors.titleEn} required>
            <input type="text" value={form.titleEn} onChange={(e) => set("titleEn", e.target.value)} />
          </ApplyField>
        </div>
        <div className="apply__row apply__row--2">
          <ApplyField label={t("apply_medium")} error={errors.medium} required>
            <input type="text" placeholder={t("apply_medium_ph")} value={form.medium} onChange={(e) => set("medium", e.target.value)} />
          </ApplyField>
          <ApplyField label={t("apply_dimensions")} error={errors.dimensions} required>
            <input type="text" placeholder={t("apply_dimensions_ph")} value={form.dimensions} onChange={(e) => set("dimensions", e.target.value)} />
          </ApplyField>
        </div>
        <div className="apply__row apply__row--2">
          <ApplyField label={t("apply_year")}>
            <input type="number" min="1900" max="2030" value={form.year} onChange={(e) => set("year", e.target.value)} />
          </ApplyField>
          <ApplyField label={t("apply_price")} error={errors.price} required={!form.nfs}>
            <div className="apply__price-row">
              <input type="number" min="0" step="500" placeholder={t("apply_price_ph")} disabled={form.nfs}
                     value={form.price} onChange={(e) => set("price", e.target.value)} />
              <label className="apply__nfs">
                <input type="checkbox" checked={form.nfs} onChange={(e) => set("nfs", e.target.checked)} />
                <span>{t("apply_nfs")}</span>
              </label>
            </div>
          </ApplyField>
        </div>
        <ApplyField label={t("apply_tags")} hint={t("apply_tags_hint")}>
          <div className="apply__chips">
            {tags.map((tag) => (
              <button key={tag.slug} type="button"
                      className={"chip" + (form.tags.includes(tag.slug) ? " is-active" : "")}
                      onClick={() => toggleTag(tag.slug)}
                      disabled={!form.tags.includes(tag.slug) && form.tags.length >= 4}>
                {bi(tag.label, lang)}
              </button>
            ))}
          </div>
        </ApplyField>
        <ApplyField label={t("apply_desc")} error={errors.description} required>
          <textarea rows={4} placeholder={t("apply_desc_ph")} value={form.description} onChange={(e) => set("description", e.target.value)} />
        </ApplyField>
      </fieldset>

      <fieldset className="apply__section">
        <legend className="apply__section-title">{t("apply_section_images")}</legend>
        {errors.image && <span className="apply__err">{errors.image}</span>}
        <div className="apply__slots">
          {images.map((img) => (
            <div key={img.id} className="apply__slot apply__slot--filled">
              <div className="apply__slot-thumb" style={{ backgroundImage: `url(${img.thumb})`, backgroundSize: "cover", backgroundPosition: "center" }} aria-hidden="true" />
              <div className="apply__slot-info">
                {img.is_primary
                  ? <span className="apply__slot-name">★ {t("md_primary")}</span>
                  : <button type="button" className="apply__signin-link" onClick={() => makePrimary(img.id)}>{t("md_make_primary")}</button>}
              </div>
              <button type="button" className="apply__slot-x" onClick={() => removeImage(img.id)} aria-label={t("apply_image_remove")}>✕</button>
            </div>
          ))}
          <label className="apply__slot apply__slot--sm">
            <input type="file" accept="image/*" onChange={onUpload} hidden />
            <svg className="apply__slot-icon" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M12 16V4" /><path d="M8 8l4-4 4 4" /><rect x="4" y="16" width="16" height="4" rx="1" />
            </svg>
            <span className="apply__slot-lbl">{t("apply_image_drop")}</span>
          </label>
        </div>
        <p className="apply__hint">{t("apply_image_format")}</p>
      </fieldset>

      <div className="apply__actions">
        {onBack ? (
          <button type="button" className="btn btn--ghost" onClick={onBack}>← {t("apply_back")}</button>
        ) : <span aria-hidden="true" />}
        <button type="submit" className="btn btn--primary btn--lg" disabled={saving}>
          {submitLabel || t("md_save")}<span className="btn__arrow" aria-hidden="true">→</span>
        </button>
      </div>
    </form>
  );
}
