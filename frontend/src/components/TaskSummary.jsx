import React from 'react';

/**
 * TaskSummary Component
 * ---------------------
 * Displays 3 metric cards showing:
 * 1. Total Tasks
 * 2. Pending Tasks
 * 3. Completed Tasks
 *
 * Props:
 * - total: number of all tasks
 * - pending: number of incomplete tasks
 * - completed: number of finished tasks
 */
function TaskSummary({ total, pending, completed }) {
  // Calculate completion percentage safely (avoid division by 0)
  const completionRate = total > 0 ? Math.round((completed / total) * 100) : 0;

  return (
    <section className="summary-grid" aria-label="Task Summary Statistics">
      {/* 1. Total Tasks Card */}
      <div className="summary-card total-card">
        <div className="card-header-row">
          <span className="card-label">Total Tasks</span>
          <div className="card-icon total-icon">📋</div>
        </div>
        <div className="card-value">{total}</div>
        <div className="card-footer">
          <span className="footer-subtext">All active & finished items</span>
        </div>
      </div>

      {/* 2. Pending Tasks Card */}
      <div className="summary-card pending-card">
        <div className="card-header-row">
          <span className="card-label">Pending Tasks</span>
          <div className="card-icon pending-icon">⏳</div>
        </div>
        <div className="card-value">{pending}</div>
        <div className="card-footer">
          <span className="footer-pill pending-pill">Needs Attention</span>
        </div>
      </div>

      {/* 3. Completed Tasks Card */}
      <div className="summary-card completed-card">
        <div className="card-header-row">
          <span className="card-label">Completed Tasks</span>
          <div className="card-icon completed-icon">✅</div>
        </div>
        <div className="card-value">{completed}</div>
        <div className="card-footer">
          <span className="footer-pill completed-pill">{completionRate}% Done</span>
        </div>
      </div>
    </section>
  );
}

export default TaskSummary;
