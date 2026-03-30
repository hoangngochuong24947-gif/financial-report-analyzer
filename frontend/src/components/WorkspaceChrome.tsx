import type { ReactNode } from "react";
import type { WorkspaceRoute, WorkspaceTab } from "../lib/routing";

export function WorkspaceChrome(props: {
  title: string;
  subtitle: string;
  tabs: WorkspaceTab[];
  activeRoute: WorkspaceRoute;
  onNavigate: (route: WorkspaceRoute) => void;
  controls?: ReactNode;
  leftRail: ReactNode;
  rightRail: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="app-shell">
      <div className="shell-glow shell-glow-a" aria-hidden="true" />
      <div className="shell-glow shell-glow-b" aria-hidden="true" />
      <div className="shell-noise" aria-hidden="true" />

      <div className="workspace-frame">
        <aside className="workspace-rail workspace-rail-left">{props.leftRail}</aside>

        <section className="workspace-main">
          <header className="workspace-masthead panel">
            <div className="masthead-copy">
              <span className="eyebrow">A-share intelligence workspace</span>
              <h1>{props.title}</h1>
              <p>{props.subtitle}</p>
            </div>

            <div className="route-tabs" role="tablist" aria-label="Workspace pages">
              {props.tabs.map((tab) => (
                <button
                  key={tab.route}
                  type="button"
                  role="tab"
                  aria-selected={tab.route === props.activeRoute}
                  className={`route-tab ${tab.route === props.activeRoute ? "route-tab-active" : ""}`}
                  onClick={() => props.onNavigate(tab.route)}
                >
                  <span>{tab.label}</span>
                  <small>{tab.note}</small>
                </button>
              ))}
            </div>
          </header>

          {props.controls ? <div className="workspace-controls panel">{props.controls}</div> : null}

          <div className="workspace-canvas">{props.children}</div>
        </section>

        <aside className="workspace-rail workspace-rail-right">{props.rightRail}</aside>
      </div>
    </div>
  );
}
