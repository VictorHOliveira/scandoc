export default function DocumentPreview({ image }: { image: string | null }) {
  if (!image) {
    return (
      <p className="empty-state">
        Não foi possível gerar a imagem anotada para este formato.
      </p>
    );
  }
  return (
    <div className="doc-preview">
      <img src={`data:image/png;base64,${image}`} alt="Documento com regiões suspeitas destacadas" />
      <p className="hint">
        Regiões em <span style={{ color: "#F87171" }}>vermelho</span> indicam suspeitas.
      </p>
    </div>
  );
}
