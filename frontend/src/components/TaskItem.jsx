import React from 'react';

/**
 * TaskItem Component
 * ------------------
 * Renders an individual task card with:
 * - Status indicator & title (with strike-through when completed)
 * - Optional description
 * - Action buttons: Complete toggle, Edit, Delete
 *
 * Props:
 * - task: task object { id, title, description, completed, createdAt }
 * - onToggleComplete: function(taskId)
 * - onEdit: function(task)
 * - onDelete: function(taskId)
 */
function TaskItem({ task, onToggleComplete, onEdit, onDelete }) {
  const { id, title, description, completed, created_at, createdAt } = task;

  const formatTimestamp = (rawDate) => {
    if (!rawDate) return '';
    try {
      const parsed = new Date(rawDate.includes('T') ? rawDate : rawDate.replace(' ', 'T') + 'Z');
      if (isNaN(parsed.getTime())) return rawDate;
      return parsed.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return rawDate;
    }
  };

  const displayTime = formatTimestamp(created_at) || createdAt;

  return (
    <article
      className={`task-card ${completed ? 'task-completed' : 'task-pending'}`}
      id={`task-card-${id}`}
    >
      <div className="task-card-main">
        {/* Checkbox / Completion Toggle Button */}
        <button
          type="button"
          className={`task-checkbox-btn ${completed ? 'checked' : ''}`}
          onClick={() => onToggleComplete(id, completed)}
          title={completed ? 'Mark as pending' : 'Mark as completed'}
          aria-label={completed ? 'Mark as pending' : 'Mark as completed'}
        >
          {completed ? '✓' : ''}
        </button>

        {/* Task Details */}
        <div className="task-content">
          <div className="task-header-row">
            <h3 className="task-title">{title}</h3>
            <span className={`task-badge ${completed ? 'badge-completed' : 'badge-pending'}`}>
              {completed ? 'Completed' : 'Pending'}
            </span>
          </div>

          {description && <p className="task-description">{description}</p>}

          {displayTime && (
            <div className="task-meta">
              <span className="task-timestamp">🕒 {displayTime}</span>
            </div>
          )}
        </div>
      </div>

      {/* Action Buttons Toolbar */}
      <div className="task-actions-toolbar">
        {/* 1. Complete / Undo Button */}
        <button
          type="button"
          className={`btn-action btn-complete ${completed ? 'btn-undo' : ''}`}
          onClick={() => onToggleComplete(id, completed)}
          title={completed ? 'Mark as incomplete' : 'Mark as complete'}
        >
          {completed ? '↩️ Mark Pending' : '✅ Complete'}
        </button>

        {/* 2. Edit Button */}
        <button
          type="button"
          className="btn-action btn-edit"
          onClick={() => onEdit(task)}
          title="Edit task title and description"
        >
          ✏️ Edit
        </button>

        {/* 3. Delete Button */}
        <button
          type="button"
          className="btn-action btn-delete"
          onClick={() => onDelete(id)}
          title="Delete task permanently"
        >
          🗑️ Delete
        </button>
      </div>
    </article>
  );
}

export default TaskItem;
