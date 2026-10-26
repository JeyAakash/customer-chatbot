from datetime import datetime
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    mobile_number = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    invoices = relationship("Invoice", back_populates="customer", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="customer", cascade="all, delete-orphan")

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    invoice_number = Column(String, nullable=False)
    date = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="INR", nullable=False)
    payment_status = Column(String, nullable=False)  # e.g., 'paid', 'unpaid'
    indexed_in_vector_db = Column(Integer, default=0) # 0 = False, 1 = True

    customer = relationship("Customer", back_populates="invoices")

    __table_args__ = (
        UniqueConstraint('customer_id', 'invoice_number', name='uq_customer_invoice_number'),
    )

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    title = Column(String, default="Chat Session")
    created_at = Column(DateTime, default=datetime.utcnow)

    customer = relationship("Customer", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(String, nullable=False)       # 'user', 'assistant', 'tool'
    content = Column(Text, nullable=False)      
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")