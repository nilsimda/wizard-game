import React, { useState, useEffect } from "react";
import './index.css';
import './App.css';
import CardDeck from './components/CardDeck';

function App() {
  const [playerId, _] = useState(
    Math.floor(new Date().getTime() / 1000)
  );
  const [websckt, setWebsckt] = useState();
  const [gamestate, setGamestate] = useState();


  useEffect(() => {
    const url = "ws://localhost:8000/ws/" + playerId;
    const ws = new WebSocket(url);

    ws.onopen = (_event) => { ws.send("connected") };

    ws.onmessage = (e) => { //server sends gameState if it changes
      const message = JSON.parse(e.data);
      setGamestate(message);
    };

    setWebsckt(ws);

    return () => ws.close();

  }, [playerId]);

  function sendMessage(message) {
    websckt.send(message);
  };

  const cards = [
    { suit: 'hearts', value: 'A' },
    { suit: 'spades', value: 'K' },
    { suit: 'diamonds', value: 'Q' },
    { suit: 'clubs', value: 'J' },
    { suit: 'W', value: '' },
    { suit: 'J', value: '' },
  ];

  return (
    <div className="container">
      <h1>Chat</h1>
      <h2>Your player id: {playerId} </h2>
      <pre>{JSON.stringify(gamestate, null, 2)}</pre>
      <CardDeck cards={cards} />
    </div>
  );

}
export default App;
