from typing import Optional, List
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, DBAPIError
import traceback
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import or_, func
from app.core.config import settings
from app.crud.users import get_user
from app.models.comments import Comment
from app.models.routes import Route
from app.models.users import DBUser, UserRole
from app.models.waypoints import Waypoint
from app.schemas.routes import RouteCreate, RouteUpdate, RouteCardOut
from app.models.bridging import RouteLike, RouteFavorite
from app.models.tag import RouteTag
from datetime import datetime, timezone

def get_public_routes(
    db: Session,
    current_user: Optional[DBUser] = None,
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    route_type_uuid: Optional[UUID] = None,
    difficulty_uuid: Optional[UUID] = None,
    location: Optional[str] = None,
    ordering: Optional[str] = None,
) -> list[dict]:
    try:
        query = db.query(Route).filter(Route.is_public.is_(True))

        if search:
            query = query.filter(Route.name.ilike(f"%{search}%"))
        if route_type_uuid:
            query = query.filter(Route.route_type_uuid == route_type_uuid)
        if difficulty_uuid:
            query = query.filter(Route.difficulty_uuid == difficulty_uuid)
        if location:
            query = query.filter(Route.location.ilike(f"%{location}%"))

        if ordering == "rating":
            query = query.order_by(Route.avg_rating.desc())
        elif ordering == "recent":
            query = query.order_by(Route.published_at.desc())

        routes = query.offset(skip).limit(limit).all()

        route_uuids = [r.uuid for r in routes]
        likes_counts = dict(
            (row[0], row[1])
            for row in db.query(
                RouteLike.route_uuid,
                func.count(RouteLike.user_uuid)
            )
            .filter(RouteLike.route_uuid.in_(route_uuids))
            .group_by(RouteLike.route_uuid)
            .all()
        )
        comments_counts = dict(
            (row[0], row[1])
            for row in db.query(
                Comment.target_uuid,
                func.count(Comment.uuid)
            )
            .filter(
                Comment.target_type_id == settings.ROUTE_TYPE_UUID,
                Comment.target_uuid.in_(route_uuids)
            )
            .group_by(Comment.target_uuid)
            .all()
        )
        favorites = set()
        if current_user:
            favorites = set(
                row[0]
                for row in db.query(RouteFavorite.route_uuid)
                .filter(
                    RouteFavorite.route_uuid.in_(route_uuids),
                    RouteFavorite.user_uuid == current_user.uuid,
                )
                .all()
            )

        result = []
        for r in routes:
            result.append({
                "uuid": r.uuid,
                "name": r.name,
                "location": r.location,
                "avg_rating": r.avg_rating,
                "likes_count": likes_counts.get(r.uuid, 0),
                "comments_count": comments_counts.get(r.uuid, 0),
                "is_favorite": r.uuid in favorites,
                "thumbnail_url": getattr(r, "thumbnail_url", None),
                "route_type_uuid": r.route_type_uuid,
                "route_type_name": r.route_type.name if r.route_type else None,
            })
        return result

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных при получении публичных маршрутов: {e.__class__.__name__}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка сервера при получении публичных маршрутов: {str(e)}"
        )

