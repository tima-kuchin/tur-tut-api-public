from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from uuid import UUID
from fastapi import HTTPException, status
from app.models.waypoints import Waypoint, WaypointType
from app.models.routes import Route
from app.models.users import DBUser, UserRole
from app.schemas.waypoints import WaypointCreate, WaypointUpdate


def _reindex_and_retype_connected(waypoints: list):
    for idx, wp in enumerate(waypoints):
        wp.order = idx
        if idx == 0:
            wp.type = WaypointType.start
        elif idx == len(waypoints) - 1:
            wp.type = WaypointType.finish
        else:
            wp.type = WaypointType.intermediate



def get_waypoints(db: Session, route_id: UUID):
    try:
        return db.query(Waypoint).filter(Waypoint.route_uuid == route_id).order_by(Waypoint.order).all()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка БД при получении точек маршрута: {str(e)}"
        )


def add_waypoint(db: Session, route_id: UUID, data: WaypointCreate, user: DBUser):
    try:
        route = db.query(Route).filter(Route.uuid == route_id).first()
        if not route:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Маршрут не найден"
            )
        if route.creator_uuid != user.uuid and user.role not in (UserRole.admin, UserRole.moderator):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Нет прав на изменение маршрута"
            )

        if data.type == "isolated":
            wp = Waypoint(
                route_uuid=route_id,
                lat=data.lat,
                lon=data.lon,
                type=WaypointType.isolated,
                description=data.description,
                photo_url=data.photo_url
            )
            db.add(wp)
            db.commit()
            db.refresh(wp)
            return wp

        connected = db.query(Waypoint).filter(
            Waypoint.route_uuid == route_id,
            Waypoint.type != WaypointType.isolated
        ).order_by(Waypoint.order).all()

        wp = Waypoint(
            route_uuid=route_id,
            lat=data.lat,
            lon=data.lon,
            description=data.description,
            photo_url=data.photo_url
        )
        db.add(wp)
        db.flush()

        connected.append(wp)
        _reindex_and_retype_connected(connected)
        db.commit()
        db.refresh(wp)
        return wp

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка БД при добавлении точки: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Непредвиденная ошибка: {str(e)}"
        )


def get_waypoint(db: Session, route_id: UUID, waypoint_id: UUID):
    try:
        wp = db.query(Waypoint).filter(
            Waypoint.uuid == waypoint_id,
            Waypoint.route_uuid == route_id
        ).first()
        if not wp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Точка не найдена"
            )
        return wp

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка БД при получении точки: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Непредвиденная ошибка: {str(e)}"
        )


def update_waypoint(
    db: Session,
    route_id: UUID,
    waypoint_id: UUID,
    data: WaypointUpdate,
    user: DBUser
):
    try:
        wp = db.query(Waypoint).filter(
            Waypoint.uuid == waypoint_id,
            Waypoint.route_uuid == route_id
        ).first()
        if not wp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Точка не найдена"
            )

        route = db.query(Route).filter(Route.uuid == route_id).first()
        if not route:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Маршрут не найден"
            )

        if route.creator_uuid != user.uuid and user.role not in (UserRole.admin, UserRole.moderator):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Нет прав на изменение точки"
            )

        if wp.type != WaypointType.isolated:
            allowed_fields = {'description', 'photo_url'}
            for key, value in data.model_dump(exclude_unset=True).items():
                if key in allowed_fields:
                    setattr(wp, key, value)
            connected = db.query(Waypoint).filter(
                Waypoint.route_uuid == route_id,
                Waypoint.type != WaypointType.isolated
            ).order_by(Waypoint.order).all()
            _reindex_and_retype_connected(connected)
        else:
            for key, value in data.model_dump(exclude_unset=True).items():
                setattr(wp, key, value)

        db.commit()
        db.refresh(wp)
        return wp

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка БД при обновлении точки: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Непредвиденная ошибка: {str(e)}"
        )


def delete_waypoint(db: Session, route_id: UUID, waypoint_id: UUID, user: DBUser):
    try:
        wp = db.query(Waypoint).filter(
            Waypoint.uuid == waypoint_id,
            Waypoint.route_uuid == route_id
        ).first()
        if not wp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Точка не найдена"
            )
        route = db.query(Route).filter(Route.uuid == route_id).first()
        if not route:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Маршрут не найден"
            )
        if route.creator_uuid != user.uuid and user.role not in (UserRole.admin, UserRole.moderator):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Нет прав на удаление точки"
            )

        if wp.type != WaypointType.isolated:
            connected = db.query(Waypoint).filter(
                Waypoint.route_uuid == route_id,
                Waypoint.type != WaypointType.isolated,
                Waypoint.uuid != waypoint_id
            ).order_by(Waypoint.order).all()
            db.delete(wp)
            _reindex_and_retype_connected(connected)
        else:
            db.delete(wp)
        db.commit()
        return {"message": "Точка успешно удалена"}
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка БД при удалении точки: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Непредвиденная ошибка: {str(e)}"
        )
