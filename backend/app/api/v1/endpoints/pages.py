"""
CMS Pages (public website content)

GET    /pages                  – list published pages (public, no auth)
GET    /pages/{slug}           – get page by slug (public)
GET    /pages/admin/all        – admin: list all pages including drafts
POST   /pages                  – admin: create page
PATCH  /pages/{page_id}        – admin: update page
DELETE /pages/{page_id}        – admin: delete page
POST   /pages/{page_id}/publish   – admin: publish page
POST   /pages/{page_id}/unpublish – admin: unpublish page
"""
import uuid
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.db.soft_delete import apply_soft_delete, not_deleted_clause, restore_soft_deleted
from app.models.page import Page
from app.models.employee import Employee
from app.api.v1.deps import get_current_user

router = APIRouter()


class ContentBlock(BaseModel):
    type: str  # text | image | cta | cards | feature_list | hero | stats | faq
    data: dict = {}


class PageCreate(BaseModel):
    slug: str
    title: str
    page_type: str = "custom"
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    hero_heading: Optional[str] = None
    hero_subheading: Optional[str] = None
    hero_image_url: Optional[str] = None
    content_blocks: List[dict] = []
    is_published: bool = False


class PageUpdate(BaseModel):
    title: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    hero_heading: Optional[str] = None
    hero_subheading: Optional[str] = None
    hero_image_url: Optional[str] = None
    content_blocks: Optional[List[dict]] = None
    is_published: Optional[bool] = None


def _page_dict(p: Page, admin: bool = False) -> dict:
    d = {
        "id": str(p.id), "slug": p.slug, "title": p.title,
        "page_type": p.page_type,
        "meta_title": p.meta_title, "meta_description": p.meta_description,
        "hero_heading": p.hero_heading, "hero_subheading": p.hero_subheading,
        "hero_image_url": p.hero_image_url,
        "content_blocks": p.content_blocks or [],
        "is_published": p.is_published,
        "published_at": p.published_at,
    }
    if admin:
        d["created_at"] = p.created_at
        d["updated_at"] = p.updated_at
    return d


# ── Public endpoints (no auth) ────────────────────────────────────────────────

@router.get("")
async def list_published_pages(db: AsyncSession = Depends(get_db)):
    q = select(Page).where(Page.is_published == True)
    clause = not_deleted_clause(Page)
    if clause is not None:
        q = q.where(clause)
    result = await db.execute(q.order_by(Page.page_type, Page.title))
    return [_page_dict(p) for p in result.scalars().all()]


@router.get("/slug/{slug}")
async def get_page_by_slug(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Page).where(Page.slug == slug))
    p = result.scalar_one_or_none()
    if not p or not p.is_published:
        raise HTTPException(status_code=404, detail="Page not found")
    return _page_dict(p)


# ── Admin endpoints ────────────────────────────────────────────────────────────

@router.get("/admin/all")
async def admin_list_pages(
    include_deleted: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin only")
    q = select(Page)
    if not include_deleted:
        clause = not_deleted_clause(Page)
        if clause is not None:
            q = q.where(clause)
    result = await db.execute(q.order_by(Page.updated_at.desc()))
    return [_page_dict(p, admin=True) for p in result.scalars().all()]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_page(
    data: PageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin only")
    existing = (await db.execute(select(Page).where(Page.slug == data.slug))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail=f"Slug '{data.slug}' already in use")
    page = Page(**data.model_dump(), created_by=current_user.id)
    if page.is_published:
        page.published_at = datetime.utcnow()
    db.add(page)
    await db.commit()
    await db.refresh(page)
    return _page_dict(page, admin=True)


@router.patch("/{page_id}")
async def update_page(
    page_id: uuid.UUID,
    data: PageUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin only")
    result = await db.execute(select(Page).where(Page.id == page_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Page not found")
    updates = data.model_dump(exclude_unset=True)
    if "is_published" in updates and updates["is_published"] and not p.published_at:
        p.published_at = datetime.utcnow()
    for field, value in updates.items():
        setattr(p, field, value)
    await db.commit()
    return _page_dict(p, admin=True)


@router.delete("/{page_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_page(
    page_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin only")
    result = await db.execute(select(Page).where(Page.id == page_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Page not found")
    apply_soft_delete(p)
    p.is_published = False
    await db.commit()


@router.post("/{page_id}/restore")
async def restore_page(
    page_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin only")
    result = await db.execute(select(Page).where(Page.id == page_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Page not found")
    restore_soft_deleted(p)
    await db.commit()
    return _page_dict(p, admin=True)


@router.post("/{page_id}/publish")
async def publish_page(
    page_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin only")
    result = await db.execute(select(Page).where(Page.id == page_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Page not found")
    p.is_published = True
    p.published_at = p.published_at or datetime.utcnow()
    await db.commit()
    return {"message": "Page published", "slug": p.slug}


@router.post("/{page_id}/unpublish")
async def unpublish_page(
    page_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin only")
    result = await db.execute(select(Page).where(Page.id == page_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Page not found")
    p.is_published = False
    await db.commit()
    return {"message": "Page unpublished"}
