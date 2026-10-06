import { useEffect } from "react";

type CreditsDialogProps = {
  open: boolean;
  onClose: () => void;
};

export function CreditsDialog({ open, onClose }: CreditsDialogProps) {
  useEffect(() => {
    if (!open) return;
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="credits-backdrop" role="presentation" onMouseDown={onClose}>
      <div
        className="credits-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="credits-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <h2 id="credits-title">Crédits</h2>
        <p>
          Squelette, ligaments, fascias, muscles, nerfs, organes et vaisseaux :{" "}
          <strong>BodyParts3D</strong>, Copyright© 2008 The Database Center for Life Science,
          licence{" "}
          <a href="https://creativecommons.org/licenses/by-sa/2.1/jp/deed.fr" target="_blank" rel="noreferrer">
            CC BY-SA 2.1 Japon
          </a>
          .
        </p>
        <p>
          Paroi abdominale en mode Z-Anatomy (droit, oblique externe, oblique interne, transverse) :{" "}
          <strong>Z-Anatomy</strong> (Gauthier Kervyn, Marcin Zielinski), licence{" "}
          <a href="https://creativecommons.org/licenses/by-sa/4.0/deed.fr" target="_blank" rel="noreferrer">
            CC BY-SA 4.0
          </a>
          , dérivé de BodyParts3D. Maillage allégé à 10 % (meshoptimizer) puis compressé en Draco.
          La gaine des droits reste le schéma procédural de l’application : la collection « rectus
          sheath » de la source est vide. Le pyramidal de l’abdomen n’est pas dans ce maillage.
        </p>
        <p>Code de l’application : MIT.</p>
        <button type="button" className="reset-btn" onClick={onClose}>
          Fermer
        </button>
      </div>
    </div>
  );
}
