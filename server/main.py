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
    id: str
    name: str
    score: int
    hand: Optional[List[Card]] = None
    bid: Optional[int] = None


class GameState(BaseModel):
    players: List[Player]
    roundNumber: int
    currentPlayerTurn: Optional[Player] = None
    trumpSuit: Optional[SuitType] = None


# initial game state
game_state = GameState(players=[], roundNumber=0)

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
    player = Player(id=player_id, name="name", score=0)
    game_state.players.append(player)
    try:
        while True:
            data = await websocket.receive_text()
            message = {"player_id": player_id, "message": data}
            await manager.broadcast(json.dumps(message))
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        message = {"player_id": player_id, "message": "disconnected"}
        await manager.broadcast(json.dumps(message))


@app.get("/gameState")
async def gameState():
    return game_state
