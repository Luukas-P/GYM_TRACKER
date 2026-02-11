import streamlit as st
import psycopg2
import pymongo
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

# Configurations
PG_HOST = os.getenv("PG_HOST")
PG_DB = os.getenv("PG_DB")
PG_USER = os.getenv("PG_USER")
PG_PASS = os.getenv("PG_PASS")
PG_PORT = os.getenv("PG_PORT", "5432")
MONGO_URI = os.getenv("MONGO_URI")

# Database connections 
def get_pg_connection():
    return psycopg2.connect(
        host=PG_HOST,
        database=PG_DB,
        user=PG_USER,
        password=PG_PASS,
        port=PG_PORT
    )

def get_mongo_collection():
    client = pymongo.MongoClient(MONGO_URI)
    db = client["gym_tracker"]
    return db["workouts"]

# App layout (UI)
st.set_page_config(page_title="GymTrack Pro", layout="wide")
st.title("GymTrack Pro")
st.markdown("Fitness Analytics Platform")
st.sidebar.header("User Login")

try:
    pg_conn = get_pg_connection()
    cur = pg_conn.cursor()
    cur.execute("SELECT user_id, username, country FROM users ORDER BY username")
    users = cur.fetchall()
    pg_conn.close()

    if not users:
        st.error("No users found. Please run python database/generate_data.py first.")
        st.stop()

    user_options = {f"{u[1]} ({u[2]})": u[0] for u in users}
    selected_label = st.sidebar.selectbox("Select User", options=list(user_options.keys()))
    current_user_id = user_options[selected_label]
    st.sidebar.success(f"Logged in as ID: {current_user_id}")

except Exception as e:
    st.error(f"PostgreSQL Error: {e}")
    st.error("Make sure PostgreSQL is running on localhost:5432")
    st.stop()

st.sidebar.markdown("")
st.sidebar.header("Pro Search Tools")

target_ex = st.sidebar.selectbox("Exercise", ["Bench Press", "Squat", "Deadlift"])
min_weight = st.sidebar.number_input("Min Weight (kg)", 40, 300, 80)
run_search = st.sidebar.button("Find Heavy Sets")

search_term = st.sidebar.text_input("Search Gym Name/Notes", placeholder="e.g. fitness")

# Main tabs
tab1, tab2, tab3, tab4 = st.tabs(["My Workouts", "Leaderboard", "Log Workout", "Manage Data"])

collection = get_mongo_collection()

# tab 1: Workout history
with tab1:
    if run_search:
        st.subheader(f"Sessions with {target_ex} > {min_weight}kg")
        query = {
            "user_id": current_user_id,
            "exercises": {
                "$elemMatch": {
                    "name": target_ex,
                    "weight_kg": {"$gte": min_weight}
                }
            }
        }
        results = list(collection.find(query, {"date": 1, "gym_name": 1, "exercises.$": 1}))
        if results:
            for r in results:
                st.write(f"**{r['date'].strftime('%Y-%m-%d')}** at {r['gym_name']}: {r['exercises'][0]['weight_kg']}kg")
        else:
            st.warning("No matches found.")
    
    elif search_term:
        st.subheader(f"Results for '{search_term}'")
        query = {
            "user_id": current_user_id,
            "$or": [
                {"gym_name": {"$regex": search_term, "$options": "i"}},
                {"notes": {"$regex": search_term, "$options": "i"}}
            ]
        }
        results = list(collection.find(query))
        if results:
            try:
                df = pd.DataFrame(results)
                display_cols = ['date', 'gym_name', 'notes']
                available_cols = [col for col in display_cols if col in df.columns]
                st.dataframe(df[available_cols], width='stretch')
            except Exception as e:
                st.error(f"Error displaying results: {e}")
        else:
            st.warning("No results found.")

    st.subheader("Recent History")
    workouts = list(collection.find({"user_id": current_user_id}).sort("date", -1).limit(10))
    if workouts:
        df = pd.DataFrame(workouts)
        st.dataframe(df[['date', 'gym_name', 'total_volume_kg']], width='stretch')
    else:
        st.info("No workouts logged yet.")

