# ============================================================
#  pipeline/db.py  — SQLAlchemy models + session factory
# ============================================================
from sqlalchemy import (
    create_engine, Column, String, Integer, Numeric, Boolean,
    DateTime, Date, Text, ARRAY, CheckConstraint, ForeignKey,
    UniqueConstraint, func
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.pool import NullPool
from contextlib import contextmanager
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from pipeline.config import DATABASE_URL

Base = declarative_base()

# ── ORM Models ───────────────────────────────────────────────

class Staff(Base):
    __tablename__ = "staff"
    id         = Column(String(20),  primary_key=True)
    name       = Column(String(100), nullable=False)
    role       = Column(String(50),  nullable=False)
    pin_hash   = Column(String(128), nullable=False)
    active     = Column(Boolean,     default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    orders     = relationship("Order", back_populates="staff_member")


class RestaurantTable(Base):
    __tablename__ = "restaurant_tables"
    id         = Column(String(10),  primary_key=True)
    number     = Column(Integer,     nullable=False, unique=True)
    seats      = Column(Integer,     nullable=False, default=4)
    status     = Column(String(20),  nullable=False, default="available")
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    orders     = relationship("Order", back_populates="table")


class MenuCategory(Base):
    __tablename__ = "menu_categories"
    id         = Column(Integer,    primary_key=True, autoincrement=True)
    name       = Column(String(50), nullable=False, unique=True)
    sort_order = Column(Integer,    default=0)
    items      = relationship("MenuItem", back_populates="category")


class MenuItem(Base):
    __tablename__ = "menu_items"
    id          = Column(String(20),  primary_key=True)
    category_id = Column(Integer,     ForeignKey("menu_categories.id"))
    name        = Column(String(100), nullable=False)
    price       = Column(Numeric(10, 2), nullable=False)
    emoji       = Column(String(10),  default="🍽️")
    active      = Column(Boolean,     default=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), server_default=func.now())
    category    = relationship("MenuCategory", back_populates="items")


class Order(Base):
    __tablename__ = "orders"
    id         = Column(String(20),     primary_key=True)
    table_id   = Column(String(10),     ForeignKey("restaurant_tables.id"))
    staff_id   = Column(String(20),     ForeignKey("staff.id"))
    status     = Column(String(20),     nullable=False, default="pending")
    note       = Column(Text)
    subtotal   = Column(Numeric(10, 2), nullable=False, default=0)
    tax        = Column(Numeric(10, 2), nullable=False, default=0)
    total      = Column(Numeric(10, 2), nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    table          = relationship("RestaurantTable", back_populates="orders")
    staff_member   = relationship("Staff",           back_populates="orders")
    items          = relationship("OrderItem",        back_populates="order",
                                  cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"
    id           = Column(Integer,      primary_key=True, autoincrement=True)
    order_id     = Column(String(20),   ForeignKey("orders.id"), nullable=False)
    menu_item_id = Column(String(20),   ForeignKey("menu_items.id"))
    name         = Column(String(100),  nullable=False)
    price        = Column(Numeric(10,2),nullable=False)
    qty          = Column(Integer,      nullable=False)
    order        = relationship("Order", back_populates="items")


class SalesDaily(Base):
    __tablename__ = "sales_daily"
    id            = Column(Integer, primary_key=True, autoincrement=True)
    date          = Column(Date,    nullable=False, unique=True)
    total_orders  = Column(Integer, nullable=False, default=0)
    total_revenue = Column(Numeric(12, 2), nullable=False, default=0)
    avg_order_val = Column(Numeric(10, 2))
    top_item      = Column(String(100))
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
    updated_at    = Column(DateTime(timezone=True), server_default=func.now())


class SalesWeekly(Base):
    __tablename__ = "sales_weekly"
    id              = Column(Integer, primary_key=True, autoincrement=True)
    week_start      = Column(Date,    nullable=False, unique=True)
    week_end        = Column(Date,    nullable=False)
    total_orders    = Column(Integer, nullable=False, default=0)
    total_revenue   = Column(Numeric(12, 2), nullable=False, default=0)
    avg_order_val   = Column(Numeric(10, 2))
    wow_change_pct  = Column(Numeric(6, 2))
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), server_default=func.now())


class SalesMonthly(Base):
    __tablename__ = "sales_monthly"
    id              = Column(Integer, primary_key=True, autoincrement=True)
    year            = Column(Integer, nullable=False)
    month           = Column(Integer, nullable=False)
    total_orders    = Column(Integer, nullable=False, default=0)
    total_revenue   = Column(Numeric(12, 2), nullable=False, default=0)
    avg_order_val   = Column(Numeric(10, 2))
    mom_change_pct  = Column(Numeric(6, 2))
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__  = (UniqueConstraint("year", "month"),)


class AlertLog(Base):
    __tablename__ = "alert_log"
    id            = Column(Integer,     primary_key=True, autoincrement=True)
    alert_type    = Column(String(50),  nullable=False)
    period        = Column(String(20),  nullable=False)
    metric        = Column(String(50),  nullable=False)
    current_val   = Column(Numeric(12, 2))
    previous_val  = Column(Numeric(12, 2))
    change_pct    = Column(Numeric(6, 2))
    threshold_pct = Column(Numeric(6, 2))
    message       = Column(Text)
    sent_at       = Column(DateTime(timezone=True), server_default=func.now())
    channels      = Column(ARRAY(Text))


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"
    id                = Column(Integer,    primary_key=True, autoincrement=True)
    run_type          = Column(String(50), nullable=False)
    status            = Column(String(20), nullable=False)
    records_processed = Column(Integer,    default=0)
    error_message     = Column(Text)
    started_at        = Column(DateTime(timezone=True), server_default=func.now())
    finished_at       = Column(DateTime(timezone=True))


# ── Engine + Session factory ──────────────────────────────────

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # reconnect on stale connections
    pool_size=5,
    max_overflow=10,
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@contextmanager
def get_db():
    """Context manager for database sessions — always commits or rolls back."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_tables():
    """Create all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)
    print("✅  All database tables created / verified.")
