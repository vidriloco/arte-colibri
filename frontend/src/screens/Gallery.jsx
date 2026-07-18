import React from "react";
import { useLang } from "../i18n.jsx";
import { useGo } from "../nav.js";
import { Public } from "../api.js";
import { useFetch } from "../hooks.js";
import {
  ArtworkCard, FilterChips, Crumbs, Loading, ErrorState, EmptyState,
} from "../components/primitives.jsx";
import { useSeoPage } from "../head.js";

export function Gallery() {
  const { lang, t } = useLang();
  const go = useGo();
  useSeoPage("gallery");
  const [active, setActive] = React.useState([]);
  const [sort, setSort] = React.useState("recent");
  const [page, setPage] = React.useState(1);

  const meta = useFetch(() => Public.meta(), []);
  const { loading, error, data, reload } = useFetch(
    () => Public.gallery({ tags: active, sort, page }),
    [active.join(","), sort, page]
  );

  const toggleTag = (tag) => {
    setActive((a) => (a.includes(tag) ? a.filter((x) => x !== tag) : [...a, tag]));
    setPage(1);
  };
  const clear = () => { setActive([]); setPage(1); };

  const totalPages = data ? Math.max(1, Math.ceil(data.count / 8)) : 1;

  return (
    <main className="screen gallery">
      <Crumbs items={[
        { label: t("breadcrumb_home"), onClick: () => go({ name: "home" }) },
        { label: t("nav_gallery") },
      ]} />
      <header className="page-head">
        <p className="page-head__eyebrow">{lang === "es" ? "Catálogo" : "Catalog"}</p>
        <h1>{t("all_works")}</h1>
        {data && (
          <p className="page-head__sub">
            {t("showing")} <strong>{data.count}</strong> {t("works")}.
          </p>
        )}
      </header>

      <div className="toolbar">
        <FilterChips
          tags={meta.data?.tags || []}
          active={active}
          onToggle={toggleTag}
          onClear={clear} />
        <label className="sort">
          <span>{t("sort")}</span>
          <select value={sort} onChange={(e) => { setSort(e.target.value); setPage(1); }}>
            <option value="recent">{t("sort_recent")}</option>
            <option value="price_asc">{t("sort_price_asc")}</option>
            <option value="price_desc">{t("sort_price_desc")}</option>
          </select>
        </label>
      </div>

      {loading ? (
        <Loading />
      ) : error ? (
        <ErrorState onRetry={reload} />
      ) : data.results.length > 0 ? (
        <section className="grid grid--4 grid--regular">
          {data.results.map((w) => <ArtworkCard key={w.slug} work={w} />)}
        </section>
      ) : (
        <EmptyState title={t("no_results")} body={t("no_results_b")}>
          <button type="button" className="btn btn--ghost" onClick={clear}>{t("clear")}</button>
        </EmptyState>
      )}

      {totalPages > 1 && (
        <nav className="pager" aria-label="Pagination">
          <button type="button" disabled={page === 1} onClick={() => setPage((p) => p - 1)}>← {t("prev")}</button>
          <span className="pager__pages">
            {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
              <button key={p} type="button" data-on={p === page} onClick={() => setPage(p)}>{p}</button>
            ))}
          </span>
          <button type="button" disabled={page === totalPages} onClick={() => setPage((p) => p + 1)}>{t("next")} →</button>
        </nav>
      )}
    </main>
  );
}