def get_route_by_id(db: Session, route_id: UUID, current_user: DBUser = None):
    try:
        route = (
            db.query(Route)
            .options(
                joinedload(Route.waypoints),
                joinedload(Route.route_type),
                joinedload(Route.difficulty_type),
                joinedload(Route.creator),
                joinedload(Route.tags),
            )
            .filter(Route.uuid == route_id)
            .first()
        )
        if not route:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Маршрут не найден")

        likes_count = db.query(func.count(RouteLike.user_uuid)).filter(RouteLike.route_uuid == route_id).scalar() or 0
        comments_count = db.query(func.count(Comment.uuid)).filter(
            Comment.target_type_id == settings.ROUTE_TYPE_UUID,
            Comment.target_uuid == route_id).scalar() or 0

        is_favorite = False
        is_liked = False
        if current_user:
            is_favorite = db.query(RouteFavorite).filter(
                RouteFavorite.route_uuid == route_id,
                RouteFavorite.user_uuid == current_user.uuid
            ).first() is not None
            is_liked = db.query(RouteLike).filter(
                RouteLike.route_uuid == route_id,
                RouteLike.user_uuid == current_user.uuid
            ).first() is not None


        can_edit = False
        can_delete = False

        if current_user:
            is_author = route.creator_uuid == current_user.uuid
            role = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
            if is_author or role == "admin":
                can_edit = True
                can_delete = True
            elif role == "moderator":
                can_edit = True

        return {
            "uuid": route.uuid,
            "name": route.name,
            "location": route.location,
            "description": route.description,
            "route_type_uuid": route.route_type_uuid,
            "difficulty_uuid": route.difficulty_uuid,
            "avg_rating": route.avg_rating,
            "duration": route.duration,
            "distance": route.distance,
            "created_at": route.created_at,
            "edited_at": route.edited_at,
            "last_edited_by_uuid": route.last_edited_by_uuid,
            "last_edited_by_role": route.last_edited_by_role,
            "waypoints": route.waypoints,
            "likes_count": likes_count,
            "comments_count": comments_count,
            "is_favorite": is_favorite,
            "is_liked": is_liked,
            "thumbnail_url": getattr(route, "thumbnail_url", None),
            "creator_login": route.creator.login if route.creator else None,
            "route_type_name": route.route_type.name if route.route_type else None,
            "difficulty_type_name": route.difficulty_type.name if route.difficulty_type else None,
            "can_edit": can_edit,
            "can_delete": can_delete,
            "tags": [t.uuid for t in route.tags] if hasattr(route, "tags") else [],
        }

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных при получении маршрута: {e.__class__.__name__}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка сервера при получении маршрута: {str(e)}"
        )


def create_route(db: Session, data: RouteCreate, creator: DBUser):
    try:
        route = Route(
            name=data.name,
            location=data.location,
            description=data.description,
            route_type_uuid=data.route_type_uuid,
            difficulty_uuid=data.difficulty_uuid,
            creator_uuid=creator.uuid,
            geo_data=data.geo_data,
            duration=data.duration,
            distance=data.distance,
            is_public=data.is_public or False,
            published_at=data.published_at
        )
        db.add(route)
        db.flush()

        if data.tags:
            tags = db.query(RouteTag).filter(RouteTag.uuid.in_(data.tags)).all()
            route.tags = tags

        if data.waypoints:
            for w in data.waypoints:
                waypoint = Waypoint(
                    route_uuid=route.uuid,
                    lat=w.lat,
                    lng=w.lng,
                    order=w.order,
                    type=w.type,
                    description=w.description,
                    photo_url=w.photo_url,
                )
                db.add(waypoint)

        db.commit()
        db.refresh(route)

        return {
            "uuid": route.uuid,
            "name": route.name,
            "location": route.location,
            "description": route.description,
            "route_type_uuid": route.route_type_uuid,
            "geo_data": route.geo_data,
            "tags": [tag.uuid for tag in route.tags],
            "duration": route.duration,
            "distance": route.distance,
            "difficulty_uuid": route.difficulty_uuid,
            "is_public": route.is_public,
            "published_at": route.published_at,
            "created_at": route.created_at,
            "edited_at": route.edited_at,
            "last_edited_by_uuid": route.last_edited_by_uuid,
            "last_edited_by_role": route.last_edited_by_role,
            "waypoints": route.waypoints,
            "likes_count": 0,
            "comments_count": 0,
            "is_liked": False,
            "is_favorite": False,
            "thumbnail_url": getattr(route, "thumbnail_url", None),
            "creator_login": creator.login,
            "route_type_name": route.route_type.name if route.route_type else None,
            "difficulty_type_name": route.difficulty_type.name if route.difficulty_type else None,
            "can_edit": True,
            "can_delete": True,
        }

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных при создании маршрута: {e.__class__.__name__}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка сервера при создании маршрута: {str(e)}"
        )


