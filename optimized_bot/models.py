from sqlalchemy import Boolean, Column, Integer, String, Text, BigInteger
from database import Base

"""
  message_id INT NOT NULL,
  chat_id INT NOT NULL,
  user_id INT NOT NULL,
  user_first_name VARCHAR(255) NOT NULL,
  username VARCHAR(255) NOT NULL,
  user_message TEXT NOT NULL,
  bot_message TEXT NOT NULL,
  PRIMARY KEY (message_id)
"""


class Message_History(Base):
    __tablename__ = "message_history"
    message_id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(BigInteger)
    user_id = Column(Integer)
    is_bot = Column(Boolean)
    user_first_name = Column(String(50))
    username = Column(String(50))
    user_message = Column(Text)
    bot_message = Column(Text)



