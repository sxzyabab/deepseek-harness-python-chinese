"""原生可执行文件在求值模型代码前需要的启动环境名。"""
__all__=['启动环境名']#仅中文公开名

启动环境名=frozenset([#原生可执行查找、Windows 系统路径与沙箱临时路径
    'PATH','PATHEXT','SYSTEMROOT','WINDIR','TEMP','TMP',#保留在 OS 环境中的启动名
])#启动环境名结束
