# Database setup for SQLAlchemy and FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Database connection URL for PostgresSQL
SQLALCHEMY_DATABASE_URL = 'postgresql://postgres.gkelvtwveftrpmocmyaf:[ismail180162192]@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres'

# ismail180162192

# Database connection URL for SQLite
# SQLALCHEMY_DATABASE_URL = 'sqlite:///./todosapp.db'  # SQLite database URL

# Create the engine that talks to the database
engine = create_engine(SQLALCHEMY_DATABASE_URL) 

# Create session factory for database requests
SessionLocal = sessionmaker(autoflush=False, autocommit=False, bind=engine)

# Base class for model classes
Base = declarative_base()

