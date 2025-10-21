import React, { useState, useEffect } from 'react';

interface TypewriterTextProps {
  text: string;
  className?: string;
  typingSpeed?: number;
  startDelay?: number;
  showCursor?: boolean;
  cursorChar?: string;
}

/**
 * Typewriter Text Component
 * Animates text with typewriter effect and blinking cursor
 * Supports reduced motion accessibility preference
 */
const TypewriterText: React.FC<TypewriterTextProps> = ({
  text,
  className = '',
  typingSpeed = 100,
  startDelay = 1000,
  showCursor = true,
  cursorChar = '|'
}) => {
  const [displayText, setDisplayText] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isTyping, setIsTyping] = useState(false);
  const [showCursorState, setShowCursorState] = useState(true);
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  // Check for reduced motion preference
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReducedMotion(mediaQuery.matches);

    const handleChange = (e: MediaQueryListEvent) => {
      setPrefersReducedMotion(e.matches);
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  // Initialize typing animation
  useEffect(() => {
    if (prefersReducedMotion) {
      // If reduced motion is preferred, show full text immediately
      setDisplayText(text);
      setIsTyping(false);
      return;
    }

    // Start typing after delay
    const startTimer = setTimeout(() => {
      setIsTyping(true);
    }, startDelay);

    return () => clearTimeout(startTimer);
  }, [text, startDelay, prefersReducedMotion]);

  // Typing animation effect
  useEffect(() => {
    if (!isTyping || prefersReducedMotion || currentIndex >= text.length) {
      if (currentIndex >= text.length) {
        setIsTyping(false);
      }
      return;
    }

    const typingTimer = setTimeout(() => {
      setDisplayText(text.slice(0, currentIndex + 1));
      setCurrentIndex(prev => prev + 1);
    }, typingSpeed);

    return () => clearTimeout(typingTimer);
  }, [currentIndex, isTyping, text, typingSpeed, prefersReducedMotion]);

  // Cursor blinking effect
  useEffect(() => {
    if (!showCursor || prefersReducedMotion) return;

    const cursorTimer = setInterval(() => {
      setShowCursorState(prev => !prev);
    }, 530); // Slightly different from CSS animation for natural feel

    return () => clearInterval(cursorTimer);
  }, [showCursor, prefersReducedMotion]);

  // Split text into lines for better responsive display
  const formatText = (text: string) => {
    // Split on common break points for better mobile display
    const words = text.split(' ');
    const lines: string[] = [];
    let currentLine = '';
    
    words.forEach((word, index) => {
      if (word === 'Quality' || word === 'You') {
        // Create line breaks at natural points
        if (currentLine) {
          lines.push(currentLine.trim());
          currentLine = word + ' ';
        } else {
          currentLine += word + ' ';
        }
      } else {
        currentLine += word + ' ';
      }
      
      // Add the last line
      if (index === words.length - 1 && currentLine) {
        lines.push(currentLine.trim());
      }
    });
    
    return lines.length > 1 ? lines : [text];
  };

  const textLines = formatText(displayText);

  return (
    <div className={`relative ${className}`} role="heading" aria-level={1}>
      {/* Screen reader text (always complete) */}
      <span className="sr-only">{text}</span>
      
      {/* Visual typewriter text */}
      <span aria-hidden="true" className="relative">
        {textLines.map((line, lineIndex) => (
          <span key={lineIndex} className="block">
            {line}
            {/* Show cursor only on the last line and when appropriate */}
            {lineIndex === textLines.length - 1 && showCursor && (
              <span 
                className={`inline-block ml-1 ${
                  prefersReducedMotion 
                    ? 'opacity-100' 
                    : showCursorState 
                      ? 'opacity-100' 
                      : 'opacity-0'
                } transition-opacity duration-100`}
                style={{
                  color: 'currentColor',
                  fontWeight: 'inherit'
                }}
              >
                {cursorChar}
              </span>
            )}
          </span>
        ))}
      </span>
      
      {/* Fallback for when JavaScript is disabled */}
      <noscript>
        <span>{text}</span>
      </noscript>
    </div>
  );
};

export default TypewriterText;