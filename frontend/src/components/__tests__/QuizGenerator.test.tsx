/**
 * Tests for QuizGenerator component
 */
/* eslint-disable testing-library/no-node-access */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import QuizGenerator from '../QuizGenerator';

describe('QuizGenerator', () => {
  const mockOnQuizGenerated = jest.fn();

  beforeEach(() => {
    mockOnQuizGenerated.mockClear();
  });

  it('renders the quiz generator form', () => {
    render(<QuizGenerator onQuizGenerated={mockOnQuizGenerated} isLoading={false} />);
    
    expect(screen.getByText('Quiz Generator')).toBeInTheDocument();
    expect(screen.getByLabelText(/What would you like to be quizzed on?/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Generate Quiz/i })).toBeInTheDocument();
  });

  it('displays feature highlights', () => {
    render(<QuizGenerator onQuizGenerated={mockOnQuizGenerated} isLoading={false} />);
    
    expect(screen.getByText('5 multiple-choice questions')).toBeInTheDocument();
    expect(screen.getByText('Instant scoring')).toBeInTheDocument();
    expect(screen.getByText('Save and retake')).toBeInTheDocument();
  });

  it('allows user to type in topic input', async () => {
    const user = userEvent.setup();
    render(<QuizGenerator onQuizGenerated={mockOnQuizGenerated} isLoading={false} />);
    
    const input = screen.getByLabelText(/What would you like to be quizzed on?/i);
    await user.type(input, 'Machine Learning');
    
    expect(input).toHaveValue('Machine Learning');
  });

  it('shows character count', async () => {
    const user = userEvent.setup();
    render(<QuizGenerator onQuizGenerated={mockOnQuizGenerated} isLoading={false} />);
    
    const input = screen.getByLabelText(/What would you like to be quizzed on?/i);
    await user.type(input, 'Python');
    
    expect(screen.getByText('6/100 characters')).toBeInTheDocument();
  });

  it('does not disable button when topic is empty', () => {
    render(<QuizGenerator onQuizGenerated={mockOnQuizGenerated} isLoading={false} />);
    
    const button = screen.getByRole('button', { name: /Generate Quiz/i });
    expect(button).not.toBeDisabled();
  });

  it('enables button when topic is entered', async () => {
    const user = userEvent.setup();
    render(<QuizGenerator onQuizGenerated={mockOnQuizGenerated} isLoading={false} />);
    
    const input = screen.getByLabelText(/What would you like to be quizzed on?/i);
    const button = screen.getByRole('button', { name: /Generate Quiz/i });
    
    await user.type(input, 'React');
    
    expect(button).not.toBeDisabled();
  });

  it('shows error for empty topic submission', async () => {
    const user = userEvent.setup();
    render(<QuizGenerator onQuizGenerated={mockOnQuizGenerated} isLoading={false} />);
    
    const button = screen.getByRole('button', { name: /Generate Quiz/i });
    
    // Try to submit without entering topic
    await user.click(button);
    
    expect(screen.getByText('Please enter a topic for your quiz')).toBeInTheDocument();
    expect(mockOnQuizGenerated).not.toHaveBeenCalled();
  });

  it('prevents typing more than 100 characters', async () => {
    const user = userEvent.setup();
    render(<QuizGenerator onQuizGenerated={mockOnQuizGenerated} isLoading={false} />);
    
    const input = screen.getByLabelText(/What would you like to be quizzed on?/i);
    const longTopic = 'a'.repeat(105); // Try to type more than 100 characters
    
    await user.type(input, longTopic);
    
    // Input should only contain 100 characters due to maxLength
    expect(input).toHaveValue('a'.repeat(100));
    expect(screen.getByText('100/100 characters')).toBeInTheDocument();
  });

  it('calls onQuizGenerated with valid topic', async () => {
    const user = userEvent.setup();
    render(<QuizGenerator onQuizGenerated={mockOnQuizGenerated} isLoading={false} />);
    
    const input = screen.getByLabelText(/What would you like to be quizzed on?/i);
    const button = screen.getByRole('button', { name: /Generate Quiz/i });
    
    await user.type(input, 'JavaScript');
    await user.click(button);
    
    expect(mockOnQuizGenerated).toHaveBeenCalledWith('JavaScript');
  });

  it('trims whitespace from topic', async () => {
    const user = userEvent.setup();
    render(<QuizGenerator onQuizGenerated={mockOnQuizGenerated} isLoading={false} />);
    
    const input = screen.getByLabelText(/What would you like to be quizzed on?/i);
    const button = screen.getByRole('button', { name: /Generate Quiz/i });
    
    await user.type(input, '  TypeScript  ');
    await user.click(button);
    
    expect(mockOnQuizGenerated).toHaveBeenCalledWith('TypeScript');
  });

  it('clears error when user starts typing after error', async () => {
    const user = userEvent.setup();
    render(<QuizGenerator onQuizGenerated={mockOnQuizGenerated} isLoading={false} />);
    
    const input = screen.getByLabelText(/What would you like to be quizzed on?/i);
    const button = screen.getByRole('button', { name: /Generate Quiz/i });
    
    // Trigger error
    await user.click(button);
    expect(screen.getByText('Please enter a topic for your quiz')).toBeInTheDocument();
    
    // Start typing
    await user.type(input, 'R');
    
    // Error should be cleared
    expect(screen.queryByText('Please enter a topic for your quiz')).not.toBeInTheDocument();
  });

  it('shows loading state', () => {
    render(<QuizGenerator onQuizGenerated={mockOnQuizGenerated} isLoading={true} />);
    
    expect(screen.getByText('Generating your quiz...')).toBeInTheDocument();
    expect(screen.getByText('Generating questions and options…')).toBeInTheDocument();
    expect(screen.getByText('This may take 10–30 seconds')).toBeInTheDocument();
    
    const button = screen.getAllByRole('button')[0];
    expect(button).toBeDisabled();
    
    const input = screen.getByLabelText(/What would you like to be quizzed on?/i);
    expect(input).toBeDisabled();
  });

  it('shows spinner in loading state', () => {
    render(<QuizGenerator onQuizGenerated={mockOnQuizGenerated} isLoading={true} />);
    
    const spinner = document.querySelector('.quiz-generator__spinner');
    expect(spinner).toBeInTheDocument();
  });

  it('prevents form submission while loading', async () => {
    const user = userEvent.setup();
    render(<QuizGenerator onQuizGenerated={mockOnQuizGenerated} isLoading={true} />);
    
    const form = screen.getAllByRole('button')[0].closest('form');
    expect(form).toBeInTheDocument();
    
    // Try to submit form while loading
    if (form) {
      fireEvent.submit(form);
    }
    
    // Should not call the callback
    expect(mockOnQuizGenerated).not.toHaveBeenCalled();
  });

  it('handles keyboard submission', async () => {
    const user = userEvent.setup();
    render(<QuizGenerator onQuizGenerated={mockOnQuizGenerated} isLoading={false} />);
    
    const input = screen.getByLabelText(/What would you like to be quizzed on?/i);
    
    await user.type(input, 'Node.js{enter}');
    
    expect(mockOnQuizGenerated).toHaveBeenCalledWith('Node.js');
  });
});
