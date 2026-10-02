import { useCallback, useEffect, useState } from 'react';
import * as todosApi from '../api/todos';

export function useTodos() {
  const [todos, setTodos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      setTodos(await todosApi.fetchTodos());
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  // Errors propagate to the caller so the form can show them next to the input.
  const addTodo = useCallback(async (description) => {
    await todosApi.createTodo(description);
    await refresh();
  }, [refresh]);

  return { todos, loading, error, addTodo };
}
