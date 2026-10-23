import React, { useState } from 'react';

/**
 * TaskForm Component
 * ------------------
 * Provides input fields for adding a new task:
 * - Title (required)
 * - Description (optional)
 *
 * Props:
 * - onAddTask: callback function to send the new task data back to App.jsx
 */
function TaskForm({ onAddTask }) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();

    // Basic validation: Title cannot be empty
    if (!title.trim()) {
      setErrorMessage('Please enter a task title before submitting.');
      return;
    }

    // Pass data up to parent state in App.jsx
    onAddTask({
      title: title.trim(),
      description: description.trim(),
    });

    // Reset input fields and error
    setTitle('');
    setDescription('');
    setErrorMessage('');
  };

  return (
    <section className="form-card" aria-label="Create New Task">
      <div className="form-header">
        <h2 className="form-title">
          <span className="form-icon">✨</span> Create New Task
        </h2>
        <p className="form-subtitle">What would you like to accomplish today?</p>
      </div>

      <form onSubmit={handleSubmit} className="task-form">
        {/* Title Input */}
        <div className="form-group">
          <label htmlFor="task-title" className="form-label">
            Task Title <span className="required-star">*</span>
          </label>
          <input
            id="task-title"
            type="text"
            className={`form-input ${errorMessage ? 'input-error' : ''}`}
            placeholder="e.g., Design database schema for user profiles"
            value={title}
            onChange={(e) => {
              setTitle(e.target.value);
              if (errorMessage) setErrorMessage('');
            }}
          />
          {errorMessage && <span className="error-text">⚠️ {errorMessage}</span>}
        </div>

        {/* Description Input */}
        <div className="form-group">
          <label htmlFor="task-description" className="form-label">
            Description <span className="optional-tag">(Optional)</span>
          </label>
          <textarea
            id="task-description"
            rows="3"
            className="form-textarea"
            placeholder="Add relevant notes, links, or sub-tasks..."
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </div>

        {/* Submit Button */}
        <div className="form-actions">
          <button type="submit" className="btn-primary" id="add-task-submit-btn">
            <span className="btn-icon">➕</span> Add Task
          </button>
        </div>
      </form>
    </section>
  );
}

export default TaskForm;
