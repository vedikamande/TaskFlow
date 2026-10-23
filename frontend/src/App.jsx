import React, { useState, useEffect, useCallback } from 'react';
import Header from './components/Header';
import TaskSummary from './components/TaskSummary';
import TaskForm from './components/TaskForm';
import TaskList from './components/TaskList';
import EditTaskModal from './components/EditTaskModal';
import {
  getAllTasks,
  createTask,
  updateTask,
  markTaskCompleted,
  deleteTask,
} from './services/taskApi';
import './App.css';

/**
 * App Component - Root TaskFlow Dashboard
 * ---------------------------------------
 * Connects directly to the Flask REST backend running at http://127.0.0.1:5000.
 * Manages full lifecycle state: loading, error messages, active filter,
 * editing modal, and real-time synchronization with the SQLite database.
 */
function App() {
  // 1. Core State
  const [tasks, setTasks] = useState([]);
  const [stats, setStats] = useState({ total: 0, pending: 0, completed: 0 });
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState('');
  const [filter, setFilter] = useState('all'); // 'all' | 'pending' | 'completed'
  const [editingTask, setEditingTask] = useState(null); // task being edited
  const [toastMessage, setToastMessage] = useState('');

  // Helper to show temporary notification toasts
  const showToast = (message) => {
    setToastMessage(message);
    setTimeout(() => setToastMessage(''), 3500);
  };

  /**
   * Load tasks from Flask backend: GET /api/tasks
   * Automatically updates both the tasks array and the computed metrics.
   */
  const loadTasks = useCallback(async (showLoadingSpinner = true) => {
    if (showLoadingSpinner) {
      setIsLoading(true);
    }
    setErrorMessage('');

    try {
      const data = await getAllTasks();
      const taskList = data.tasks || [];
      setTasks(taskList);

      if (data.stats) {
        setStats(data.stats);
      } else {
        const total = taskList.length;
        const completed = taskList.filter((t) => t.completed).length;
        setStats({ total, completed, pending: total - completed });
      }
    } catch (err) {
      console.error('Error fetching tasks from Flask backend:', err);
      setErrorMessage(
        err.message ||
          'Failed to connect to Flask backend at http://127.0.0.1:5000. Please ensure the Python server is running.'
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  // 2. Load tasks once when application opens
  useEffect(() => {
    loadTasks(true);
  }, [loadTasks]);

  // 3. Computed Metrics (Derived from state & backend stats)
  const totalTasks = stats.total;
  const completedTasks = stats.completed;
  const pendingTasks = stats.pending;

  // 4. Filtered task list based on active tab ('all' | 'pending' | 'completed')
  const filteredTasks = tasks.filter((task) => {
    if (filter === 'pending') return !task.completed;
    if (filter === 'completed') return task.completed;
    return true; // 'all'
  });

  /**
   * Feature 1: Create a new task (POST /api/tasks)
   * Validates title and refreshes the list on success.
   */
  const handleAddTask = async ({ title, description }) => {
    // Frontend validation: prevent empty submissions
    const cleanTitle = (title || '').trim();
    if (!cleanTitle) {
      showToast('⚠️ Task title is required.');
      return;
    }

    try {
      const result = await createTask({
        title: cleanTitle,
        description: (description || '').trim(),
      });

      showToast(`✨ Created: "${result.task?.title || cleanTitle}"`);

      // Refresh displayed tasks from database
      await loadTasks(false);
    } catch (err) {
      console.error('Failed to create task:', err);
      showToast(`❌ ${err.message || 'Error creating task'}`);
    }
  };

  /**
   * Feature 2: Toggle completion status (PATCH /api/tasks/:id/complete)
   * Updates SQLite record and refreshes metrics and lists.
   */
  const handleToggleComplete = async (taskId, currentStatus) => {
    const nextStatus = !currentStatus;
    try {
      await markTaskCompleted(taskId, nextStatus);
      showToast(nextStatus ? '🎉 Task marked as completed!' : '⏳ Task marked as pending.');

      // Refresh displayed tasks from database
      await loadTasks(false);
    } catch (err) {
      console.error('Failed to update task completion:', err);
      showToast(`❌ ${err.message || 'Error toggling completion'}`);
    }
  };

  /**
   * Feature 3: Delete task permanently (DELETE /api/tasks/:id)
   * Removes record from SQLite and refreshes list.
   */
  const handleDeleteTask = async (taskId) => {
    const taskToDelete = tasks.find((t) => t.id === taskId);
    try {
      await deleteTask(taskId);
      showToast(`🗑️ Deleted: "${taskToDelete?.title || 'Task'}"`);

      // Refresh displayed tasks from database
      await loadTasks(false);
    } catch (err) {
      console.error('Failed to delete task:', err);
      showToast(`❌ ${err.message || 'Error deleting task'}`);
    }
  };

  /**
   * Feature 4: Open Edit Modal
   */
  const handleOpenEdit = (task) => {
    setEditingTask(task);
  };

  /**
   * Feature 5: Save Edited Task (PUT /api/tasks/:id)
   * Updates SQLite and refreshes list.
   */
  const handleSaveEdit = async (updatedTask) => {
    const cleanTitle = (updatedTask.title || '').trim();
    if (!cleanTitle) {
      showToast('⚠️ Task title cannot be empty.');
      return;
    }

    try {
      await updateTask(updatedTask.id, {
        title: cleanTitle,
        description: (updatedTask.description || '').trim(),
        completed: updatedTask.completed,
      });

      setEditingTask(null);
      showToast('✏️ Task updated successfully!');

      // Refresh displayed tasks from database
      await loadTasks(false);
    } catch (err) {
      console.error('Failed to update task:', err);
      showToast(`❌ ${err.message || 'Error updating task'}`);
    }
  };

  return (
    <div className="taskflow-app">
      {/* Toast Notification */}
      {toastMessage && (
        <aside className="toast-notification" role="status" aria-live="polite">
          <span>🔔</span> {toastMessage}
        </aside>
      )}

      <div className="app-container">
        {/* Header with TaskFlow Branding */}
        <Header />

        {/* Backend API Connection Status Chip */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div className="api-status-chip">
            <span className="api-status-dot"></span>
            <span>Flask REST API Connected (http://127.0.0.1:5000)</span>
          </div>
          <button
            type="button"
            className="filter-tab"
            style={{ fontSize: '0.8rem', padding: '6px 12px' }}
            onClick={() => loadTasks(true)}
            title="Reload tasks from SQLite"
          >
            🔄 Sync with DB
          </button>
        </div>

        {/* Error Banner with Retry Action */}
        {errorMessage && (
          <aside className="api-error-banner" role="alert">
            <div className="api-error-content">
              <span className="error-banner-icon">⚠️</span>
              <div>
                <div className="api-error-title">Backend Connection Error</div>
                <p className="api-error-desc">{errorMessage}</p>
              </div>
            </div>
            <button
              type="button"
              className="btn-retry"
              onClick={() => loadTasks(true)}
            >
              🔄 Retry
            </button>
          </aside>
        )}

        <main className="dashboard-main">
          {/* Summary Metric Cards: Total, Pending, Completed */}
          <TaskSummary
            total={totalTasks}
            pending={pendingTasks}
            completed={completedTasks}
          />

          {/* Form to Add a Task with Input Validation */}
          <TaskForm onAddTask={handleAddTask} />

          {/* Loading Indicator or Task List */}
          {isLoading && tasks.length === 0 ? (
            <div className="loading-state-card" aria-live="polite">
              <div className="spinner"></div>
              <p className="loading-text">Loading tasks from Flask backend...</p>
            </div>
          ) : (
            <TaskList
              tasks={filteredTasks}
              currentFilter={filter}
              onFilterChange={setFilter}
              counts={{
                total: totalTasks,
                pending: pendingTasks,
                completed: completedTasks,
              }}
              onToggleComplete={handleToggleComplete}
              onEdit={handleOpenEdit}
              onDelete={handleDeleteTask}
            />
          )}
        </main>
      </div>

      {/* Edit Task Modal */}
      {editingTask && (
        <EditTaskModal
          task={editingTask}
          onSave={handleSaveEdit}
          onClose={() => setEditingTask(null)}
        />
      )}
    </div>
  );
}

export default App;
