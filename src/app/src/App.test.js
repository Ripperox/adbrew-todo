import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from './App';
import * as todosApi from './api/todos';

jest.mock('./api/todos');

beforeEach(() => {
  jest.resetAllMocks();
});

test('renders todos fetched from the API', async () => {
  todosApi.fetchTodos.mockResolvedValue([{ id: '1', description: 'Learn Docker' }]);

  render(<App />);

  expect(await screen.findByText('Learn Docker')).toBeInTheDocument();
});

test('submitting the form creates a todo and refreshes the list', async () => {
  todosApi.fetchTodos
    .mockResolvedValueOnce([])
    .mockResolvedValueOnce([{ id: '1', description: 'Buy milk' }]);
  todosApi.createTodo.mockResolvedValue({ id: '1', description: 'Buy milk' });

  render(<App />);
  await screen.findByText('No TODOs yet.');

  userEvent.type(screen.getByLabelText(/todo/i), '  Buy milk ');
  userEvent.click(screen.getByRole('button', { name: /add todo/i }));

  expect(await screen.findByText('Buy milk')).toBeInTheDocument();
  expect(todosApi.createTodo).toHaveBeenCalledWith('Buy milk');
  await waitFor(() => expect(screen.getByLabelText(/todo/i)).toHaveValue(''));
});

test('shows the server error when creating fails', async () => {
  todosApi.fetchTodos.mockResolvedValue([]);
  todosApi.createTodo.mockRejectedValue(new Error('description is required'));

  render(<App />);
  await screen.findByText('No TODOs yet.');

  userEvent.type(screen.getByLabelText(/todo/i), 'x');
  userEvent.click(screen.getByRole('button', { name: /add todo/i }));

  expect(await screen.findByRole('alert')).toHaveTextContent('description is required');
});

test('shows an error when the list cannot be loaded', async () => {
  todosApi.fetchTodos.mockRejectedValue(new Error('Could not reach the server. Is the API running?'));

  render(<App />);

  expect(await screen.findByRole('alert')).toHaveTextContent(/could not reach the server/i);
});
