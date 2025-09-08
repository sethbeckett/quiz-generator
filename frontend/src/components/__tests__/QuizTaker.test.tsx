/**
 * Tests for QuizTaker component
 */
/* eslint-disable testing-library/no-node-access */
/* eslint-disable jest/no-conditional-expect */
import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import QuizTaker from '../QuizTaker';
import { Quiz } from '../../types/quiz';

const mockQuiz: Quiz = {
  id: 1,
  topic: 'JavaScript',
  created_at: '2024-01-01T00:00:00Z',
  questions: [
    {
      id: 1,
      question_text: 'What is JavaScript?',
      question_order: 1,
      options: [
        { id: 1, option_text: 'A snake', option_letter: 'A', is_correct: false },
        { id: 2, option_text: 'A programming language', option_letter: 'B', is_correct: true },
        { id: 3, option_text: 'A coffee brand', option_letter: 'C', is_correct: false },
        { id: 4, option_text: 'A framework', option_letter: 'D', is_correct: false },
      ],
    },
    {
      id: 2,
      question_text: 'What does "const" mean?',
      question_order: 2,
      options: [
        { id: 5, option_text: 'Constant', option_letter: 'A', is_correct: true },
        { id: 6, option_text: 'Variable', option_letter: 'B', is_correct: false },
        { id: 7, option_text: 'Function', option_letter: 'C', is_correct: false },
        { id: 8, option_text: 'Object', option_letter: 'D', is_correct: false },
      ],
    },
  ],
};

