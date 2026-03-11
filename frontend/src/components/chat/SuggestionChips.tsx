/**
 * SuggestionChips.tsx — Horizontally scrollable pill buttons
 *
 * Rendered below the last assistant message. Clicking a chip
 * populates the input and auto-submits. Chips animate in with
 * staggered fade-up transitions.
 */

import React from 'react';

interface SuggestionChipsProps {
  chips: string[];
  onChipClick: (text: string) => void;
  disabled: boolean;
}

const SuggestionChips: React.FC<SuggestionChipsProps> = ({
  chips,
  onChipClick,
  disabled,
}) => {
  if (chips.length === 0) return null;

  return (
    <div
      className="suggestion-chips"
      role="group"
      aria-label="Suggested follow-up questions"
    >
      <div className="suggestion-chips__scroll">
        {chips.map((chip, index) => (
          <button
            key={`${chip}-${index}`}
            className="suggestion-chip"
            onClick={() => onChipClick(chip)}
            disabled={disabled}
            aria-label={`Suggest: ${chip}`}
            style={{
              animationDelay: `${index * 80}ms`,
            }}
          >
            {chip}
          </button>
        ))}
      </div>
    </div>
  );
};

export default SuggestionChips;
