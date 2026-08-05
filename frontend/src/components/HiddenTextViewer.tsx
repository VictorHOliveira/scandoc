export default function HiddenTextViewer({ text }: { text: string }) {
  if (!text || !text.trim()) {
    return <p className="empty-state">Nenhum texto oculto foi extraído.</p>;
  }
  return (
    <div className="hidden-text">
      <p className="hint">
        Texto extraído de trechos de baixo contraste, fonte minúscula, ocultos ou cobertos:
      </p>
      <pre>{text}</pre>
    </div>
  );
}
