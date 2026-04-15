from sqlalchemy import BigInteger, String, Integer, Boolean, DateTime, Numeric, ForeignKey, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    referral_code: Mapped[str] = mapped_column(String(16), unique=True, index=True, nullable=False)
    referred_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )

    balance: Mapped[float] = mapped_column(Numeric(20, 2), default=0, nullable=False)
    energy: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)
    max_energy: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)

    tap_power: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    passive_income: Mapped[float] = mapped_column(Numeric(10, 4), default=0, nullable=False)

    last_energy_update: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    last_tap_timestamp: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_combo_claim: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    referrals: Mapped[list["User"]] = relationship(
        "User", back_populates="referrer", remote_side=[id], foreign_keys=[referred_by]
    )
    referrer: Mapped["User | None"] = relationship(
        "User", back_populates="referrals", remote_side=[referred_by], foreign_keys=[referred_by]
    )
    upgrades: Mapped[list["Upgrade"]] = relationship(
        "Upgrade", back_populates="user", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_users_balance", "balance"),
        Index("idx_users_energy", "energy"),
        Index("idx_users_created", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<User(tg_id={self.tg_id}, balance={self.balance}, energy={self.energy})>"


class Upgrade(Base):
    __tablename__ = "upgrades"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)

    upgrade_type: Mapped[str] = mapped_column(String(50), nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    bonus_tap_power: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    bonus_max_energy: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    bonus_passive: Mapped[float] = mapped_column(Numeric(10, 4), default=0, nullable=False)

    purchased_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="upgrades")

    __table_args__ = (Index("idx_upgrades_user_type", "user_id", "upgrade_type", unique=True),)

    def __repr__(self) -> str:
        return f"<Upgrade(user_id={self.user_id}, type={self.upgrade_type}, level={self.level})>"


class ComboCode(Base):
    __tablename__ = "combo_codes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    bonus_multiplier: Mapped[float] = mapped_column(Numeric(3, 2), default=2.0, nullable=False)
    duration_hours: Mapped[int] = mapped_column(Integer, default=6, nullable=False)

    valid_from: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    valid_until: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    __table_args__ = (Index("idx_combo_validity", "valid_from", "valid_until"),)

    def __repr__(self) -> str:
        return f"<ComboCode(code={self.code}, valid={self.valid_from} to {self.valid_until})>"
