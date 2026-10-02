const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const TODOS_URL = `${API_BASE_URL}/todos/`;

async function request(url, options) {
  let response;
  try {
    response = await fetch(url, options);
  } catch {
    throw new Error('Could not reach the server. Is the API running?');
  }

  const body = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error((body && body.detail) || `Request failed (${response.status})`);
  }
  return body;
}

export function fetchTodos() {
  return request(TODOS_URL);
}

export function createTodo(description) {
  return request(TODOS_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ description }),
  });
}
