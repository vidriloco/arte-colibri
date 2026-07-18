// Maps the prototype's {name, id} screen descriptors to SPA routes, so screen
// code can keep calling go({name, id}).
import { useNavigate } from "react-router-dom";

export function pathFor(s) {
  switch (s.name) {
    case "home":
      return "/";
    case "gallery":
      return "/gallery";
    case "artwork":
      return `/artwork/${s.id}`;
    case "artist":
      return `/artist/${s.id}`;
    case "artists":
      return "/artists";
    case "locations":
      return s.region ? `/locations#region-${s.region}` : "/locations";
    case "dashboard":
      return "/dashboard";
    default:
      return "/";
  }
}

export function useGo() {
  const navigate = useNavigate();
  return (s) => navigate(pathFor(s));
}
