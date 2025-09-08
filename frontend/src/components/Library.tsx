import React from 'react';
import { SavedQuizzesStore, SavedQuizSummary } from '../services/savedQuizzes';
import './Library.css';

interface LibraryProps {
  onOpenQuiz: (id: number) => void;
}

const Library: React.FC<LibraryProps> = ({ onOpenQuiz }) => {
  const [items, setItems] = React.useState<SavedQuizSummary[]>([]);

  React.useEffect(() => {
    setItems(SavedQuizzesStore.list());
  }, []);

  const handleDelete = (id: number) => {
    SavedQuizzesStore.remove(id);
    setItems(SavedQuizzesStore.list());
  };

  return (
    <div className="library">
      <div className="library__inner">
        <h1 className="library__title">Saved Quizzes</h1>
        {items.length === 0 ? (
          <p className="library__empty">No saved quizzes yet.</p>
        ) : (
          <ul className="library__list">
            {items.map(q => (
              <li key={q.id} className="library__item">
                <div className="library__meta">
                  <div className="library__topic">{q.topic}</div>
                  <div className="library__date">Saved {new Date(q.created_at).toLocaleString()}</div>
                </div>
                <div className="library__actions">
                  <button className="library__btn library__btn--primary" onClick={() => onOpenQuiz(q.id)}>Retake</button>
                  <button className="library__btn" onClick={() => handleDelete(q.id)}>Delete</button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default Library;


