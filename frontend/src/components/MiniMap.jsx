// Read-only Mapbox map that plots one or more markers. Renders nothing when no
// token is configured or there's nothing to plot, so pages degrade gracefully.
import React from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import { useMapboxToken } from "./mapbox.js";

const CDMX = [-99.133, 19.432];

export function MiniMap({ markers = [], zoom = 11, height = 260 }) {
  const token = useMapboxToken();
  const elRef = React.useRef(null);
  const pts = markers.filter((m) => m && m.lat != null && m.lng != null);
  const key = pts.map((m) => `${m.lat},${m.lng}`).join("|");

  React.useEffect(() => {
    if (!token || !elRef.current || pts.length === 0) return;
    mapboxgl.accessToken = token;
    const map = new mapboxgl.Map({
      container: elRef.current,
      style: "mapbox://styles/mapbox/light-v11",
      center: [pts[0].lng, pts[0].lat],
      zoom,
      attributionControl: false,
    });
    map.addControl(new mapboxgl.NavigationControl({ showCompass: false }), "top-right");

    pts.forEach((m) => {
      const marker = new mapboxgl.Marker({ color: "#117360" }).setLngLat([m.lng, m.lat]);
      if (m.label) marker.setPopup(new mapboxgl.Popup({ offset: 18 }).setText(m.label));
      marker.addTo(map);
      if (m.onClick) marker.getElement().addEventListener("click", m.onClick);
    });

    if (pts.length > 1) {
      const b = new mapboxgl.LngLatBounds();
      pts.forEach((m) => b.extend([m.lng, m.lat]));
      map.fitBounds(b, { padding: 48, maxZoom: 13, duration: 0 });
    }
    return () => map.remove();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, key, zoom]);

  if (!token || pts.length === 0) return null;
  return <div ref={elRef} className="mini-map" style={{ height }} />;
}
