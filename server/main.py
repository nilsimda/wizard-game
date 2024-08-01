import random
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Literal, Optional, Dict


# init app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# used to handle the socket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for con in self.active_connections:
            await con.send_text(message)


manager = ConnectionManager()

# some pydantic models for the wizard game
SuitType = Literal["hearts", "diamonds", "clubs", "spades", "wizard", "jester"]


class Card(BaseModel):
    value: int
    suit: SuitType


class Player(BaseModel):
    name: str
    score: int
    hand: Optional[List[Card]] = None
    bid: Optional[int] = None
    ready: bool


class GameState(BaseModel):
    players: dict
    roundNumber: int
    currentPlayerTurn: Optional[Player] = None
    trumpSuit: Optional[SuitType] = None

    def add_player(self, id: str) -> None:
        self.players[id] = Player(name="name", score=0, ready=False)

    def remove_player(self, id: str) -> None:
        del self.players[id]

    def all_ready(self) -> bool:
        return all(player.ready for player in self.players.values())

    def deal_cards(self, deck: List[Card]):
        hands = random.sample(
            deck,
            len(self.players) * self.roundNumber + 1,  # +1 for trump Card
        )
        self.trumpSuit = hands.pop().suit
        for i, player in enumerate(self.players.values()):
            start = i * self.roundNumber
            player.hand = hands[start : start + self.roundNumber]

    def eval_round(
        self, played_cards: Dict[int, Card], player_order: Dict[int, Player]
    ) -> Player:
        played_suits = list(map(lambda c: c.suit, played_cards.values()))

        winning_suit = (
            "wizard"
            if "wizard" in played_suits
            else (
                self.trumpSuit
                if self.trumpSuit in played_suits
                else played_cards[0].suit
            )
        )
        winning_n = min(
            (n for n, card in played_cards.items() if card.suit == winning_suit)
        )

        return player_order[winning_n]


# initial game state
game_state = GameState(players={}, roundNumber=0)

# create deck of cards, jesters have value 0 and wizards 14 for easy evaluation
suit_options: List[SuitType] = ["hearts", "diamonds", "clubs", "spades"]
deck = [Card(value=value, suit=suit) for value in range(1, 13) for suit in suit_options]
jesters, wizards = (
    [Card(value=0, suit="jester")] * 4,
    [Card(value=14, suit="wizard")] * 4,
)
deck = deck + jesters + wizards


@app.get("/")
async def root():
    return deck


@app.websocket("/ws/{player_id}")
async def websocket_endpoint(websocket: WebSocket, player_id: str):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            match data:
                case "connected":  # send by websocket client when it connects
                    game_state.add_player(player_id)
                case "ready":  # a player is ready to start the next round
                    game_state.players[player_id].ready = True
                    if game_state.all_ready():
                        game_state.roundNumber += 1
                        for player in game_state.players.values():
                            player.ready = False
                        game_state.deal_cards(deck)

            await manager.broadcast(game_state.model_dump_json())

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        game_state.remove_player(player_id)
        await manager.broadcast(game_state.model_dump_json())


@app.get("/gameState")
async def gameState():
    return game_state
