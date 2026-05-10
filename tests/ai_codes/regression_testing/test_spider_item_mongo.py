# -*- coding: utf-8 -*-
"""
funspider SpiderItem MongoDB 方法回归测试
连接本地 MongoDB（无密码），测试 mongo_save / mongo_upsert / mongo_bulk_upsert。
"""
import unittest
from typing import ClassVar, Optional, List

import pymongo
from sqlmodel import Field

from funboost.contrib.funspider import SpiderItem

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "funspider_test_db"

client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
db = client[DB_NAME]
coll = db["test_news"]
coll_multi = db["test_multi_key"]


class MongoNews(SpiderItem, table=False):
    __mongo_collection__ = coll
    __default_upsert_unique_fields__ = ["news_id"]

    news_id: int = 0
    title: str = ""
    score: int = 0


class MongoMultiKey(SpiderItem, table=False):
    __mongo_collection__ = coll_multi
    __default_upsert_unique_fields__ = ["source", "ext_id"]

    source: str = ""
    ext_id: int = 0
    content: str = ""


class TestMongoIndex(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        try:
            client.admin.command('ping')
        except Exception:
            raise unittest.SkipTest("MongoDB 未启动，跳过测试")

    def setUp(self):
        coll.delete_many({})
        coll.drop_indexes()

    def test_ensure_indexes_single_field(self):
        index_name = MongoNews.ensure_mongo_indexes()
        self.assertIsNotNone(index_name)
        indexes = coll.index_information()
        self.assertIn(index_name, indexes)
        self.assertTrue(indexes[index_name].get('unique'))

    def test_ensure_indexes_multi_field(self):
        coll_multi.delete_many({})
        coll_multi.drop_indexes()
        index_name = MongoMultiKey.ensure_mongo_indexes()
        self.assertIsNotNone(index_name)
        indexes = coll_multi.index_information()
        self.assertIn(index_name, indexes)
        idx_info = indexes[index_name]
        field_names = [k for k, _ in idx_info['key']]
        self.assertEqual(field_names, ['source', 'ext_id'])

    def test_ensure_indexes_non_unique(self):
        index_name = MongoNews.ensure_mongo_indexes(unique=False)
        indexes = coll.index_information()
        self.assertFalse(indexes[index_name].get('unique', False))


class TestMongoSave(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        try:
            client.admin.command('ping')
        except Exception:
            raise unittest.SkipTest("MongoDB 未启动，跳过测试")

    def setUp(self):
        coll.delete_many({})

    def test_mongo_save(self):
        item = MongoNews(news_id=1, title="hello", score=10)
        result = item.mongo_save()
        self.assertIsNotNone(result.inserted_id)
        doc = coll.find_one({"news_id": 1})
        self.assertEqual(doc["title"], "hello")
        self.assertEqual(doc["score"], 10)

    def test_mongo_save_no_sql_id(self):
        """确认 _to_mongo_doc 排除了 SQL 自增 id=None"""
        item = MongoNews(news_id=2, title="no_id")
        item.mongo_save()
        doc = coll.find_one({"news_id": 2})
        self.assertNotIn("id", doc)


class TestMongoUpsert(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        try:
            client.admin.command('ping')
        except Exception:
            raise unittest.SkipTest("MongoDB 未启动，跳过测试")

    def setUp(self):
        coll.delete_many({})
        coll_multi.delete_many({})

    def test_insert_new(self):
        item = MongoNews(news_id=10, title="new", score=5)
        result = item.mongo_upsert()
        self.assertEqual(result.upserted_id is not None, True)
        self.assertEqual(coll.count_documents({}), 1)

    def test_update_existing(self):
        MongoNews(news_id=20, title="old", score=1).mongo_upsert()
        MongoNews(news_id=20, title="updated", score=99).mongo_upsert()
        self.assertEqual(coll.count_documents({"news_id": 20}), 1)
        doc = coll.find_one({"news_id": 20})
        self.assertEqual(doc["title"], "updated")
        self.assertEqual(doc["score"], 99)

    def test_multi_unique_fields(self):
        MongoMultiKey(source="github", ext_id=1, content="old").mongo_upsert()
        MongoMultiKey(source="github", ext_id=1, content="new").mongo_upsert()
        MongoMultiKey(source="gitlab", ext_id=1, content="other").mongo_upsert()
        self.assertEqual(coll_multi.count_documents({}), 2)
        doc = coll_multi.find_one({"source": "github", "ext_id": 1})
        self.assertEqual(doc["content"], "new")


class TestMongoBulkUpsert(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        try:
            client.admin.command('ping')
        except Exception:
            raise unittest.SkipTest("MongoDB 未启动，跳过测试")

    def setUp(self):
        coll.delete_many({})

    def test_bulk_insert_new(self):
        items = [
            MongoNews(news_id=100 + i, title=f"t_{i}", score=i)
            for i in range(5)
        ]
        result = MongoNews.mongo_bulk_upsert(items)
        self.assertEqual(result.upserted_count, 5)
        self.assertEqual(coll.count_documents({}), 5)

    def test_bulk_update_existing(self):
        for i in range(3):
            MongoNews(news_id=200 + i, title=f"old_{i}", score=0).mongo_save()
        items = [
            MongoNews(news_id=200 + i, title=f"new_{i}", score=i * 10)
            for i in range(3)
        ]
        result = MongoNews.mongo_bulk_upsert(items)
        self.assertEqual(result.modified_count, 3)
        self.assertEqual(coll.count_documents({}), 3)
        doc = coll.find_one({"news_id": 201})
        self.assertEqual(doc["title"], "new_1")
        self.assertEqual(doc["score"], 10)

    def test_bulk_mixed(self):
        MongoNews(news_id=300, title="exist", score=1).mongo_save()
        items = [
            MongoNews(news_id=300, title="updated", score=50),
            MongoNews(news_id=301, title="brand_new", score=60),
        ]
        result = MongoNews.mongo_bulk_upsert(items)
        self.assertEqual(coll.count_documents({}), 2)

    def test_bulk_empty(self):
        result = MongoNews.mongo_bulk_upsert([])
        self.assertIsNone(result)

    def test_bulk_large_batch(self):
        items = [
            MongoNews(news_id=500 + i, title=f"batch_{i}", score=i)
            for i in range(100)
        ]
        result = MongoNews.mongo_bulk_upsert(items)
        self.assertEqual(result.upserted_count, 100)
        self.assertEqual(coll.count_documents({}), 100)

    def test_missing_unique_fields_raises(self):
        class NoUniqueMongoItem(SpiderItem, table=False):
            __mongo_collection__ = coll
            val: str = ""

        with self.assertRaises(ValueError):
            NoUniqueMongoItem.mongo_bulk_upsert([NoUniqueMongoItem(val="x")])

    def test_pass_collection_param(self):
        """通过参数传入 collection 而非类属性"""
        bare_coll = db["test_bare"]
        bare_coll.delete_many({})

        class BareItem(SpiderItem, table=False):
            __default_upsert_unique_fields__ = ["key"]
            key: int = 0
            data: str = ""

        items = [BareItem(key=1, data="a"), BareItem(key=2, data="b")]
        result = BareItem.mongo_bulk_upsert(items, collection=bare_coll)
        self.assertEqual(result.upserted_count, 2)


class TestMongoCleanup(unittest.TestCase):
    """测试完成后清理"""
    @classmethod
    def tearDownClass(cls):
        try:
            client.drop_database(DB_NAME)
        except Exception:
            pass


if __name__ == '__main__':
    unittest.main()
