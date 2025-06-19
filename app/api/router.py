from fastapi import APIRouter
from app.api.v1 import auth, users, admin, routes, waypoints, comments, utils

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(admin.router)
api_router.include_router(users.router)
api_router.include_router(routes.router)
api_router.include_router(waypoints.router)
api_router.include_router(comments.router)
api_router.include_router(utils.router)