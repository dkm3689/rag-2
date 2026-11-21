from groq import Groq


from app.config import settings


client = Groq(api_key=settings.groq_api_key)

SYSTEM_PROMPT = (
    "You answer questions using only the provided context. "
    "If the answer is not in the context, say you could not find it in the documents. "
    "Do not use outside knowledge. Cite the sources you used like [1], [2]."
    "Only cite a source if you actually used it. If you could not find the answer, do not cite anything."
)


def answer_question(question:str, chunks:list[str]) -> str:
    context = "\n\n".join( f"[{i}], {text}" for i, text in enumerate(chunks, start=1) )

    response = client.chat.completions.create(
        model=settings.llm_model,
        max_tokens=500,
        messages=[
            {"role":"system", "content":SYSTEM_PROMPT},
            {"role":"user", "content":f"Context\n\n{context}\n\nQuestion{question}"}
        ]
    )

    return response.choices[0].message.content