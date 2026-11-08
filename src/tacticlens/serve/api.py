"""HTTP API (FastAPI): POST /analyze, GET /health, GET /taxonomy.

Run:  python -m tacticlens.cli serve           (then open http://127.0.0.1:8000/docs)
"""

# No `from __future__ import annotations` here: FastAPI must see the request model's real type,
# not a string, or it treats the body as query parameters (422).
from .predictor import Predictor


def create_app(predictor: Predictor):
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel, Field

    from .parse import MAX_CHARS

    class AnalyzeRequest(BaseModel):
        text: str = Field(..., description='One message, or a conversation as "Name: text" lines', max_length=MAX_CHARS)
        actor: str | None = Field(None, description="Speaker to check (suspected persuader/manipulator/scammer)")
        mode: str = Field("balanced", description="balanced (F1 thresholds) or careful (fewer false alarms)")
        evidence: bool = True

    app = FastAPI(title="TacticLens API", version="1.0",
                  description="Influence-tactic detection across persuasion, manipulation and scams (research prototype).")

    @app.get("/health")
    def health():
        return {"status": "ok", "model": predictor.model_name, "modes": predictor.modes()}

    @app.get("/taxonomy")
    def taxonomy():
        return {"tactics": predictor.tactics, "genres": predictor.genres}

    @app.post("/analyze")
    def analyze(req: AnalyzeRequest):
        if req.mode not in predictor.modes():
            raise HTTPException(422, f"mode must be one of {predictor.modes()}")
        if not req.text.strip():
            raise HTTPException(422, "text is empty")
        return predictor.analyze(req.text, actor=req.actor, mode=req.mode, evidence=req.evidence)

    return app
