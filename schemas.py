"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogpost" collection
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import datetime

class BlogPost(BaseModel):
    """
    Blog posts collection schema
    Collection name: "blogpost" (lowercase of class name)
    """
    title: str = Field(..., description="Post title", min_length=3)
    slug: str = Field(..., description="URL-friendly identifier", min_length=3)
    excerpt: Optional[str] = Field(None, description="Short summary for previews")
    content: str = Field(..., description="Full post content (Markdown supported)")
    author: str = Field(..., description="Author display name")
    cover_image_url: Optional[HttpUrl] = Field(None, description="Hero/cover image URL")
    tags: List[str] = Field(default_factory=list, description="Tags for filtering")
    published: bool = Field(default=False, description="Whether the post is visible on site")
    published_at: Optional[datetime] = Field(None, description="Timestamp when published")

# Example schemas (you may still use these elsewhere)
class User(BaseModel):
    name: str
    email: str
    address: str
    age: Optional[int] = None
    is_active: bool = True

class Product(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    category: str
    in_stock: bool = True
