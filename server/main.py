import random
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Literal, Optional, Dict

# TODO: handle next turn and round correctly

# init app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SuitType = Literal["red", "blue", "green", "yellow", "wizard", "jester"]


class Card(BaseModel):
    value: int
    suit: SuitType


class Player(BaseModel):
    websocket: WebSocket
    score: int = 0
    hand: Optional[List[Card]] = None
    bid: Optional[int] = None
    ready: bool = False
    turn: bool = (
        True  # for debugging, should be adaptively changed later and start as False
    )

    class Config:
        arbitrary_types_allowed = True

    def play_card(self, card: Card):
        if self.hand and self.turn and (card in self.hand):
            self.hand.remove(card)


class Game:
    def __init__(self, players: dict) -> None:
        self.n_players: int = len(players)
        suit_options: list = ["red", "blue", "green", "yellow"]
        basic_deck: list = [
            Card(value=value, suit=suit)
            for value in range(1, 14)
            for suit in suit_options
        ]
        jesters, wizards = (
            [Card(value=0, suit="jester") for _ in range(4)],
            [Card(value=14, suit="wizard") for _ in range(4)],
        )
        self.deck: list = basic_deck + jesters + wizards
        self.n_rounds: int = len(self.deck) // self.n_players
        self.players: dict = players
        self.round_number: int = 5  # for debugging, should be 1
        self.trump_card: Optional[Card] = None
        self.played_cards: Dict[str, Card] = {}

    def play_card(self, player_id: str, card: Card) -> None:
        self.played_cards[player_id] = card
        self.players[player_id].play_card(card)

    def deal_cards(self) -> None:
        hands = random.sample(
            self.deck,
            len(self.players) * self.round_number + 1,  # +1 for trump Card
        )
        self.trump_card = hands.pop()
        for i, player in enumerate(self.players.values()):
            start = i * self.round_number
            player.hand = hands[start : start + self.round_number]

    def round_done(self) -> bool:
        return len(self.played_cards) == self.n_players

    def eval_round(
        self, played_cards: Dict[int, Card], player_order: Dict[int, Player]
    ) -> Player:
        played_suits = list(map(lambda c: c.suit, played_cards.values()))
        assert self.trump_card, "Trump card not set"

        winning_suit = (
            "wizard"
            if "wizard" in played_suits
            else (
                self.trump_card.suit
                if self.trump_card.suit in played_suits
                else played_cards[0].suit
            )
        )
        winning_n = min(
            (n for n, card in played_cards.items() if card.suit == winning_suit)
        )

        return player_order[winning_n]


# used to handle the socket connections
class ConnectionManager:
    def __init__(self):
        self.active_players: dict[str, Player] = {}

    async def connect(self, player_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_players[player_id] = Player(websocket=websocket)

    def disconnect(self, player_id):
        self.active_players.pop(player_id)

    async def send_state(self) -> None:
        assert game, "Cannot send state before game has started."
        for player in self.active_players.values():
            await player.websocket.send_json(
                {
                    **player.model_dump(exclude={"websocket"}),
                    "trump_card": [game.trump_card.model_dump()]
                    if game.trump_card
                    else "undefined",
                    "played_cards": [
                        {"player_id": player_id, **card.model_dump()}
                        for player_id, card in game.played_cards.items()
                    ],
                }
            )


manager = ConnectionManager()
game = None


@app.websocket("/ws/{player_id}")
async def websocket_endpoint(websocket: WebSocket, player_id: str):
    global game
    await manager.connect(player_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            match data["action"]:
                case "ready":
                    manager.active_players[player_id].ready = True
                    if all(player.ready for player in manager.active_players.values()):
                        game = Game(players=manager.active_players)
                        game.deal_cards()
                        await manager.send_state()
                case "play_card":
                    assert game, "Cannot play card before game has started."
                    print(data["card"])
                    card = Card(**data["card"])
                    game.play_card(player_id, card)
                    await manager.send_state()

    except WebSocketDisconnect:
        manager.disconnect(websocket)
