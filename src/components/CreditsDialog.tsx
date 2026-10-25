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
          Mode « Anciens (procéduraux) » — squelette, ligaments, fascias, muscles, nerfs, organes et
          vaisseaux : <strong>BodyParts3D</strong>, Copyright© 2008 The Database Center for Life
          Science, licence{" "}
          <a href="https://creativecommons.org/licenses/by-sa/2.1/jp/deed.fr" target="_blank" rel="noreferrer">
            CC BY-SA 2.1 Japon
          </a>
          . Certains nerfs, ligaments et fascias de ce mode sont des schémas pédagogiques.
        </p>
        <p>
          Mode « Z-Anatomy » (défaut) — os, cartilages, muscles, fascias, ligaments, nerfs, organes
          et vaisseaux : <strong>Z-Anatomy</strong> (Gauthier Kervyn, Marcin Zielinski),{" "}
          <code>Startup.blend</code> du 2 mai 2023, licence{" "}
          <a href="https://creativecommons.org/licenses/by-sa/4.0/deed.fr" target="_blank" rel="noreferrer">
            CC BY-SA 4.0
          </a>
          , dérivé de BodyParts3D (CC BY-SA 2.1 Japon). Chaque système est un GLB Draco chargé
          seulement quand sa couche est ouverte. Les vaisseaux du tronc et l’encéphale sont
          légèrement simplifiés ; mains, pieds, muscles, os, fascias, ligaments et nerfs périphériques
          restent au détail d’origine. Le menu Couches permet de revenir aux anciens maillages.
        </p>
        <p>Code de l’application : MIT.</p>
        <button type="button" className="reset-btn" onClick={onClose}>
          Fermer
        </button>
      </div>
    </div>
  );
}
