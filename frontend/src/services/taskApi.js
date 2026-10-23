/**
 * taskApi.js - Reusable API Service Layer for TaskFlow
 * ----------------------------------------------------
 * Connects the React frontend with the Flask REST backend.
 * Base Address: http://127.0.0.1:5000/api
 *
 * Provides functions for complete task lifecycle operations:
 * 1. getAllTasks()         -> GET /api/tasks
 * 2. createTask(data)      -> POST /api/tasks
 * 3. updateTask(id, data)  -> PUT /api/tasks/:id
 * 4. markTaskCompleted(id) -> PATCH /api/tasks/:id/complete
 * 5. deleteTask(id)        -> DELETE /api/tasks/:id
 */

// Target URL of the running Flask REST API
const API_BASE_URL = 'http://127.0.0.1:5000/api';

/**
 * Internal helper to parse responses and handle HTTP errors gracefully.
 * Extracts JSON payload and generates clear error messages.
 */
async function handleResponse(response) {
  let data = null;
  try {
    data = await response.json();
  } catch (err) {
    // Response had no JSON body
  }

  if (!response.ok) {
    const message =
      (data && (data.error || data.message)) ||
      `HTTP error ${response.status}: ${response.statusText}`;
    const error = new Error(message);
    error.status = response.status;
    error.data = data;
    throw error;
  }

  return data;
}

/**
 * Fetch all tasks and summary statistics from SQLite via Flask.
 * GET /api/tasks
 * @returns {Promise<{tasks: Array, stats: {total: number, pending: number, completed: number}}>}
 */
export async function getAllTasks() {
  const response = await fetch(`${API_BASE_URL}/tasks`, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
    },
  });
  return handleResponse(response);
}

/**
 * Create a new task in SQLite via Flask.
 * POST /api/tasks
 * @param {{title: string, description?: string}} taskData
 * @returns {Promise<{message: string, task: Object}>}
 */
export async function createTask({ title, description = '' }) {
  if (!title || !title.trim()) {
    throw new Error('Task title is required.');
  }

  const response = await fetch(`${API_BASE_URL}/tasks`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify({
      title: title.trim(),
      description: description ? description.trim() : '',
    }),
  });
  return handleResponse(response);
}

/**
 * Update an existing task's title, description, or completion status.
 * PUT /api/tasks/:id
 * @param {number|string} taskId
 * @param {{title: string, description?: string, completed?: boolean}} taskData
 * @returns {Promise<{message: string, task: Object}>}
 */
export async function updateTask(taskId, { title, description = '', completed }) {
  if (!title || !title.trim()) {
    throw new Error('Task title cannot be empty.');
  }

  const payload = {
    title: title.trim(),
    description: description ? description.trim() : '',
  };

  if (completed !== undefined) {
    payload.completed = Boolean(completed);
  }

  const response = await fetch(`${API_BASE_URL}/tasks/${taskId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify(payload),
  });
  return handleResponse(response);
}

/**
 * Mark a task as completed (or toggle pending/completed).
 * PATCH /api/tasks/:id/complete
 * @param {number|string} taskId
 * @param {boolean} [completed=true]
 * @returns {Promise<{message: string, task: Object}>}
 */
export async function markTaskCompleted(taskId, completed = true) {
  const response = await fetch(`${API_BASE_URL}/tasks/${taskId}/complete`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify({
      completed: Boolean(completed),
    }),
  });
  return handleResponse(response);
}

/**
 * Permanently delete a task by ID from SQLite.
 * DELETE /api/tasks/:id
 * @param {number|string} taskId
 * @returns {Promise<{message: string}>}
 */
export async function deleteTask(taskId) {
  const response = await fetch(`${API_BASE_URL}/tasks/${taskId}`, {
    method: 'DELETE',
    headers: {
      Accept: 'application/json',
    },
  });
  return handleResponse(response);
}

export default {
  getAllTasks,
  createTask,
  updateTask,
  markTaskCompleted,
  deleteTask,
};