describe('QuizTaker', () => {
  const mockOnQuizSubmit = jest.fn();

  beforeEach(() => {
    mockOnQuizSubmit.mockClear();
  });

  it('renders quiz title and first question', () => {
    render(<QuizTaker quiz={mockQuiz} onQuizSubmit={mockOnQuizSubmit} isSubmitting={false} />);
    
    expect(screen.getByText('JavaScript')).toBeInTheDocument();
    expect(screen.getByText('What is JavaScript?')).toBeInTheDocument();
    expect(screen.getByText('Question 1 of 2')).toBeInTheDocument();
  });

  it('renders all options for current question', () => {
    render(<QuizTaker quiz={mockQuiz} onQuizSubmit={mockOnQuizSubmit} isSubmitting={false} />);
    
    expect(screen.getByText('A snake')).toBeInTheDocument();
    expect(screen.getByText('A programming language')).toBeInTheDocument();
    expect(screen.getByText('A coffee brand')).toBeInTheDocument();
    expect(screen.getByText('A framework')).toBeInTheDocument();
  });

  it('shows progress correctly', () => {
    render(<QuizTaker quiz={mockQuiz} onQuizSubmit={mockOnQuizSubmit} isSubmitting={false} />);
    
    const progressBar = document.querySelector('.quiz-taker__progress-fill');
    expect(progressBar).toHaveStyle('width: 50%'); // Question 1 of 2 = 50%
  });

  it('allows selecting an option', async () => {
    const user = userEvent.setup();
    render(<QuizTaker quiz={mockQuiz} onQuizSubmit={mockOnQuizSubmit} isSubmitting={false} />);
    
    const optionB = screen.getByText('A programming language').closest('button');
    expect(optionB).toBeInTheDocument();
    
    if (optionB) {
      await user.click(optionB);
      expect(optionB).toHaveClass('quiz-taker__option--selected');
    }
  });

  it('disables Previous button on first question', () => {
    render(<QuizTaker quiz={mockQuiz} onQuizSubmit={mockOnQuizSubmit} isSubmitting={false} />);
    
    const previousButton = screen.getByText('← Previous');
    expect(previousButton).toBeDisabled();
  });

  it('enables Next button after selecting an option', async () => {
    const user = userEvent.setup();
    render(<QuizTaker quiz={mockQuiz} onQuizSubmit={mockOnQuizSubmit} isSubmitting={false} />);
    
    const nextButton = screen.getByText('Next →');
    expect(nextButton).toBeDisabled();
    
    const optionA = screen.getByText('A snake').closest('button');
    if (optionA) {
      await user.click(optionA);
      expect(nextButton).not.toBeDisabled();
    }
  });

  it('navigates to next question', async () => {
    const user = userEvent.setup();
    render(<QuizTaker quiz={mockQuiz} onQuizSubmit={mockOnQuizSubmit} isSubmitting={false} />);
    
    // Select an option
    const optionB = screen.getByText('A programming language').closest('button');
    if (optionB) {
      await user.click(optionB);
    }
    
    // Click Next
    const nextButton = screen.getByText('Next →');
    await user.click(nextButton);
    
    // Should now show question 2
    expect(screen.getByText('What does "const" mean?')).toBeInTheDocument();
    expect(screen.getByText('Question 2 of 2')).toBeInTheDocument();
  });

  it('navigates back to previous question', async () => {
    const user = userEvent.setup();
    render(<QuizTaker quiz={mockQuiz} onQuizSubmit={mockOnQuizSubmit} isSubmitting={false} />);
    
    // Go to question 2
    const optionB = screen.getByText('A programming language').closest('button');
    if (optionB) {
      await user.click(optionB);
    }
    await user.click(screen.getByText('Next →'));
    
    // Go back to question 1
    const previousButton = screen.getByText('← Previous');
    await user.click(previousButton);
    
    expect(screen.getByText('What is JavaScript?')).toBeInTheDocument();
    expect(screen.getByText('Question 1 of 2')).toBeInTheDocument();
  });

  it('shows Submit button on last question', async () => {
    const user = userEvent.setup();
    render(<QuizTaker quiz={mockQuiz} onQuizSubmit={mockOnQuizSubmit} isSubmitting={false} />);
    
    // Navigate to last question
    const optionB = screen.getByText('A programming language').closest('button');
    if (optionB) {
      await user.click(optionB);
    }
    await user.click(screen.getByText('Next →'));
    
    expect(screen.getByText('Submit Quiz')).toBeInTheDocument();
    expect(screen.queryByText('Next →')).not.toBeInTheDocument();
  });

  it('tracks answered questions correctly', async () => {
    const user = userEvent.setup();
    render(<QuizTaker quiz={mockQuiz} onQuizSubmit={mockOnQuizSubmit} isSubmitting={false} />);
    
    expect(screen.getByText('0 of 2 answered')).toBeInTheDocument();
    
    // Answer first question
    const optionB = screen.getByText('A programming language').closest('button');
    if (optionB) {
      await user.click(optionB);
    }
    
    expect(screen.getByText('1 of 2 answered')).toBeInTheDocument();
  });

  it('enables Submit button only when all questions are answered', async () => {
    const user = userEvent.setup();
    render(<QuizTaker quiz={mockQuiz} onQuizSubmit={mockOnQuizSubmit} isSubmitting={false} />);
    
    // Answer question 1
    const optionB = screen.getByText('A programming language').closest('button');
    if (optionB) {
      await user.click(optionB);
    }
    
    // Go to question 2
    await user.click(screen.getByText('Next →'));
    
    const submitButton = screen.getByText('Submit Quiz');
    expect(submitButton).toBeDisabled();
    
    // Answer question 2
    const optionA = screen.getByText('Constant').closest('button');
    if (optionA) {
      await user.click(optionA);
    }
    
    expect(submitButton).not.toBeDisabled();
  });

  it('submits quiz with all answers', async () => {
    const user = userEvent.setup();
    render(<QuizTaker quiz={mockQuiz} onQuizSubmit={mockOnQuizSubmit} isSubmitting={false} />);
    
    // Answer question 1
    const optionB = screen.getByText('A programming language').closest('button');
    if (optionB) {
      await user.click(optionB);
    }
    
    // Go to question 2
    await user.click(screen.getByText('Next →'));
    
    // Answer question 2
    const optionA = screen.getByText('Constant').closest('button');
    if (optionA) {
      await user.click(optionA);
    }
    
    // Submit
    const submitButton = screen.getByText('Submit Quiz');
    await user.click(submitButton);
    
    expect(mockOnQuizSubmit).toHaveBeenCalledWith([
      { question_id: 1, selected_option_id: 2 },
      { question_id: 2, selected_option_id: 5 },
    ]);
  });

  it('shows submitting state', () => {
    render(<QuizTaker quiz={mockQuiz} onQuizSubmit={mockOnQuizSubmit} isSubmitting={true} />);
    
    // All buttons should be disabled
    const options = screen.getAllByRole('button');
    options.forEach((option) => {
      if (option.textContent?.includes('A') || option.textContent?.includes('B') || 
          option.textContent?.includes('C') || option.textContent?.includes('D')) {
        expect(option).toBeDisabled();
      }
    });
  });

  it('allows navigation via question dots', async () => {
    const user = userEvent.setup();
    render(<QuizTaker quiz={mockQuiz} onQuizSubmit={mockOnQuizSubmit} isSubmitting={false} />);
    
    // Click on question 2 dot
    const questionDot2 = screen.getByTitle('Question 2');
    await user.click(questionDot2);
    
    expect(screen.getByText('What does "const" mean?')).toBeInTheDocument();
  });

  it('highlights answered questions in dots', async () => {
    const user = userEvent.setup();
    render(<QuizTaker quiz={mockQuiz} onQuizSubmit={mockOnQuizSubmit} isSubmitting={false} />);
    
    // Answer question 1
    const optionB = screen.getByText('A programming language').closest('button');
    if (optionB) {
      await user.click(optionB);
    }
    
    const questionDot1 = screen.getByTitle('Question 1 (answered)');
    expect(questionDot1).toHaveClass('quiz-taker__dot--answered');
  });

  it('preserves selected answers when navigating', async () => {
    const user = userEvent.setup();
    render(<QuizTaker quiz={mockQuiz} onQuizSubmit={mockOnQuizSubmit} isSubmitting={false} />);
    
    // Select option B on question 1
    const optionB = screen.getByText('A programming language').closest('button');
    if (optionB) {
      await user.click(optionB);
    }
    
    // Navigate to question 2 and back
    await user.click(screen.getByText('Next →'));
    await user.click(screen.getByText('← Previous'));
    
    // Option B should still be selected
    expect(optionB).toHaveClass('quiz-taker__option--selected');
  });
});
