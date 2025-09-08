/**
 * TypeScript type definitions for quiz-related data structures
 */

export interface QuestionOption {
  id: number;
  option_text: string;
  option_letter: string;
  is_correct: boolean;
}

export interface Question {
  id: number;
  question_text: string;
  question_order: number;
  options: QuestionOption[];
}

export interface Quiz {
  id: number;
  topic: string;
  created_at: string;
  questions: Question[];
}

export interface UserAnswer {
  question_id: number;
  selected_option_id: number;
}

export interface QuizSubmission {
  quiz_id: number;
  answers: UserAnswer[];
}

export interface QuizResult {
  score: number;
  total_questions: number;
  percentage: number;
  correct_answers: {
    question_id: number;
    question_text: string;
    correct_option: string;
    correct_text: string;
    user_selected: string;
    user_selected_text: string;
    is_correct: boolean;
  }[];
}

export interface QuizAttempt {
  id: number;
  quiz_id: number;
  attempted_at: string;
  score: number;
  total_questions: number;
}

// API response types
export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}

// Component state types
export interface QuizState {
  currentQuestionIndex: number;
  answers: UserAnswer[];
  timeStarted?: Date;
  isSubmitting: boolean;
}

export interface AppState {
  currentQuiz: Quiz | null;
  isLoading: boolean;
  error: string | null;
  quizResult: QuizResult | null;
}
