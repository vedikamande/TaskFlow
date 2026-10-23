import React from 'react';
import TaskItem from './TaskItem';

/**
 * TaskList Component
 * ------------------
 * Renders the collection of tasks, along with filter tabs:
 * - All
 * - Pending
 * - Completed
 *
 * Props:
 * - tasks: filtered array of task objects
 * - currentFilter: 'all' | 'pending' | 'completed'
 * - onFilterChange: function(filterName)
 * - counts: { total, pending, completed }
 * - onToggleComplete: function(taskId)
 * - onEdit: function(task)
 * - onDelete: function(taskId)
 */
function TaskList({
  tasks,
  currentFilter,
  onFilterChange,
  counts,
  onToggleComplete,
  onEdit,
  onDelete,
}) {
  return (
    <section className="task-list-section" aria-label="Task Management List">
      {/* List Header with Filter Tabs */}
      <div className="task-list-header">
        <div className="list-title-group">
          <h2 className="list-title">My Tasks</h2>
          <span className="tasks-counter-tag">{tasks.length} displayed</span>
        </div>

        {/* Filter Navigation */}
        <div className="filter-tabs">
          <button
            type="button"
            className={`filter-tab ${currentFilter === 'all' ? 'active' : ''}`}
            onClick={() => onFilterChange('all')}
          >
            All <span className="tab-pill">{counts.total}</span>
          </button>
          <button
            type="button"
            className={`filter-tab ${currentFilter === 'pending' ? 'active' : ''}`}
            onClick={() => onFilterChange('pending')}
          >
            Pending <span className="tab-pill">{counts.pending}</span>
          </button>
          <button
            type="button"
            className={`filter-tab ${currentFilter === 'completed' ? 'active' : ''}`}
            onClick={() => onFilterChange('completed')}
          >
            Completed <span className="tab-pill">{counts.completed}</span>
          </button>
        </div>
      </div>

      {/* Tasks Container or Empty State */}
      {tasks.length === 0 ? (
        <div className="empty-state-card">
          <div className="empty-icon">📂</div>
          <h3 className="empty-title">No tasks found</h3>
          <p className="empty-description">
            {currentFilter === 'all'
              ? 'Your task list is empty. Add a new task above to get started!'
              : currentFilter === 'pending'
              ? 'Great job! You have no pending tasks right now.'
              : 'You have not completed any tasks yet. Finish a task to see it here!'}
          </p>
        </div>
      ) : (
        <div className="tasks-container">
          {tasks.map((task) => (
            <TaskItem
              key={task.id}
              task={task}
              onToggleComplete={onToggleComplete}
              onEdit={onEdit}
              onDelete={onDelete}
            />
          ))}
        </div>
      )}
    </section>
  );
}

export default TaskList;
