"""InputTriggerService（ctx.inputTriggers）：触发管线的根半边。

对齐上游 `ui-input-trigger/src/client/service.ts`。公开面仅中文名。
无状态源登记表加上每会话控制器映射；可变交互状态住在控制器上。
"""
from ...依赖 import cordis#外部依赖胶水
服务=cordis.服务#Cordis 服务基类
from .控制器 import 触发控制器#每会话控制器

__all__=['触发服务']#仅中文公开名

class 触发服务(服务):#ctx.inputTriggers 触发管线
    """根登记表 + 控制器解析。"""
    inject=['sessions']#依赖会话服务

    def __init__(自身,上下文):#挂到 inputTriggers
        """初始化源表与每会话控制器表。"""
        super().__init__(上下文,'inputTriggers')#以 inputTriggers 登记
        自身.源们=[]#已登记的触发源
        自身.控制器们={}#按会话身份索引的控制器

    def registerSource(自身,源):#登记一个触发源
        """trigger+name 必须唯一——重复则抛；返回拆除器。"""
        触发=源.get('trigger') if isinstance(源,dict) else getattr(源,'trigger',None)#触发字符
        名=源.get('name') if isinstance(源,dict) else getattr(源,'name',None)#源名
        for 已 in 自身.源们:#查重
            已触=已.get('trigger') if isinstance(已,dict) else getattr(已,'trigger',None)#已触发
            已名=已.get('name') if isinstance(已,dict) else getattr(已,'name',None)#已名
            if 已触==触发 and 已名==名:#重复
                raise Exception('slash source "'+str(触发)+str(名)+'" is already registered')#抛
        自身.源们.append(源)#写入花名册
        for 控 in list(自身.控制器们.values()):#通知每个已活会话
            try:#晚到源仍须预热并入词库
                控.sourceAdded(源)#通知该会话源已加入
            except Exception as 错误:#源回调故障
                print('[ui-input-trigger] source "'+str(触发)+str(名)+'" late-registration setup failed:',错误)#记错误
        def 拆():#拆除该源
            """从花名册摘掉并通知控制器。"""
            if 源 not in 自身.源们:#已拆除则幂等
                return#返回
            自身.源们.remove(源)#摘掉
            for 控 in list(自身.控制器们.values()):#通知各会话
                控.sourceRemoved(源)#拆除通知
        return 拆#拆除器

    def sessionOf(自身,作用域):#按会话取触发控制器
        """惰性；作用域拆除器会移除并拆除它。"""
        会话们=自身.ctx.get('sessions')#会话面
        if 会话们 is None:#未挂载
            raise Exception('ui-input-trigger: sessions service unavailable')#抛
        标识=会话们.scopeOf(作用域) if hasattr(会话们,'scopeOf') else getattr(作用域,'sessionId',None)#会话身份
        if 标识 is None:#必须在会话作用域内
            raise Exception('slash.sessionOf requires a session scope')#抛
        已有=自身.控制器们.get(标识)#已有则复用
        if 已有 is not None:#常驻
            return 已有#控制器
        def 名册视图():#根服务花名册视图
            """同触发字符的源，按 order 排。"""
            def 按触发(触发字符):#过滤排序
                """登记顺序保留，order 越小越前。"""
                出=[s for s in 自身.源们 if (s.get('trigger') if isinstance(s,dict) else getattr(s,'trigger',None))==触发字符]#同触发
                出.sort(key=lambda s:(s.get('order') if isinstance(s,dict) else getattr(s,'order',None)) or 0)#按 order
                return 出#列表
            return {'sources':按触发,'all':lambda:list(自身.源们)}#视图
        控=触发控制器({'actx':作用域,'sessionId':标识,'roster':名册视图()})#本会话触发控制器
        自身.控制器们[标识]=控#记入每会话表
        def 拆():#会话作用域拆除时清控制器
            """dispose 并删表。"""
            def 清():#清
                """拆除。"""
                控.dispose()#拆控制器
                自身.控制器们.pop(标识,None)#从表删除
            return 清#拆除器
        if hasattr(作用域,'effect'):#有 effect
            作用域.effect(拆,'slash: session controller')#登记
        return 控#新常驻控制器
