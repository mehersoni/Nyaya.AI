# Nyayamrit  
## An Intelligent Legal Assistance System for Consumer Protection in India  

**Nyayamrit (न्यायामृत)** — meaning “essence of justice” — is a Graph-Constrained Legal Reasoning System designed to improve the reliability, traceability, and accessibility of consumer law in India.

The system currently focuses on the **Consumer Protection Act, 2019** and enables users to ask natural language questions while ensuring responses are grounded in verifiable statutory sources.

---

## 🚨 Problem

India has over 4.5 crore pending court cases, with a substantial number involving civil and consumer disputes.

Structural challenges include:

- Legal English limits citizen accessibility  
- Professional consultation is costly  
- General-purpose LLM legal chatbots hallucinate statutory provisions  
- Government portals assist with filing complaints but do not explain the law  
- Limited availability of explainable, statute-grounded AI systems  

Legal AI systems must prioritize **traceability and correctness**, not fluency alone.

---

## 💡 Approach

Nyayamrit implements a **Graph-Constrained Retrieval-Augmented Generation (GraphRAG)** architecture.

Instead of free-form generation, the system:

1. Retrieves verified statutory nodes from a structured Legal Knowledge Graph  
2. Performs deterministic graph traversal for section-level grounding  
3. Uses an LLM strictly for constrained explanation  
4. Returns citation-first responses  

This architecture separates:

- **Deterministic retrieval and reasoning (graph-based)**
- **Controlled explanation (generation layer)**

This reduces hallucination risk and improves legal reliability.

---

## 🏗 System Architecture

### 1️⃣ Legal Text Ingestion
- Source: Official India Code repository  
- Structured parsing: Act → Chapter → Section → Clause  

### 2️⃣ Knowledge Graph Construction
- Entity extraction: definitions, rights, penalties, remedies  
- Graph database: Neo4j  
- Section-level node indexing  
- Explicit relationship modeling (e.g., defines, penalizes, remedies)

### 3️⃣ Query Processing Pipeline
- Natural language query input  
- Graph-based deterministic retrieval  
- Section-level verification  
- Constrained LLM explanation  
- Citation-first structured output  

### 4️⃣ Multilingual Layer
- Integrated via Bhashini API  
- Semantic mapping prior to retrieval  

---

## 📊 Evaluation (Preliminary)

### Evaluation Setup
- Total queries tested: 15  
- Queries manually constructed to cover rights, remedies, penalties, and definitions  
- Ground truth validated against official statutory text  

### Results
- Section-level retrieval accuracy: 15/15  
- No hallucinated sections observed within test set  
- Average response latency: ~2.49 seconds  
- Average confidence score: 0.90  

> Note: Results are preliminary and based on a limited evaluation set.  
> Larger-scale benchmarking and adversarial testing remain future work.

---

## 🔍 Features

### For Citizens
- Plain English and Hindi queries  
- Citation-first statutory references  
- Simplified explanation of legal rights  

Example use cases:
- Defective goods  
- Misleading advertisements  
- Overcharging  
- Deficiency in service  

### For Legal & Academic Use
- Rapid statutory verification  
- Explainable AI case study  
- Benchmark framework for graph-constrained legal reasoning  

---

## 🧠 Technical Stack

- Python + FastAPI  
- Neo4j (Legal Knowledge Graph)  
- LangChain (Pipeline orchestration)  
- Open-source LLMs (explanation layer only)  
- Bhashini API (multilingual processing)  
- PostgreSQL (audit logging)  
- AMD-based cloud infrastructure  

---

## 🛡 Design Philosophy

| Component | Nyayamrit |
|------------|------------|
| Retrieval | Deterministic graph traversal |
| Explanation | Constrained generation |
| Citation | Section-level grounding |
| Hallucination Mitigation | Graph-first architecture |
| Traceability | Fully verifiable reasoning path |

Nyayamrit prioritizes **legal reliability over generative flexibility**.

---

## ⚠ Limitations

- Evaluation dataset currently small (n=15 queries)  
- Limited to Consumer Protection Act, 2019  
- No adversarial robustness testing conducted yet  
- Multilingual support depends on translation quality  
- Provides legal information, not legal advice  

---

## 🚀 Future Work

- Expansion to additional statutes (BNS, BNSS, IT Act, Constitution)  
- Integration with E-Daakhil portal  
- Complaint drafting assistance module  
- Large-scale benchmarking and stress testing  
- Adversarial hallucination evaluation  
- Formal comparison against generic LLM systems  

---

## 👩‍💻 Author

**Meher Soni**  
Birla Institute of Technology Mesra, Jaipur  
📧 mehersoni06@gmail.com  

**Mentor:** Dr. Piyush Gupta  
Birla Institute of Technology Mesra, Jaipur  

---

## 📜 License

This project is intended for academic and research purposes.  
It provides legal information, not legal advice.