def update_route(
    db: Session,
    route_id: UUID,
    data: RouteUpdate,
    current_user: DBUser
) -> dict:
    route = db.query(Route).filter(Route.uuid == route_id).first()
    if not route:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Маршрут не найден")

    if (route.creator_uuid != current_user.uuid
        and current_user.role not in (UserRole.admin, UserRole.moderator)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к редактированию")

    update_data = data.model_dump(exclude_unset=True)

    for field in [
        "name", "location", "description", "route_type_uuid", "difficulty_uuid",
        "geo_data", "duration", "distance", "is_public", "published_at", "thumbnail_url"
    ]:
        if field in update_data:
            setattr(route, field, update_data[field])

    if "tags" in update_data and update_data["tags"] is not None:
        tags = db.query(RouteTag).filter(RouteTag.uuid.in_(update_data["tags"])).all()
        route.tags = tags

    if "waypoints" in update_data and update_data["waypoints"] is not None:
        db.query(Waypoint).filter(Waypoint.route_uuid == route.uuid).delete()
        for w in update_data["waypoints"]:
            wp = Waypoint(
                route_uuid=route.uuid,
                lat=w["lat"],
                lng=w["lng"],
                order=w["order"],
                type=w["type"],
                description=w.get("description"),
                photo_url=w.get("photo_url"),
            )
            db.add(wp)

    route.last_edited_by_uuid = current_user.uuid
    route.last_edited_by_role = current_user.role

    try:
        db.commit()
        db.refresh(route)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при сохранении изменений маршрута"
        )

    likes_count = db.query(func.count(RouteLike.user_uuid)) \
                    .filter(RouteLike.route_uuid == route.uuid) \
                    .scalar() or 0
    comments_count = db.query(func.count(Comment.uuid)) \
                       .filter(Comment.target_type_id == settings.ROUTE_TYPE_UUID,
                               Comment.target_uuid == route.uuid) \
                       .scalar() or 0
    is_favorite = db.query(RouteFavorite) \
                    .filter(
                        RouteFavorite.route_uuid == route.uuid,
                        RouteFavorite.user_uuid == current_user.uuid
                    ).first() is not None
    is_liked = (db.query(RouteLike)
                    .filter(
                        RouteLike.route_uuid == route.uuid,
                        RouteLike.user_uuid == current_user.uuid
                    ).first() is not None)

    is_author = (route.creator_uuid == current_user.uuid)
    role = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    can_edit = is_author or role in ("admin", "moderator")
    can_delete = is_author or role == "admin"

    return {
        "uuid": route.uuid,
        "name": route.name,
        "location": route.location,
        "description": route.description,
        "route_type_uuid": route.route_type_uuid,
        "geo_data": route.geo_data,
        "tags": [tag.uuid for tag in route.tags],
        "duration": route.duration,
        "distance": route.distance,
        "difficulty_uuid": route.difficulty_uuid,
        "is_public": route.is_public,
        "published_at": route.published_at,
        "created_at": route.created_at,
        "edited_at": route.edited_at,
        "last_edited_by_uuid": route.last_edited_by_uuid,
        "last_edited_by_role": route.last_edited_by_role,
        "waypoints": route.waypoints,
        "likes_count": likes_count,
        "comments_count": comments_count,
        "is_favorite": is_favorite,
        "is_liked": is_liked,
        "thumbnail_url": getattr(route, "thumbnail_url", None),
        "creator_login": route.creator.login if route.creator else None,
        "route_type_name": route.route_type.name if route.route_type else None,
        "difficulty_type_name": route.difficulty_type.name if route.difficulty_type else None,
        "can_edit": can_edit,
        "can_delete": can_delete,
    }


