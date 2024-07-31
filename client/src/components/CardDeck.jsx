import React from 'react';
import PlayingCard from './PlayingCard';

export default function CardDeck({ cards }) {
  return (
    <div className="flex items-center justify-center min-h-screen bg-green-700 p-4">
      <div className="flex overflow-x-auto p-4">
        {cards.map((card, index) => (
          <div
            key={`${card.suit}-${card.value}`}
            className="inline-block"
            style={{
              marginLeft: index > 0 ? '-60px' : '0', // Overlap cards
              zIndex: index, // Ensure proper stacking
              transition: 'transform 0.3s ease-in-out',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-20px)';
              e.currentTarget.style.zIndex = '50';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.zIndex = index;
            }}
          >
            <PlayingCard suit={card.suit} value={card.value} />
          </div>
        ))}
      </div>
    </div>
  );
};
