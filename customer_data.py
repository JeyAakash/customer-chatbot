from database import SessionLocal, engine
from models import Base, Customer, Invoice
from rag import index_invoice_record

def seed_data():
    # Ensure tables are created first
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()

    # Retrieve or create customers
    c1 = db.query(Customer).filter(Customer.mobile_number == "7095155157").first()
    if not c1:
        c1 = Customer(name="Aakash", mobile_number="7095155157")
        db.add(c1)

    c2 = db.query(Customer).filter(Customer.mobile_number == "7096156157").first()
    if not c2:
        c2 = Customer(name="Suriya", mobile_number="7096156157")
        db.add(c2)

    db.commit()
    db.refresh(c1)
    db.refresh(c2)

    # Check if invoices already exist; if not, create them
    if not db.query(Invoice).first():
        aakash_invoices = [
            Invoice(customer_id=c1.id, invoice_number="INV-101", date="2026-10-01", amount=1500.0, currency="INR", payment_status="paid"),
            Invoice(customer_id=c1.id, invoice_number="INV-102", date="2026-10-05", amount=2500.0, currency="INR", payment_status="unpaid"),
            Invoice(customer_id=c1.id, invoice_number="INV-103", date="2026-10-10", amount=3000.0, currency="INR", payment_status="unpaid"),
            Invoice(customer_id=c1.id, invoice_number="INV-104", date="2026-10-15", amount=1200.0, currency="INR", payment_status="paid"),
            Invoice(customer_id=c1.id, invoice_number="INV-105", date="2026-10-20", amount=4500.0, currency="INR", payment_status="unpaid"),
        ]

        suriya_invoices = [
            Invoice(customer_id=c2.id, invoice_number="INV-201", date="2026-10-02", amount=5000.0, currency="INR", payment_status="paid"),
            Invoice(customer_id=c2.id, invoice_number="INV-202", date="2026-10-06", amount=1500.0, currency="INR", payment_status="unpaid"),
            Invoice(customer_id=c2.id, invoice_number="INV-203", date="2026-10-11", amount=2200.0, currency="INR", payment_status="paid"),
            Invoice(customer_id=c2.id, invoice_number="INV-204", date="2026-10-16", amount=3300.0, currency="INR", payment_status="unpaid"),
            Invoice(customer_id=c2.id, invoice_number="INV-205", date="2026-10-21", amount=1100.0, currency="INR", payment_status="unpaid"),
        ]

        db.add_all(aakash_invoices + suriya_invoices)
        db.commit()

    # Fetch all invoices from PostgreSQL to index them into Qdrant
    all_invoices = db.query(Invoice).all()

    print("Generating embeddings and indexing records into Qdrant...")
    for inv in all_invoices:
        index_invoice_record(
            customer_id=inv.customer_id,
            invoice_id=inv.id,
            invoice_number=inv.invoice_number,
            date=inv.date,
            amount=inv.amount,
            currency=inv.currency,
            status=inv.payment_status
        )

    db.close()
    print("Successfully seeded database and indexed all invoice vectors in Qdrant!")

if __name__ == "__main__":
    seed_data()