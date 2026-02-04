from fastapi import FastAPI

app = FastAPI(title="GitHub App Preview URL Service")

@app.get("/")
async def root():
    return {"status": "healthy"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
