import { useRef, useState, type DragEvent } from "react";

interface Props {
  onScan: (file: File) => void;
  busy: boolean;
}

const ACCEPTED = ".pdf,.docx,.txt,.md,.markdown,.html,.htm,.png,.jpg,.jpeg,.gif,.bmp,.webp,.tiff";

export default function UploadZone({ onScan, busy }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  const handleFile = (file: File | undefined | null) => {
    if (file && !busy) onScan(file);
  };

  const onDrop = (e: DragEvent) => {
    e.preventDefault();
    setDragging(false);
    handleFile(e.dataTransfer.files?.[0]);
  };

  return (
    <div
      className={`upload-zone${dragging ? " dragging" : ""}`}
      onClick={() => inputRef.current?.click()}
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={onDrop}
    >
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED}
        hidden
        onChange={(e) => {
          handleFile(e.target.files?.[0]);
          e.target.value = "";
        }}
      />
      <div className="upload-icon">📄</div>
      <p className="upload-title">
        {busy ? "Analisando documento..." : "Arraste um documento aqui ou clique para escolher"}
      </p>
      <p className="upload-sub">
        Formatos: PDF, DOCX, TXT, MD, HTML e imagens (PNG/JPG)
      </p>
    </div>
  );
}
