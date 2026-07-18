import React from "react";
import { Routes, Route, Outlet, useLocation } from "react-router-dom";
import { Nav } from "./components/Nav.jsx";
import { Footer } from "./components/Footer.jsx";
import { ApplyModal } from "./components/ApplyModal.jsx";
import { Home } from "./screens/Home.jsx";
import { Gallery } from "./screens/Gallery.jsx";
import { ArtworkDetail } from "./screens/ArtworkDetail.jsx";
import { Artist } from "./screens/Artist.jsx";
import { Artists } from "./screens/Artists.jsx";
import { Locations } from "./screens/Locations.jsx";
import { NotFound } from "./screens/NotFound.jsx";
import { Dashboard } from "./dashboard/Dashboard.jsx";

function ScrollToTop() {
  const { pathname } = useLocation();
  React.useEffect(() => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, [pathname]);
  return null;
}

function Layout() {
  const [applyOpen, setApplyOpen] = React.useState(false);
  const openApply = React.useCallback(() => setApplyOpen(true), []);
  const closeApply = React.useCallback(() => setApplyOpen(false), []);
  return (
    <>
      <Nav onApply={openApply} />
      <div className="app">
        <Outlet context={{ onApply: openApply }} />
      </div>
      <Footer onApply={openApply} />
      {applyOpen && <ApplyModal onClose={closeApply} />}
    </>
  );
}

export default function App() {
  return (
    <>
      <ScrollToTop />
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="gallery" element={<Gallery />} />
          <Route path="artwork/:slug" element={<ArtworkDetail />} />
          <Route path="artist/:slug" element={<Artist />} />
          <Route path="artists" element={<Artists />} />
          <Route path="locations" element={<Locations />} />
          <Route path="dashboard/*" element={<Dashboard />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </>
  );
}
