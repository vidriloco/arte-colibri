import React from "react";
import { useOutletContext } from "react-router-dom";
import { useAuth } from "../auth.jsx";
import { Loading } from "../components/primitives.jsx";
import { SignIn } from "./SignIn.jsx";
import { ArtistDashboard } from "./ArtistDashboard.jsx";
import { CuratorDashboard } from "./CuratorDashboard.jsx";

export function Dashboard() {
  const { ready, user, role } = useAuth();
  const ctx = useOutletContext();
  const onApply = ctx?.onApply;

  if (!ready) return <main className="screen"><Loading /></main>;
  if (!user) return <SignIn onApply={onApply} />;
  return role === "curator" ? <CuratorDashboard /> : <ArtistDashboard />;
}
