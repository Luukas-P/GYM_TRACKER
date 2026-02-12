# GymTrack Pro
A course project for NoSQL course (DATA.DB.300).

## Overview & Business Domain

GymTrack Pro is a fitness platform designed for the Nordic market (FI, SE, NO, EE). It uses a polyglot-persistence model to handle high-performance analytics while maintaining strict user data consistency.

- **Traffic:** 90% Read / 10% Write
- **Peak Load:** Designed for ~5,000 concurrent peak users

---

## Quick Start & Setup

### Prerequisites

This project requires active instances of PostgreSQL and MongoDB. These can be provided via:

- Docker Compose (recommended)
- Local installations of PostgreSQL and MongoDB
- Cloud-hosted databases (e.g., MongoDB Atlas / Supabase)
Note: Ensure the connection details in your .env file match your running services.

### Project Structure

```
GYM_TRACKER/
├── app/
│   └── main.py              # Streamlit application
├── database/
│   └── generate_data.py     # Database seeding script
├── docs/
│   ├── assets/              # Images and diagrams
│   └── DOCUMENTATION.md     # Technical documentation
├── venv/                    # Python virtual environment (Created locally)
├── .env                     # Local environment variables (Created locally)
├── README.md                # Project overview and setup guide
└── requirements.txt         # Python dependencies
```

### Installation

```bash
# 1. Clone or extract the project
cd GYM_TRACKER

# 2. Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables (See Environment Configuration below)
Create your .env file before proceeding

# 5. Seed databases with sample data
python database/generate_data.py

# 6. Launch the application
streamlit run app/main.py
```

### Environment Configuration
For security, database credentials are managed via environment variables.
1. Create a file named .env in the root directory (GYM_TRACKER/).
2. Define the following variables inside the file:

```text
# Database Connection Settings
PG_HOST=your_host_address
PG_PORT=5432
PG_DB=your_database_name
PG_USER=your_username
PG_PASS=your_password

# MongoDB Connection String
MONGO_URI=mongodb://your_host:your_port/
```
Note: The .env file is excluded from version control via .gitignore to prevent credential leaks.

### First-Time Setup

1. Ensure PostgreSQL is running on port 5432 (or as configured in `.env`)
2. Ensure MongoDB is running on port 27017 (or as configured in `.env`)
3. The `generate_data.py` script will automatically:
   - Create the `users` table in PostgreSQL
   - Create the `workouts` collection in MongoDB
   - Generate 50 sample users
   - Generate 250 sample workout sessions
   - Create necessary indexes

## Additional

- **Full Technical Documentation:** See `docs/DOCUMENTATION.md` for detailed database schema, use-cases, and distribution strategy: [View Documentation](docs/DOCUMENTATION.md)
- **Source Code:** Application logic in `app/main.py`, data generation in `database/generate_data.py`
- **Requirements:** See `requirements.txt` for complete dependency list