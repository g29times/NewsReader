import uvicorn
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database.connection import get_db, init_db
from models.article import Article

app = FastAPI(
    title="AI News Reader",
    description="Collect and manage AI news and research papers"
)

@app.on_event("startup")
def startup_event():
    """
    Initialize the database on application startup
    """
    init_db()

@app.get("/articles")
def list_articles(
    db: Session = Depends(get_db), 
    skip: int = 0, 
    limit: int = 10
):
    """
    Retrieve a list of articles
    """
    articles = db.query(Article).offset(skip).limit(limit).all()
    return articles

@app.get("/health")
def health_check():
    """
    Simple health check endpoint
    """
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
