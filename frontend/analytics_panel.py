import streamlit as st
import boto3
import pandas as pd
import json
from io import BytesIO
from fpdf import FPDF
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import time
import streamlit.components.v1 as components
import urllib.request
import os


# AWS Clients
dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
kinesis_client = boto3.client('kinesis', region_name='ap-south-1')

# DynamoDB Tables
votes_table = dynamodb.Table('Votes')
elections_table = dynamodb.Table('Elections')
candidates_table = dynamodb.Table('Candidates')

# Geocoder
geolocator = Nominatim(user_agent="geoapi")

def geocode_location(city, state, country):
    try:
        location = geolocator.geocode(f"{city}, {state}, {country}")
        if location:
            return location.latitude, location.longitude
    except GeocoderTimedOut:
        time.sleep(1)
        return geocode_location(city, state, country)
    return None, None

# Functions
def get_all_elections():
    response = elections_table.scan()
    return response.get('Items', [])

def get_candidates_by_election(election_id):
    response = candidates_table.scan(
        FilterExpression="election_id = :eid",
        ExpressionAttributeValues={":eid": election_id}
    )
    return response.get('Items', [])

def get_votes_from_dynamodb(selected_election_id):
    response = votes_table.scan(
        FilterExpression="election_id = :eid",
        ExpressionAttributeValues={":eid": selected_election_id}
    )
    return response.get('Items', [])

def get_votes_from_kinesis(stream_name='Vote_Major_Project', limit=100):
    shard_id = kinesis_client.describe_stream(StreamName=stream_name)['StreamDescription']['Shards'][0]['ShardId']
    shard_iterator = kinesis_client.get_shard_iterator(
        StreamName=stream_name,
        ShardId=shard_id,
        ShardIteratorType='LATEST'
    )['ShardIterator']

    out = []
    record_response = kinesis_client.get_records(ShardIterator=shard_iterator, Limit=limit)
    records = record_response['Records']

    for record in records:
        payload = json.loads(record['Data'])
        out.append(payload)

    return out

def generate_pdf(election_info, candidates, df):
    pdf = FPDF(format='A4')
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
    pdf.set_font("DejaVu", size=12)
    pdf.add_page()

    # Title
    pdf.set_font("DejaVu", "", 16)
    pdf.cell(0, 10, "Election Report", ln=True, align='C')
    pdf.ln(10)

    # Election Details
    pdf.set_font("DejaVu", size=12)
    pdf.cell(0, 10, "Election Details:", ln=True)
    for key in ['name', 'description', 'start_date', 'end_date']:
        if key in election_info:
            pdf.cell(0, 10, f"{key.replace('_', ' ').capitalize()}: {election_info[key]}", ln=True)
    pdf.ln(5)

    # Candidates with images
    pdf.set_font("DejaVu", size=12)
    pdf.cell(0, 10, "Candidates:", ln=True)
    for candidate in candidates:
        pdf.cell(0, 10, f"Name: {candidate.get('name', '')}", ln=True)
        pdf.cell(0, 10, f"Party: {candidate.get('party', '')}", ln=True)
        pdf.multi_cell(0, 10, f"Bio: {candidate.get('bio', '')}", align='L')
        img_url = candidate.get('image_url', '')
        if img_url:
            try:
                response = requests.get(img_url)
                if response.status_code == 200:
                    img = BytesIO(response.content)
                    pdf.image(img, w=40, h=40)
            except Exception as e:
                pdf.cell(0, 10, "[Image load failed]", ln=True)
        pdf.ln(5)

    # Summary
    pdf.add_page()
    pdf.set_font("DejaVu", "", 14)
    pdf.cell(0, 10, "Election Summary", ln=True)
    pdf.set_font("DejaVu", size=12)
    pdf.multi_cell(0, 10, f"A total of {len(df)} votes were cast in the election. Candidate-wise details are shown below.")
    pdf.ln(5)

    # Results Table
    vote_counts = df['candidate_name'].value_counts().reset_index()
    vote_counts.columns = ['Candidate', 'Votes']

    pdf.set_font("DejaVu", size=11)
    col_width = pdf.w / 3
    pdf.cell(col_width, 10, "Candidate", border=1)
    pdf.cell(col_width, 10, "Votes", border=1)
    pdf.ln()
    for idx, row in vote_counts.iterrows():
        pdf.cell(col_width, 10, str(row['Candidate']), border=1)
        pdf.cell(col_width, 10, str(row['Votes']), border=1)
        pdf.ln()

    pdf.ln(5)
    pdf.multi_cell(0, 10, f"Congratulations to {vote_counts.iloc[0]['Candidate']} for receiving the highest votes!")

    return bytes(pdf.output(dest='S').encode('latin-1'))


