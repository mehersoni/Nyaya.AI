

# Nyayamrit

### An Intelligent Legal Assistance System for Consumer Protection in India

Nyayamrit (न्यायामृत) — meaning *“essence of justice”* — is an AI-powered legal assistance system designed to make consumer law in India accessible, accurate, and trustworthy.

The system focuses on the **Consumer Protection Act, 2019** and enables users to ask natural language questions and receive **statute-grounded, explainable, and hallucination-free responses**.

---

## 🚨 Problem

India has over **4.5 crore pending court cases**, with a significant number involving civil and consumer disputes.

Key challenges:

* Complex legal English limits citizen understanding
* Legal consultation is costly
* AI legal chatbots often hallucinate non-existent legal sections
* Government portals help file complaints, but not understand the law

There is no trustworthy, multilingual, explainable AI system for consumer law guidance.

---

## 💡 Solution

Nyayamrit uses a **Graph-Constrained Legal Reasoning Architecture (GraphRAG)** to ensure:

* ✅ 100% statutory section accuracy
* ✅ Zero hallucinated legal provisions
* ✅ Explainable reasoning paths
* ✅ Multilingual support (via Bhashini)
* ✅ Low-latency responses

Unlike generic LLM chatbots, Nyayamrit does not freely generate legal content.
It retrieves verified statutory nodes from a Legal Knowledge Graph and uses an LLM only for explanation within strict constraints.

---

## 🏗 System Architecture

1. Legal text ingestion from official sources (India Code)
2. Structural parsing (Act → Chapter → Section → Clause)
3. Entity extraction (definitions, rights, remedies, penalties)
4. Neo4j Legal Knowledge Graph construction
5. Deterministic graph traversal for query retrieval
6. Graph-constrained LLM explanation
7. Multilingual semantic mapping via Bhashini
8. Citation-first response delivery

This ensures every answer is traceable to official statutory law.

---

## 📊 Evaluation Results

* **Total Queries Tested:** 15
* **Success Rate:** 100%
* **Section Accuracy:** 100%
* **Hallucination Incidents:** 0
* **Average Response Time:** ~2.49s (paper evaluation)
* **Average Confidence Score:** 0.90

Nyayamrit achieved zero hallucination by strictly constraining reasoning to the Legal Knowledge Graph.

---

## 🔍 Features

### For Citizens

* Ask questions in plain English or Hindi
* Retrieve exact statutory sections with citations
* Understand rights and remedies in simple language
* Get guidance for real-world issues:

  * Defective goods
  * Misleading advertisements
  * Overcharging
  * Deficiency in service

### For Legal & Academic Use

* Rapid statutory verification
* Teaching and research support
* Explainable AI benchmark for legal reasoning

---

## 🧠 Core Technical Stack

* Python + FastAPI
* Neo4j (Legal Knowledge Graph)
* LangChain (Reasoning Orchestration)
* Open-source LLMs (explanation only)
* Bhashini API (multilingual processing)
* PostgreSQL (audit logs)
* AMD-based cloud infrastructure

---

## 🛡 Why Nyayamrit is Different

| Feature            | Nyayamrit                   | Generic LLMs    |
| ------------------ | --------------------------- | --------------- |
| Reasoning Type     | Deterministic (Graph-Based) | Probabilistic   |
| Hallucination Risk | None                        | High            |
| Citation Accuracy  | Exact Section-Level         | Often Incorrect |
| Explainability     | Fully Traceable             | Limited         |
| Legal Reliability  | Statute-Verified            | Not Guaranteed  |

Nyayamrit functions as **“Legal First Aid”** — bridging the gap between hallucination-prone AI and inaccessible professional legal services.

---

## 🌍 Impact

* Democratizes access to consumer law
* Reduces misinformation risk in legal AI
* Saves time and legal consultation costs
* Supports legal aid clinics and NGOs
* Provides a scalable foundation for public legal infrastructure

---

## 🚀 Future Roadmap

* Integration with E-Daakhil and grievance portals
* Expansion to additional Indian laws (BNS, BNSS, IT Act)
* Constitution integration
* Complaint drafting assistance
* Nationwide scalable deployment

---

## 👩‍💻 Author

**Meher Soni**
Birla Institute of Technology Mesra, Jaipur
📧 [mehersoni06@gmail.com](mailto:mehersoni06@gmail.com)

Mentor:
**Dr. Piyush Gupta**
Birla Institute of Technology Mesra, Jaipur

---

## 📜 License

This project is intended for academic and research purposes.
It provides legal information, not legal advice.
