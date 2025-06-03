import streamlit as st
import boto3
import json
import uuid
from datetime import datetime, timedelta
import random
import logging
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from decimal import Decimal

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VotingPanel")

# AWS setup
region = 'ap-south-1'
dynamodb = boto3.resource('dynamodb', region_name=region)
election_table = dynamodb.Table('Elections')
candidate_table = dynamodb.Table('Candidates')
vote_table = dynamodb.Table('Votes')
ses = boto3.client('ses', region_name=region)
kinesis = boto3.client('kinesis', region_name=region)

# Geo setup
geolocator = Nominatim(user_agent="vote_panel")

def geocode_location(city, state, country):
    try:
        location = geolocator.geocode(f"{city}, {state}, {country}")
        if location:
            return location.latitude, location.longitude
    except GeocoderTimedOut:
        pass
    return None, None

def get_available_elections():
    return election_table.scan().get("Items", [])

def get_candidates_by_election(election_id):
    return [c for c in candidate_table.scan().get("Items", []) if c["election_id"] == election_id]

def has_already_voted(voter_id, election_id):
    response = vote_table.get_item(Key={'voter_id': voter_id})
    return response.get('Item') and response["Item"].get("election_id") == election_id

def send_otp_email(email, otp):
    ses.send_email(
        Source="rudrasrivastava2003@gmail.com",
        Destination={"ToAddresses": [email]},
        Message={
            "Subject": {"Data": "🗳️ Your Voting OTP"},
            "Body": {"Text": {"Data": f"Your OTP is: {otp} (Valid for 5 minutes)"}}
        }
    )
    logger.info(f"OTP {otp} sent to {email}")

def send_receipt_email(email, vote_data):
    body = (
        f"Hello {vote_data['voter_name']},\n\n"
        f"You have successfully voted in election: {vote_data['election_id']}\n"
        f"Candidate: {vote_data['candidate_name']} ({vote_data['party']})\n"
        f"Vote ID: {vote_data['vote_id']}\n"
        f"Time: {vote_data['timestamp']}\n"
        f"Location: {vote_data['city']}, {vote_data['state']}, {vote_data['country']}\n\n"
        f"Thank you for participating!\n"
    )
    ses.send_email(
        Source="rudrasrivastava2003@gmail.com",
        Destination={"ToAddresses": [email]},
        Message={
            "Subject": {"Data": "🧾 Vote Receipt"},
            "Body": {"Text": {"Data": body}}
        }
    )
    logger.info(f"Vote receipt sent to {email}")

def record_vote(voter_id, voter_name, email, election_id, candidate_id, candidate_name, party, city, state, country):
    lat, lon = geocode_location(city, state, country)
    vote_id = str(uuid.uuid4())
    vote_data = {
        "vote_id": vote_id,
        "voter_id": voter_id,
        "voter_name": voter_name,
        "email": email,
        "election_id": election_id,
        "candidate_id": candidate_id,
        "candidate_name": candidate_name,
        "party": party,
        "city": city,
        "state": state,
        "country": country,
        "latitude": Decimal(str(lat)) if lat else None,
        "longitude": Decimal(str(lon)) if lon else None,
        "timestamp": datetime.utcnow().isoformat()
    }

    vote_table.put_item(Item=vote_data)

    kinesis_data = vote_data.copy()
    if isinstance(kinesis_data["latitude"], Decimal):
        kinesis_data["latitude"] = float(kinesis_data["latitude"])
    if isinstance(kinesis_data["longitude"], Decimal):
        kinesis_data["longitude"] = float(kinesis_data["longitude"])

    kinesis.put_record(
        StreamName="election-votes-stream",
        Data=json.dumps(kinesis_data),
        PartitionKey="vote"
    )
    logger.info(f"Vote recorded: {vote_id}")
    return vote_id, vote_data

# Streamlit app
def show():
    st.title("📩 Secure Voting Panel")

    st.subheader("Voter Verification")
    voter_name = st.text_input("Your Name")
    voter_email = st.text_input("Email (OTP & Receipt)")
    voter_id = st.text_input("Voter ID")
    city = st.text_input("City")
    state = st.text_input("State")
    country = st.text_input("Country")

    if not all([voter_name, voter_email, voter_id, city, state, country]):
        st.warning("Please complete all voter and location fields.")
        return

    if "otp_sent_count" not in st.session_state:
        st.session_state.otp_sent_count = 0
    if "otp_verified" not in st.session_state:
        st.session_state.otp_verified = False

    if st.session_state.otp_sent_count < 3 and not st.session_state.otp_verified:
        if st.button("📧 Send OTP"):
            otp_code = str(random.randint(100000, 999999))
            try:
                send_otp_email(voter_email, otp_code)
                st.session_state.otp_code = otp_code
                st.session_state.otp_timestamp = datetime.utcnow()
                st.session_state.otp_sent_count += 1
                st.success("OTP sent! Please check your email.")
            except Exception as e:
                st.error(f"Error sending OTP: {e}")
    elif st.session_state.otp_sent_count >= 3 and not st.session_state.otp_verified:
        st.error("❌ Maximum OTP attempts reached (3). Please try later.")
        return

    if "otp_code" in st.session_state:
        input_otp = st.text_input("Enter OTP")
        if st.button("✅ Verify OTP"):
            now = datetime.utcnow()
            if now - st.session_state.otp_timestamp > timedelta(minutes=5):
                st.error("❌ OTP expired. Please request again.")
                st.session_state.pop("otp_code", None)
                st.session_state.pop("otp_timestamp", None)
                st.session_state.otp_sent_count = 0
            elif input_otp == st.session_state.otp_code:
                st.success("OTP verified ✅")
                st.session_state.otp_verified = True
            else:
                st.error("Incorrect OTP ❌")

    if not st.session_state.otp_verified:
        return

    elections = get_available_elections()
    election_map = {e["name"]: e["election_id"] for e in elections}
    if not election_map:
        st.warning("No available elections.")
        return

    selected_election = st.selectbox("Select Election", list(election_map.keys()))
    selected_election_id = election_map[selected_election]

    if has_already_voted(voter_id, selected_election_id):
        st.error("⚠️ You’ve already voted in this election.")
        return

    candidates = get_candidates_by_election(selected_election_id)
    if not candidates:
        st.info("No candidates listed.")
        return

    st.subheader("🧑‍💼 Choose Your Candidate")

    for candidate in candidates:
        col1, col2 = st.columns([1, 5])
        with col1:
            if 'image_url' in candidate and candidate['image_url']:
                st.image(candidate['image_url'], width=80)
            else:
                st.image("https://upload.wikimedia.org/wikipedia/commons/8/89/Portrait_Placeholder.png", width=80)
        with col2:
            st.markdown(f"**{candidate['name']}** ({candidate.get('party', 'Independent')})")
            st.caption(candidate.get("bio", ""))

    option_map = {
        f"{c['name']} ({c['party']})": (c["candidate_id"], c["name"], c["party"])
        for c in candidates
    }
    selected_option = st.radio("Confirm your vote for:", list(option_map.keys()))
    candidate_id, candidate_name, party = option_map[selected_option]

    if st.button("🗳️ Submit Vote"):
        try:
            vote_id, vote_data = record_vote(
                voter_id, voter_name, voter_email,
                selected_election_id, candidate_id, candidate_name, party,
                city, state, country
            )
            send_receipt_email(voter_email, vote_data)
            st.success(f"🎉 Vote submitted! ID: {vote_id}")
            st.balloons()
        except Exception as e:
            st.error(f"Vote submission failed: {e}")
            logger.exception("Vote submission failed")

# Run
if __name__ == "__main__":
    show()
