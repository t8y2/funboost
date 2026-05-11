import json
from typing import List, Optional,Union
from sqlmodel import SQLModel, Session, select,create_engine
from sqlalchemy import Engine, or_, and_
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

    __mongo_collection__ = None        # pymongo.collection.Collection（同步）
    __async_mongo_collection__ = None   # motor.motor_asyncio.AsyncIOMotorCollection（异步）

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

    @classmethod
    def bulk_upsert(cls, items, unique_fields=None, engine=None):
        # type: (List[SpiderItem], List[str], Engine) -> List[SpiderItem]
        unique_fields = unique_fields or cls.__default_upsert_unique_fields__
        if not unique_fields:
            raise ValueError(f"{cls.__name__} 未设置 __default_upsert_unique_fields__，且调用 bulk_upsert 时未传 unique_fields")
        if not items:
            return []
        eng = engine or cls._get_class_engine()
        results = []
        with cls._get_session(eng) as session:
            if len(unique_fields) == 1:
                col = getattr(cls, unique_fields[0])
                vals = [getattr(it, unique_fields[0]) for it in items]
                stmt = select(cls).where(col.in_(vals))
            else:
                conditions = [
                    and_(*[getattr(cls, f) == getattr(it, f) for f in unique_fields])
                    for it in items
                ]
                stmt = select(cls).where(or_(*conditions))
            existing_map = {
                tuple(getattr(rec, f) for f in unique_fields): rec
                for rec in session.exec(stmt).all()
            }
            for item in items:
                key = tuple(getattr(item, f) for f in unique_fields)
                existing = existing_map.get(key)
                if existing:
                    for k, v in item.to_dict(exclude_unset=True).items():
                        setattr(existing, k, v)
                    session.add(existing)
                    results.append(existing)
                else:
                    session.add(item)
                    results.append(item)
            session.commit()
            for r in results:
                session.refresh(r)
        return results

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

    @classmethod
    async def aio_bulk_upsert(cls, items, unique_fields=None):
        # type: (List[SpiderItem], List[str]) -> List[SpiderItem]
        unique_fields = unique_fields or cls.__default_upsert_unique_fields__
        if not unique_fields:
            raise ValueError(f"{cls.__name__} 未设置 __default_upsert_unique_fields__，且调用 aio_bulk_upsert 时未传 unique_fields")
        if not items:
            return []
        factory = cls._get_async_session_factory()
        results = []
        async with factory() as session:
            if len(unique_fields) == 1:
                col = getattr(cls, unique_fields[0])
                vals = [getattr(it, unique_fields[0]) for it in items]
                stmt = select(cls).where(col.in_(vals))
            else:
                conditions = [
                    and_(*[getattr(cls, f) == getattr(it, f) for f in unique_fields])
                    for it in items
                ]
                stmt = select(cls).where(or_(*conditions))
            result = await session.execute(stmt)
            existing_map = {
                tuple(getattr(rec, f) for f in unique_fields): rec
                for rec in result.scalars().all()
            }
            for item in items:
                key = tuple(getattr(item, f) for f in unique_fields)
                existing = existing_map.get(key)
                if existing:
                    for k, v in item.to_dict(exclude_unset=True).items():
                        setattr(existing, k, v)
                    session.add(existing)
                    results.append(existing)
                else:
                    session.add(item)
                    results.append(item)
            await session.commit()
            for r in results:
                await session.refresh(r)
        return results

    # ---------- MongoDB 同步 ----------
    def _to_mongo_doc(self):
        doc = self.to_dict()
        if doc.get('id') is None:
            doc.pop('id', None)
        return doc

    @classmethod
    def _resolve_mongo_coll(cls, collection=None):
        coll = collection if collection is not None else cls.__mongo_collection__
        if coll is None:
            raise RuntimeError(f"{cls.__name__} 未设置 __mongo_collection__，请在类上配置或传入 collection 参数")
        return coll

    @classmethod
    def _resolve_async_mongo_coll(cls, collection=None):
        coll = collection if collection is not None else cls.__async_mongo_collection__
        if coll is None:
            raise RuntimeError(f"{cls.__name__} 未设置 __async_mongo_collection__，请在类上配置或传入 collection 参数")
        return coll

    @classmethod
    def ensure_mongo_indexes(cls, collection=None, unique=True):
        """根据 __default_upsert_unique_fields__ 在 MongoDB 集合上创建索引（同步）"""
        unique_fields = cls.__default_upsert_unique_fields__
        if not unique_fields:
            logger.warning(f"{cls.__name__} 未设置 __default_upsert_unique_fields__，跳过索引创建")
            return
        coll = cls._resolve_mongo_coll(collection)
        import pymongo as _pymongo
        index_keys = [(f, _pymongo.ASCENDING) for f in unique_fields]
        index_name = coll.create_index(index_keys, unique=unique)
        logger.info(f"MongoDB 索引已创建: {coll.full_name} -> {index_name} (fields={unique_fields}, unique={unique})")
        return index_name

    @classmethod
    async def aio_ensure_mongo_indexes(cls, collection=None, unique=True):
        """根据 __default_upsert_unique_fields__ 在 MongoDB 集合上创建索引（异步）"""
        unique_fields = cls.__default_upsert_unique_fields__
        if not unique_fields:
            logger.warning(f"{cls.__name__} 未设置 __default_upsert_unique_fields__，跳过索引创建")
            return
        coll = cls._resolve_async_mongo_coll(collection)
        import pymongo as _pymongo
        index_keys = [(f, _pymongo.ASCENDING) for f in unique_fields]
        index_name = await coll.create_index(index_keys, unique=unique)
        logger.info(f"MongoDB 索引已创建: {coll.full_name} -> {index_name} (fields={unique_fields}, unique={unique})")
        return index_name

    def mongo_save(self, collection=None):
        coll = self.__class__._resolve_mongo_coll(collection)
        doc = self._to_mongo_doc()
        return coll.insert_one(doc)

    def mongo_upsert(self, unique_fields=None, collection=None):
        unique_fields = unique_fields or self.__class__.__default_upsert_unique_fields__
        if not unique_fields:
            raise ValueError(f"{self.__class__.__name__} 未设置 __default_upsert_unique_fields__，且调用 mongo_upsert 时未传 unique_fields")
        coll = self.__class__._resolve_mongo_coll(collection)
        doc = self._to_mongo_doc()
        filter_dict = {f: doc[f] for f in unique_fields}
        return coll.update_one(filter_dict, {"$set": doc}, upsert=True)

    @classmethod
    def mongo_bulk_upsert(cls, items, unique_fields=None, collection=None):
        unique_fields = unique_fields or cls.__default_upsert_unique_fields__
        if not unique_fields:
            raise ValueError(f"{cls.__name__} 未设置 __default_upsert_unique_fields__，且调用 mongo_bulk_upsert 时未传 unique_fields")
        if not items:
            return None
        coll = cls._resolve_mongo_coll(collection)
        from pymongo import UpdateOne
        ops = []
        for item in items:
            doc = item._to_mongo_doc()
            filter_dict = {f: doc[f] for f in unique_fields}
            ops.append(UpdateOne(filter_dict, {"$set": doc}, upsert=True))
        return coll.bulk_write(ops)

    # ---------- MongoDB 异步 ----------
    async def aio_mongo_save(self, collection=None):
        coll = self.__class__._resolve_async_mongo_coll(collection)
        doc = self._to_mongo_doc()
        return await coll.insert_one(doc)

    async def aio_mongo_upsert(self, unique_fields=None, collection=None):
        unique_fields = unique_fields or self.__class__.__default_upsert_unique_fields__
        if not unique_fields:
            raise ValueError(f"{self.__class__.__name__} 未设置 __default_upsert_unique_fields__，且调用 aio_mongo_upsert 时未传 unique_fields")
        coll = self.__class__._resolve_async_mongo_coll(collection)
        doc = self._to_mongo_doc()
        filter_dict = {f: doc[f] for f in unique_fields}
        return await coll.update_one(filter_dict, {"$set": doc}, upsert=True)

    @classmethod
    async def aio_mongo_bulk_upsert(cls, items, unique_fields=None, collection=None):
        unique_fields = unique_fields or cls.__default_upsert_unique_fields__
        if not unique_fields:
            raise ValueError(f"{cls.__name__} 未设置 __default_upsert_unique_fields__，且调用 aio_mongo_bulk_upsert 时未传 unique_fields")
        if not items:
            return None
        coll = cls._resolve_async_mongo_coll(collection)
        from pymongo import UpdateOne
        ops = []
        for item in items:
            doc = item._to_mongo_doc()
            filter_dict = {f: doc[f] for f in unique_fields}
            ops.append(UpdateOne(filter_dict, {"$set": doc}, upsert=True))
        return await coll.bulk_write(ops)