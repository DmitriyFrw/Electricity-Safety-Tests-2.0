import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { initCsrf, setupCsrfInterceptor } from "./api/csrf";
import "../../app/static/dashboard.css";

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
