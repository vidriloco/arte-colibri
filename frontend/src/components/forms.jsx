import React from "react";
import { useLang, bi } from "../i18n.jsx";
import { Public, Dash } from "../api.js";
import { useFetch } from "../hooks.js";
import { LocationField } from "./LocationField.jsx";

export const DISCIPLINES = [
  { value: "pintura", es: "Pintura", en: "Painting" },
  { value: "escultura", es: "Escultura", en: "Sculpture" },
  { value: "fotografia", es: "Fotografía", en: "Photography" },
  { value: "ceramica", es: "Cerámica", en: "Ceramics" },
  { value: "textil", es: "Textil", en: "Textile" },
  { value: "grabado", es: "Grabado", en: "Printmaking" },
  { value: "otra", es: "Otra", en: "Other" },
];

// Common techniques for the artwork "Técnica / medio" selector, grouped by
// discipline. The Spanish label doubles as the option value; "Otra…" reveals a
// free-text input so anything not listed (photography, textile, …) still works.
export const MEDIA_TECHNIQUES = [
  {
    label: { es: "Pintura", en: "Painting" },
    options: [
      { es: "Óleo", en: "Oil" },
      { es: "Acrílico", en: "Acrylic" },
      { es: "Acuarela", en: "Watercolor" },
      { es: "Gouache", en: "Gouache" },
      { es: "Pastel", en: "Pastel" },
      { es: "Tinta", en: "Ink" },
      { es: "Témpera", en: "Tempera" },
      { es: "Encáustica", en: "Encaustic" },
      { es: "Técnica mixta", en: "Mixed media" },
    ],
  },
  {
    label: { es: "Escultura", en: "Sculpture" },
    options: [
      { es: "Talla en madera", en: "Wood carving" },
      { es: "Talla en piedra", en: "Stone carving" },
      { es: "Fundición en bronce", en: "Bronze casting" },
      { es: "Metal soldado", en: "Welded metal" },
      { es: "Modelado", en: "Modeling" },
      { es: "Yeso", en: "Plaster" },
      { es: "Resina", en: "Resin" },
      { es: "Ensamblaje", en: "Assemblage" },
    ],
  },
  {
    label: { es: "Cerámica", en: "Ceramics" },
    options: [
      { es: "Gres (alta temperatura)", en: "Stoneware" },
      { es: "Barro", en: "Earthenware" },
      { es: "Porcelana", en: "Porcelain" },
      { es: "Raku", en: "Raku" },
      { es: "Modelado a mano", en: "Hand-building" },
      { es: "Torno", en: "Wheel-throwing" },
      { es: "Esmalte", en: "Glazed" },
    ],
  },
];

const MEDIA_OTHER = "__otra__";
const flatTechniques = MEDIA_TECHNIQUES.flatMap((g) => g.options);
const findTechniqueByEs = (es) => flatTechniques.find((o) => o.es === es) || null;

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
  lat: artist?.location?.lat ?? null,
  lng: artist?.location?.lng ?? null,
  disciplineValue:
    DISCIPLINES.find((d) => d.es === bi(artist?.discipline, "es"))?.value || "",
  instagram: artist?.instagram || "",
  tiktok: artist?.tiktok || "",
  web: artist?.web || "",
  statement: bi(artist?.bio, "es") || "",
});

