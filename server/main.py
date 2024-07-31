import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Literal, Optional


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
SuitType = Literal["heart", "diamonds", "clubs", "spades", "wizard", "jester"]


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

    def add_player(self, id: str):
        self.players[id] = Player(name="name", score=0, ready=False)

    def remove_player(self, id: str):
        del self.players[id]


# initial game state
game_state = GameState(players={}, roundNumber=0)

# create deck of cards, jesters have value 0 and wizards 14 for easy evaluation
suit_options: List[SuitType] = ["heart", "diamonds", "clubs", "spades"]
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
                case "ready":
                    pass

            await manager.broadcast(game_state.model_dump_json())

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        game_state.remove_player(player_id)
        message = {"playerId": player_id, "message": "disconnected"}
        await manager.broadcast(json.dumps(message))


@app.get("/gameState")
async def gameState():
    return game_state
