/**
 * API service for communicating with the quiz generator backend
 */
import axios, { AxiosResponse } from 'axios';
import { Quiz, QuizSubmission, QuizResult, QuizAttempt } from '../types/quiz';

export interface FeedbackRequestItem {
  question_id: number;
  question_text: string;
  user_selected: string;
  user_selected_text: string;
  correct_option: string;
  correct_text: string;
}

export interface FeedbackRequestBody {
  topic: string;
  items: FeedbackRequestItem[];
}

export interface FeedbackResponseItem { question_id: number; explanation: string; }
export interface FeedbackResponse { items: FeedbackResponseItem[]; }

// Create axios instance with base configuration
const api = axios.create({
  baseURL: process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api/v1',
  timeout: 30000, // 30 seconds timeout for quiz generation
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`Making ${config.method?.toUpperCase()} request to ${config.url}`);
    return config;
  },
  (error) => {
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('Response error:', error);
    
    // Handle common error cases
    if (error.response?.status === 404) {
      throw new Error('Resource not found');
    } else if (error.response?.status >= 500) {
      throw new Error('Server error. Please try again later.');
    } else if (error.response?.data?.detail) {
      throw new Error(error.response.data.detail);
    } else if (error.message) {
      throw new Error(error.message);
    } else {
      throw new Error('An unexpected error occurred');
    }
  }
);

export class QuizApiService {
  /**
   * Generate a new quiz based on the provided topic
   */
  static async generateQuiz(topic: string): Promise<Quiz> {
    try {
      const response: AxiosResponse<Quiz> = await api.post('/quiz/generate', {
        topic: topic.trim(),
      });
      return response.data;
    } catch (error) {
      console.error('Error generating quiz:', error);
      throw error;
    }
  }

  /**
   * Get a specific quiz by ID
   */
  static async getQuiz(quizId: number): Promise<Quiz> {
    try {
      const response: AxiosResponse<Quiz> = await api.get(`/quiz/${quizId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching quiz:', error);
      throw error;
    }
  }

  /**
   * Get all quizzes with pagination
   */
  static async getAllQuizzes(limit: number = 20, offset: number = 0): Promise<Quiz[]> {
    try {
      const response: AxiosResponse<Quiz[]> = await api.get('/quiz/', {
        params: { limit, offset },
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching quizzes:', error);
      throw error;
    }
  }

  /**
   * Submit quiz answers and get results
   */
  static async submitQuiz(submission: QuizSubmission): Promise<QuizResult> {
    try {
      const response: AxiosResponse<QuizResult> = await api.post(
        `/quiz/${submission.quiz_id}/submit`,
        submission
      );
      return response.data;
    } catch (error) {
      console.error('Error submitting quiz:', error);
      throw error;
    }
  }

  /**
   * Get all attempts for a specific quiz
   */
  static async getQuizAttempts(quizId: number): Promise<QuizAttempt[]> {
    try {
      const response: AxiosResponse<QuizAttempt[]> = await api.get(`/quiz/${quizId}/attempts`);
      return response.data;
    } catch (error) {
      console.error('Error fetching quiz attempts:', error);
      throw error;
    }
  }

  /**
   * Request explanations for incorrect answers
   */
  static async getFeedback(quizId: number, body: FeedbackRequestBody): Promise<FeedbackResponse> {
    const response = await api.post<FeedbackResponse>(`/quiz/${quizId}/feedback`, body);
    return response.data;
  }

  /**
   * Health check endpoint
   */
  static async healthCheck(): Promise<{ status: string; database: string; gemini_api: string }> {
    try {
      const response = await api.get('/health');
      return response.data;
    } catch (error) {
      console.error('Error checking API health:', error);
      throw error;
    }
  }
}

export default QuizApiService;
