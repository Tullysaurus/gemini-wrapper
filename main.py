import uvicorn
from api import app
from database import init_db
from ai import init_ai


if __name__ == "__main__":
    init_db()
    uvicorn.run(app, host="0.0.0.0", port=8000)