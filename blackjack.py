import random

SUITS = ["S", "H", "D", "C"]
RANKS = [
    (1, "A", 11),
    (2, "2", 2),
    (3, "3", 3),
    (4, "4", 4),
    (5, "5", 5),
    (6, "6", 6),
    (7, "7", 7),
    (8, "8", 8),
    (9, "9", 9),
    (10, "10", 10),
    (11, "J", 10),
    (12, "Q", 10),
    (13, "K", 10),
]

def calc_hand_value(hand):
    """Returns (best_total, is_soft) handling Aces as 11 or 1."""
    total = 0
    aces = 0
    for card in hand:
        rank = card[:-1]
        if rank == "A":
            aces += 1
            total += 11
        elif rank in ("J", "Q", "K"):
            total += 10
        else:
            total += int(rank)

    while total > 21 and aces > 0:
        total -= 10
        aces -= 1

    return total, (aces > 0)


class BlackjackTable:
    def __init__(self, num_decks=6):
        self.num_decks = num_decks
        self.shoe = []
        self.cut_card_threshold = 75  # Reshuffle when < 75 cards remain (~75% penetration)
        self.reshuffled_recently = False
        self.build_shoe()

        self.players = []  # Ordered list of usernames (max 5)
        self.seats = {}    # username -> {hand, bet, status, result}
        self.dealer_hand = []
        self.phase = "betting"  # "betting" | "playing" | "round_over"
        self.turn_index = 0
        self.message = "Place your bets!"

    def build_shoe(self):
        self.shoe = [
            f"{rank_code}{suit}"
            for _ in range(self.num_decks)
            for suit in SUITS
            for _, rank_code, _ in RANKS
        ]
        random.shuffle(self.shoe)
        self.reshuffled_recently = True

    def draw_card(self):
        if not self.shoe:
            self.build_shoe()
        return self.shoe.pop()

    def add_player(self, username):
        if username not in self.players and len(self.players) < 5:
            self.players.append(username)
            self.seats[username] = {
                "hand": [],
                "bet": 0,
                "status": "waiting",  # waiting | bet_placed | playing | stuck | bust | blackjack
                "result": ""
            }

    def remove_player(self, username):
        if username in self.players:
            idx = self.players.index(username)
            self.players.remove(username)
            del self.seats[username]
            if self.phase == "playing":
                if idx < self.turn_index:
                    self.turn_index -= 1
                self.advance_turn_if_needed()
            elif self.phase == "betting" and self.players:
                self.check_all_bets_placed()

    def place_bet(self, username, amount):
        if self.phase == "round_over":
            self.reset_for_next_round()

        if self.phase != "betting" or username not in self.seats:
            return False, "Cannot bet right now"

        seat = self.seats[username]
        if seat["status"] == "bet_placed":
            return False, "Bet already placed for this hand"

        seat["bet"] = amount
        seat["status"] = "bet_placed"
        seat["result"] = ""
        self.check_all_bets_placed()
        return True, "Bet placed"

    def check_all_bets_placed(self):
        active = [u for u in self.players if self.seats[u]["status"] == "bet_placed"]
        if len(active) > 0 and len(active) == len(self.players):
            self.start_round()

    def start_round(self):
        self.reshuffled_recently = False
        if len(self.shoe) < self.cut_card_threshold:
            self.build_shoe()

        self.phase = "playing"
        self.dealer_hand = [self.draw_card(), self.draw_card()]

        for u in self.players:
            seat = self.seats[u]
            seat["hand"] = [self.draw_card(), self.draw_card()]
            val, _ = calc_hand_value(seat["hand"])
            if val == 21:
                seat["status"] = "blackjack"
            else:
                seat["status"] = "playing"

        self.turn_index = 0
        self.advance_turn_if_needed()

    def advance_turn_if_needed(self):
        while self.turn_index < len(self.players):
            current_user = self.players[self.turn_index]
            if self.seats[current_user]["status"] == "playing":
                self.message = f"{current_user}'s turn: Twist or Stick?"
                return
            self.turn_index += 1

        # All players have finished their turns -> Dealer plays
        self.finish_dealer_and_payouts()

    def twist(self, username):
        if self.phase != "playing" or self.players[self.turn_index] != username:
            return False, "Not your turn"

        seat = self.seats[username]
        seat["hand"].append(self.draw_card())
        val, _ = calc_hand_value(seat["hand"])

        if val > 21:
            seat["status"] = "bust"
            self.advance_turn_if_needed()
        elif val == 21:
            seat["status"] = "stuck"
            self.advance_turn_if_needed()

        return True, "Twisted"

    def stick(self, username):
        if self.phase != "playing" or self.players[self.turn_index] != username:
            return False, "Not your turn"

        self.seats[username]["status"] = "stuck"
        self.advance_turn_if_needed()
        return True, "Stuck"

    def finish_dealer_and_payouts(self):
        self.phase = "round_over"
        any_live_players = any(
            self.seats[u]["status"] in ("stuck", "blackjack") for u in self.players
        )

        if any_live_players:
            while True:
                d_val, _ = calc_hand_value(self.dealer_hand)
                if d_val < 17:
                    self.dealer_hand.append(self.draw_card())
                else:
                    break

        d_val, _ = calc_hand_value(self.dealer_hand)
        dealer_bj = (d_val == 21 and len(self.dealer_hand) == 2)

        self.payout_results = {}
        for u in self.players:
            seat = self.seats[u]
            bet = seat["bet"]
            if bet <= 0:
                continue

            p_val, _ = calc_hand_value(seat["hand"])
            player_bj = (seat["status"] == "blackjack")

            if seat["status"] == "bust":
                seat["result"] = f"BUST (-£{bet})"
                payout = 0
            elif player_bj and not dealer_bj:
                winnings = int(bet * 2.5)
                seat["result"] = f"BLACKJACK! (+£{winnings - bet})"
                payout = winnings
            elif dealer_bj and not player_bj:
                seat["result"] = f"DEALER BJ (-£{bet})"
                payout = 0
            elif d_val > 21 or p_val > d_val:
                winnings = bet * 2
                seat["result"] = f"WIN (+£{bet})"
                payout = winnings
            elif p_val == d_val:
                seat["result"] = "PUSH (Returned)"
                payout = bet
            else:
                seat["result"] = f"LOSE (-£{bet})"
                payout = 0

            if payout > 0:
                self.payout_results[u] = payout

        self.message = "Round over! Place a bet for the next hand."

    def reset_for_next_round(self):
        self.phase = "betting"
        self.dealer_hand = []
        self.turn_index = 0
        for u in self.players:
            self.seats[u] = {
                "hand": [],
                "bet": 0,
                "status": "waiting",
                "result": ""
            }
        self.message = "Place your bets!"

    def to_dict(self):
        hide_hole = (self.phase == "playing")
        if not self.dealer_hand:
            visible_dealer = []
            dealer_total_str = ""
        elif hide_hole:
            visible_dealer = [self.dealer_hand[0], "Back"]
            up_val, _ = calc_hand_value([self.dealer_hand[0]])
            dealer_total_str = f"({up_val})"
        else:
            visible_dealer = self.dealer_hand
            d_val, _ = calc_hand_value(self.dealer_hand)
            dealer_total_str = f"({d_val})"

        active_player = (
            self.players[self.turn_index]
            if (self.phase == "playing" and self.turn_index < len(self.players))
            else None
        )

        players_data = []
        for u in self.players:
            s = self.seats[u]
            val, is_soft = calc_hand_value(s["hand"])
            total_label = ""
            if s["hand"]:
                if is_soft and val <= 21 and val - 10 > 0:
                    total_label = f"{val - 10}/{val}"
                else:
                    total_label = str(val)

            players_data.append({
                "username": u,
                "hand": s["hand"],
                "total": total_label,
                "bet": s["bet"],
                "status": s["status"],
                "result": s["result"],
                "is_turn": (u == active_player)
            })

        return {
            "phase": self.phase,
            "message": self.message,
            "active_player": active_player,
            "cards_remaining": len(self.shoe),
            "reshuffled": self.reshuffled_recently,
            "dealer": {
                "hand": visible_dealer,
                "total": dealer_total_str
            },
            "players": players_data
        }