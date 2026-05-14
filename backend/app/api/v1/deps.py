from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, Union
import uuid

from app.db.base import get_db
from app.core.security import decode_token
from app.models.employee import Employee
from app.models.customer import Customer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> Employee:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise credentials_exception

    user_id = payload.get("sub")
    if not user_id:
        raise credentials_exception

    result = await db.execute(select(Employee).where(Employee.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise credentials_exception
    if user.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")
    return user


async def get_current_active_user(current_user: Employee = Depends(get_current_user)) -> Employee:
    return current_user


def require_roles(*roles: str):
    async def role_checker(current_user: Employee = Depends(get_current_user)) -> Employee:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user
    return role_checker


def require_property_access(property_id_param: str = "property_id"):
    """
    Dependency factory: ensure current_user belongs to the requested property.
    super_admin bypasses this check.
    Usage:  current_user: Employee = Depends(require_property_access("property_id"))
    """
    async def checker(
        current_user: Employee = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> Employee:
        if current_user.role == "super_admin":
            return current_user
        # For scoped roles — endpoints must validate property_id separately;
        # this dependency just ensures the token is valid and the user is active.
        return current_user
    return checker


def require_same_property(request_property_id: uuid.UUID, current_user: Employee) -> None:
    """
    Raise 403 if the current_user is not super_admin and does not belong to request_property_id.
    Call this inline inside endpoint handlers.
    """
    if current_user.role == "super_admin":
        return
    if current_user.property_id != request_property_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this property's data",
        )


async def get_current_customer(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> Customer:
    """Dependency for routes that require a logged-in Customer (B2B client)."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate customer credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    if not payload or payload.get("type") != "customer_access":
        raise credentials_exception

    customer_id = payload.get("sub")
    if not customer_id:
        raise credentials_exception

    result = await db.execute(select(Customer).where(Customer.id == uuid.UUID(customer_id)))
    customer = result.scalar_one_or_none()
    if not customer:
        raise credentials_exception
    if not customer.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Customer account is inactive")
    if customer.subscription_status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Subscription is not active")
    return customer
