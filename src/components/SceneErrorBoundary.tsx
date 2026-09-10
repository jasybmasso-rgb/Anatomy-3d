import { Component, type ErrorInfo, type ReactNode } from "react";

type Props = { children: ReactNode };
type State = { error: Error | null };

export class SceneErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Anatomy-3d scene error", error, info.componentStack);
  }

  render() {
    if (!this.state.error) return this.props.children;

    return (
      <div className="scene-error" role="alert">
        <p className="scene-error-kicker">Erreur d’affichage</p>
        <h2>Impossible d’afficher la scène 3D</h2>
        <p>
          WebGL ou Three.js a rencontré une erreur. Vérifiez que l’accélération graphique est
          activée, puis rechargez la page.
        </p>
        <pre>{this.state.error.message}</pre>
      </div>
    );
  }
}
