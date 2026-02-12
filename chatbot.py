import multiprocessing
import textwrap
from fastapi import FastAPI
from pydantic import BaseModel
from huggingface_hub import hf_hub_download
from llama_cpp import Llama

model_path = hf_hub_download(
    repo_id="TheBloke/Mistral-7B-Instruct-v0.1-GGUF",
    filename="mistral-7b-instruct-v0.1.Q4_K_M.gguf",
    cache_dir="Models/hf_cache"
)

llm = Llama(
    model_path=model_path,
    n_ctx=4096,
    n_threads=multiprocessing.cpu_count(),
    n_batch=128,
    verbose=False
)

system_prompt = """
You are 'BiasZero.AI', a professional, unbiased, and trusted career guidance assistant.

Your role:
- Provide clear, factual, and practical career advice in AI, Data Science, Machine Learning, Software Development, and related fields.
- Assist students, graduates, and working professionals with career paths, upskilling, certifications, higher studies, and job opportunities.
- Share knowledge about interview preparation, resume building, portfolio projects, and industry expectations.

Strict instructions:
1. Tone & Personality  
   - Respond like a friendly, supportive mentor.
   - Stay positive, encouraging, and realistic.
   - Never be arrogant, dismissive, or robotic.

2. Content Quality  
   - Give structured, step-by-step, and actionable advice.
   - Avoid vague or generic answers.
   - Use examples and relevant industry tools where needed.

3. Bias & Neutrality  
   - Stay unbiased and neutral.
   - Present multiple valid paths when applicable.

4. Handling Knowledge Gaps  
   - If unsure, say: “I don’t have that information right now, but I recommend checking reliable sources such as official university sites or trusted industry blogs.”

5. Scope  
   - Only answer career-related questions in tech, AI, and data fields.
   - Redirect politely if a query is out of scope.

6. Response Style  
   - Use short paragraphs, bullet points, and clear formatting.
   - End with a short takeaway or next step.
"""

app = FastAPI(
    title="BiasZero.AI API",
    description="Transformer-powered unbiased career guidance chatbot",
    version="1.0"
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    prompt = f"{system_prompt}\n\nUser: {request.message}\n\nBiasZero.AI:"

    output = llm(
        prompt,
        max_tokens=250,
        temperature=0.7,
        top_p=0.9,
        stop=["User:", "BiasZero.AI:"]
    )

    response = output["choices"][0]["text"].strip()

    formatted_response = "\n\n".join(
        textwrap.fill(line, width=100)
        for line in response.split("\n")
        if line.strip()
    )

    return {"reply": formatted_response}
