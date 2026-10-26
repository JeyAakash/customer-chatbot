# Secure RAG-Based Customer AI Chatbot

A secure, multi-tenant Retrieval-Augmented Generation (RAG) chatbot backend built with **FastAPI**, **PostgreSQL**, **Qdrant**, and local **Ollama** (`Mistral` & `nomic-embed-text`).

The application enables authenticated customers to query their private account data and invoices using natural language while enforcing strict multi-tenant isolation at the vector database level to prevent cross-customer data leakage.

---

## 🏗 Architecture & Key Features

* **JWT-Based OTP Authentication**: Mobile-based OTP verification (`/auth/request-otp`, `/auth/verify-otp`) generating signed JWT access tokens.
* **Multi-Tenant Data Isolation**: Customer IDs are embedded directly into JWT payloads and applied as mandatory Qdrant payload filters (`MatchValue(value=customer_id)`).
* **Vector Search Pipeline**: Direct integration with Qdrant vector database using `nomic-embed-text` (768 dimensions) for semantic retrieval.
* **Local Privacy-Centric LLM**: Contextual responses powered locally via Ollama (`Mistral`), ensuring sensitive financial data does not leave your local environment.
* **Automated Data Seeding**: Dual-seeding script (`customer_data.py`) syncing relational database tables (PostgreSQL/SQLAlchemy) with Qdrant vector embeddings.
* **Interactive OpenAPI/Swagger UI**: Full interactive API documentation with Bearer token authentication testing enabled.

---

## 🛠 Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Backend Framework** | FastAPI (Python) running on Uvicorn |
| **Relational Database** | PostgreSQL / SQLite via SQLAlchemy ORM |
| **Vector Database** | Qdrant Vector DB |
| **LLM & Embeddings** | Ollama (`Mistral` for text generation, `nomic-embed-text` for embeddings) |
| **Authentication** | PyJWT / Passlib (Bearer Token Authentication) |

---

## 🚀 Getting Started

### Prerequisites

* Python 3.10+
* [Ollama](https://ollama.com/) installed and running locally
* Required Ollama models:
  ```bash
  ollama pull mistral
  ollama pull nomic-embed-text
  ```

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/JeyAakash/customer-chatbot.git
   cd customer-chatbot
   ```

2. **Set up a virtual environment:**
   ```bash
   python -m venv venv
   # On Windows (PowerShell):
   .\venv\Scripts\Activate.ps1
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   *(If `requirements.txt` is missing, install the core dependencies directly:)*
   ```bash
   pip install fastapi uvicorn sqlalchemy qdrant-client requests pyjwt passlib
   ```

---

## 📊 Database Seeding & Initialization

To populate the relational database and index vector embeddings into Qdrant:

```bash
python customer_data.py
```

*Expected output:*
```text
Generating embeddings and indexing records into Qdrant...
Successfully seeded database and indexed all invoice vectors in Qdrant!
```

---

## 🏃 Running the Application

Start the FastAPI server:

```bash
uvicorn main:app --reload
```

The server will launch at `http://127.0.0.1:8000`.

---

## 🧪 Testing with Swagger UI

1. Open your browser and navigate to **`http://127.0.0.1:8000/docs`**.
2. **Request OTP**: Call `POST /auth/request-otp` with your registered mobile number.
3. **Verify OTP**: Call `POST /auth/verify-otp` to receive your JWT access token.
4. **Authorize**: Click the green **Authorize** button in Swagger UI and paste your Bearer token.
5. **Chat**: Execute `POST /chat` with a query like:
   ```json
   {
     "conversation_id": 1,
     "message": "What are my unpaid invoices?"
   }
   ```

---

## 🔐 Security Highlights

* **Token Expiration**: Invalid or expired JWT tokens return `401 Unauthorized`.
* **Tenant Shield**: Qdrant queries strictly enforce `customer_id` filtering, preventing any user from accessing another customer's vectorized context.

---

## 📝 License

Distributed under the MIT License. See `LICENSE` for more information.