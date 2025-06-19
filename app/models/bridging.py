from sqlalchemy import Column, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class PostsPostTags(Base):
    """
    Промежуточная таблица для связи M:N между постами и тегами постов.
    """
    __tablename__ = "posts_post_tags"

    post_uuid = Column(UUID(as_uuid=True), ForeignKey("posts.uuid", ondelete="CASCADE"), primary_key=True)
    post_tag_uuid = Column(UUID(as_uuid=True), ForeignKey("post_tags.uuid", ondelete="CASCADE"), primary_key=True)

class RoutesRouteTags(Base):
    """
    Промежуточная таблица для связи M:N между маршрутами и их тегами.
    """
    __tablename__ = "routes_route_tags"

    route_uuid = Column(UUID(as_uuid=True), ForeignKey("routes.uuid", ondelete="CASCADE"), primary_key=True)
    route_tag_uuid = Column(UUID(as_uuid=True), ForeignKey("route_tags.uuid", ondelete="CASCADE"), primary_key=True)



class RoutesUsersRates(Base):
    """
    Таблица для хранения пользовательских оценок маршрутов (M:N + поле rating).
    """
    __tablename__ = "routes_users_rates"

    route_uuid = Column(UUID(as_uuid=True), ForeignKey("routes.uuid", ondelete="CASCADE"), primary_key=True)
    user_uuid = Column(UUID(as_uuid=True), ForeignKey("users.uuid", ondelete="CASCADE"), primary_key=True)
    rating = Column(Float, nullable=False)


class RouteSubscriptions(Base):
    """
    Промежуточная таблица для связи M:N между пользователями и маршрутами (подписки).
    """
    __tablename__ = "route_subscriptions"

    route_uuid = Column(UUID(as_uuid=True), ForeignKey("routes.uuid", ondelete="CASCADE"), primary_key=True)
    user_uuid = Column(UUID(as_uuid=True), ForeignKey("users.uuid", ondelete="CASCADE"), primary_key=True)


class CommentLike(Base):
    """
    Промежуточная таблица для фиксации лайков комментариев (M:N).
    """
    __tablename__ = "comment_likes"

    comment_uuid = Column(UUID(as_uuid=True), ForeignKey("comments.uuid", ondelete="CASCADE"), primary_key=True)
    user_uuid = Column(UUID(as_uuid=True), ForeignKey("users.uuid", ondelete="CASCADE"), primary_key=True)


class RouteLike(Base):
    """
    Промежуточная таблица для хранения лайков маршрутов пользователей (M:N).
    """
    __tablename__ = "route_likes"

    route_uuid = Column(UUID(as_uuid=True), ForeignKey("routes.uuid", ondelete="CASCADE"), primary_key=True)
    user_uuid = Column(UUID(as_uuid=True), ForeignKey("users.uuid", ondelete="CASCADE"), primary_key=True)


class RouteFavorite(Base):
    """
    Промежуточная таблица для хранения избранных маршрутов пользователей (M:N).
    """
    __tablename__ = "route_favorites"

    route_uuid = Column(UUID(as_uuid=True), ForeignKey("routes.uuid", ondelete="CASCADE"), primary_key=True)
    user_uuid = Column(UUID(as_uuid=True), ForeignKey("users.uuid", ondelete="CASCADE"), primary_key=True)