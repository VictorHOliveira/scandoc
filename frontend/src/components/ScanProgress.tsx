interface Props {
  progress: { percent: number; stage: string };
}

export default function ScanProgress({ progress }: Props) {
  return (
    <div className="scan-progress">
      <div className="progress-track">
        <div
          className="progress-fill"
          role="progressbar"
          aria-valuenow={progress.percent}
          aria-valuemin={0}
          aria-valuemax={100}
          style={{ width: `${progress.percent}%` }}
        />
      </div>
      <p className="muted">{progress.stage}</p>
    </div>
  );
}
