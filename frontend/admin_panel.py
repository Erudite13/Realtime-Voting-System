import streamlit as st
import boto3
import uuid
import datetime
import os

# AWS Services
dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
s3 = boto3.client('s3')
BUCKET_NAME = "votesbucketmajorproject"

# DynamoDB Tables
election_table = dynamodb.Table('Elections')
candidate_table = dynamodb.Table('Candidates')

# --- Authentication ---
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"  

def authenticate():
    with st.sidebar:
        st.subheader("🔐 Admin Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_btn = st.button("Login")

    if login_btn:
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            st.session_state["is_admin"] = True
            st.success("✅ Login successful.")
        else:
            st.error("❌ Invalid credentials.")

    return st.session_state.get("is_admin", False)

# --- Election Storage ---
def save_election_to_dynamo(name, start_date, end_date, description):
    election_id = str(uuid.uuid4())
    item = {
        'election_id': election_id,
        'name': name,
        'description': description,
        'start_date': str(start_date),
        'end_date': str(end_date),
        'created_at': datetime.datetime.utcnow().isoformat()
    }
    election_table.put_item(Item=item)
    return election_id

# --- Candidate Storage ---
def upload_candidate_image(candidate_name, file):
    if file is None:
        return None

    ext = os.path.splitext(file.name)[-1].lower()
    key = f"candidate-images/{candidate_name}_{uuid.uuid4().hex}{ext}"
    s3.upload_fileobj(file, BUCKET_NAME, key, ExtraArgs={'ContentType': file.type})
    return f"https://{BUCKET_NAME}.s3.amazonaws.com/{key}"

def save_candidate_to_dynamo(election_id, name, party, age, bio, image_url=None):
    candidate_id = str(uuid.uuid4())
    item = {
        'candidate_id': candidate_id,
        'election_id': election_id,
        'name': name,
        'party': party,
        'age': age,
        'bio': bio,
        'image_url': image_url or "",  # Store empty if no image
        'created_at': datetime.datetime.utcnow().isoformat()
    }
    candidate_table.put_item(Item=item)
    return candidate_id

def get_all_elections():
    response = election_table.scan()
    return response.get('Items', [])

# --- Main Admin Panel ---
def show():
    if not authenticate():
        return  # Don't proceed if not logged in

    st.title("🗳️ Admin Control Panel")

    tab1, tab2, tab3 = st.tabs(["➕ Create Election", "👤 Add Candidate", "⚙️ Settings"])

    # --- Tab 1: Create Election ---
    with tab1:
        st.subheader("➕ Create New Election")
        name = st.text_input("Election Name")
        description = st.text_area("Election Description")
        start_date = st.date_input("Start Date", datetime.date.today())
        end_date = st.date_input("End Date", datetime.date.today() + datetime.timedelta(days=7))

        if st.button("Create Election"):
            if name:
                election_id = save_election_to_dynamo(name, start_date, end_date, description)
                st.success(f"✅ Election '{name}' created successfully with ID: {election_id}")
            else:
                st.error("⚠️ Please enter a valid election name.")

    # --- Tab 2: Add Candidate ---
    with tab2:
        st.subheader("👤 Add Candidate")
        elections = get_all_elections()
        election_names = {e["name"]: e["election_id"] for e in elections}

        if election_names:
            selected_election_name = st.selectbox("Select Election", list(election_names.keys()))
            selected_election_id = election_names[selected_election_name]

            candidate_name = st.text_input("Candidate Name")
            party = st.text_input("Political Party")
            age = st.number_input("Age", min_value=18, max_value=100)
            bio = st.text_area("Bio / Manifesto")
            image_file = st.file_uploader("Candidate Image (optional)", type=["png", "jpg", "jpeg"])

            if st.button("Add Candidate"):
                if candidate_name and party:
                    image_url = upload_candidate_image(candidate_name, image_file)
                    candidate_id = save_candidate_to_dynamo(
                        selected_election_id, candidate_name, party, age, bio, image_url
                    )
                    st.success(f"✅ Candidate '{candidate_name}' added to election '{selected_election_name}'.")
                else:
                    st.error("⚠️ Please enter both candidate name and political party.")
        else:
            st.warning("⚠️ No elections found. Please create one first.")

    # --- Tab 3: Settings ---
    with tab3:
        st.subheader("⚙️ System Settings / Logs")
        st.info("This section can include admin logs or future settings.")


