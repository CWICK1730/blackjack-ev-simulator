import streamlit as st
import random


# Blackjack Simulator Class
class BlackjackSimulator:
    def __init__(self, num_decks=1):
        self.num_decks = num_decks
        self.reset_deck()
        self.card_mapping = {
            "A": 1,  # Ace
            "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10,
            "J": 10, "Q": 10, "K": 10  # Face cards
        }

    def reset_deck(self):
        """Create and shuffle the deck."""
        self.deck = [value for value in range(1, 14) for _ in range(4)] * self.num_decks
        random.shuffle(self.deck)

    def draw_card(self):
        """Draw a card from the deck. If the deck is empty, reset it."""
        if len(self.deck) == 0:
            self.reset_deck()
        return self.deck.pop()

    def convert_input_to_values(self, input_cards):
        """Convert card notation (e.g., 'A', 'K') to numerical values."""
        return [self.card_mapping[card.upper()] for card in input_cards]

    @staticmethod
    def calculate_hand_value(hand):
        """Calculate the best value of a blackjack hand."""
        value = 0
        aces = 0
        for card in hand:
            if card > 10:  # Face cards
                value += 10
            elif card == 1:  # Ace
                aces += 1
                value += 11
            else:
                value += card

        # Adjust for aces
        while value > 21 and aces:
            value -= 10
            aces -= 1
        return value

    def simulate_outcome(self, player_hand, dealer_card, blackjack_3_2=False):
        """Simulate the dealer's turn and compare hands."""
        dealer_hand = [dealer_card, self.draw_card()]
        while self.calculate_hand_value(dealer_hand) < 17:
            dealer_hand.append(self.draw_card())

        player_value = self.calculate_hand_value(player_hand)
        dealer_value = self.calculate_hand_value(dealer_hand)

        # Check for blackjack payout for player
        if len(player_hand) == 2 and player_value == 21 and blackjack_3_2:
            if len(dealer_hand) == 2 and dealer_value == 21:  # Both have blackjack
                return 0  # Push
            return 1.5  # Player wins with 3:2 payout on blackjack

        if dealer_value > 21 or player_value > dealer_value:
            return 1  # Player wins
        elif player_value < dealer_value:
            return -1  # Player loses
        else:
            return 0  # Push

    def simulate_split(self, player_hand, dealer_card):
        """Simulate splitting the hand."""
        card_value = player_hand[0]
        first_hand = [card_value, self.draw_card()]
        second_hand = [card_value, self.draw_card()]

        ev_first = self.simulate_outcome(first_hand, dealer_card)
        ev_second = self.simulate_outcome(second_hand, dealer_card)
        return (ev_first + ev_second) / 2  # Average EV of both hands

    def simulate_double(self, player_hand, dealer_card):
        """Simulate doubling the hand."""
        player_hand.append(self.draw_card())  # Draw exactly one more card
        if self.calculate_hand_value(player_hand) > 21:
            return -2  # Double bet is lost if player busts
        return 2 * self.simulate_outcome(player_hand, dealer_card)  # Double the bet outcome

    def simulate_hand(self, player_hand, dealer_card, action, simulations=100000):
        """Simulate a hand and calculate the EV and probabilities."""
        ev = 0
        win_count = 0
        lose_count = 0
        push_count = 0

        for _ in range(simulations):
            if action == "hit":
                result = self.simulate_hit(player_hand[:], dealer_card)
            elif action == "stand":
                result = self.simulate_stand(player_hand[:], dealer_card)
            elif action == "split":
                result = self.simulate_split(player_hand[:], dealer_card)
            elif action == "double":
                result = self.simulate_double(player_hand[:], dealer_card)
            else:
                continue

            if result > 0:
                win_count += 1
            elif result < 0:
                lose_count += 1
            else:
                push_count += 1

            ev += result  # Only wins (+1/+1.5) and losses (-1/-2) affect EV; pushes contribute 0

        total = simulations
        probabilities = {
            "win": win_count / total,
            "lose": lose_count / total,
            "push": push_count / total,
        }
        return ev / simulations, probabilities

    def simulate_hit(self, player_hand, dealer_card):
        """Simulate hitting and returning the result."""
        player_hand.append(self.draw_card())
        if self.calculate_hand_value(player_hand) > 21:
            return -1  # Player busts
        return self.simulate_outcome(player_hand, dealer_card)

    def simulate_stand(self, player_hand, dealer_card):
        """Simulate standing and returning the result."""
        return self.simulate_outcome(player_hand, dealer_card, blackjack_3_2=True)

    def simulate(self, player_hand, dealer_card):
        """Calculate EV and probabilities for all actions."""
        results = {}
        actions = ["stand", "hit"]
        player_hand_value = self.calculate_hand_value(player_hand)

        # Add split only if the cards are identical
        if len(player_hand) == 2 and player_hand[0] == player_hand[1]:
            actions.append("split")

        # Add double only if the hand value is 10 or 11
        if player_hand_value in [10, 11]:
            actions.append("double")

        for action in actions:
            ev, probabilities = self.simulate_hand(player_hand[:], dealer_card, action)
            results[action] = {"EV": ev, **probabilities}
        return results


# Streamlit Interface
st.title("Blackjack EV Simulator")
st.write("Calculate the Expected Value (EV) and probabilities for your blackjack hands!")

# User Input
player_hand = st.text_input("Enter your hand (e.g., 'A 8'):")
dealer_card = st.text_input("Enter dealer's up-card (e.g., '10'):")

if player_hand and dealer_card:
    simulator = BlackjackSimulator(num_decks=6)
    player_hand_values = simulator.convert_input_to_values(player_hand.split())
    dealer_card_value = simulator.convert_input_to_values([dealer_card])[0]

    # Run Simulation
    results = simulator.simulate(player_hand_values, dealer_card_value)

    # Display Results
    st.write("### Results")
    for action, metrics in results.items():
        st.write(f"**{action.capitalize()}**:")
        st.write(f"- EV: {metrics['EV']:.2f}")
        st.write(f"- Win Probability: {metrics['win']:.2%}")
        st.write(f"- Lose Probability: {metrics['lose']:.2%}")
        st.write(f"- Push Probability: {metrics['push']:.2%}")
