/**
 * Sidebar — Left navigation panel.
 */

const NAV_ITEMS = [
  { id: 'overview',  label: 'Overview',  icon: '⌂' },
  { id: 'analyse',   label: 'Analyse',   icon: '◎' },
  { id: 'prepare',   label: 'Prepare',   icon: '⚙' },
  { id: 'github',    label: 'GitHub',    icon: '↗' },
];

export default function Sidebar({ activePage, onNavigate, projectSelected }) {
  return (
    <aside className="sidebar">
      <nav className="sidebar-nav">
        <div className="sidebar-section">
          <div className="sidebar-section-title">CLAP</div>
          {NAV_ITEMS.map((item) => {
            // Disable pages beyond overview if no project is selected
            const disabled = !projectSelected && item.id !== 'overview';
            return (
              <button
                key={item.id}
                className={`sidebar-item ${activePage === item.id ? 'active' : ''}`}
                onClick={() => !disabled && onNavigate(item.id)}
                style={disabled ? { opacity: 0.35, cursor: 'default' } : {}}
                title={disabled ? 'Select a project first' : item.label}
              >
                <span className="sidebar-item-icon">{item.icon}</span>
                {item.label}
              </button>
            );
          })}
        </div>
      </nav>
      <div className="sidebar-footer">
        <span className="sidebar-version">v0.1.0</span>
      </div>
    </aside>
  );
}