def display_overview(votes, election_info, candidates):
    st.header("📋 Overview Dashboard")
    if election_info:
        st.subheader("Election Details")
        st.write(f"**Name:** {election_info.get('name')}")
        st.write(f"**Description:** {election_info.get('description')}")

    st.subheader("Candidates")
    st.write(f"**Total Candidates:** {len(candidates)}")
    for idx, candidate in enumerate(candidates, 1):
        st.write(f"{idx}. {candidate['name']} - {candidate.get('party', 'Independent')}")

    total_votes = len(votes)
    st.metric(label="Total Votes Casted", value=total_votes)
    
def display_detailed_analysis():
    st.header("📊 Detailed Analysis")
    

    st.markdown("""
        This dashboard provides deep insights into real-time voting trends, geographical breakdown,
        candidate popularity, and engagement metrics.
    """)

    # AWS QuickSight Embedding Configuration
    account_id = "471112827892"  
    dashboard_id = "30b382df-f86a-4c93-80a8-0bcbf7c92f8d"
    namespace = "default"  
    user_arn = "arn:aws:quicksight:ap-south-1:471112827892:user/default/471112827892" 

    try:
        qs_client = boto3.client("quicksight", region_name="ap-south-1")

        response = qs_client.get_dashboard_embed_url(
            AwsAccountId=account_id,
            DashboardId=dashboard_id,
            IdentityType="QUICKSIGHT",
            UserArn=user_arn,
            SessionLifetimeInMinutes=600,
            UndoRedoDisabled=False,
            ResetDisabled=False
        )

        embed_url = response['EmbedUrl']
        components.iframe(embed_url, width=960, height=720)

    except Exception as e:
        st.error(f"Failed to load dashboard: {str(e)}")

def display_download_reports(votes, election_info, candidates):
    st.header("📥 Download Reports")
    if votes:
        df = pd.DataFrame(votes)
        pdf_buffer = generate_pdf(election_info, candidates, df)
        st.download_button(
            label="Download Election Report (PDF)",
            data=pdf_buffer,
            file_name="election_report.pdf",
            mime="application/pdf"
        )
        csv_data = df.to_csv(index=False)
        csv_buffer = BytesIO(csv_data.encode('utf-8'))
        st.download_button(
            label="Download Votes Data (CSV)",
            data=csv_buffer,
            file_name="votes_data.csv",
            mime="text/csv"
        )
    else:
        st.warning("No data available to download.")

def show():
    st.title("📊 Voting Analytics Panel")

    elections = get_all_elections()
    election_options = {election['name']: election['election_id'] for election in elections}
    selected_election_name = st.selectbox("🗳️ Select Election", list(election_options.keys()))
    selected_election_id = election_options[selected_election_name]

    selected_election_info = next((e for e in elections if e['election_id'] == selected_election_id), {})
    candidates = get_candidates_by_election(selected_election_id)

    data_source = st.radio(
        "🔍 Select Data Source",
        options=["All Votes (DynamoDB)"],
        horizontal=True
    )

                #, "Live Votes (Kinesis)"

    if data_source == "All Votes (DynamoDB)":
        votes = get_votes_from_dynamodb(selected_election_id)
    else:
        votes = get_votes_from_kinesis()

    tabs = st.radio(
        "🚀 Navigate",
        options=["Overview", "Detailed Analysis", "Download Reports"],
        horizontal=True,
        index=0,
    )

    st.markdown("---")

    if tabs == "Overview":
        display_overview(votes, selected_election_info, candidates)
    elif tabs == "Detailed Analysis":
        display_detailed_analysis()
    elif tabs == "Download Reports":
        display_download_reports(votes, selected_election_info, candidates)

if __name__ == "__main__":
    show()
