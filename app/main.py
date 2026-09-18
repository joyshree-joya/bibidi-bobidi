from fastapi import FastAPI

app = FastAPI(
    title="GridWise Energy Optimization API",
    description="LLM-powered smart campus energy optimization service",
    version="1.0.0"
)


@app.get("/health")
def health_check():
    return {"status": "ok"}