"""
Live integration test — calls the running backend and prints answers.
Does NOT print the API key.
Run with:  .venv\Scripts\python.exe test_chat_live.py
"""
import asyncio
import httpx

BASE = "http://127.0.0.1:8001"
COURSE_ID = 1   # Data Structures (seeded as id=1)

QUESTIONS = [
    ("Q1 — Unit content", "What is Unit 3 about?", []),
    ("Q2 — Concept explain", "Explain binary trees in simple words.", []),
    ("Q3 — Why/rationale", "Why do we use binary search trees?", []),
    ("Q4 — Prerequisites", "What should I learn before AVL trees?", []),
    ("Q5 — Topic search", "Which unit contains hashing?", []),
    ("Q6 — Textbook advice", "Which textbook should I use for trees?", []),
    ("Q7 — Open resource", "Can you open the binary trees textbook?", []),
    ("Q8 — Comparison", "Compare stacks and queues.", []),
    ("Q9 — Exam tips", "What are the important topics for my exam?", []),
    ("Q10 — CO mapping", "Which course outcome is related to Unit 3?", []),
]

# Test conversation memory
MEMORY_CONV = [
    "What is Unit 3 about?",
    "Explain that in simpler words.",
    "What was the second topic you mentioned?",
]


async def ask(client: httpx.AsyncClient, label: str, question: str, history: list) -> list:
    payload = {"course_id": COURSE_ID, "message": question, "history": history}
    r = await client.post(f"{BASE}/api/chat", json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()["data"]
    answer = data["answer"]
    citations = data.get("citations", [])
    resources = data.get("resources", [])

    print(f"\n{'='*60}")
    print(f"{label}")
    print(f"Q: {question}")
    print(f"A: {answer[:400]}{'...' if len(answer) > 400 else ''}")
    if citations:
        print(f"  Citations: {[c.get('unit') or c.get('filename') for c in citations[:3]]}")
    if resources:
        print(f"  Resources: {[r['title'] for r in resources]}")
    print()

    # Return updated history for memory tests
    return history + [
        {"role": "user", "content": question},
        {"role": "assistant", "content": answer},
    ]


async def main():
    async with httpx.AsyncClient() as client:
        # Health check
        h = await client.get(f"{BASE}/health")
        print(f"Health: {h.json()}")

        # Individual questions (no memory)
        for label, q, hist in QUESTIONS:
            await ask(client, label, q, hist)

        # Memory / follow-up test
        print("\n" + "="*60)
        print("MEMORY TEST — 3 sequential follow-up questions")
        history: list = []
        for i, q in enumerate(MEMORY_CONV, 1):
            history = await ask(client, f"Memory Q{i}", q, history)


if __name__ == "__main__":
    asyncio.run(main())
