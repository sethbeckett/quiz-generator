import React from 'react';
import './TopNav.css';
import { HomeIcon, BookOpenIcon } from './icons';

interface TopNavProps {
  onHome: () => void;
  onLibrary: () => void;
}

const TopNav: React.FC<TopNavProps> = ({ onHome, onLibrary }) => {
  return (
    <header className="topnav">
      <div className="topnav__inner">
        <button className="topnav__brand" onClick={onHome} aria-label="Home">
          <span className="topnav__logo">QG</span>
          <span className="topnav__title">Quiz Generator</span>
        </button>
        <nav className="topnav__nav">
          <button className="topnav__link" onClick={onHome}><HomeIcon /> Home</button>
          <button className="topnav__link" onClick={onLibrary}><BookOpenIcon /> Library</button>
        </nav>
      </div>
    </header>
  );
};

export default TopNav;


