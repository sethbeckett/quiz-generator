import React from 'react';
import { FeedbackResponse, FeedbackRequestItem } from '../services/api';
import './QuizFeedbackModal.css';

interface QuizFeedbackModalProps {
  open: boolean;
  onClose: () => void;
  feedback: FeedbackResponse | null;
  incorrectMeta?: FeedbackRequestItem[];
}

const QuizFeedbackModal: React.FC<QuizFeedbackModalProps> = ({ open, onClose, feedback, incorrectMeta }) => {
  if (!open) return null;
  return (
    <div className="qf__backdrop" role="dialog" aria-modal="true">
      <div className="qf__panel">
        <div className="qf__header">
          <h2 className="qf__title">Answer Feedback</h2>
          <button className="qf__close" onClick={onClose} aria-label="Close">×</button>
        </div>
        <div className="qf__content">
          {!feedback || feedback.items.length === 0 ? (
            <p className="qf__empty">No feedback available.</p>
          ) : (
            <ul className="qf__list">
              {feedback.items.map((item, index) => {
                const meta = incorrectMeta?.find(m => m.question_id === item.question_id);
                return (
                  <li key={item.question_id} className="qf__item">
                    <div className="qf__qid">Question {index + 1}</div>
                    {meta && (
                      <div className="qf__meta">
                        <div><strong>Your answer:</strong> {meta.user_selected}. {meta.user_selected_text}</div>
                        <div><strong>Correct:</strong> {meta.correct_option}. {meta.correct_text}</div>
                      </div>
                    )}
                    <div className="qf__text">{item.explanation}</div>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
};

export default QuizFeedbackModal;



