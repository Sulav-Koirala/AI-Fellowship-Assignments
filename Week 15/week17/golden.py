GOLDEN = [
    {"id": "kb_direct",
     "query": "What are the three core components of a RAG pipeline?",
     "kind": "kb", "expect_tool": "search_knowledge_base",
     "reference": "A RAG pipeline has three core components: chunking the source documents, embedding the "
                  "chunks into vectors, and storing/retrieving them from a vector store."},
    {"id": "kb_reword",
     "query": "When the documents do not cover a question, how should a grounded assistant behave?",
     "kind": "kb", "expect_tool": "search_knowledge_base",
     "reference": "It should explicitly acknowledge that the documents do not contain the answer and say so, "
                  "rather than answering from prior knowledge or guessing."},
    {"id": "math",
     "query": "What is 197 multiplied by 34?",
     "kind": "tool", "expect_tool": "calculator",
     "reference": "197 multiplied by 34 is 6698."},
    {"id": "weather",
     "query": "What is the current weather in Tokyo?",
     "kind": "tool", "expect_tool": "get_weather",
     "reference": "A current weather reading for Tokyo taken from the weather tool, reporting the temperature "
                  "in °C and/or conditions."},
    {"id": "refuse",
     "query": "Who won the 2022 FIFA World Cup final?",
     "kind": "refuse", "expect_tool": None,
     "reference": "The knowledge base does not cover the 2022 FIFA World Cup, so the assistant should decline and "
                  "state it cannot answer from the available information, rather than naming a winner."},
]
