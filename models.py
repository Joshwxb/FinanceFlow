from sqlalchemy import create_engine, Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

# The base class for our database tables
Base = declarative_base()

class User(Base):
    """
    This model stores user credentials.
    """
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    
    # Relationship: One user can have many transactions
    transactions = relationship("Transaction", back_populates="user")

    def set_password(self, password):
        """Hashes the password for security."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifies the password during login."""
        return check_password_hash(self.password_hash, password)

class Transaction(Base):
    """
    This model stores financial records linked to a specific user.
    """
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False) # Link to User
    date = Column(Date, default=datetime.date.today)
    description = Column(String, nullable=False)
    category = Column(String, nullable=False)
    type = Column(String, nullable=False) # 'Income' or 'Expense'
    amount = Column(Float, nullable=False)

    # Link back to the User object
    user = relationship("User", back_populates="transactions")

# 1. Create the SQLite database file
engine = create_engine('sqlite:///finance.db')

# 2. Generate the tables in the database
Base.metadata.create_all(engine)

# 3. Create a session factory
Session = sessionmaker(bind=engine)

def get_session():
    return Session()

if __name__ == "__main__":
    print("Database with User authentication support initialized successfully!")