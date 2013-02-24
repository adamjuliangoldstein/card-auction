#!/usr/bin/env python2.7

import random

# TODO add to github

class Table:
    def __init__(self):
        self.hole_card = None
        self.deck = Deck()
        self.players = [PassBot('Adam'), PassBot('Bob')]
        self.next_first_player_index = 0 # Who starts the next hand
    
    def reset(self):
        self.hole_card = None
        self.deck = Deck()
        for p in self.players:
            p.reset()
        self.next_first_player_index = 0
    
    def other_players(self, player):
        res = []
        for p in self.players:
            if p != player:
                res.append(p)
        return res
    
    def _next_player(self, player):
        if not player: # If we're selecting the first player of the hand
            return self.players[self.next_first_player_index]
        else: 
            candidate_index = self.players.index(player)
            candidate_index = (candidate_index + 1) % len(self.players)
            return self.players[candidate_index]

    def assign_winner(self, winner):
        for p in self.players:
            if p == winner:
                p.hand_over(self.hole_card)
            else:
                p.hand_over()
        print "The hand is over and {} wins {}".format(winner.name,
                                                       self.hole_card)

    def check_over(self):
        last_man_standing = None
        num_live = 0
        for p in self.players:
            if not p.passed_current_hand:
                last_man_standing = p
                num_live += 1
        if num_live == 1:
            return last_man_standing
        else:
            return False

    # Return True if play continues, or False if the game is over
    def run_hand(self):
        self.hole_card = self.deck.show_top_card()
        if not self.hole_card:
            print "The game is over because the deck is empty"
            return False
        print "A card is drawn into the hole: {}".format(self.hole_card)
        # Who starts the next bid:
        player = None
        winner = None
        passes = 0
        print "The hand begins"
        while True:
            player = self._next_player(player)
            bids = player.play(self)
            if not bids:
                print "{} passes".format(player.name)
            else:
                print "{} plays {}".format(player.name, bids)
            winner = self.check_over()
            # If the hand is over
            if winner:
                self.assign_winner(winner)
                break
        self.next_first_player_index = (self.next_first_player_index +
                                        1) % len(self.players)
        if all((p.is_out() for p in self.players)):
            return False
        else:
            return True
    
    def run_game(self):
        while True:
            game_continues = self.run_hand()
            for player in self.players:
                player.print_desc()
            if not game_continues:
                break            
        print "Game over"
        return self.winners()
    
    # Possible for there to be multiple winners if there's a tie
    def winners(self):
        max_score = 0
        winners = []
        for player in self.players:
            score = player.score()
            if score > max_score:
                max_score = score
        for player in self.players:
            if player.score() == max_score:
                winners.append(player)
        return winners
        
    def verify_play(self, player, bid_to_verify):
        current_totals = {}
        for p in self.players:
            current_totals[p] = sum(p.plays)
        top_score = max(current_totals.values())
        # Verify that playing this bid for player will make them the top total
        return current_totals[player] + bid_to_verify > top_score

class Deck:
    def __init__(self):
        self.cards = range(2,15)*2

    def show_top_card(self):
        # If we're out of cards
        if not self.cards:
            return None
        else:
            random.shuffle(self.cards)
            return self.cards.pop()

class Player:
    def __init__(self, name):
        self.name = name
        self.biddables = range(2, 15)
        self.wins = [] # Cards won
        self.plays = [] # Cards played in current hand
        self.discards = [] # Cards played in previous hands
        self.passed_current_hand = False
    
    # TODO refactor this and the other reset function to be less redundant
    def reset(self):
        self.biddables = range(2, 15)
        self.wins = []
        self.plays = []
        self.discards = []
        self.passed_current_hand = False
    
    def __repr__(self):
        return "{}:{}".format(self.__class__.__name__, self.name)
    
    def play(self, table):
        # If we've already passed the current hand, keep passing
        if self.passed_current_hand:
            return None
        res = self._play(table)
        # If we're passing
        if not res:
            self.passed_current_hand = True
            return None
        # If we're bidding, but our bid is not valid
        elif not table.verify_play(self, res):
            print "INVALID PLAY"
            self.passed_current_hand = True
            return None
        # If we're bidding, and our bid is valid
        else:
            self.biddables.remove(res)
            self.plays.append(res)
            return sum(self.plays)
    
    # Prompt the player to play a card
    # None indicates the player is passing
    # Otherwise return the sum of the player's plays (including this hand)
    def _play(self, table):
        # If we have no cards or we've already played a call
        if not self.biddables or self.plays:
            return None
        else:
            return self.biddables[-1]

    # Do cleanup after the hand ends
    def hand_over(self, won = None):
        self.discards += self.plays
        self.plays = []
        if won:
            self.wins.append(won)
        self.passed_current_hand = False
    
    def score(self):
        return sum(self.wins)
    
    def is_out(self):
        return len(self.biddables) == 0
    
    def print_desc(self):
        print "{} has biddables: {}\n   wins: {}, {}\n   discards: {}".format(self.name,
                                                                          self.biddables,
                                                                          self.wins,
                                                                          sum(self.wins),
                                                                          self.discards)

class PassBot(Player):
    def _play(self, table):
        return None

def main():
    scoreboard = {}
    table = Table()
    players = table.players
    for p in players:
        if not scoreboard.has_key(p):
            scoreboard[p] = 0
    for i in range(1000):
        table.reset()
        winners = table.run_game()
        for w in winners:
            scoreboard[w] = scoreboard[w] + (1.0/len(winners))
        print "Winner(s): {}".format([p.name for p in winners])
    print "Final score: {}".format(scoreboard)

if __name__ == '__main__':
    main()