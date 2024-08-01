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


  return (
    <div className="container">
      <h2>Your player id: {playerId} </h2>
      <h3>Round: {gamestate?.roundNumber}</h3>
      <h3>Trump Suit: {gamestate?.trumpSuit}</h3>
      <pre>{JSON.stringify(gamestate, null, 2)}</pre>
      <button onClick={() => websckt?.send("ready")}>Next Round</button>
      <CardDeck cards={gamestate?.players[playerId].hand} />
    </div>
  );

}
export default App;
