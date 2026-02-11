import os
import psycopg2
import pymongo
import random
from faker import Faker
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

PG_HOST = os.getenv("PG_HOST", "localhost")
PG_DB = os.getenv("PG_DB", "labdb")
PG_USER = os.getenv("PG_USER", "student")
PG_PASS = os.getenv("PG_PASS", "password") 
PG_PORT = os.getenv("PG_PORT", "5432")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")


NUM_USERS = 50
NUM_WORKOUTS = 250

fake = Faker(['en_US', 'fi_FI']) 

def create_postgres_data():
    print(f"Connecting to PostgreSQL at {PG_HOST}...")
    conn = None
    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            database=PG_DB,
            user=PG_USER,
            password=PG_PASS,
            port=PG_PORT
        )
        cur = conn.cursor()
        
        print("Creating users table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                full_name VARCHAR(100),
                country VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        cur.execute("TRUNCATE TABLE users RESTART IDENTITY CASCADE;")
        
        user_ids = []
        print(f"Generating {NUM_USERS} users...")
        for _ in range(NUM_USERS):
            u_name = fake.user_name() + str(random.randint(1, 99))
            f_name = fake.name()
            u_country = random.choice(["Finland", "Sweden", "Estonia", "Norway"])
            
            cur.execute(
                "INSERT INTO users (username, full_name, country) VALUES (%s, %s, %s) RETURNING user_id;",
                (u_name, f_name, u_country)
            )
            user_ids.append(cur.fetchone()[0])
        
        print("Creating PostgreSQL indexes...")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);")
        
        conn.commit()
        cur.close()
        print("PostgreSQL: Created table, inserted users, and created indexes.")
        return user_ids
        
    except Exception as e:
        print(f"PostgreSQL Error: {e}")
        return []
    finally:
        if conn: conn.close()

def create_mongo_data(user_ids):
    print(f"Connecting to MongoDB at {MONGO_URI}...")
    try:
        client = pymongo.MongoClient(MONGO_URI)
        db = client["gym_tracker"]
        collection = db["workouts"]
        
        collection.delete_many({})
        
        workouts = []
        print(f"Generating {NUM_WORKOUTS} workouts...")
        
        exercises_list = [
            "Bench Press", "Squat", "Deadlift", "Overhead Press", 
            "Pull Up", "Dumbbell Row", "Leg Press", "Bicep Curl"
        ]
        
        for _ in range(NUM_WORKOUTS):
            uid = random.choice(user_ids)
            
            session_exercises = []
            num_exercises = random.randint(3, 6)
            total_volume = 0
            
            for _ in range(num_exercises):
                ex_name = random.choice(exercises_list)
                sets = random.randint(3, 5)
                reps = random.randint(6, 12)
                weight = random.randint(40, 140)
                
                vol = sets * reps * weight
                total_volume += vol
                
                session_exercises.append({
                    "name": ex_name,
                    "sets": sets,
                    "reps": reps,
                    "weight_kg": weight
                })

            workout = {
                "user_id": uid,
                "date": fake.date_time_between(start_date='-60d', end_date='now'),
                "gym_name": random.choice(["Fitness24Seven Pori", "Elixia", "Liikuntakeskus"]),
                "exercises": session_exercises,
                "total_volume_kg": total_volume, 
                "duration_min": random.randint(30, 90),
                "notes": fake.sentence()
            }
            workouts.append(workout)
            
        collection.insert_many(workouts)
        
        print("Creating MongoDB indexes...")
        collection.create_index([("user_id", 1), ("date", -1)])
        collection.create_index([("total_volume_kg", -1)])
        
        print("MongoDB: Inserted workouts and created 2 indexes.")
        
    except Exception as e:
        print(f"MongoDB Error: {e}")

if __name__ == "__main__":
    print("GymTrack Pro - Database Setup & Data Generation")
    
    ids = create_postgres_data()
    
    if ids:
        create_mongo_data(ids)
        
    print("Setup Complete!")
    print(f"PostgreSQL: {NUM_USERS} users created")
    print(f"MongoDB: {NUM_WORKOUTS} workouts created")
    print("All indexes created successfully")