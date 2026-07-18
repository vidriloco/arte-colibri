// Central API client. Attaches the auth token, normalizes errors, handles
// JSON + multipart. All screens call these helpers, never fetch directly.

const BASE = import.meta.env.VITE_API_BASE || "/api";
const TOKEN_KEY = "ac_token";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}
export function setToken(token) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  constructor(status, data) {
    super(typeof data === "string" ? data : data?.detail || "Request failed");
    this.status = status;
    this.data = data; // field errors map, when available
  }
}

async function request(path, { method = "GET", body, multipart = false } = {}) {
  const headers = {};
  const token = getToken();
  if (token) headers["Authorization"] = `Token ${token}`;

  let payload;
  if (multipart) {
    payload = body; // FormData; let the browser set the boundary
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  const res = await fetch(`${BASE}${path}`, { method, headers, body: payload });
  if (res.status === 204) return null;

  let data = null;
  const text = await res.text();
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
  }
  if (!res.ok) throw new ApiError(res.status, data);
  return data;
}

export const api = {
  get: (p) => request(p),
  post: (p, body) => request(p, { method: "POST", body }),
  put: (p, body) => request(p, { method: "PUT", body }),
  patch: (p, body) => request(p, { method: "PATCH", body }),
  del: (p) => request(p, { method: "DELETE" }),
  upload: (p, formData) => request(p, { method: "POST", body: formData, multipart: true }),
};

// ── Endpoint helpers ─────────────────────────────────────────────────────────
export const Public = {
  home: () => api.get("/home/"),
  gallery: ({ tags = [], sort = "recent", page = 1 } = {}) => {
    const q = new URLSearchParams();
    tags.forEach((t) => q.append("tag", t));
    if (sort) q.set("sort", sort);
    if (page) q.set("page", page);
    return api.get(`/artworks/?${q.toString()}`);
  },
  artwork: (slug) => api.get(`/artworks/${slug}/`),
  artists: () => api.get("/artists/"),
  artist: (slug) => api.get(`/artists/${slug}/`),
  locations: () => api.get("/locations/"),
  meta: () => api.get("/meta/"),
  seo: (page = "default") => api.get(`/seo/?page=${encodeURIComponent(page)}`),
  inquire: (slug, body) => api.post(`/artworks/${slug}/inquiries/`, body),
};

export const Auth = {
  signup: (body) => api.post("/auth/signup/", body),
  login: (body) => api.post("/auth/login/", body),
  logout: () => api.post("/auth/logout/", {}),
  me: () => api.get("/auth/me/"),
};

export const Dash = {
  profile: () => api.get("/dashboard/profile/"),
  saveProfile: (body) => api.patch("/dashboard/profile/", body),
  submitProfile: () => api.post("/dashboard/profile/", {}),
  artworks: () => api.get("/dashboard/artworks/"),
  artwork: (id) => api.get(`/dashboard/artworks/${id}/`),
  createArtwork: (body) => api.post("/dashboard/artworks/", body),
  updateArtwork: (id, body) => api.patch(`/dashboard/artworks/${id}/`, body),
  deleteArtwork: (id) => api.del(`/dashboard/artworks/${id}/`),
  submitArtwork: (id) => api.post(`/dashboard/artworks/${id}/submit/`, {}),
  addImage: (id, formData) => api.upload(`/dashboard/artworks/${id}/images/`, formData),
  deleteImage: (id, imageId) => api.del(`/dashboard/artworks/${id}/images/${imageId}/`),
  reorderImages: (id, body) => api.post(`/dashboard/artworks/${id}/images/reorder/`, body),
  inquiries: () => api.get("/dashboard/inquiries/"),
};

export const Curation = {
  queue: () => api.get("/curation/queue/"),
  allArtworks: (status) =>
    api.get(`/curation/artworks/${status ? `?status=${status}` : ""}`),
  approveArtwork: (id) => api.post(`/curation/artworks/${id}/approve/`, {}),
  rejectArtwork: (id, notes) => api.post(`/curation/artworks/${id}/reject/`, { notes }),
  featureArtwork: (id) => api.post(`/curation/artworks/${id}/feature/`, {}),
  approveArtist: (id) => api.post(`/curation/artists/${id}/approve/`, {}),
  rejectArtist: (id, notes) => api.post(`/curation/artists/${id}/reject/`, { notes }),
  inquiries: () => api.get("/curation/inquiries/"),
  seo: () => api.get("/curation/seo/"),
  saveSeo: (key, body) => api.patch(`/curation/seo/${key}/`, body),
  uploadSeoImage: (key, formData) => api.upload(`/curation/seo/${key}/image/`, formData),
};
