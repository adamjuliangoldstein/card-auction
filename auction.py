#!/usr/bin/env python2.7

import random
import numpy

# TODO separate these into different files
# TODO add a "silent auction" version
# TODO add tests
# TODO remove prints/improve logging so it can be turned off

class Table:
    def __init__(self):
        self.hole_card = None
        self.deck = Deck()
        self.players = [HumanPlayer('Adam'), SmartBot('Bob')]
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
            candidate_index = self.next_first_player_index
        else: 
            candidate_index = self.players.index(player)
            candidate_index = (candidate_index + 1) % len(self.players)
        num_tries = 0
        # Keep going until we find a player who isn't out:
        while self.players[candidate_index].is_out():
            if num_tries > len(self.players):
                break
            candidate_index = (candidate_index + 1) % len(self.players)
            num_tries += 1
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
            print "The deck is empty"
            return False
        print "\nA card is drawn into the hole: {}".format(self.hole_card)
        # Who starts the next bid:
        player = None
        winner = None
        passes = 0
        print "The hand begins"
        while True:
            last_player = player
            player = self._next_player(player)
            # If we've gone all the way around and ended on the same player
            if player == last_player:
                self.assign_winner(player)
                break
            # Otherwise
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
        # If the player doesn't have the given card
        if bid_to_verify not in player.biddables:
            return False
        current_totals = {}
        for p in self.players:
            current_totals[p] = sum(p.plays)
        top_score = max(current_totals.values())
        # Verify that playing this bid for player will make them the top total
        return current_totals[player] + bid_to_verify > top_score
    
    def all_others_out(self, player):
        return all(p.is_out() for p in self.other_players(player))

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
    
    def expected_value(self):
        if self.cards:
            return numpy.mean(self.cards)
        else:
            return 0

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
    
    # Get my desired play via _play(), then do housekeeping
    # returning None means passing
    def play(self, table):
        # If we've already passed the current hand, keep passing
        if self.passed_current_hand:
            return None
        # If we're already out of cards, pass:
        if self.is_out():            
            self.passed_current_hand = True
            return None
        res = self._play(table)
        # If we're passing
        if not res:
            self.passed_current_hand = True
            return None
        # If we're bidding, but our bid is not valid
        elif not table.verify_play(self, res):
            print "INVALID PLAY: {}".format(res)
            self.passed_current_hand = True
            return None
        # If we're bidding, and our bid is valid
        else:
            self.biddables.remove(res)
            self.plays.append(res)
            return sum(self.plays)
    
    # This is where the playing logic/AI happens; override in subclasses
    # TODO figure out how to make play (not _play) un-overridable
    def _play(self, table):
        raise

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

# TODO make a player that prompts the human to play

class HumanPlayer(Player):
    def _play(self, table):
        for p in table.other_players(self):
            print "{} has played {} = {}".format(p, p.plays, sum(p.plays))
            print "{} has biddables {}".format(p, p.biddables)
        print "You have played {} = {}".format(self.plays, sum(self.plays))
        print "You currently have biddables: {}".format(self.biddables)
        c = raw_input('Enter a card (or 0 to pass): ')
        n = int(c)
        if n == 0:
            # Pass
            return None
        else:
            return n

# Keep trying to play the highest card no matter what
class HighBot(Player):
    def _play(self, table):
        if self.is_out():
            return None
        else:
            return max(self.biddables)

# Pass no matter what
class PassBot(Player):
    def _play(self, table):
        return None

# Pass if any of the other players have cards left; otherwise play
class PassThenPlayBot(Player):
    def _play(self, table):
        # If everyone else is out, bid
        if table.all_others_out(self):
            return min(self.biddables)
        else:
            return None

# Pass if any of the other players have cards left; otherwise pass only if 
# it's the highest-EV thing to do
class SmarterPassBot(Player):
    def _play(self, table):
        # If everyone else is out, bid if it's worth it
        if table.all_others_out(self):
            if table.hole_card > table.deck.expected_value():
                return min(self.biddables)
            else:
                return None
        # If at least one other player has cards, pass
        else:
            return None

# If nobody else has any cards, play if it's the highest-EV thing to do
# Never play more than one card per hand
# Otherwise, play the chosen card
class SmartBot(Player):
    def _play(self, table):
        # If everyone else is out, bid if it's the highest-EV thing to do
        if table.all_others_out(self):
            if table.hole_card > table.deck.expected_value():
                return min(self.biddables)
            else:
                return None
        # If I've already played a card, pass
        elif self.plays:
            return None
        # Try to play the highest card less than the hole card:
        else:
            return self._chosen_card(table)
    
    # TODO: Make table a field on Player so it doesn't have to be passed around
    def _chosen_card(self, table):
        lesser_cards = filter(lambda c: c < table.hole_card, self.biddables)
        if not lesser_cards:
            return None
        else:
            return max(lesser_cards)

# TODO break out the running of one game from the running of N
def main():
    # Initialize the table and players
    scoreboard = {}
    table = Table()
    players = table.players
    for p in players:
        if not scoreboard.has_key(p):
            scoreboard[p] = 0
    # Run the games
    n = 1
    for i in range(n):
        table.reset()
        winners = table.run_game()
        for w in winners:
            scoreboard[w] = scoreboard[w] + (1.0/len(winners))
        print "Winner(s): {}".format([p.name for p in winners])
    print "Final score: {}".format(scoreboard)

if __name__ == '__main__':
    main()