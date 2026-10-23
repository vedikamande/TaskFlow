import React, { useState, useEffect } from 'react';

/**
 * EditTaskModal Component
 * -----------------------
 * Modal dialog for editing an existing task's title and description.
 *
 * Props:
 * - task: task object being edited
 * - onSave: function(updatedTask)
 * - onClose: function() to close modal without saving
 */
function EditTaskModal({ task, onSave, onClose }) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  // Sync state whenever the task prop changes
  useEffect(() => {
    if (task) {
      setTitle(task.title || '');
      setDescription(task.description || '');
      setErrorMessage('');
    }
  }, [task]);

  if (!task) return null;

  const handleSubmit = (e) => {
    e.preventDefault();

    if (!title.trim()) {
      setErrorMessage('Title cannot be empty.');
      return;
    }

    onSave({
      ...task,
      title: title.trim(),
      description: description.trim(),
    });
  };

  return (
    <div className="modal-backdrop" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2 className="modal-title">✏️ Edit Task</h2>
          <button
            type="button"
            className="modal-close-btn"
            onClick={onClose}
            aria-label="Close modal"
          >
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit} className="modal-form">
          <div className="form-group">
            <label htmlFor="edit-task-title" className="form-label">
              Task Title <span className="required-star">*</span>
            </label>
            <input
              id="edit-task-title"
              type="text"
              className={`form-input ${errorMessage ? 'input-error' : ''}`}
              value={title}
              onChange={(e) => {
                setTitle(e.target.value);
                if (errorMessage) setErrorMessage('');
              }}
              autoFocus
            />
            {errorMessage && <span className="error-text">⚠️ {errorMessage}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="edit-task-desc" className="form-label">
              Description <span className="optional-tag">(Optional)</span>
            </label>
            <textarea
              id="edit-task-desc"
              rows="3"
              className="form-textarea"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>

          <div className="modal-actions">
            <button type="button" className="btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn-primary" id="save-task-edit-btn">
              💾 Save Changes
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default EditTaskModal;
