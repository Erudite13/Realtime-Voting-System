import json
import os
import uuid

DATA_PATH = "elections_data"

# Ensure the data directory exists
os.makedirs(DATA_PATH, exist_ok=True)

# Generate a unique vote ID
def generate_vote_id():
    return str(uuid.uuid4())

# Save a new election with name and dates
def save_election(name, start_date, end_date):
    data = {
        "name": name,
        "start_date": str(start_date),
        "end_date": str(end_date),
        "candidates": [],
        "votes": {}
    }
    with open(f"{DATA_PATH}/{name}.json", "w") as f:
        json.dump(data, f)

# Load all elections
def load_elections():
    return [f.replace(".json", "") for f in os.listdir(DATA_PATH) if f.endswith(".json")]

# Add a candidate to an election
def add_candidate(election_name, candidate_name):
    path = f"{DATA_PATH}/{election_name}.json"
    with open(path, "r") as f:
        data = json.load(f)

    if candidate_name not in data["candidates"]:
        data["candidates"].append(candidate_name)
        data["votes"][candidate_name] = 0

    with open(path, "w") as f:
        json.dump(data, f)

# Get candidates for a specific election
def get_candidates(election_name=None):
    if election_name:
        path = f"{DATA_PATH}/{election_name}.json"
        if os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
            return data.get("candidates", [])
        return []
    # fallback if no election is provided
    return ["Alice", "Bob", "Charlie"]

# Get results for a specific election
def get_results(election_name):
    path = f"{DATA_PATH}/{election_name}.json"
    with open(path, "r") as f:
        data = json.load(f)
    return data.get("votes", {})