export function ProfileForm({ artist, onSaved, submitLabel, onBack }) {
  const { lang, t } = useLang();
  const [form, setForm] = React.useState(() => emptyProfile(artist));
  const [errors, setErrors] = React.useState({});
  const [saving, setSaving] = React.useState(false);
  const [avatarUrl, setAvatarUrl] = React.useState(artist?.avatar || "");
  const [avatarBusy, setAvatarBusy] = React.useState(false);
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  // Avatar uploads persist immediately (≤ 200 KB, stored on S3). We don't call
  // onSaved here so it doesn't advance any multi-step flow — just show the new one.
  const onAvatar = async (e) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    setAvatarBusy(true);
    setErrors((x) => ({ ...x, avatar: null }));
    try {
      const fd = new FormData();
      fd.append("avatar", file);
      const saved = await Dash.uploadAvatar(fd);
      setAvatarUrl(saved.avatar || "");
    } catch (err) {
      const d = err?.data;
      const msg = (d && typeof d === "object" && (d.avatar || d.detail)) || t("error_b");
      setErrors((x) => ({ ...x, avatar: msg }));
    } finally {
      setAvatarBusy(false);
    }
  };

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
        lat: form.lat ?? null,
        lng: form.lng ?? null,
        discipline: { es: disc.es, en: disc.en },
        bio: { es: form.statement, en: form.statement },
        instagram: form.instagram,
        tiktok: form.tiktok,
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
        <ApplyField label={t("apply_avatar")} error={errors.avatar} hint={t("apply_avatar_hint")}>
          <div className="avatar-upload">
            {avatarUrl
              ? <img className="avatar-upload__img" src={avatarUrl} alt="" />
              : <span className="avatar-upload__ph" aria-hidden="true">{artist?.initials || "○"}</span>}
            <label className="btn btn--ghost btn--sm avatar-upload__btn">
              {avatarBusy ? t("apply_avatar_busy") : t("apply_avatar_upload")}
              <input type="file" accept="image/*" hidden disabled={avatarBusy} onChange={onAvatar} />
            </label>
          </div>
        </ApplyField>
        <ApplyField label={t("apply_discipline")} error={errors.discipline} required>
          <select value={form.disciplineValue} onChange={(e) => set("disciplineValue", e.target.value)}>
            <option value="">{lang === "es" ? "Seleccionar…" : "Select…"}</option>
            {DISCIPLINES.map((d) => (
              <option key={d.value} value={d.value}>{lang === "es" ? d.es : d.en}</option>
            ))}
          </select>
        </ApplyField>
        <ApplyField label={t("apply_location")} error={errors.city} required hint={t("apply_location_hint")}>
          <LocationField
            value={{ city: form.city, lat: form.lat, lng: form.lng }}
            onChange={({ city, lat, lng }) => setForm((f) => ({ ...f, city, lat, lng }))}
          />
        </ApplyField>
        <div className="apply__row apply__row--2">
          <ApplyField label={t("apply_instagram")}>
            <input type="text" placeholder="@usuario" value={form.instagram} onChange={(e) => set("instagram", e.target.value)} />
          </ApplyField>
          <ApplyField label={t("apply_tiktok")}>
            <input type="text" placeholder="@usuario" value={form.tiktok} onChange={(e) => set("tiktok", e.target.value)} />
          </ApplyField>
        </div>
        <div className="apply__row apply__row--2">
          <ApplyField label={t("apply_web")}>
            <input type="url" placeholder="https://" value={form.web} onChange={(e) => set("web", e.target.value)} />
          </ApplyField>
          <span aria-hidden="true" />
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
const emptyArtwork = (a) => {
  const mediumEs = bi(a?.medium, "es") || "";
  const known = findTechniqueByEs(mediumEs);
  return {
  titleEs: bi(a?.title, "es") || "",
  // Raw English (not the bi() fallback) so an unset English stays blank.
  titleEn: a?.title?.en || "",
  // A known technique preselects its option; anything else → "Otra" + free text.
  mediumSel: mediumEs ? (known ? mediumEs : MEDIA_OTHER) : "",
  mediumCustom: known ? "" : mediumEs,
  width: a?.width != null ? String(parseFloat(a.width)) : "",
  height: a?.height != null ? String(parseFloat(a.height)) : "",
  depth: a?.depth != null ? String(parseFloat(a.depth)) : "",
  weight: a?.weight != null ? String(parseFloat(a.weight)) : "",
  year: a?.year || new Date().getFullYear(),
  price: a?.price ? String(parseFloat(a.price)) : "",
  availability: a?.availability || "available",
  soldPrice: a?.sold_price ? String(parseFloat(a.sold_price)) : "",
  tags: a?.tags || [],
  description: bi(a?.description, "es") || "",
  descriptionEn: a?.description?.en || "",
  };
};

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
    // English title is optional — display falls back to Spanish.
    const mediumOtra = form.mediumSel === MEDIA_OTHER;
    const tech = mediumOtra ? null : findTechniqueByEs(form.mediumSel);
    const mediumEsVal = (mediumOtra ? form.mediumCustom : form.mediumSel).trim();
    if (!mediumEsVal) er.medium = t("form_required");
    // width/height/depth/weight are all optional.
    if (form.availability !== "nfs" && !String(form.price).trim()) er.price = t("form_required");
    if (!form.description.trim()) er.description = t("form_required");
    setErrors(er);
    if (Object.keys(er).length) return null;
    const soldPrice =
      form.availability === "sold" && String(form.soldPrice).trim()
        ? form.soldPrice
        : null;
    const medium = tech
      ? { es: tech.es, en: tech.en }
      : { es: mediumEsVal, en: mediumEsVal };
    const num = (v) => (String(v).trim() ? Number(v) : null);
    const payload = {
      title: { es: form.titleEs, en: form.titleEn },
      medium,
      description: { es: form.description, en: form.descriptionEn },
      width: num(form.width),
      height: num(form.height),
      depth: num(form.depth),
      weight: num(form.weight),
      year: Number(form.year),
      price: form.availability === "nfs" ? null : form.price,
      sold_price: soldPrice,
      availability: form.availability,
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
      const d = err?.data;
      const msg = (d && typeof d === "object" && (d.image || d.detail)) || t("error_b");
      setErrors((x) => ({ ...x, image: msg }));
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
          <ApplyField label={t("apply_title_en")} hint={t("apply_en_optional")}>
            <input type="text" value={form.titleEn} onChange={(e) => set("titleEn", e.target.value)} />
          </ApplyField>
        </div>
        <div className="apply__row apply__row--2">
          <ApplyField label={t("apply_medium")} error={errors.medium} required>
            <select value={form.mediumSel} onChange={(e) => set("mediumSel", e.target.value)}>
              <option value="">{lang === "es" ? "Seleccionar…" : "Select…"}</option>
              {MEDIA_TECHNIQUES.map((g) => (
                <optgroup key={g.label.es} label={lang === "es" ? g.label.es : g.label.en}>
                  {g.options.map((o) => (
                    <option key={o.es} value={o.es}>{lang === "es" ? o.es : o.en}</option>
                  ))}
                </optgroup>
              ))}
              <option value={MEDIA_OTHER}>{lang === "es" ? "Otra…" : "Other…"}</option>
            </select>
            {form.mediumSel === MEDIA_OTHER && (
              <input type="text" className="apply__subinput" placeholder={t("apply_medium_ph")}
                     value={form.mediumCustom} onChange={(e) => set("mediumCustom", e.target.value)} />
            )}
          </ApplyField>
          <ApplyField label={t("apply_year")}>
            <input type="number" min="1900" max="2030" value={form.year} onChange={(e) => set("year", e.target.value)} />
          </ApplyField>
        </div>
        <div className="apply__row apply__row--4">
          <ApplyField label={t("apply_width")}>
            <input type="number" min="0" step="0.1" placeholder="cm" value={form.width} onChange={(e) => set("width", e.target.value)} />
          </ApplyField>
          <ApplyField label={t("apply_height")}>
            <input type="number" min="0" step="0.1" placeholder="cm" value={form.height} onChange={(e) => set("height", e.target.value)} />
          </ApplyField>
          <ApplyField label={t("apply_depth")}>
            <input type="number" min="0" step="0.1" placeholder="cm" value={form.depth} onChange={(e) => set("depth", e.target.value)} />
          </ApplyField>
          <ApplyField label={t("apply_weight")}>
            <input type="number" min="0" step="0.1" placeholder="kg" value={form.weight} onChange={(e) => set("weight", e.target.value)} />
          </ApplyField>
        </div>
        <div className="apply__row apply__row--2">
          <ApplyField label={t("apply_price")} error={errors.price} required={form.availability !== "nfs"}>
            <input type="number" min="0" step="500" placeholder={t("apply_price_ph")} disabled={form.availability === "nfs"}
                   value={form.price} onChange={(e) => set("price", e.target.value)} />
          </ApplyField>
          <ApplyField label={t("apply_availability")}>
            <select value={form.availability} onChange={(e) => set("availability", e.target.value)}>
              <option value="available">{t("avail_available")}</option>
              <option value="sold">{t("avail_sold")}</option>
              <option value="nfs">{t("apply_nfs")}</option>
            </select>
          </ApplyField>
        </div>
        {form.availability === "sold" && (
          <ApplyField label={t("apply_sold_price")} hint={t("apply_sold_price_hint")}>
            <input type="number" min="0" step="500" placeholder={t("apply_price_ph")}
                   value={form.soldPrice} onChange={(e) => set("soldPrice", e.target.value)} />
          </ApplyField>
        )}
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
        <ApplyField label={t("apply_desc_en")} hint={t("apply_en_optional")}>
          <textarea rows={4} value={form.descriptionEn} onChange={(e) => set("descriptionEn", e.target.value)} />
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
