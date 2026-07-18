// Mapbox helpers: the public token (served by the backend via /api/meta) and a
// forward-geocoder scoped to Mexican municipalities.
import React from "react";
import { Public } from "../api.js";

// Module-level cache so multiple maps don't each refetch /api/meta.
// undefined = not fetched yet, "" = fetched but none configured, string = token.
let _token; // undefined
let _pending = null;

export function useMapboxToken() {
  const [token, setToken] = React.useState(_token);
  React.useEffect(() => {
    if (_token !== undefined) {
      setToken(_token);
      return;
    }
    _pending =
      _pending ||
      Public.meta()
        .then((m) => {
          _token = m?.mapbox_token || "";
          return _token;
        })
        .catch(() => {
          _token = "";
          return _token;
        });
    let alive = true;
    _pending.then((tok) => alive && setToken(tok));
    return () => {
      alive = false;
    };
  }, []);
  return token; // undefined while loading, "" if none, else the token
}

// Forward-geocode a query to Mexican municipalities / places.
export async function geocode(query, token, { limit = 6 } = {}) {
  if (!query || !query.trim() || !token) return [];
  const url =
    "https://api.mapbox.com/geocoding/v5/mapbox.places/" +
    encodeURIComponent(query.trim()) +
    ".json?country=mx&language=es&limit=" +
    limit +
    "&types=place,locality,district,region&access_token=" +
    token;
  try {
    const res = await fetch(url);
    if (!res.ok) return [];
    const data = await res.json();
    return (data.features || []).map((f) => ({
      id: f.id,
      name: f.place_name, // "Coyoacán, Ciudad de México, México"
      shortName: f.text, // "Coyoacán"
      lat: f.center[1],
      lng: f.center[0],
    }));
  } catch {
    return [];
  }
}
