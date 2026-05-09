import json
from typing import List, Optional,Union
from sqlmodel import SQLModel, Session, select,create_engine
from sqlalchemy import Engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker
from funboost.core.loggers import get_funboost_file_logger

logger = get_funboost_file_logger('funspider.item')

class SpiderItem(SQLModel, table=False):
    """
    爬虫 Item 基类 – 同步/异步双引擎。
    子类通过 __engine__ 绑定同步数据库，__async_engine__ 绑定异步数据库。
    """

    __engine__: Optional[Engine] = None  # 同步数据库引擎
    __async_engine__: Optional[AsyncEngine] = None  # 异步数据库引擎
    __async_session_factory__ = None  # 异步会话工厂（懒加载）
    __default_upsert_unique_fields__: List[str] = []  # upsert 去重字段默认值，子类可覆盖。你如果不写的话 upsert时候需要传递 unique_fields 参数。

    @classmethod
    def _get_class_engine(cls) -> Engine:
        if cls.__engine__ is not None:
            return cls.__engine__
        from sqlmodel import create_engine
        return create_engine("sqlite:///funspider_default.db")

    @classmethod
    def _get_class_async_engine(cls):
        if cls.__async_engine__ is not None:
            return cls.__async_engine__
        raise RuntimeError(f"{cls.__name__} 未设置 __async_engine__，无法使用异步方法。")

    @classmethod
    def _get_async_session_factory(cls):
        if cls.__async_session_factory__ is None:
            engine = cls._get_class_async_engine()
            cls.__async_session_factory__ = sessionmaker(
                engine, class_=AsyncSession, expire_on_commit=False
            )
        return cls.__async_session_factory__

    @classmethod
    def create_table(cls):
        eng = cls._get_class_engine()
        SQLModel.metadata.create_all(eng, tables=[cls.__table__])
        logger.info(f"表 {cls.__tablename__} 已创建 (引擎: {eng.url})")

    @classmethod
    def _get_session(cls, engine: Engine):
        return Session(engine)

    def _resolve_engine(self, engine: Engine = None) -> Engine:
        if engine is not None:
            return engine
        return self.__class__._get_class_engine()

    def to_dict(self, exclude_unset: bool = False) -> dict:
        if hasattr(self, "model_dump"):
            return self.model_dump(exclude_unset=exclude_unset)
        return self.dict(exclude_unset=exclude_unset)

    def to_json(self, exclude_unset: bool = False) -> str:
        return json.dumps(self.to_dict(exclude_unset=exclude_unset), ensure_ascii=False)

    # ---------- 同步 ----------
    def insert(self, engine: Engine = None):
        eng = self._resolve_engine(engine)
        with self._get_session(eng) as session:
            session.add(self)
            session.commit()
            session.refresh(self)
        return self

    def upsert(self, unique_fields: List[str] = None, engine: Engine = None):
        unique_fields = unique_fields or self.__class__.__default_upsert_unique_fields__
        if not unique_fields:
            raise ValueError(f"{self.__class__.__name__} 未设置 __default_upsert_unique_fields__，且调用 upsert 时未传 unique_fields")
        eng = self._resolve_engine(engine)
        with self._get_session(eng) as session:
            filters = {f: getattr(self, f) for f in unique_fields}
            stmt = select(type(self)).filter_by(**filters)
            existing = session.exec(stmt).first()
            if existing:
                for key, val in self.to_dict(exclude_unset=True).items():
                    setattr(existing, key, val)
                session.add(existing)
                session.commit()
                session.refresh(existing)
                return existing
            session.add(self)
            session.commit()
            session.refresh(self)
            return self

    # ---------- 异步 ----------
    async def aio_insert(self):
        factory = self.__class__._get_async_session_factory()
        async with factory() as session:
            session.add(self)
            await session.commit()
            await session.refresh(self)
        return self

    async def aio_upsert(self, unique_fields: List[str] = None):
        unique_fields = unique_fields or self.__class__.__default_upsert_unique_fields__
        if not unique_fields:
            raise ValueError(f"{self.__class__.__name__} 未设置 __default_upsert_unique_fields__，且调用 aio_upsert 时未传 unique_fields")
        factory = self.__class__._get_async_session_factory()
        async with factory() as session:
            filters = {f: getattr(self, f) for f in unique_fields}
            stmt = select(type(self)).filter_by(**filters)
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            if existing:
                for key, val in self.to_dict(exclude_unset=True).items():
                    setattr(existing, key, val)
                session.add(existing)
                await session.commit()
                await session.refresh(existing)
                return existing
            session.add(self)
            await session.commit()
            await session.refresh(self)
            return self