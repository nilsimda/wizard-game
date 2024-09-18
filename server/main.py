import random
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Literal, Optional

# TODO: change player dict to just use a natural int ordering instead of strings to make things simpler
# TODO: send playable attr with each card
# TODO: deal new cards once round is done
# TODO: make bids

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SuitType = Literal["jester", "blue", "green", "yellow", "wizard", "red"]


class Card(BaseModel):
    value: int
    suit: SuitType

    def __eq__(self, other):
        return other.suit == self.suit and other.value == self.value


class Player(BaseModel):
    websocket: WebSocket
    score: int = 0
    hand: Optional[list[Card]] = None
    bid: Optional[int] = None
    ready: bool = False
    turn: bool = False
    current_tricks: int = 0

    class Config:
        arbitrary_types_allowed = True

    def play_card(self, card: Card):
        if self.hand and self.turn and (card in self.hand):
            self.hand.remove(card)


class Game:
    def __init__(self, players: dict) -> None:
        self.n_players: int = len(players)
        self.deck: list[Card] = self._create_deck()
        self.n_rounds: int = len(self.deck) // self.n_players
        self.players: dict[str, Player] = players
        self.player_order: dict[int, Player] = {
            i: p for i, p in enumerate(players.values())
        }
        self.player_order[0].turn = True
        self.round_number: int = 5  # for debugging, should be 1
        self.trump_card: Optional[Card] = None
        self.played_cards: list[Card] = []

    def _create_deck(self) -> list[Card]:
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
        return basic_deck + jesters + wizards

    def deal_cards(self) -> None:
        hands = random.sample(
            self.deck,
            len(self.players) * self.round_number + 1,  # +1 for trump Card
        )
        self.trump_card = hands.pop()
        for i, player in enumerate(self.players.values()):
            start = i * self.round_number
            player.hand = hands[start : start + self.round_number]

    def play_card(self, player_id: str, card: Card) -> None:
        assert self.players[player_id], "This player cannot play cards now."
        self.played_cards.append(card)
        self.players[player_id].play_card(card)
        self.next_turn()

    def _current_player(self) -> int:
        return next(iter(i for i in self.player_order if self.player_order[i].turn))

    def next_turn(self) -> None:
        current_player = self._current_player()
        self.player_order[current_player].turn = False
        self.player_order[(current_player + 1) % self.n_players].turn = True

    def next_trick(self) -> None:
        winner = self.eval_trick()
        for player in self.players.values():
            player.turn = False
        self.played_cards = []
        winner.current_tricks += 1
        winner.turn = True  # the previous winner starts

    def trick_done(self) -> bool:
        return len(self.played_cards) == self.n_players

    def _winning_suit(self) -> SuitType:
        assert self.trump_card, "Trump card not set"  # to shut up pyright
        played_suits: list[SuitType] = [c.suit for c in self.played_cards]
        if "wizard" in played_suits:
            return "wizard"
        if self.trump_card.suit in played_suits:
            return self.trump_card.suit
        else:  # why does pyright complain about this?
            return next(
                iter(suit for suit in played_suits if suit != "jester"), "jester"
            )

    def eval_trick(self) -> Player:
        winning_suit = self._winning_suit()
        winning_value = max(
            card.value for card in self.played_cards if card.suit == winning_suit
        )
        winning_n = self.played_cards.index(
            Card(value=winning_value, suit=winning_suit)
        )

        return self.player_order[(self._current_player() + winning_n) % self.n_players]


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
                        {"player_id": "", **card.model_dump()}
                        for card in game.played_cards
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
                    if game.trick_done():
                        game.next_trick()
                    await manager.send_state()

    except WebSocketDisconnect:
        manager.disconnect(websocket)
