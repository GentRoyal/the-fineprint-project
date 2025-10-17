# 🕵️‍♂️ the-fineprint-project

We’ve all been there — clicking “I agree” without reading a word.  
**the-fineprint-project** is an **LLM-powered analyzer** that reads Terms & Conditions for you, identifies harmful or vague clauses, and explains them in plain, human language.  

To make it even easier, it can **turn the analysis into a short podcast** using text-to-speech — because if you won’t read it, you might as well listen.

---

## 🚀 Features

- **LLM-Powered Clause Analysis:** Uses groq’s **Llama-3.1-8B-Instant** to analyze each clause and detect risky, vague, or overreaching language.  
- **Risk Categorization:** Labels each clause as *high*, *medium*, or *low* based on semantic context.  
- **Plain-Language Summaries:** Explains what each risky clause *actually means* in everyday terms.  
- **Podcast Mode:** Converts the full analysis into speech using **Gemini 2.5 Flash Preview (TTS)** — smooth, clear, and natural.  
- **Vector Search & Context Memory:** Stores embeddings in **Pinecone** for fast retrieval and future comparisons.  
- **Clean Dashboard:** Simple interface to upload or paste text and get instant insights.

---

## 🧠 Tech Stack

| Layer | Tools / Frameworks |
|-------|--------------------|
| **LLM (Text Analysis)** | Groq API (Llama-3.1-8B-Instant) |
| **Audio / Podcast Mode** | Gemini 2.5 Flash Preview TTS |
| **Vector Store** | Pinecone |
| **Backend** | FastAPI, LangChain, Python |
| **Frontend** | React + Tailwind CSS |
| **Deployment** | Docker, GitHub Actions, AWS (In Progress) |


---

## 🧪 How It Works

1. **Upload or paste** your Terms & Conditions text.  
2. **Groq’s Llama-3.1-8B-Instant** analyzes each clause and tags potential red flags.  
3. The system **summarizes findings** in clear, everyday language.  
4. Optionally, **Gemini 2.5 Flash Preview TTS** converts the results into a podcast-style narration.  
5. **Pinecone** stores embeddings for clause-level retrieval and contextual queries.

---

## ⚙️ Setup

```bash
# Clone the repo
git clone https://github.com/<your-username>/the-fineprint-project.git
cd the-fineprint-project

# Backend setup
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend setup
cd ../frontend
npm install
npm run dev
````

---

## 🧑‍💻 Contributing

Contributions are welcome — from prompt engineering and audio pipelines to frontend UI ideas.
If you like turning legal jargon into human speech, you’ll fit right in.

---

## 📄 License

MIT License — open and community-driven.

---