// TODO: show other peoples bids
// TODO: show last card played
// TODO: improve UI (move to react?)

const playerId = Math.random().toString(36).substr(2, 9);
let socket;

function connectWebSocket() {
  socket = new WebSocket(`ws://localhost:8000/ws/${playerId}`);

  socket.onopen = function (_) {
    document.getElementById('connection-status').textContent = 'Connected';
    document.getElementById('ready-button').style.display = 'inline-block';
  };

  socket.onmessage = function (event) {
    console.log(event.data);
    const data = JSON.parse(event.data);
    bidding = data.bidding;
    displayCards(data.trump_card, 'trump-card');
    displayCards(data.hand, 'hand');
    displayCards(data.played_cards, 'played-cards');
    document.getElementById('ready-button').style.display = 'none';
    isMyTurn = data.turn;
    document.getElementById('score').innerHTML = `<h4>Your Score</h4><div>${data.score}</div>`
    if (data.bid !== null) {
      document.getElementById('bid').innerHTML = `<h4>Your Bid</h4><div>${data.bid}</div>`
      document.getElementById('tricks').innerHTML = `<h4>Your Tricks</h4><div>${data.current_tricks}</div>`
    }
    else {
      const bid_container = document.getElementById('bid');
      bid_container.innerHTML = ``;
      const label = document.createElement('label');
      label.for = 'bid-selector';
      label.textContent = "Make your bid:"
      const bid_select = document.createElement('select');
      bid_select.id = 'bid-selector';
      for (let i = 0; i <= data.n_round; i++) {
        const option = document.createElement('option');
        option.value = i;
        option.text = i;
        bid_select.appendChild(option);
      }
      const bid_button = document.createElement('button');
      bid_button.textContent = 'Submit Bid';
      bid_button.onclick = submitBid;
      document.getElementById('bid').append(bid_select);
      document.getElementById('bid').append(bid_button);
      if (!isMyTurn) {
        bid_button.disabled = true;
      }
    }
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
    if (!bidding && id === "hand" && card.playable) {
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

function submitBid() {
  const bidSelect = document.getElementById('bid-selector');
  const selectedBid = bidSelect.value;
  socket.send(JSON.stringify({
    action: 'bid',
    n_tricks: parseInt(selectedBid)
  }));
  // Disable the select and button after submitting
  bidSelect.disabled = true;
  this.disabled = true;
}

document.getElementById('ready-button').addEventListener('click', function () {
  socket.send(JSON.stringify({ action: 'ready' }));
  this.disabled = true;
  this.textContent = 'Waiting for other players...';
});

connectWebSocket();
