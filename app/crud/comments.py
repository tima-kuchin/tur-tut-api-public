from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from uuid import UUID

from app.models.bridging import CommentLike
from app.models.comments import Comment
from app.models.users import DBUser
from app.models.target_types import TargetType
from app.schemas.common import UserRole


def get_comments(
    db: Session,
    target_type: str,
    target_uuid: UUID,
    current_user: DBUser | None = None
):
    try:
        target_type_obj = db.query(TargetType).filter(TargetType.name == target_type).first()
        if not target_type_obj:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Некорректный тип сущности")
        target_type_id = target_type_obj.uuid

        comments = (
            db.query(Comment)
            .filter(Comment.target_type_id == target_type_id, Comment.target_uuid == target_uuid)
            .order_by(Comment.created_at)
            .all()
        )
        comment_uuids = [c.uuid for c in comments]
        likes_counts = dict(
            db.query(CommentLike.comment_uuid, func.count(CommentLike.user_uuid))
            .filter(CommentLike.comment_uuid.in_(comment_uuids))
            .group_by(CommentLike.comment_uuid)
            .all()
        )
        liked_set = set()
        if current_user:
            liked_set = set(
                row[0]
                for row in db.query(CommentLike.comment_uuid)
                .filter(
                    CommentLike.comment_uuid.in_(comment_uuids),
                    CommentLike.user_uuid == current_user.uuid
                )
                .all()
            )
        users = db.query(DBUser).filter(DBUser.uuid.in_([c.creator_uuid for c in comments])).all()
        user_dict = {u.uuid: u for u in users}
        result = []
        for c in comments:
            user = user_dict.get(c.creator_uuid)
            result.append({
                "uuid": c.uuid,
                "comment_text": c.comment_text,
                "created_at": c.created_at,
                "creator_login": user.login if user else "???",
                "creator_avatar": user.profile_picture if user else None,
                "likes_count": likes_counts.get(c.uuid, 0),
                "is_liked": c.uuid in liked_set,
            })
        return result
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных при получении комментариев: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Неизвестная ошибка при получении комментариев: {str(e)}"
        )


from fastapi import HTTPException, status

def create_comment(
    db: Session,
    target_type: str,
    target_uuid: UUID,
    data,
    current_user: DBUser
):
    try:
        target_type_obj = db.query(TargetType).filter(TargetType.name == target_type).first()
        if not target_type_obj:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Некорректный тип сущности"
            )
        target_type_id = target_type_obj.uuid

        comment = Comment(
            creator_uuid=current_user.uuid,
            target_type_id=target_type_id,
            target_uuid=target_uuid,
            comment_text=data.comment_text.strip(),
        )
        db.add(comment)
        db.commit()
        db.refresh(comment)

        user = db.query(DBUser).filter(DBUser.uuid == current_user.uuid).first()

        return {
            "uuid": comment.uuid,
            "comment_text": comment.comment_text,
            "created_at": comment.created_at,
            "creator_login": user.login if user else "???",
            "creator_avatar": user.profile_picture if user else None,
            "likes_count": 0,
            "is_liked": False,
        }

    except HTTPException:
        raise

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка сервера при создании комментария"
        )



def delete_comment(db: Session, comment_id: UUID, current_user: DBUser):
    try:
        comment = db.query(Comment).filter(Comment.uuid == comment_id).first()
        if not comment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Комментарий не найден")

        creator = db.query(DBUser).filter(DBUser.uuid == comment.creator_uuid).first()

        if current_user.role == UserRole.moderator:
            if not creator or creator.role != UserRole.user:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Модератор может удалять только комментарии обычных пользователей"
                )
        elif current_user.role == UserRole.admin:
            if creator and creator.role == UserRole.admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Админ не может удалять комментарии других админов"
                )
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет прав на удаление комментария")

        db.delete(comment)
        db.commit()
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных при удалении комментария: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Неизвестная ошибка при удалении комментария: {str(e)}"
        )


def like_comment(db: Session, comment_id: UUID, current_user: DBUser):
    try:
        if not db.query(Comment).filter(Comment.uuid == comment_id).first():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Комментарий не найден")

        if db.query(CommentLike).filter_by(user_uuid=current_user.uuid, comment_uuid=comment_id).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Комментарий уже лайкнут")

        like = CommentLike(user_uuid=current_user.uuid, comment_uuid=comment_id)
        db.add(like)
        db.commit()
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных при добавлении лайка: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Неизвестная ошибка при добавлении лайка: {str(e)}"
        )



def unlike_comment(db: Session, comment_id: UUID, current_user: DBUser):
    try:
        if not db.query(Comment).filter(Comment.uuid == comment_id).first():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Комментарий не найден")

        like = db.query(CommentLike).filter_by(user_uuid=current_user.uuid, comment_uuid=comment_id).first()
        if not like:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Комментарий не был лайкнут")

        db.delete(like)
        db.commit()
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных при удалении лайка: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Неизвестная ошибка при удалении лайка: {str(e)}"
        )