def delete_route(db: Session, route_id: UUID, current_user: DBUser):
    try:
        route = db.query(Route).filter(Route.uuid == route_id).first()
        if not route:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Маршрут не найден")
        if current_user.role != UserRole.admin and route.creator_uuid != current_user.uuid:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к удалению")

        db.delete(route)
        db.commit()
        return {"detail": "Маршрут успешно удалён"}

    except HTTPException:
        raise

    except IntegrityError as e:
        db.rollback()
        error_message = str(e.orig) if hasattr(e, 'orig') else str(e)
        print("INTEGRITY ERROR:", error_message)
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"IntegrityError: {error_message}"
        )

    except DBAPIError as e:
        db.rollback()
        error_message = str(e.orig) if hasattr(e, 'orig') else str(e)
        print("DBAPI ERROR:", error_message)
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"DBAPIError: {error_message}"
        )

    except SQLAlchemyError as e:
        db.rollback()
        error_message = str(e)
        print("SQLALCHEMY ERROR:", error_message)
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SQLAlchemyError: {error_message}"
        )

    except Exception as e:
        db.rollback()
        print("UNEXPECTED ERROR:", str(e))
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected server error: {str(e)}"
        )


def get_routes_by_user(
    db: Session,
    user: DBUser,
    skip: int = 0,
    limit: int = 100
) -> list[dict]:
    try:
        routes = (
            db.query(Route)
            .filter(Route.creator_uuid == user.uuid)
            .order_by(Route.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        route_uuids = [r.uuid for r in routes]
        likes_counts = dict(
            (row[0], row[1])
            for row in db.query(
                RouteLike.route_uuid,
                func.count(RouteLike.user_uuid)
            )
            .filter(RouteLike.route_uuid.in_(route_uuids))
            .group_by(RouteLike.route_uuid)
            .all()
        )
        comments_counts = dict(
            (row[0], row[1])
            for row in db.query(
                Comment.target_uuid,
                func.count(Comment.uuid)
            )
            .filter(
                Comment.target_type_id == settings.ROUTE_TYPE_UUID,
                Comment.target_uuid.in_(route_uuids)
            )
            .group_by(Comment.target_uuid)
            .all()
        )
        favorites = set(
            row[0]
            for row in db.query(RouteFavorite.route_uuid)
            .filter(
                RouteFavorite.route_uuid.in_(route_uuids),
                RouteFavorite.user_uuid == user.uuid,
            )
            .all()
        )

        result = []
        for r in routes:
            result.append({
                "uuid": r.uuid,
                "name": r.name,
                "location": r.location,
                "avg_rating": r.avg_rating,
                "likes_count": likes_counts.get(r.uuid, 0),
                "comments_count": comments_counts.get(r.uuid, 0),
                "is_favorite": r.uuid in favorites,
                "thumbnail_url": getattr(r, "thumbnail_url", None),
                "route_type_uuid": r.route_type_uuid,
                "route_type_name": r.route_type.name if r.route_type else None
            })
        return result

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных при получении маршрутов пользователя: {e.__class__.__name__}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка сервера при получении маршрутов пользователя: {str(e)}"
        )


def get_public_routes_by_user(
    db: Session,
    user_identifier: str,
    skip=0,
    limit=20,
    current_user: DBUser = None
):
    try:
        user = get_user(db, user_identifier)
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        routes = (
            db.query(Route)
            .filter(
                Route.creator_uuid == user.uuid,
                Route.is_public.is_(True)
            )
            .order_by(Route.published_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        route_uuids = [r.uuid for r in routes]

        likes_counts = dict(
            (row[0], row[1])
            for row in db.query(
                RouteLike.route_uuid,
                func.count(RouteLike.user_uuid)
            )
            .filter(RouteLike.route_uuid.in_(route_uuids))
            .group_by(RouteLike.route_uuid)
            .all()
        )

        comments_counts = dict(
            (row[0], row[1])
            for row in db.query(
                Comment.target_uuid,
                func.count(Comment.uuid)
            )
            .filter(
                Comment.target_type_id == settings.ROUTE_TYPE_UUID,
                Comment.target_uuid.in_(route_uuids)
            )
            .group_by(Comment.target_uuid)
            .all()
        )

        favorites = set()
        if current_user:
            favorites = set(
                row[0]
                for row in db.query(RouteFavorite.route_uuid)
                .filter(
                    RouteFavorite.route_uuid.in_(route_uuids),
                    RouteFavorite.user_uuid == current_user.uuid,
                )
                .all()
            )

        result = []
        for r in routes:
            result.append({
                "uuid": r.uuid,
                "name": r.name,
                "location": r.location,
                "avg_rating": r.avg_rating,
                "likes_count": likes_counts.get(r.uuid, 0),
                "comments_count": comments_counts.get(r.uuid, 0),
                "is_favorite": r.uuid in favorites,
                "thumbnail_url": getattr(r, "thumbnail_url", None),
                "difficulty_type_name": r.difficulty_type.name if getattr(r, "difficulty_type", None) else None,
                "route_type_uuid": r.route_type_uuid,
                "route_type_name": r.route_type.name if getattr(r, "route_type", None) else None,
            })
        return result

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных при получении маршрутов пользователя: {e.__class__.__name__}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка сервера при получении маршрутов пользователя: {str(e)}"
        )


def like_route(db: Session, user: DBUser, route_id: UUID):
    try:
        if not db.query(Route).filter_by(uuid=route_id).first():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Маршрут не найден")
        if db.query(RouteLike).filter_by(user_uuid=user.uuid, route_uuid=route_id).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Уже лайкнуто")
        like = RouteLike(user_uuid=user.uuid, route_uuid=route_id)
        db.add(like)
        db.commit()
        return {"detail": "Маршрут лайкнут"}
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных при лайке маршрута: {e.__class__.__name__}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка при лайке маршрута: {str(e)}"
        )

def unlike_route(db: Session, user: DBUser, route_id: UUID):
    try:
        if not db.query(Route).filter_by(uuid=route_id).first():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Маршрут не найден")
        like = db.query(RouteLike).filter_by(user_uuid=user.uuid, route_uuid=route_id).first()
        if not like:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Лайка не было")
        db.delete(like)
        db.commit()
        return {"detail": "Лайк снят"}
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных при снятии лайка: {e.__class__.__name__}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка при снятии лайка: {str(e)}"
        )


