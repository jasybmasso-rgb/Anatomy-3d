import { useEffect, useState } from "react";
import { isIphone, isStandaloneDisplay } from "../lib/pwaClient";

const STORAGE_KEY = "anatomy3d.iosInstallHint";

export function IosInstallHint() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!isIphone() || isStandaloneDisplay()) return;
    try {
      if (localStorage.getItem(STORAGE_KEY) === "dismissed") return;
    } catch {
      /* show the hint when storage is blocked */
    }
    setOpen(true);
  }, []);

  if (!open) return null;

  function dismiss() {
    try {
      localStorage.setItem(STORAGE_KEY, "dismissed");
    } catch {
      /* the hint still closes for this visit */
    }
    setOpen(false);
  }

  return (
    <div className="ios-install" role="note">
      <p>
        Sur iPhone : touchez <strong>Partager</strong>, puis <strong>Ajouter à l’écran d’accueil</strong>.
      </p>
      <button type="button" onClick={dismiss}>
        Compris
      </button>
    </div>
  );
}
