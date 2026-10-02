/**
 * FileList — Scrollable list of file paths.
 */
export default function FileList({ files, maxVisible = 200 }) {
  const visible = files.slice(0, maxVisible);
  const remaining = files.length - visible.length;

  return (
    <div className="file-list">
      {visible.map((file, i) => (
        <div className="file-list-item" key={i}>
          <span style={{ opacity: 0.4 }}>📄</span>
          {file}
        </div>
      ))}
      {remaining > 0 && (
        <div className="file-list-count">
          … and {remaining} more file{remaining !== 1 ? 's' : ''}
        </div>
      )}
    </div>
  );
}
