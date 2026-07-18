// Client-side document-head manager. Keeps <title>/meta in sync during SPA
// navigation and language toggling, mirroring the server-injected head so the
// values stay correct after in-app navigation. Managed pages fetch their resolved
// SEO slot from /api/seo/; detail pages pass content-derived values.

import React from "react";
import { Public } from "./api.js";
import { useLang, bi } from "./i18n.jsx";

const SITE_NAME = "Arte Colibrí";

function upsertMeta(attr, key, content) {
  const sel = `meta[${attr}="${key}"]`;
  let el = document.head.querySelector(sel);
  if (!content) {
    if (el && el.hasAttribute("data-managed-seo")) el.remove();
    return;
  }
  if (!el) {
    el = document.createElement("meta");
    el.setAttribute(attr, key);
    el.setAttribute("data-managed-seo", "");
    document.head.appendChild(el);
  }
  el.setAttribute("content", content);
}

function upsertLink(rel, href) {
  let el = document.head.querySelector(`link[rel="${rel}"]`);
  if (!href) {
    if (el && el.hasAttribute("data-managed-seo")) el.remove();
    return;
  }
  if (!el) {
    el = document.createElement("link");
    el.setAttribute("rel", rel);
    el.setAttribute("data-managed-seo", "");
    document.head.appendChild(el);
  }
  el.setAttribute("href", href);
}

// Apply a flat, already-language-resolved SEO object to the document head.
export function applyHead(seo) {
  const title = seo.title || SITE_NAME;
  document.title = title;

  const ogTitle = seo.og_title || title;
  const ogDesc = seo.og_description || seo.description || "";
  const url = window.location.href;

  const image = seo.image || "";
  const imageAlt = image ? seo.image_alt || "" : "";

  upsertMeta("name", "description", seo.description || "");
  upsertMeta("name", "keywords", seo.keywords || "");
  upsertMeta("name", "robots", seo.robots || "index,follow");
  upsertMeta("property", "og:type", "website");
  upsertMeta("property", "og:site_name", SITE_NAME);
  upsertMeta("property", "og:title", ogTitle);
  upsertMeta("property", "og:description", ogDesc);
  upsertMeta("property", "og:url", url);
  upsertMeta("name", "twitter:card", "summary_large_image");
  upsertMeta("name", "twitter:title", ogTitle);
  upsertMeta("name", "twitter:description", ogDesc);
  upsertMeta("property", "og:image", image);
  upsertMeta("name", "twitter:image", image);
  upsertMeta("property", "og:image:alt", imageAlt);
  upsertMeta("name", "twitter:image:alt", imageAlt);
  upsertLink("canonical", seo.canonical || url.split("?")[0]);
}

// Managed pages: fetch the bilingual resolved slot once, re-apply on lang change.
export function useSeoPage(pageKey) {
  const { lang } = useLang();
  const [payload, setPayload] = React.useState(null);

  React.useEffect(() => {
    let alive = true;
    Public.seo(pageKey)
      .then((d) => alive && setPayload(d))
      .catch(() => {});
    return () => {
      alive = false;
    };
  }, [pageKey]);

  React.useEffect(() => {
    if (!payload) return;
    applyHead({
      title: bi(payload.title, lang),
      description: bi(payload.description, lang),
      og_title: bi(payload.og_title, lang),
      og_description: bi(payload.og_description, lang),
      image: payload.og_image || "",
      image_alt: bi(payload.image_alt, lang),
      keywords: bi(payload.keywords, lang),
      canonical: payload.canonical || "",
      robots: payload.robots || "index,follow",
    });
  }, [payload, lang]);
}

// Content/detail pages: caller supplies already-resolved strings (or null to skip
// while data is still loading, leaving the current head untouched).
export function useHead(seo) {
  const dep = seo ? JSON.stringify(seo) : "";
  React.useEffect(() => {
    if (seo) applyHead(seo);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dep]);
}
