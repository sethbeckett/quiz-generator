/**
 * Quiz Taker component - handles quiz taking interface
 */
import React, { useState } from 'react';
import { Quiz, UserAnswer, QuizState } from '../types/quiz';
import './QuizTaker.css';

interface QuizTakerProps {
  quiz: Quiz;
  onQuizSubmit: (answers: UserAnswer[]) => void;
  isSubmitting: boolean;
}

const QuizTaker: React.FC<QuizTakerProps> = ({ quiz, onQuizSubmit, isSubmitting }) => {
  const [quizState, setQuizState] = useState<QuizState>({
    currentQuestionIndex: 0,
    answers: [],
    timeStarted: new Date(),
    isSubmitting: false
  });

  const currentQuestion = quiz.questions[quizState.currentQuestionIndex];
  const isLastQuestion = quizState.currentQuestionIndex === quiz.questions.length - 1;
  const progress = ((quizState.currentQuestionIndex + 1) / quiz.questions.length) * 100;

  // Get current answer for this question
  const currentAnswer = quizState.answers.find(
    answer => answer.question_id === currentQuestion.id
  );

  const handleOptionSelect = (optionId: number) => {
    setQuizState(prev => {
      const newAnswers = prev.answers.filter(
        answer => answer.question_id !== currentQuestion.id
      );
      
      newAnswers.push({
        question_id: currentQuestion.id,
        selected_option_id: optionId
      });

      return {
        ...prev,
        answers: newAnswers
      };
    });
  };

  const handleNext = () => {
    if (quizState.currentQuestionIndex < quiz.questions.length - 1) {
      setQuizState(prev => ({
        ...prev,
        currentQuestionIndex: prev.currentQuestionIndex + 1
      }));
    }
  };

  const handlePrevious = () => {
    if (quizState.currentQuestionIndex > 0) {
      setQuizState(prev => ({
        ...prev,
        currentQuestionIndex: prev.currentQuestionIndex - 1
      }));
    }
  };

  const handleSubmit = () => {
    if (quizState.answers.length === quiz.questions.length) {
      setQuizState(prev => ({ ...prev, isSubmitting: true }));
      onQuizSubmit(quizState.answers);
    }
  };

  const isAnswered = (questionIndex: number): boolean => {
    const question = quiz.questions[questionIndex];
    return quizState.answers.some(answer => answer.question_id === question.id);
  };

  const getAnsweredCount = (): number => {
    return quizState.answers.length;
  };

  const canProceed = currentAnswer !== undefined;
  const allQuestionsAnswered = getAnsweredCount() === quiz.questions.length;

  return (
    <div className="quiz-taker">
      <div className="quiz-taker__container">
        {/* Header */}
        <div className="quiz-taker__header">
          <h1 className="quiz-taker__title">{quiz.topic}</h1>
          <div className="quiz-taker__progress">
            <div className="quiz-taker__progress-bar">
              <div 
                className="quiz-taker__progress-fill"
                style={{ width: `${progress}%` }}
              ></div>
            </div>
            <span className="quiz-taker__progress-text">
              Question {quizState.currentQuestionIndex + 1} of {quiz.questions.length}
            </span>
          </div>
        </div>

        {/* Question */}
        <div className="quiz-taker__question">
          <h2 className="quiz-taker__question-text">
            {currentQuestion.question_text}
          </h2>
          
          <div className="quiz-taker__options">
            {currentQuestion.options
              .sort((a, b) => a.option_letter.localeCompare(b.option_letter))
              .map((option) => (
                <button
                  key={option.id}
                  onClick={() => handleOptionSelect(option.id)}
                  className={`quiz-taker__option ${
                    currentAnswer?.selected_option_id === option.id 
                      ? 'quiz-taker__option--selected' 
                      : ''
                  }`}
                  disabled={isSubmitting}
                >
                  <span className="quiz-taker__option-letter">
                    {option.option_letter}
                  </span>
                  <span className="quiz-taker__option-text">
                    {option.option_text}
                  </span>
                </button>
              ))}
          </div>
        </div>

        {/* Navigation */}
        <div className="quiz-taker__navigation">
          <div className="quiz-taker__nav-buttons">
            <button
              onClick={handlePrevious}
              disabled={quizState.currentQuestionIndex === 0 || isSubmitting}
              className="quiz-taker__nav-button quiz-taker__nav-button--secondary"
            >
              ← Previous
            </button>
            
            {!isLastQuestion ? (
              <button
                onClick={handleNext}
                disabled={!canProceed || isSubmitting}
                className="quiz-taker__nav-button quiz-taker__nav-button--primary"
              >
                Next →
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={!allQuestionsAnswered || isSubmitting}
                className="quiz-taker__nav-button quiz-taker__nav-button--submit"
              >
                {isSubmitting ? (
                  <>
                    <span className="quiz-taker__spinner"></span>
                    Submitting...
                  </>
                ) : (
                  'Submit Quiz'
                )}
              </button>
            )}
          </div>
          
          <div className="quiz-taker__status">
            <span className="quiz-taker__answered-count">
              {getAnsweredCount()} of {quiz.questions.length} answered
            </span>
          </div>
        </div>

        {/* Question dots indicator */}
        <div className="quiz-taker__dots">
          {quiz.questions.map((_, index) => (
            <button
              key={index}
              onClick={() => setQuizState(prev => ({ ...prev, currentQuestionIndex: index }))}
              className={`quiz-taker__dot ${
                index === quizState.currentQuestionIndex ? 'quiz-taker__dot--current' : ''
              } ${
                isAnswered(index) ? 'quiz-taker__dot--answered' : ''
              }`}
              disabled={isSubmitting}
              title={`Question ${index + 1}${isAnswered(index) ? ' (answered)' : ''}`}
            >
              {index + 1}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default QuizTaker;
