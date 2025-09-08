/**
 * Quiz Generator component - handles topic input and quiz generation
 */
import React, { useState } from 'react';
import './QuizGenerator.css';

interface QuizGeneratorProps {
  onQuizGenerated: (quiz: any) => void;
  isLoading: boolean;
}

const QuizGenerator: React.FC<QuizGeneratorProps> = ({ onQuizGenerated, isLoading }) => {
  const [topic, setTopic] = useState<string>('');
  const [error, setError] = useState<string>('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate topic
    const trimmedTopic = topic.trim();
    if (!trimmedTopic) {
      setError('Please enter a topic for your quiz');
      return;
    }
    
    if (trimmedTopic.length > 100) {
      setError('Topic must be 100 characters or less');
      return;
    }
    
    // Clear error and generate quiz
    setError('');
    onQuizGenerated(trimmedTopic);
  };

  const handleTopicChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setTopic(e.target.value);
    if (error) {
      setError(''); // Clear error when user starts typing
    }
  };

  const suggestions = [
    'Electric Guitars',
    'Tennis',
    'Astronomy',
    'Entrata',
  ];

  return (
    <div className="quiz-generator">
      <div className="quiz-generator__container">
        <h1 className="quiz-generator__title">Quiz Generator</h1>
        <p className="quiz-generator__subtitle">
          Generate a custom multiple-choice quiz on any topic using AI
        </p>
        
        <form onSubmit={handleSubmit} className="quiz-generator__form">
          <div className="quiz-generator__input-group">
            <label htmlFor="topic" className="quiz-generator__label">
              What would you like to be quizzed on?
            </label>
            <input
              type="text"
              id="topic"
              value={topic}
              onChange={handleTopicChange}
              placeholder="Try: Electric Guitars, Tennis, Astronomy, Entrata"
              className={`quiz-generator__input ${error ? 'quiz-generator__input--error' : ''}`}
              disabled={isLoading}
              maxLength={100}
            />
            <div className="quiz-generator__char-count">
              {topic.length}/100 characters
            </div>
            {error && (
              <div className="quiz-generator__error" role="alert">
                {error}
              </div>
            )}
          </div>
          
          <button
            type="submit"
            disabled={isLoading}
            className="quiz-generator__button"
          >
            {isLoading ? (
              <>
                <span className="quiz-generator__spinner"></span>
                Generating your quiz...
              </>
            ) : (
              'Generate Quiz'
            )}
          </button>
        </form>
        
        {isLoading && (
          <div className="quiz-generator__loading">
            <p>Generating questions and options…</p>
            <p className="quiz-generator__loading-sub">This may take 10–30 seconds</p>
          </div>
        )}
        
        <div style={{ fontSize: '0.85rem', color: 'var(--color-muted)', textAlign: 'center', marginTop: '0.75rem' }}>Suggestions</div>
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', justifyContent: 'center', marginTop: '0.35rem' }}>
          {suggestions.slice(0,4).map(s => (
            <button key={s} type="button" className="quiz-generator__feature" onClick={() => setTopic(s)} style={{ border: '1px solid var(--color-border)', padding: '0.35rem 0.6rem', borderRadius: '999px', background: 'var(--color-surface)', cursor: 'pointer' }}>
              {s}
            </button>
          ))}
        </div>

        <div className="quiz-generator__features" style={{ marginTop: '1rem' }}>
          <div className="quiz-generator__feature">5 multiple-choice questions</div>
          <div className="quiz-generator__feature">Instant scoring</div>
          <div className="quiz-generator__feature">Save and retake</div>
        </div>
      </div>
    </div>
  );
};

export default QuizGenerator;
