import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';

test('renders quiz generator app', () => {
  render(<App />);
  const titleElement = screen.getByRole('heading', { name: /Quiz Generator/i });
  expect(titleElement).toBeInTheDocument();
});
