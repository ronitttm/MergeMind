from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from services.github import parse_pr_url, fetch_pull_request
import httpx

app = FastAPI(
    title="MergeMind",
    description="Agentic AI Code Review System",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "Welcome to MergeMind!"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "MergeMind Backend"
    }

class PRRequest(BaseModel):
    pr_url: HttpUrl

@app.post("/api/reviews/preview")
async def preview_pull_request(request: PRRequest):

    try:
        pr_info = parse_pr_url(str(request.pr_url))

        result = await fetch_pull_request(
            pr_info["owner"],
            pr_info["repo"],
            pr_info["pr_number"]
        )

        return {
            "success": True,
            "data": result
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except httpx.HTTPStatusError as e:
        status = e.response.status_code

        if status == 404:
            raise HTTPException(
                status_code=404,
                detail="Pull request or repository not found, or repository is private."
            )

        if status == 403:
            raise HTTPException(
                status_code=403,
                detail="GitHub API rate limit exceeded or access forbidden."
            )

        raise HTTPException(
            status_code=status,
            detail="GitHub API request failed."
        )

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Unable to connect to GitHub."
        )