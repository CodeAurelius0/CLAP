/**
 * CheckItem — A single pass/warn/fail check result.
 */
export default function CheckItem({ status, label, detail }) {
  const icons = {
    pass: '✓',
    warn: '⚠',
    fail: '✕',
    info: 'ℹ',
  };

  return (
    <div className="check-item">
      <span className={`check-icon ${status}`}>{icons[status] || '•'}</span>
      <div>
        <div className="check-label">{label}</div>
        {detail && <div className="check-detail">{detail}</div>}
      </div>
    </div>
  );
}