def get_favorites(db: Session, user: DBUser) -> List[RouteCardOut]:
    try:
        routes = (
            db.query(Route)
            .join(RouteFavorite, RouteFavorite.route_uuid == Route.uuid)
            .filter(RouteFavorite.user_uuid == user.uuid)
            .all()
        )
        route_uuids = [r.uuid for r in routes]

        likes_counts = dict(
            (row[0], row[1])
            for row in db.query(
                RouteLike.route_uuid,
                func.count(RouteLike.user_uuid)
            )
            .filter(RouteLike.route_uuid.in_(route_uuids))
            .group_by(RouteLike.route_uuid)
            .all()
        )
        comments_counts = dict(
            (row[0], row[1])
            for row in db.query(
                Comment.target_uuid,
                func.count(Comment.uuid)
            )
            .filter(
                Comment.target_type_id == settings.ROUTE_TYPE_UUID,
                Comment.target_uuid.in_(route_uuids)
            )
            .group_by(Comment.target_uuid)
            .all()
        )
        liked_uuids = set(
            row[0]
            for row in db.query(RouteLike.route_uuid)
            .filter(
                RouteLike.route_uuid.in_(route_uuids),
                RouteLike.user_uuid == user.uuid,
            )
            .all()
        )

        result = []
        for r in routes:
            result.append(RouteCardOut(
                uuid=r.uuid,
                name=r.name,
                location=r.location,
                avg_rating=r.avg_rating,
                likes_count=likes_counts.get(r.uuid, 0),
                comments_count=comments_counts.get(r.uuid, 0),
                is_favorite=True,
                is_liked=r.uuid in liked_uuids,
                thumbnail_url=getattr(r, "thumbnail_url", None),
            ))
        return result

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных при получении избранных маршрутов: {e.__class__.__name__}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка сервера при получении избранных маршрутов: {str(e)}"
        )

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных при получении избранных маршрутов: {e.__class__.__name__}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка сервера при получении избранных маршрутов: {str(e)}"
        )


