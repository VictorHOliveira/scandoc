import type { ReactNode } from "react";

export default function StaticPage({
  title,
  updated,
  children,
}: {
  title: string;
  updated?: string;
  children: ReactNode;
}) {
  return (
    <div className="static-page">
      <h2>{title}</h2>
      {updated && <p className="muted updated-at">Última atualização: {updated}</p>}
      <div className="card static-card">{children}</div>
    </div>
  );
}
