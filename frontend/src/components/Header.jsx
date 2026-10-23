import React from 'react';

/**
 * Header Component
 * ----------------
 * Displays the main TaskFlow brand header, application badge,
 * and current date.
 */
function Header() {
  const today = new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'short',
    day: 'numeric',
  });

  return (
    <header className="taskflow-header">
      <div className="header-top">
        <div className="brand-badge">
          <span className="badge-dot"></span>
          <span>Personal Workspace</span>
        </div>
        <div className="header-date">
          <span>📅 {today}</span>
        </div>
      </div>

      <div className="header-content">
        <h1 className="brand-title">
          Task<span>Flow</span>
        </h1>
        <p className="brand-tagline">
          Organize, track, and complete your daily goals with a streamlined full-stack workflow.
        </p>
      </div>
    </header>
  );
}

export default Header;
