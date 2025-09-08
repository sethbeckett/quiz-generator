/**
 * Quiz Results component - displays quiz results and feedback
 */
import React, { useState } from 'react';
import { QuizResult } from '../types/quiz';
import QuizApiService, { FeedbackRequestBody, FeedbackResponse, FeedbackRequestItem } from '../services/api';
import './QuizResults.css';
import { MessageSquareIcon, RotateCcwIcon, SaveIcon } from './icons';

interface QuizResultsProps {
  result: QuizResult;
  quizTopic: string;
  onNewQuiz: () => void;
  onSaveQuiz?: () => void;
  onGetFeedback?: (feedback: FeedbackResponse, incorrect: FeedbackRequestItem[]) => void;
  quizId?: number;
}

const QuizResults: React.FC<QuizResultsProps> = ({ 
  result, 
  quizTopic, 
  onNewQuiz,
  onSaveQuiz,
  onGetFeedback,
  quizId
}) => {
  const [isGettingFeedback, setIsGettingFeedback] = useState(false);
  const getScoreColor = (percentage: number): string => {
    if (percentage >= 80) return '#48bb78'; // Green
    if (percentage >= 60) return '#ed8936'; // Orange  
    return '#e53e3e'; // Red
  };

  const getScoreMessage = (percentage: number): string => {
    if (percentage === 100) return '🎉 Perfect Score!';
    if (percentage >= 80) return '🌟 Excellent Work!';
    if (percentage >= 60) return '👍 Good Job!';
    if (percentage >= 40) return '📚 Keep Studying!';
    return '💪 Try Again!';
  };

  // iconography removed in new design

  return (
    <div className="quiz-results">
      <div className="quiz-results__container">
        {/* Header */}
        <div className="quiz-results__header">
          <h1 className="quiz-results__title">Quiz Complete!</h1>
          <p className="quiz-results__topic">Topic: {quizTopic}</p>
        </div>

        {/* Score Summary */}
        <div className="quiz-results__score-card">
          <div 
            className="quiz-results__score"
            style={{ color: getScoreColor(result.percentage) }}
          >
            {result.score}/{result.total_questions}
          </div>
          <div 
            className="quiz-results__percentage"
            style={{ color: getScoreColor(result.percentage) }}
          >
            {result.percentage}%
          </div>
          <div className="quiz-results__message">
            {getScoreMessage(result.percentage)}
          </div>
        </div>

        {/* Detailed Results */}
        <div className="quiz-results__details">
          <h2 className="quiz-results__details-title">Review Your Answers</h2>
          
          <div className="quiz-results__questions">
            {result.correct_answers.map((answer, index) => (
              <div 
                key={answer.question_id} 
                className={`quiz-results__question ${
                  answer.is_correct 
                    ? 'quiz-results__question--correct' 
                    : 'quiz-results__question--incorrect'
                }`}
              >
                <div className="quiz-results__question-header">
                  <span className="quiz-results__question-number">
                    Question {index + 1}
                  </span>
                  <span className={`quiz-results__question-status ${
                    answer.is_correct 
                      ? 'quiz-results__question-status--correct'
                      : 'quiz-results__question-status--incorrect'
                  }`}>
                    {answer.is_correct ? '✓ Correct' : '✗ Incorrect'}
                  </span>
                </div>
                
                <div className="quiz-results__question-text">
                  {answer.question_text}
                </div>
                
                <div className="quiz-results__answers">
                  <div className="quiz-results__answer quiz-results__answer--yours">
                    <span className="quiz-results__answer-label">Your answer:</span>
                    <span className={`quiz-results__answer-content ${
                      answer.is_correct 
                        ? 'quiz-results__answer-content--correct'
                        : 'quiz-results__answer-content--incorrect'
                    }`}>
                      {answer.user_selected}. {answer.user_selected_text}
                    </span>
                  </div>
                  
                  {!answer.is_correct && (
                    <div className="quiz-results__answer quiz-results__answer--correct">
                      <span className="quiz-results__answer-label">Correct answer:</span>
                      <span className="quiz-results__answer-content quiz-results__answer-content--correct">
                        {answer.correct_option}. {answer.correct_text}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className="quiz-results__actions">
          {onGetFeedback && result.correct_answers.some(a => !a.is_correct) && (
            <button
              onClick={async () => {
                try {
                  setIsGettingFeedback(true);
                  const incorrectFull = result.correct_answers.filter(a => !a.is_correct);
                  if (incorrectFull.length === 0) {
                    onGetFeedback({ items: [] }, []);
                    return;
                  }
                  const items: FeedbackRequestItem[] = incorrectFull.map(a => ({
                    question_id: a.question_id,
                    question_text: a.question_text,
                    user_selected: a.user_selected,
                    user_selected_text: a.user_selected_text,
                    correct_option: a.correct_option,
                    correct_text: a.correct_text
                  }));

                  const body: FeedbackRequestBody = {
                    topic: quizTopic,
                    items
                  };
                  const id = quizId ?? (window as any).currentQuizId ?? 0;

                  // Create cache key based on quiz ID AND the specific incorrect question IDs
                  const incorrectQuestionIds = items.map(item => item.question_id).sort().join(',');
                  const cacheKey = `quiz_feedback_v1_${id}_${incorrectQuestionIds}`;
                  const cached = localStorage.getItem(cacheKey);
                  if (cached) {
                    const parsed: FeedbackResponse = JSON.parse(cached);
                    onGetFeedback(parsed, items);
                    return;
                  }

                  const feedback = await QuizApiService.getFeedback(id, body);
                  try { localStorage.setItem(cacheKey, JSON.stringify(feedback)); } catch {}
                  onGetFeedback(feedback, items);
                } catch(e) {
                  // noop UI-level error; rely on global error handler if present
                } finally {
                  setIsGettingFeedback(false);
                }
              }}
              className="quiz-results__button quiz-results__button--secondary"
              disabled={isGettingFeedback}
            >
              {isGettingFeedback ? (<><span className="quiz-generator__spinner"></span> Getting feedback…</>) : (<><MessageSquareIcon /> Get feedback</>)}
            </button>
          )}
          <button
            onClick={onNewQuiz}
            className="quiz-results__button quiz-results__button--primary"
          >
            <RotateCcwIcon /> Take another quiz
          </button>
          
          {onSaveQuiz && (
            <button
              onClick={onSaveQuiz}
              className="quiz-results__button quiz-results__button--secondary"
            >
              <SaveIcon /> Save quiz
            </button>
          )}
        </div>

        {/* Stats */}
        <div className="quiz-results__stats">
          <div className="quiz-results__stat">
            <span className="quiz-results__stat-value">{result.score}</span>
            <span className="quiz-results__stat-label">Correct</span>
          </div>
          <div className="quiz-results__stat">
            <span className="quiz-results__stat-value">{result.total_questions - result.score}</span>
            <span className="quiz-results__stat-label">Incorrect</span>
          </div>
          <div className="quiz-results__stat">
            <span className="quiz-results__stat-value">{result.total_questions}</span>
            <span className="quiz-results__stat-label">Total</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QuizResults;
