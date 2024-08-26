const suits = ['♠', '♥', '♦', '♣'];
        const values = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A'];
        let deck = [];
        let playerHand = [];
        let trumpCard;

        function createDeck() {
            deck = [];
            for (let suit of suits) {
                for (let value of values) {
                    deck.push({ suit, value });
                }
            }
            // Add Wizard (Z) and Jester (N) cards
            deck.push({ suit: 'W', value: 'Z' }, { suit: 'W', value: 'Z' }, { suit: 'W', value: 'Z' }, { suit: 'W', value: 'Z' });
            deck.push({ suit: 'J', value: 'N' }, { suit: 'J', value: 'N' }, { suit: 'J', value: 'N' }, { suit: 'J', value: 'N' });
        }

        function shuffleDeck() {
            for (let i = deck.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [deck[i], deck[j]] = [deck[j], deck[i]];
            }
        }

        function dealCards(numCards) {
            playerHand = deck.splice(0, numCards);
            trumpCard = deck.pop();
            renderPlayerHand();
            renderTrumpCard();
        }

        function renderPlayerHand() {
            const playerHandElement = document.getElementById('playerHand');
            playerHandElement.innerHTML = '';
            for (let card of playerHand) {
                const cardElement = document.createElement('div');
                cardElement.className = 'card';
                cardElement.textContent = `${card.value}${card.suit}`;
                cardElement.onclick = () => playCard(card);
                playerHandElement.appendChild(cardElement);
            }
        }

        function renderTrumpCard() {
            const trumpCardElement = document.getElementById('trumpCard');
            trumpCardElement.innerHTML = '';
            const cardElement = document.createElement('div');
            cardElement.className = 'card';
            cardElement.textContent = `${trumpCard.value}${trumpCard.suit}`;
            trumpCardElement.appendChild(cardElement);
        }

        function playCard(card) {
            const playAreaElement = document.getElementById('playArea');
            const cardElement = document.createElement('div');
            cardElement.className = 'card';
            cardElement.textContent = `${card.value}${card.suit}`;
            playAreaElement.appendChild(cardElement);

            playerHand = playerHand.filter(c => c !== card);
            renderPlayerHand();
        }

        document.getElementById('startGame').onclick = () => {
            createDeck();
            shuffleDeck();
            dealCards(8); // Start with 8 cards for simplicity
            document.getElementById('playArea').innerHTML = '';
        };

        // Initialize the game
        createDeck();
        shuffleDeck();
        dealCards(8);