def add_to_favorites(db: Session, user: DBUser, route_id: UUID):
    try:
        if not db.query(Route).filter_by(uuid=route_id).first():
            raise HTTPException(status_code=404, detail="Маршрут не найден")
        if db.query(RouteFavorite).filter_by(user_uuid=user.uuid, route_uuid=route_id).first():
            raise HTTPException(status_code=400, detail="Уже в избранном")
        fav = RouteFavorite(user_uuid=user.uuid, route_uuid=route_id)
        db.add(fav)
        db.commit()
        return {"detail": "Маршрут добавлен в избранное"}
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных при добавлении в избранное: {e.__class__.__name__}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка сервера при добавлении в избранное: {str(e)}"
        )

def remove_from_favorites(db: Session, user: DBUser, route_id: UUID):
    try:
        if not db.query(Route).filter_by(uuid=route_id).first():
            raise HTTPException(status_code=404, detail="Маршрут не найден")
        fav = db.query(RouteFavorite).filter_by(user_uuid=user.uuid, route_uuid=route_id).first()
        if not fav:
            raise HTTPException(status_code=400, detail="Не было в избранном")
        db.delete(fav)
        db.commit()
        return {"detail": "Маршрут удалён из избранного"}
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных при удалении из избранного: {e.__class__.__name__}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка сервера при удалении из избранного: {str(e)}"
        )


def set_draft(db: Session, route_id: UUID, current_user: DBUser):
    try:
        route = db.query(Route).filter(Route.uuid == route_id).first()
        if not route:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Маршрут не найден")
        if route.creator_uuid != current_user.uuid and current_user.role not in (UserRole.admin, UserRole.moderator):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа")
        if not route.is_public:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Маршрут уже черновик")
        route.is_public = False
        route.published_at = None
        route.last_edited_by_uuid = current_user.uuid
        route.last_edited_by_role = current_user.role
        db.commit()
        db.refresh(route)
        return route
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных при переводе маршрута в черновик: {e.__class__.__name__}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка сервера при переводе маршрута в черновик: {str(e)}"
        )


def publish_route(db: Session, route_id: UUID, current_user: DBUser):
    try:
        route = db.query(Route).filter(Route.uuid == route_id).first()
        if not route:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Маршрут не найден")
        if route.creator_uuid != current_user.uuid and current_user.role not in (UserRole.admin, UserRole.moderator):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа")
        if route.is_public:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Маршрут уже опубликован")

        errors = []
        if not route.name or not route.name.strip():
            errors.append("Название маршрута не заполнено.")
        if not route.location or not route.location.strip():
            errors.append("Локация маршрута не заполнена.")
        if not route.description or not route.description.strip():
            errors.append("Описание маршрута не заполнено.")

        waypoints_count = len(route.waypoints) if route.waypoints else 0
        if waypoints_count < 2:
            errors.append("Для публикации требуется минимум две точки маршрута.")

        if errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=" ".join(errors)
            )

        route.is_public = True
        route.published_at = datetime.now(timezone.utc)
        route.last_edited_by_uuid = current_user.uuid
        route.last_edited_by_role = current_user.role

        db.commit()
        db.refresh(route)
        return route

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных при публикации маршрута: {e.__class__.__name__}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка сервера при публикации маршрута: {str(e)}"
        )



