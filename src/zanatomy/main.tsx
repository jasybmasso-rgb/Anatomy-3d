import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { OriginalApp } from "./OriginalApp";
import "../index.css";
import "./original.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <OriginalApp />
  </StrictMode>,
);
