import os
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import db, create_document, get_documents
from schemas import BlogPost
from bson import ObjectId

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class BlogPostCreate(BlogPost):
    pass


class BlogPostOut(BaseModel):
    id: str
    title: str
    slug: str
    excerpt: Optional[str]
    content: str
    author: str
    cover_image_url: Optional[str]
    tags: List[str] = []
    published: bool = False
    published_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@app.get("/")
def read_root():
    return {"message": "Blog API is running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": [],
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, "name") else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response


# Utility to convert Mongo document to API-friendly dict

def serialize_post(doc) -> BlogPostOut:
    return BlogPostOut(
        id=str(doc.get("_id")),
        title=doc.get("title"),
        slug=doc.get("slug"),
        excerpt=doc.get("excerpt"),
        content=doc.get("content"),
        author=doc.get("author"),
        cover_image_url=doc.get("cover_image_url"),
        tags=doc.get("tags", []),
        published=doc.get("published", False),
        published_at=doc.get("published_at"),
        created_at=doc.get("created_at"),
        updated_at=doc.get("updated_at"),
    )


# Posts API
@app.get("/api/posts", response_model=List[BlogPostOut])
def list_posts(published: Optional[bool] = None, tag: Optional[str] = None, limit: int = 50):
    filter_query = {}
    if published is not None:
        filter_query["published"] = published
    if tag:
        filter_query["tags"] = {"$in": [tag]}
    docs = db["blogpost"].find(filter_query).sort("created_at", -1).limit(limit)
    return [serialize_post(d) for d in docs]


@app.get("/api/posts/{post_id}", response_model=BlogPostOut)
def get_post(post_id: str):
    try:
        doc = db["blogpost"].find_one({"_id": ObjectId(post_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid post id")
    if not doc:
        raise HTTPException(status_code=404, detail="Post not found")
    return serialize_post(doc)


@app.post("/api/posts", response_model=BlogPostOut)
def create_post(payload: BlogPostCreate):
    # Set published_at if marking as published
    data = payload.model_dump()
    now = datetime.utcnow()
    if data.get("published") and not data.get("published_at"):
        data["published_at"] = now
    inserted_id = create_document("blogpost", data)
    doc = db["blogpost"].find_one({"_id": ObjectId(inserted_id)})
    return serialize_post(doc)


class BlogPostUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    excerpt: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None
    cover_image_url: Optional[str] = None
    tags: Optional[List[str]] = None
    published: Optional[bool] = None
    published_at: Optional[datetime] = None


@app.put("/api/posts/{post_id}", response_model=BlogPostOut)
@app.patch("/api/posts/{post_id}", response_model=BlogPostOut)
def update_post(post_id: str, payload: BlogPostUpdate):
    try:
        oid = ObjectId(post_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid post id")

    update_data = {k: v for k, v in payload.model_dump(exclude_unset=True).items()}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")

    # If toggling publish state, manage published_at
    if "published" in update_data and update_data["published"]:
        update_data.setdefault("published_at", datetime.utcnow())
    if "published" in update_data and update_data["published"] is False:
        update_data.setdefault("published_at", None)

    update_data["updated_at"] = datetime.utcnow()

    result = db["blogpost"].update_one({"_id": oid}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Post not found")
    doc = db["blogpost"].find_one({"_id": oid})
    return serialize_post(doc)


@app.delete("/api/posts/{post_id}")
def delete_post(post_id: str):
    try:
        oid = ObjectId(post_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid post id")
    result = db["blogpost"].delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Post not found")
    return {"success": True}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
