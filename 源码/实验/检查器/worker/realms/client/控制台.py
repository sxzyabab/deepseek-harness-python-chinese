"""类型化 Client Console 事件传输上的 ConsoleBackend。"""
#对齐上游 worker/realms/client/console.ts

from .值 import Client控制台事件#Console转换

__all__=['Client控制台后端']#仅中文公开名

class Client控制台后端:#Client Console后端
    """将会话本地 Client Console 事件适配为公共 Runtime 值。"""
    def __init__(自身,目标,会话id,路由,脚本身份):#构造
        """保存路由依赖。"""
        自身.目标=目标#目标
        自身.会话id=会话id#会话
        自身.路由=路由#路由
        自身.脚本身份=脚本身份#脚本身份
        自身._拆除器=set()#拆除器集合

    def 订阅(自身,监听):#订阅
        """订阅 Client Console 事件。"""
        def 回调(事件):#转换后通知
            """映射脚本身份后投递。"""
            监听(Client控制台事件(事件,自身.脚本身份.转Runtime))#转换
        拆除=自身.路由.订阅控制台(自身.目标,自身.会话id,回调)#订阅Console
        自身._拆除器.add(拆除)#登记
        def 卸除():#拆除
            """移除本订阅。"""
            if 拆除 not in 自身._拆除器:#已无
                return#返回
            自身._拆除器.discard(拆除)#删除
            拆除()#执行
        return 卸除#拆除器

    def 清空(自身):#清空
        """Client Console 清空无操作。"""
        return#无操作

    def 关闭(自身):#关闭
        """禁用本连接的每一个活动 Console 订阅。"""
        for 拆除 in list(自身._拆除器):#全部拆除
            拆除()#执行
        自身._拆除器.clear()#清空
