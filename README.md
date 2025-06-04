# 🗳️ Real-Time Voting System (AWS-Powered)

A fully serverless, real-time voting system built using **AWS Kinesis**, **DynamoDB**, **Lambda**, **S3**, **Glue**, **Athena**, and **QuickSight**, with a frontend built using **Streamlit**. This project demonstrates how to build an end-to-end data pipeline for collecting, processing, analyzing, and visualizing vote data in real time.

---

## 🔧 Features

- 📥 Real-time vote capture through Streamlit interface
- 🔄 Streaming data ingestion via AWS Kinesis
- 🗃️ Scalable, NoSQL vote storage using DynamoDB
- 🧠 Predictive modeling with Amazon SageMaker (optional)
- 📊 Live dashboards using Amazon QuickSight
- 🔎 SQL-based ad hoc analytics with Amazon Athena
- 🌐 Serverless infrastructure using AWS Lambda and Glue

---

## 🧱 Architecture

![image](https://github.com/user-attachments/assets/e955d503-7ee9-4b11-bf9c-756bcabffbcf)


---

## 🛠️ Tech Stack

- **Frontend:** Python, Streamlit
- **Backend Services:** AWS Kinesis, Lambda, DynamoDB, S3
- **Analytics:** Glue, Athena, QuickSight
- **ML (Optional):** Amazon SageMaker
- **Language & Tools:** Python (boto3, pandas), SQL

---

## 📁 Data Flow 

![image](https://github.com/user-attachments/assets/6da5e244-96d6-4c5d-9830-23c722e696e5)


---

## 🚀 How to Deploy

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Erudite13/Realtime-Voting-System.git
   cd Realtime-Voting-System
2. **Set up AWS resources:**

   Kinesis Data Stream (VoteStream)
   DynamoDB Table (Votes)
   S3 bucket (votesbucket)
   IAM roles and Lambda functions

Run the frontend:

Copy
Edit
cd voting-app
streamlit run app.py

Create ETL pipeline:
Glue Crawler to catalog S3 data
Athena for SQL queries
Connect QuickSight to Athena for visualization

📊 Sample Dashboard

![image](https://github.com/user-attachments/assets/825292a8-1e18-41f8-b28f-3d801d93a359)


📦 Future Enhancements
Add user authentication and admin dashboard
Generate automatic PDF election summaries
Visualize voter distribution on interactive maps
Integrate location-based analytics and alerts

👨‍💻 Author
Rudra Srivastava
href{https://linkedin.com/in/rudra-srivastava, Linkedin}| GitHub



