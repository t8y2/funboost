# -*- coding: utf-8 -*-
"""
funspider SpiderItem bulk_upsert / aio_bulk_upsert 回归测试
使用 SQLite 内存数据库，无需外部依赖。
"""
import asyncio
import unittest
from typing import ClassVar, Optional, List

from sqlmodel import Field, create_engine, SQLModel
from sqlalchemy.ext.asyncio import create_async_engine

from funboost.contrib.funspider import SpiderItem


SYNC_ENGINE = create_engine("sqlite:///:memory:", echo=False)
ASYNC_ENGINE = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)


class FakeNews(SpiderItem, table=True):
    __tablename__: ClassVar[str] = "fake_news"
    __engine__ = SYNC_ENGINE
    __async_engine__ = ASYNC_ENGINE
    __default_upsert_unique_fields__ = ["news_id"]

    id: Optional[int] = Field(default=None, primary_key=True)
    news_id: int = Field(unique=True)
    title: str = ""
    score: int = 0


class MultiKeyItem(SpiderItem, table=True):
    """多唯一字段场景"""
    __tablename__: ClassVar[str] = "multi_key"
    __engine__ = SYNC_ENGINE
    __async_engine__ = ASYNC_ENGINE
    __default_upsert_unique_fields__ = ["source", "ext_id"]

    id: Optional[int] = Field(default=None, primary_key=True)
    source: str
    ext_id: int
    content: str = ""


def _create_tables():
    SQLModel.metadata.create_all(SYNC_ENGINE)


async def _create_async_tables():
    async with ASYNC_ENGINE.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


class TestBulkUpsertSync(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        _create_tables()

    def test_insert_all_new(self):
        items = [
            FakeNews(news_id=1001, title="A", score=10),
            FakeNews(news_id=1002, title="B", score=20),
            FakeNews(news_id=1003, title="C", score=30),
        ]
        results = FakeNews.bulk_upsert(items)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].title, "A")
        self.assertIsNotNone(results[0].id)

    def test_update_existing(self):
        FakeNews(news_id=2001, title="OLD", score=1).insert()
        items = [FakeNews(news_id=2001, title="NEW", score=99)]
        results = FakeNews.bulk_upsert(items)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "NEW")
        self.assertEqual(results[0].score, 99)

    def test_mixed_insert_and_update(self):
        FakeNews(news_id=3001, title="exist", score=5).insert()
        items = [
            FakeNews(news_id=3001, title="updated", score=50),
            FakeNews(news_id=3002, title="brand_new", score=60),
        ]
        results = FakeNews.bulk_upsert(items)
        self.assertEqual(len(results), 2)
        titles = {r.title for r in results}
        self.assertIn("updated", titles)
        self.assertIn("brand_new", titles)

    def test_empty_list(self):
        results = FakeNews.bulk_upsert([])
        self.assertEqual(results, [])

    def test_missing_unique_fields_raises(self):
        class NoUniqueItem(SpiderItem, table=True):
            __tablename__: ClassVar[str] = "no_unique"
            __engine__ = SYNC_ENGINE
            id: Optional[int] = Field(default=None, primary_key=True)
            val: str = ""

        SQLModel.metadata.create_all(SYNC_ENGINE)
        with self.assertRaises(ValueError):
            NoUniqueItem.bulk_upsert([NoUniqueItem(val="x")])

    def test_multi_unique_fields(self):
        MultiKeyItem(source="github", ext_id=1, content="old").insert()
        items = [
            MultiKeyItem(source="github", ext_id=1, content="updated"),
            MultiKeyItem(source="github", ext_id=2, content="new_one"),
            MultiKeyItem(source="gitlab", ext_id=1, content="different_source"),
        ]
        results = MultiKeyItem.bulk_upsert(items)
        self.assertEqual(len(results), 3)
        content_set = {r.content for r in results}
        self.assertIn("updated", content_set)
        self.assertIn("new_one", content_set)
        self.assertIn("different_source", content_set)

    def test_large_batch(self):
        items = [FakeNews(news_id=9000 + i, title=f"item_{i}", score=i) for i in range(100)]
        results = FakeNews.bulk_upsert(items)
        self.assertEqual(len(results), 100)


class TestBulkUpsertAsync(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        asyncio.get_event_loop().run_until_complete(_create_async_tables())

    def _run(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    def test_aio_insert_all_new(self):
        items = [
            FakeNews(news_id=5001, title="async_A", score=10),
            FakeNews(news_id=5002, title="async_B", score=20),
        ]
        results = self._run(FakeNews.aio_bulk_upsert(items))
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].title, "async_A")

    def test_aio_update_existing(self):
        self._run(FakeNews(news_id=6001, title="old_async", score=1).aio_insert())
        items = [FakeNews(news_id=6001, title="new_async", score=88)]
        results = self._run(FakeNews.aio_bulk_upsert(items))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "new_async")
        self.assertEqual(results[0].score, 88)

    def test_aio_mixed(self):
        self._run(FakeNews(news_id=7001, title="exist_async", score=5).aio_insert())
        items = [
            FakeNews(news_id=7001, title="updated_async", score=55),
            FakeNews(news_id=7002, title="new_async_item", score=66),
        ]
        results = self._run(FakeNews.aio_bulk_upsert(items))
        self.assertEqual(len(results), 2)

    def test_aio_empty_list(self):
        results = self._run(FakeNews.aio_bulk_upsert([]))
        self.assertEqual(results, [])

    def test_aio_multi_unique_fields(self):
        self._run(MultiKeyItem(source="npm", ext_id=1, content="old_npm").aio_insert())
        items = [
            MultiKeyItem(source="npm", ext_id=1, content="updated_npm"),
            MultiKeyItem(source="npm", ext_id=2, content="new_npm"),
        ]
        results = self._run(MultiKeyItem.aio_bulk_upsert(items))
        self.assertEqual(len(results), 2)
        content_set = {r.content for r in results}
        self.assertIn("updated_npm", content_set)
        self.assertIn("new_npm", content_set)


if __name__ == '__main__':
    unittest.main()
