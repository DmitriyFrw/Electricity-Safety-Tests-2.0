import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { initCsrf, setupCsrfInterceptor } from "./api/csrf";

import "./styles/razvivaisia/variables.css";
import "./styles/razvivaisia/reset.css";
import "./styles/razvivaisia/base.css";
import "./styles/razvivaisia/components.css";
import "./styles/razvivaisia/layout.css";
import "./styles/razvivaisia/pages.css";
import "./styles/razvivaisia/responsive.css";
import "./styles/react-bridge.css";
import "./styles/constructor.css";
import "./styles/constructor-catalog.css";
import "./styles/responsive-app.css";
import "./styles/test-flow.css";
import "./styles/mockup-theme.css";
import "./styles/profile-page.css";

setupCsrfInterceptor();

async function bootstrap() {
  try {
    await initCsrf();
  } catch (e) {
    console.error("Не удалось получить CSRF-токен", e);
  }

  ReactDOM.createRoot(document.getElementById("root")!).render(
    <React.StrictMode>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </React.StrictMode>
  );
}

void bootstrap();
