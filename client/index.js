const playerId = Math.random().toString(36).substr(2, 9);
let socket;

function connectWebSocket() {
  socket = new WebSocket(`ws://localhost:8000/ws/${playerId}`);

  socket.onopen = function (e) {
    document.getElementById('connection-status').textContent = 'Connected';
    document.getElementById('ready-button').style.display = 'inline-block';
  };

  socket.onmessage = function (event) {
    const data = JSON.parse(event.data);
    console.log(data);
    if (data.hand) {
      displayHand(data.hand);
      document.getElementById('ready-button').style.display = 'none';
    }
  };

  socket.onclose = function (event) {
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
    const cardElement = document.createElement('div');
    cardElement.className = 'card';
    cardElement.style.backgroundColor = card.suit;
    cardElement.innerHTML = `
            <div>${card.value}</div>
            <div>${card.suit}</div>
        `;
    handContainer.appendChild(cardElement);
  });
}

document.getElementById('ready-button').addEventListener('click', function () {
  socket.send('ready');
  this.disabled = true;
  this.textContent = 'Waiting for other players...';
});

connectWebSocket();
