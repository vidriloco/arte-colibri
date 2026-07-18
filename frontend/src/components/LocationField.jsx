// Municipality picker for the profile form: a Mapbox-geocoded search + a small
// map with a draggable pin. Emits { city, lat, lng }. With no token it falls
// back to a plain text input (city only), so the form still works.
import React from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import { useLang } from "../i18n.jsx";
import { useMapboxToken, geocode } from "./mapbox.js";

export function LocationField({ value, onChange }) {
  const { t } = useLang();
  const token = useMapboxToken();
  const [query, setQuery] = React.useState(value?.city || "");
  const [results, setResults] = React.useState([]);
  const [open, setOpen] = React.useState(false);
  const elRef = React.useRef(null);
  const mapRef = React.useRef(null);
  const markerRef = React.useRef(null);

  // Debounced geocoding as the curator types.
  React.useEffect(() => {
    if (!token || !query.trim()) {
      setResults([]);
      return;
    }
    const id = setTimeout(async () => {
      const r = await geocode(query, token);
      setResults(r);
      setOpen(r.length > 0);
    }, 300);
    return () => clearTimeout(id);
  }, [query, token]);

  const pick = (r) => {
    setQuery(r.shortName);
    setResults([]);
    setOpen(false);
    onChange({ city: r.shortName, lat: r.lat, lng: r.lng });
  };

  // Create the map once a token is available; keep the marker in sync with value.
  React.useEffect(() => {
    if (!token || !elRef.current) return;
    if (!mapRef.current) {
      mapboxgl.accessToken = token;
      const hasPt = value?.lat != null && value?.lng != null;
      mapRef.current = new mapboxgl.Map({
        container: elRef.current,
        style: "mapbox://styles/mapbox/light-v11",
        center: hasPt ? [value.lng, value.lat] : [-99.133, 19.432],
        zoom: hasPt ? 12 : 9,
        attributionControl: false,
      });
    }
    const map = mapRef.current;
    if (value?.lat != null && value?.lng != null) {
      if (!markerRef.current) {
        markerRef.current = new mapboxgl.Marker({ color: "#117360", draggable: true })
          .setLngLat([value.lng, value.lat])
          .addTo(map);
        markerRef.current.on("dragend", () => {
          const ll = markerRef.current.getLngLat();
          onChange({ city: query || value?.city || "", lat: ll.lat, lng: ll.lng });
        });
      } else {
        markerRef.current.setLngLat([value.lng, value.lat]);
      }
      map.easeTo({ center: [value.lng, value.lat], duration: 300 });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, value?.lat, value?.lng]);

  React.useEffect(
    () => () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    },
    []
  );

  // No token → plain text input (stores the name only).
  if (token === "") {
    return (
      <input
        type="text"
        value={query}
        onChange={(e) => {
          setQuery(e.target.value);
          onChange({ city: e.target.value, lat: value?.lat ?? null, lng: value?.lng ?? null });
        }}
      />
    );
  }

  return (
    <div className="locfield">
      <div className="locfield__search">
        <input
          type="text"
          value={query}
          placeholder={t("loc_search_ph")}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => results.length && setOpen(true)}
          onBlur={() => setTimeout(() => setOpen(false), 150)}
        />
        {open && results.length > 0 && (
          <ul className="locfield__results">
            {results.map((r) => (
              <li key={r.id}>
                <button type="button" onMouseDown={() => pick(r)}>{r.name}</button>
              </li>
            ))}
          </ul>
        )}
      </div>
      <div ref={elRef} className="locfield__map" />
      {token === undefined && <p className="apply__hint">{t("loading")}</p>}
    </div>
  );
}
