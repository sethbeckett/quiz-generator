/**
 * Main App component - manages the overall quiz application state and flow
 */
import React, { useState, useCallback } from 'react';
import { UserAnswer, AppState } from './types/quiz';
import QuizApiService from './services/api';
import QuizGenerator from './components/QuizGenerator';
import QuizTaker from './components/QuizTaker';
import QuizResults from './components/QuizResults';
import TopNav from './components/TopNav';
import Library from './components/Library';
import './App.css';
import QuizFeedbackModal from './components/QuizFeedbackModal';
import { SavedQuizzesStore } from './services/savedQuizzes';
import type { FeedbackResponse, FeedbackRequestItem } from './services/api';

type AppView = 'generate' | 'taking' | 'results' | 'library';

function App() {
  const [appState, setAppState] = useState<AppState>({
    currentQuiz: null,
    isLoading: false,
    error: null,
    quizResult: null
  });
  
  const [currentView, setCurrentView] = useState<AppView>('generate');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedbackOpen, setFeedbackOpen] = useState(false);
  const [feedback, setFeedback] = useState<FeedbackResponse | null>(null);
  const [feedbackMeta, setFeedbackMeta] = useState<FeedbackRequestItem[] | undefined>(undefined);

  const handleQuizGeneration = useCallback(async (topic: string) => {
    setAppState(prev => ({ ...prev, isLoading: true, error: null }));
    
    try {
      const quiz = await QuizApiService.generateQuiz(topic);
      setAppState(prev => ({
        ...prev,
        currentQuiz: quiz,
        isLoading: false,
        error: null
      }));
      ;(window as any).currentQuizId = quiz.id;
      setCurrentView('taking');
    } catch (error) {
      const errorMessage = error instanceof Error 
        ? error.message 
        : 'Failed to generate quiz. Please try again.';
      
      setAppState(prev => ({
        ...prev,
        isLoading: false,
        error: errorMessage,
        currentQuiz: null
      }));
    }
  }, []);

  const handleQuizSubmission = useCallback(async (answers: UserAnswer[]) => {
    if (!appState.currentQuiz) return;
    
    setIsSubmitting(true);
    
    try {
      const submission = {
        quiz_id: appState.currentQuiz.id,
        answers: answers
      };
      
      const result = await QuizApiService.submitQuiz(submission);
      setAppState(prev => ({
        ...prev,
        quizResult: result,
        error: null
      }));
      // Ensure quiz id is available for feedback requests later
      ;(window as any).currentQuizId = appState.currentQuiz.id;
      setCurrentView('results');
    } catch (error) {
      const errorMessage = error instanceof Error 
        ? error.message 
        : 'Failed to submit quiz. Please try again.';
      
      setAppState(prev => ({
        ...prev,
        error: errorMessage
      }));
    } finally {
      setIsSubmitting(false);
    }
  }, [appState.currentQuiz]);

  const handleNewQuiz = useCallback(() => {
    setAppState({
      currentQuiz: null,
      isLoading: false,
      error: null,
      quizResult: null
    });
    setCurrentView('generate');
    setIsSubmitting(false);
  }, []);

  const handleOpenSavedQuiz = useCallback(async (id: number) => {
    setAppState(prev => ({ ...prev, isLoading: true, error: null }));
    try {
      const quiz = await QuizApiService.getQuiz(id);
      setAppState(prev => ({ ...prev, currentQuiz: quiz, isLoading: false }));
      setCurrentView('taking');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to open quiz';
      setAppState(prev => ({ ...prev, error: errorMessage, isLoading: false }));
    }
  }, []);

  const renderErrorMessage = () => {
    if (!appState.error) return null;
    
    return (
      <div className="app__error">
        <div className="app__error-content">
          <h3>Oops! Something went wrong</h3>
          <p>{appState.error}</p>
          <button 
            onClick={() => setAppState(prev => ({ ...prev, error: null }))}
            className="app__error-button"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  };

  const handleSaveQuiz = useCallback(() => {
    if (!appState.currentQuiz) return;
    SavedQuizzesStore.save({ id: appState.currentQuiz.id, topic: appState.currentQuiz.topic, created_at: appState.currentQuiz.created_at });
  }, [appState.currentQuiz]);

  const handleShowFeedback = useCallback((resp: FeedbackResponse, incorrectMeta: FeedbackRequestItem[]) => {
    setFeedback(resp);
    setFeedbackMeta(incorrectMeta);
    setFeedbackOpen(true);
  }, []);

  const renderCurrentView = () => {
    switch (currentView) {
      case 'generate':
        return (
          <QuizGenerator
            onQuizGenerated={handleQuizGeneration}
            isLoading={appState.isLoading}
          />
        );
      
      case 'taking':
        if (!appState.currentQuiz) {
          return <div>No quiz available. Please generate a new quiz.</div>;
        }
        return (
          <QuizTaker
            quiz={appState.currentQuiz}
            onQuizSubmit={handleQuizSubmission}
            isSubmitting={isSubmitting}
          />
        );
      
      case 'results':
        if (!appState.quizResult || !appState.currentQuiz) {
          return <div>No results available. Please take a quiz first.</div>;
        }
        return (
          <QuizResults
            result={appState.quizResult}
            quizTopic={appState.currentQuiz.topic}
            onNewQuiz={handleNewQuiz}
            quizId={appState.currentQuiz.id}
            onSaveQuiz={handleSaveQuiz}
            onGetFeedback={handleShowFeedback}
          />
        );

      case 'library':
        return (
          <Library onOpenQuiz={handleOpenSavedQuiz} />
        );
      
      default:
        return <div>Unknown view</div>;
    }
  };

  return (
    <div className="app">
      <TopNav onHome={() => setCurrentView('generate')} onLibrary={() => setCurrentView('library')} />
      {appState.error ? renderErrorMessage() : renderCurrentView()}
      <QuizFeedbackModal open={feedbackOpen} onClose={() => setFeedbackOpen(false)} feedback={feedback} incorrectMeta={feedbackMeta} />
    </div>
  );
}

export default App;
