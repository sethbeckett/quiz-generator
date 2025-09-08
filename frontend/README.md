# Quiz Generator Frontend

React + TypeScript frontend for the AI Quiz Generator technical interview project.

## Quick Start

```bash
# Install dependencies
npm install

# Set up environment
echo "REACT_APP_API_BASE_URL=http://localhost:8000/api/v1" > .env

# Start development server
npm start
```

The app will be available at [http://localhost:3000](http://localhost:3000).

## Available Scripts

- `npm start` - Start development server
- `npm test` - Run component tests
- `npm run build` - Build for production
- `npm run eject` - Eject from Create React App (not recommended)

## Architecture

- **Components**: Modular React components with TypeScript
- **State Management**: React hooks with proper error handling
- **API Integration**: Axios client with interceptors
- **Testing**: React Testing Library with comprehensive test coverage
- **Styling**: Modern CSS with responsive design

## Components

- `QuizGenerator` - Topic input and quiz generation
- `QuizTaker` - Interactive quiz taking interface  
- `QuizResults` - Score display and answer review

Built with Create React App for rapid development and industry-standard tooling.
