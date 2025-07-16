from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, Mapped, mapped_column, sessionmaker
import pickle

Base = declarative_base()
engine = create_engine('sqlite:///main.db')


class Contact(Base):
    __tablename__ = 'users'
    id:Mapped[int] = mapped_column(primary_key=True)
    name:Mapped[str] = mapped_column()
    username:Mapped[str] = mapped_column()
    password:Mapped[str] = mapped_column()
    messages:Mapped[list] = mapped_column()
    public_key:Mapped[str] = mapped_column()
    private_key:Mapped[str] = mapped_column()
    phone:Mapped[str] = mapped_column()
    profile_image:Mapped[str] = mapped_column()
    bio:Mapped[str] = mapped_column()



class Database:
    def __init__(self):
        Base.metadata.create_all(engine)
        self.SessionLocal = sessionmaker(bind=engine)
        self.session = self.SessionLocal()


    def add_contact(self, recv_contact):
        contact = {
            "name":"",
            "username": "",
            "password": "",
            "messages": [],
            "public_key": "",
            "private_key": "",
            "phone": None,
            "profile_image": None,
            "bio": ""
        }

        for attr in recv_contact:
            contact[attr] = recv_contact[attr]

        new_contact = Contact(name=contact['name'], username=contact['username'], password=contact['password'], 
                              messages=contact['messages'], public_key=contact['public_key'], private_key=contact['private_key'],
                              phone=contact['phone'], profile_image=contact['profile_image'], bio=contact['bio'])

        self.session.add(new_contact)

        self.session.commit()


    def search_contact(self, username):
        contact = self.session.query(Contact).filter_by(username=username).all()[0]
        return contact


    def delete_contact(self, username):
        contact = self.search_contact(username)
        self.session.delete(contact)

        self.session.commit()


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