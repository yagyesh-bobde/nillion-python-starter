"""
Program 3: So basically a voting system rank based
nr of voters: m = 4
nr of candidates: n = 3
"""
from nada_dsl import *

def nada_main():
    # 1. Parties initialization
    voter0 = Party(name="Voter0")
    voter1 = Party(name="Voter1")
    voter2 = Party(name="Voter2")
    voter3 = Party(name="Voter3")
    outparty = Party(name="OutParty")

    # 2. Inputs initialization
    # Each voter ranks the candidates (0, 1, 2)
    # Lower number means higher preference
    votes = [
        [SecretUnsignedInteger(Input(name=f"v{i}_c{j}", party=globals()[f"voter{i}"])) 
         for j in range(3)] 
        for i in range(4)
    ]

    # 3. Computation
    # Initialize vote counts for each candidate
    vote_counts = [SecretUnsignedInteger(0) for _ in range(3)]

    # First round: Count first preferences
    for voter_votes in votes:
        for i, rank in enumerate(voter_votes):
            vote_counts[i] += (rank == 0).if_else(1, 0)

    # Check if any candidate has majority
    total_votes = SecretUnsignedInteger(len(votes))
    majority = total_votes // 2 + 1
    
    has_majority = SecretUnsignedInteger(0)
    winner = SecretUnsignedInteger(0)

    for i, count in enumerate(vote_counts):
        is_majority = count >= majority
        has_majority += is_majority
        winner += is_majority * i

    # If no majority, eliminate last place and redistribute votes
    if has_majority == 0:
        last_place = SecretUnsignedInteger(0)
        for i in range(1, 3):
            last_place += (vote_counts[i] < vote_counts[last_place]).if_else(i, last_place)

        # Redistribute votes
        for voter_votes in votes:
            for i, rank in enumerate(voter_votes):
                is_not_last = i != last_place
                is_second_choice = voter_votes[last_place] + 1 == rank
                vote_counts[i] += is_not_last * is_second_choice

        # Determine winner after redistribution
        for i, count in enumerate(vote_counts):
            is_most_votes = SecretUnsignedInteger(1)
            for j in range(3):
                if i != j:
                    is_most_votes *= count > vote_counts[j]
            winner += is_most_votes * i

    # 4. Output
    final_winner = Output(winner, "final_winner", outparty)
    vote_count_0 = Output(vote_counts[0], "vote_count_c0", outparty)
    vote_count_1 = Output(vote_counts[1], "vote_count_c1", outparty)
    vote_count_2 = Output(vote_counts[2], "vote_count_c2", outparty)

    return [final_winner, vote_count_0, vote_count_1, vote_count_2]
