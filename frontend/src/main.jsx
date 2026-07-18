import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App.jsx";
import { LangProvider } from "./i18n.jsx";
import { AuthProvider } from "./auth.jsx";
import "./styles.css";
import "./extra.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <LangProvider>
        <AuthProvider>
          <App />
        </AuthProvider>
      </LangProvider>
    </BrowserRouter>
  </React.StrictMode>
);
