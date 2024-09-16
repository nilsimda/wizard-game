const playerId = Math.random().toString(36).substr(2, 9);
let socket;

//TODO: display trump card
//TODO: display played cards

function connectWebSocket() {
  socket = new WebSocket(`ws://localhost:8000/ws/${playerId}`);

  socket.onopen = function (_) {
    document.getElementById('connection-status').textContent = 'Connected';
    document.getElementById('ready-button').style.display = 'inline-block';
  };

  socket.onmessage = function (event) {
    const data = JSON.parse(JSON.parse(event.data));
    displayHand(data.hand);
    document.getElementById('ready-button').style.display = 'none';
    isMyTurn = data.turn
  };

  socket.onclose = function (_) {
    document.getElementById('connection-status').textContent = 'Disconnected, make sure the server is running';
    setTimeout(connectWebSocket, 1000);
  };

  socket.onerror = function (error) {
    console.log(`WebSocket Error: ${error}`);
  };
}

function displayHand(hand) {
  const handContainer = document.getElementById('hand');
  handContainer.innerHTML = '';
  hand.forEach(card => {
    const cardButton = document.createElement('button');
    cardButton.className = 'card';
    cardButton.style.backgroundColor = card.suit;
    cardButton.innerHTML = `
            <div>${card.value}</div>
            <div>${card.suit}</div>
        `;
    cardButton.onclick = () => playCard(card);
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
