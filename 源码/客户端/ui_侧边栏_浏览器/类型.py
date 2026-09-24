__all__=['桌面浏览器租约标识','桌面浏览器预约','桌面浏览器打开请求','桌面浏览器桥']

#常量
桌面浏览器预约={'lease':None,'partition':''}#进程内已批准存储分区
桌面浏览器打开请求={'lease':None,'url':''}#已有宾客打开 HTTP(S) 页
桌面浏览器桥={'acquire':None,'release':None,'onOpenRequested':None}#源站范围操作，不穿过 Electron 对象

#工具
def 桌面浏览器租约标识(标识):
    """主进程签发的宾客预约身份，不做校验。"""
    return 标识
