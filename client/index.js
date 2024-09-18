const playerId = Math.random().toString(36).substr(2, 9);
let socket;

// TODO: show the last card being played

function connectWebSocket() {
  socket = new WebSocket(`ws://localhost:8000/ws/${playerId}`);

  socket.onopen = function (_) {
    document.getElementById('connection-status').textContent = 'Connected';
    document.getElementById('ready-button').style.display = 'inline-block';
  };

  socket.onmessage = function (event) {
    console.log(event.data);
    const data = JSON.parse(event.data);
    displayCards(data.trump_card, 'trump-card');
    displayCards(data.hand, 'hand');
    displayCards(data.played_cards, 'played-cards');
    document.getElementById('ready-button').style.display = 'none';
    isMyTurn = data.turn;
    document.getElementById('score').innerHTML = `<h4>Your Score</h4><div>${data.score}</div>`
    document.getElementById('bid').innerHTML = `<h4>Your Bid</h4><div>${data.bid}</div>`
    document.getElementById('tricks').innerHTML = `<h4>Your Tricks</h4><div>${data.current_tricks}</div>`
  };

  socket.onclose = function (_) {
    document.getElementById('connection-status').textContent = 'Disconnected, make sure the server is running';
    setTimeout(connectWebSocket, 1000);
  };

  socket.onerror = function (error) {
    console.log(`WebSocket Error: ${error}`);
  };
}

function displayCards(hand, id) {
  const handContainer = document.getElementById(id);
  switch (id) {
    case 'hand':
      handContainer.innerHTML = '<h4>Your Hand</h4>';
      break;
    case 'trump-card':
      handContainer.innerHTML = '<h4>Trump Card</h4>';
      break;
    case 'played-cards':
      handContainer.innerHTML = `<h4>Play Area</h4>`;
      break;
    default:
      throw new Error('Invalid id');
  }
  hand.forEach(card => {
    const cardButton = document.createElement('button');
    cardButton.className = 'card';
    cardButton.style.backgroundColor = card.suit;
    if (!card.playable) {
      cardButton.style.opacity = 0.5;
    }
    cardButton.innerHTML = `
            <div>${card.value}</div>
            <div>${card.suit}</div>
        `;
    if (id === "hand" && card.playable) {
      cardButton.onclick = () => playCard(card);
    }
    handContainer.appendChild(cardButton);
  });
}

function playCard(card) {
  if (isMyTurn) {
    socket.send(JSON.stringify({
      action: 'play_card',
      card: card
    }));
  }
}

document.getElementById('ready-button').addEventListener('click', function () {
  socket.send(JSON.stringify({ action: 'ready' }));
  this.disabled = true;
  this.textContent = 'Waiting for other players...';
});

connectWebSocket();
