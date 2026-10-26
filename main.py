from fastapi import FastAPI, Depends, HTTPException, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import engine, get_db
from models import Base, Customer, Invoice, Conversation, Message
from auth import request_otp_logic, verify_otp_logic, get_current_customer
from rag import search_customer_records, index_invoice_record
import requests

# Create database tables automatically
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Secure Customer AI Chatbot", version="1.0.0")

class VerifyOtpRequest(BaseModel):
    mobile: str
    otp: str

@app.post("/auth/request-otp")
def request_otp(mobile: str = Body(..., embed=True), db: Session = Depends(get_db)):
    return request_otp_logic(mobile, db)

@app.post("/auth/verify-otp")
def verify_otp(data: VerifyOtpRequest, db: Session = Depends(get_db)):
    return verify_otp_logic(data.mobile, data.otp, db)

@app.get("/auth/me")
def get_logged_in_customer(current_customer: Customer = Depends(get_current_customer)):
    return {"id": current_customer.id, "name": current_customer.name, "mobile": current_customer.mobile_number}

@app.post("/conversations")
def create_conversation(current_customer: Customer = Depends(get_current_customer), db: Session = Depends(get_db)):
    conv = Conversation(customer_id=current_customer.id, title="Customer Chat")
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return {"conversation_id": conv.id, "title": conv.title}

@app.get("/conversations")
def list_conversations(current_customer: Customer = Depends(get_current_customer), db: Session = Depends(get_db)):
    convs = db.query(Conversation).filter(Conversation.customer_id == current_customer.id).all()
    return [{"conversation_id": c.id, "title": c.title} for c in convs]

@app.get("/conversations/{conversation_id}/messages")
def get_messages(conversation_id: int, current_customer: Customer = Depends(get_current_customer), db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id, Conversation.customer_id == current_customer.id).first()
    if not conv:
        raise HTTPException(status_code=403, detail="Access denied to this conversation.")
    messages = db.query(Message).filter(Message.conversation_id == conversation_id).all()
    return [{"role": m.role, "content": m.content, "timestamp": m.created_at} for m in messages]

@app.post("/chat")
def chat_endpoint(
    conversation_id: int = Body(...),
    message: str = Body(...),
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id, Conversation.customer_id == current_customer.id).first()
    if not conv:
        raise HTTPException(status_code=403, detail="Unauthorized access to conversation.")

    # Save user message
    user_msg = Message(conversation_id=conv.id, role="user", content=message)
    db.add(user_msg)
    db.commit()

    lower_msg = message.lower()
    if any(g in lower_msg for g in ["hello", "hi", "hey"]):
        reply = f"Hello {current_customer.name}! How can I assist you with your account and invoices today?"
    else:
        retrieved_docs = search_customer_records(current_customer.id, message)
        context_str = "\n".join([doc["content"] for doc in retrieved_docs]) if retrieved_docs else "No matching records found."
        
        prompt = f"Customer Name: {current_customer.name}\nContext Records:\n{context_str}\n\nQuestion: {message}\nAnswer accurately based only on the context provided:"
        
        try:
            llm_resp = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": "mistral", "prompt": prompt, "stream": False}
            )
            reply = llm_resp.json().get("response", "I am unable to process your request.") if llm_resp.status_code == 200 else "LLM service unavailable."
        except Exception:
            reply = "Error communicating with LLM provider."

    # Save assistant response
    assistant_msg = Message(conversation_id=conv.id, role="assistant", content=reply)
    db.add(assistant_msg)
    db.commit()

    return {"response": reply, "cited_records": search_customer_records(current_customer.id, message) if "invoice" in lower_msg or "unpaid" in lower_msg else []}

@app.post("/admin/reindex")
def retry_reindex(db: Session = Depends(get_db)):
    failed_invoices = db.query(Invoice).filter(Invoice.indexed_in_vector_db == 0).all()
    count = 0
    for inv in failed_invoices:
        try:
            index_invoice_record(inv.customer_id, inv.id, inv.invoice_number, inv.date, inv.amount, inv.currency, inv.payment_status)
            inv.indexed_in_vector_db = 1
            count += 1
        except Exception:
            pass
    db.commit()
    return {"message": f"Successfully reindexed {count} invoices."}