# Tab 2: Leaderboard
with tab2:
    st.subheader("Top Athletes (Aggregation Pipeline)")
    st.caption("Uses MongoDB group, sum, and sort")
    
    pipeline = [
        {"$group": {
            "_id": "$user_id", 
            "total_lifted": {"$sum": "$total_volume_kg"}, 
            "sessions": {"$count": {}}
        }},
        {"$sort": {"total_lifted": -1}},
        {"$limit": 10}
    ]
    data = list(collection.aggregate(pipeline))
    
    if data:
        display = []
        try:
            pg_conn = get_pg_connection()
            cur = pg_conn.cursor()
            for entry in data:
                cur.execute("SELECT username, country FROM users WHERE user_id = %s", (entry["_id"],))
                u = cur.fetchone()
                if u: 
                    display.append({
                        "Rank": len(display) + 1,
                        "Athlete": u[0], 
                        "Country": u[1], 
                        "Volume (kg)": entry["total_lifted"], 
                        "Sessions": entry["sessions"]
                    })
            pg_conn.close()
            st.table(pd.DataFrame(display))
        except Exception as e:
            st.error(f"Error fetching leaderboard: {e}")
    else:
        st.info("No workout data available.")

# Tab 3: Log workout
with tab3:
    st.subheader("Log New Session")
    
    if "buffer" not in st.session_state: 
        st.session_state.buffer = []
    
    gym = st.text_input("Gym Name", "Fitness24Seven")
    
    col1, col2, col3, col4, col5 = st.columns([3,1,1,1,1])
    with col1: 
        name = st.text_input("Exercise", key="ex_name")
    with col2: 
        sets = st.number_input("Sets", 1, 10, 3, key="ex_sets")
    with col3: 
        reps = st.number_input("Reps", 1, 50, 10, key="ex_reps")
    with col4: 
        weight = st.number_input("Kg", 0, 500, 60, key="ex_weight")
    with col5: 
        if st.button("Add"): 
            if name.strip():
                st.session_state.buffer.append({
                    "name": name, 
                    "sets": sets, 
                    "reps": reps, 
                    "weight_kg": weight
                })
                st.rerun()
            else:
                st.warning("Please enter an exercise name.")

    if st.session_state.buffer:
        st.table(pd.DataFrame(st.session_state.buffer))
        
        col_save, col_clear = st.columns(2)
        with col_save:
            if st.button("Save Workout", type="primary", use_container_width=True):
                try:
                    vol = sum([x['sets'] * x['reps'] * x['weight_kg'] for x in st.session_state.buffer])
                    collection.insert_one({
                        "user_id": current_user_id, 
                        "date": datetime.now(), 
                        "gym_name": gym, 
                        "total_volume_kg": vol, 
                        "exercises": st.session_state.buffer, 
                        "notes": "Logged via App"
                    })
                    st.session_state.buffer = []
                    st.success("Workout saved!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error saving workout: {e}")
        
        with col_clear:
            if st.button("Clear", use_container_width=True):
                st.session_state.buffer = []
                st.rerun()

# Tab 4: Account and Data Management
with tab4:
    st.subheader("Account and Data Management")
    
    st.markdown("Update Profile (PostgreSQL)")
    new_country = st.selectbox(
        "Update My Country", 
        ["Finland", "Sweden", "Norway", "Estonia", "Denmark"]
    )
    if st.button("Update Country"):
        try:
            pg_conn = get_pg_connection()
            cur = pg_conn.cursor()
            cur.execute(
                "UPDATE users SET country = %s WHERE user_id = %s", 
                (new_country, current_user_id)
            )
            pg_conn.commit()
            pg_conn.close()
            st.success(f"Country updated to {new_country}!")
        except Exception as e:
            st.error(f"Error updating country: {e}")

    st.markdown("")

    st.markdown("Delete Workouts (MongoDB)")
    user_workouts = list(collection.find(
        {"user_id": current_user_id}, 
        {"_id": 1, "date": 1, "gym_name": 1}
    ))
    
    if user_workouts:
        options = {
            f"{w['date'].strftime('%Y-%m-%d')} at {w['gym_name']}": w['_id'] 
            for w in user_workouts
        }
        to_delete = st.selectbox("Select Workout to Remove", options=list(options.keys()))
        
        if st.button("Delete Workout", type="secondary"):
            try:
                collection.delete_one({"_id": options[to_delete]})
                st.warning("Workout deleted.")
                st.rerun()
            except Exception as e:
                st.error(f"Error deleting workout: {e}")
    else:
        st.info("No workouts found to delete.")