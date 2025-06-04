// src/components/Header.tsx
import React, { useState, useRef, useEffect } from 'react';
import '../app.css';
import menuIcon from '../images/menu-button.png';

type HeaderProps = {
  userId: number;
  alpha: number;
  selectedOption: number | null;
  setSelectedOption: (opt: number | null) => void;
  onExit: () => void;
};

const Header: React.FC<HeaderProps> = ({
  userId,
  alpha,
  selectedOption,
  setSelectedOption,
  onExit,
}) => {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (opt: number) => {
    setSelectedOption(opt);
    setDropdownOpen(false);
    if (opt === 8) {
      // When “Exit” is chosen, inform parent to reset everything.
      onExit();
    }
  };

  return (
    <div className="d-flex justify-content-between align-items-center px-4 py-2 header-bar bg-primary border-bottom">
      {/* Dropdown menu button */}
      <div className="dropdown" ref={dropdownRef}>
        <button
          className="btn btn-outline-dark btn-sm"
          onClick={() => setDropdownOpen((prev) => !prev)}
          aria-expanded={dropdownOpen}
        >
          <img src={menuIcon} alt="Menu" style={{ width: '48px', height: '48px' }} />
        </button>
        {dropdownOpen && (
          <ul className="dropdown-menu dropdown-menu-end show">
            {/* Options 1–7 */}
            {[1, 2, 3, 4, 5, 6, 7].map((opt) => (
              <li key={opt}>
                <button
                  className="dropdown-item"
                  onClick={() => handleSelect(opt)}
                >
                  {opt}. {optionText(opt)}
                </button>
              </li>
            ))}

            <li><hr className="dropdown-divider" /></li>

            {/* Option 8: Exit */}
            <li>
              <button
                className="dropdown-item text-danger"
                onClick={() => handleSelect(8)}
              >
                8. Exit
              </button>
            </li>
          </ul>
        )}
      </div>

      {/* Display current User ID and alpha */}
      <div>
        <span className="me-3"><strong>User ID:</strong> {userId}</span>
        <span><strong>Alpha:</strong> {alpha.toFixed(2)}</span>
      </div>
    </div>
  );
};

function optionText(opt: number): string {
  switch (opt) {
    case 1:
      return 'Top movie recommendation';
    case 2:
      return 'Top-rated movies list';
    case 3:
      return 'Talk about specific movie';
    case 4:
      return 'Personalize (adjust alpha)';
    case 5:
      return 'Chat with assistant';
    case 6:
      return 'Change user ID';
    case 7:
      return 'Manually change alpha';
    default:
      return '';
  }
}

export default Header;
