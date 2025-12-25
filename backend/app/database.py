from sqlalchemy import create_engine

DATABASE_URI = "mysql+mysqlconnector://root:1537@localhost/inventory_db"

engine = create_engine(DATABASE_URI)
