import React from 'react';

export default function PlayingCard({ suit, value }) {

  const getSuitSymbol = (suit) => {
    switch (suit.toLowerCase()) {
      case 'hearts': return '♥';
      case 'diamonds': return '♦';
      case 'clubs': return '♣';
      case 'spades': return '♠';
      case 'wizard': return 'W';
      case 'jester': return 'J';
      default: return suit;
    }
  };

  const isRed = suit.toLowerCase() === 'hearts' || suit.toLowerCase() === 'diamonds';

  return (
    <div className={`w-32 h-48 bg-white rounded-lg shadow-md border border-gray-300 flex flex-col justify-between p-2 ${isRed ? 'text-red-600' : 'text-black'}`}>
      <div className="text-left text-xl font-bold">{value}</div>
      <div className="text-center text-4xl">{getSuitSymbol(suit)}</div>
      <div className="text-right text-xl font-bold rotate-180">{value}</div>
    </div>
  );
};

