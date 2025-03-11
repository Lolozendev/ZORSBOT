
from typing import Optional

import loguru
from sqlalchemy import String
from sqlmodel import SQLModel, Field, BigInteger,Relationship

from utils.color import Color

class StreamerModeratorRelation(SQLModel, table=True):
    streamer_id: int | None = Field(default=None, foreign_key="streamer.id", primary_key=True)
    moderator_id: int | None = Field(default=None, foreign_key="user.id", primary_key=True)

class User(SQLModel, table=True):
    id: int = Field(primary_key=True, sa_type=BigInteger)
    name: str

    habitue: Optional["Habitue"] = Relationship(back_populates="user", sa_relationship_kwargs={"uselist": False}, cascade_delete=True,passive_deletes=True)
    streamer: Optional["Streamer"] = Relationship(back_populates="user", sa_relationship_kwargs={"uselist": False}, cascade_delete=True,passive_deletes=True)
    moderate_for: Optional[list["Streamer"]] = Relationship(back_populates="moderators", link_model=StreamerModeratorRelation)

class Habitue(SQLModel, table=True):
    id: int | None = Field(primary_key=True, default=None, foreign_key="user.id", sa_type=BigInteger)
    color: str = Field(regex=r"^#[0-9a-fA-F]{6}$")

    user: User = Relationship(back_populates="habitue")

    @property
    async def color_name(self) -> str:
        return await Color.get_color_name(Color.from_hexstring(self.color))


class Streamer(SQLModel, table=True):
    id: int | None = Field(primary_key=True, default=None, foreign_key="user.id", sa_type=BigInteger)
    channel_tag: str | None = Field(sa_type=String, nullable=True)

    moderators: list[User] = Relationship(back_populates="moderate_for", link_model=StreamerModeratorRelation)
    user: User = Relationship(back_populates="streamer")