from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, Mapped, mapped_column, sessionmaker
import pickle

class Database:
    def __init__(self):
        self.Base = declarative_base()
        self.engine = create_engine('sqlite:///main.db')
        self.Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.session = self.SessionLocal()

    def load_contacts(self):
        try:
            with open('contacts.db', 'rb') as file:
                contacts = pickle.load(file)
        except:
            with open('user_data.conf', 'rb') as file:
                user_data = pickle.load(file)
            user_data['name'] = 'SavedMessage'
            user_data['messages'] = []
            contacts = {'SavedMessage' : user_data}
            self.save_contact_list(contacts)
        return contacts

    def save_contact_list(self, contacts):
        with open('contacts.db', 'wb') as file:
            pickle.dump(contacts, file)