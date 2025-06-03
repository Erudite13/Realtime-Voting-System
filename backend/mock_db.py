import json
import os

VOTES_FILE = "data/votes.json"
os.makedirs("data", exist_ok=True)

def store_vote_locally(vote_data):
    with open(VOTES_FILE, "a") as f:
        f.write(json.dumps(vote_data) + "\n")
