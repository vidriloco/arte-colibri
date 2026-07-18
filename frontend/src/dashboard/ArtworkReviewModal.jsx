// Full artwork detail for the curator: opened from a review-queue / all-works
// row. Read-only info + inline approve/reject in the footer. Uses the data
// already returned by ReviewArtworkSerializer — no extra fetch.
import React from "react";
import { useLang, bi, formatPrice } from "../i18n.jsx";
import { ModStatusBadge, RejectControl } from "./shared.jsx";

const AVAIL_KEY = { available: "avail_available", sold: "avail_sold", nfs: "apply_nfs" };

function Row({ label, children }) {
  if (children === null || children === undefined || children === "") return null;
  return (
    <div className="artdetail__row">
      <dt className="artdetail__k">{label}</dt>
      <dd className="artdetail__v">{children}</dd>
    </div>
  );
}

export function ArtworkReviewModal({ work, onClose, onApprove, onReject }) {
  const { lang, t } = useLang();

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

  const images = work.images || [];
  const num = (v) => (v != null && String(v).trim() !== "" ? parseFloat(v) : null);
  const weight = num(work.weight);
  const soldPrice = num(work.sold_price);

  return (
    <div className="modal" role="dialog" aria-modal="true">
      <div className="modal__scrim" onClick={onClose} />
      <div className="modal__panel modal__panel--wide">
        <button type="button" className="modal__close" onClick={onClose} aria-label="Close">✕</button>

        <header className="modal__head">
          <p className="modal__eyebrow">{t("md_detail")}</p>
          <h2><em>{bi(work.title, lang)}</em>{work.year ? `, ${work.year}` : ""}</h2>
          <p className="modal__sub">
            {work.artist_name}
            {work.artist?.city ? ` · ${work.artist.city}` : ""}
            {" "}<ModStatusBadge status={work.status} />
          </p>
        </header>

        {images.length > 0 && (
          <div className="artdetail__gallery">
            {images.map((img) => (
              <img key={img.id} src={img.url || img.thumb} alt="" className="artdetail__img" />
            ))}
          </div>
        )}

        <dl className="artdetail">
          <Row label={t("medium")}>{bi(work.medium, lang)}</Row>
          <Row label={t("dimensions")}>{work.dimensions}</Row>
          <Row label={t("apply_weight")}>{weight != null ? `${weight} kg` : ""}</Row>
          <Row label={t("md_price")}>
            {work.price != null ? formatPrice(work.price, lang, work.currency) : "—"}
          </Row>
          <Row label={t("apply_availability")}>{t(AVAIL_KEY[work.availability] || work.availability)}</Row>
          <Row label={t("apply_sold_price")}>
            {soldPrice != null ? formatPrice(soldPrice, lang, work.currency) : ""}
          </Row>
          <Row label={t("apply_tags")}>
            {(work.tags || []).length ? (work.tags || []).join(", ") : ""}
          </Row>
          <Row label={t("md_description")}>{bi(work.description, lang)}</Row>
          <Row label={t("md_reject_notes")}>{work.review_notes}</Row>
        </dl>

        {(onApprove || onReject) && (
          <div className="artdetail__actions">
            {onReject && <RejectControl onReject={onReject} />}
            {onApprove && (
              <button type="button" className="btn btn--primary" onClick={onApprove}>
                {t("md_approve")}
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
