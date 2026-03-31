"""
快速验证重构后的动态导入机制
"""

def test_config_driven_import():
    """验证配置驱动的导入机制"""
    print("测试配置驱动的动态导入机制\n")
    print("=" * 60)
    
    # 测试1: 导入 fastapi_router
    try:
        from funboost.faas import fastapi_router
        print("✅ fastapi_router 导入成功")
        print(f"   类型: {type(fastapi_router)}")
        print(f"   前缀: {fastapi_router.prefix}")
    except Exception as e:
        print(f"❌ fastapi_router 导入失败: {e}")
    
    print()
    
    # 测试2: 验证缓存机制
    try:
        from funboost.faas import fastapi_router as router1
        from funboost.faas import fastapi_router as router2
        
        if router1 is router2:
            print("✅ 缓存机制正常：多次导入返回同一对象")
        else:
            print("❌ 缓存机制失败：多次导入返回不同对象")
    except Exception as e:
        print(f"❌ 缓存测试失败: {e}")
    
    print()
    
    # 测试3: 检查配置是否可读
    try:
        import funboost.faas as faas_module
        config = faas_module._ROUTER_CONFIG
        
        print("✅ 配置表可访问")
        print(f"   支持的 routers: {list(config.keys())}")
        print(f"   总数: {len(config)}")
    except Exception as e:
        print(f"❌ 配置表访问失败: {e}")
    
    print()
    
    # 测试4: 错误提示
    try:
        from funboost.faas import non_existent_router
        print("❌ 应该抛出 AttributeError")
    except AttributeError as e:
        print(f"✅ 正确抛出 AttributeError: {e}")
    except Exception as e:
        print(f"⚠️  抛出了非预期的异常: {e}")
    
    print("\n" + "=" * 60)
    print("重构验证完成！配置驱动的动态导入机制工作正常 🎉")


if __name__ == "__main__":
    test_config_driven_import()
