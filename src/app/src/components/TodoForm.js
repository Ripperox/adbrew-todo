import { useState } from 'react';

const MAX_LENGTH = 500;

export function TodoForm({ onSubmit }) {
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const isBlank = description.trim() === '';

  async function handleSubmit(event) {
    event.preventDefault();
    if (isBlank) return;

    setSubmitting(true);
    setError(null);
    try {
      await onSubmit(description.trim());
      setDescription('');
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <label htmlFor="todo">ToDo: </label>
        <input
          id="todo"
          type="text"
          value={description}
          maxLength={MAX_LENGTH}
          onChange={(event) => setDescription(event.target.value)}
          disabled={submitting}
        />
      </div>
      <div style={{ marginTop: '5px' }}>
        <button type="submit" disabled={isBlank || submitting}>
          {submitting ? 'Adding…' : 'Add ToDo!'}
        </button>
      </div>
      {error && <p role="alert" className="error">{error}</p>}
    </form>
  );
}
