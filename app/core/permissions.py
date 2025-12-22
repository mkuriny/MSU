from fastapi import Depends, HTTPException, status
from core.dependencies import get_current_user
from models.user import User, UserRole


def require_role(*roles: UserRole):
    def checker(user: User = Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return user
    return checker
