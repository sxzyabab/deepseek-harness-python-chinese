'各自拥有的会话业务定义'
from ...异常 import 对话错误
from .定义注册表 import 会话定义注册表

__all__=['会话事件注册表']

def 断言目标成对(定义):
    'target 和 buildViewNode 必须一起有或一起没有'
    有目标=定义.get('target') is not None
    有构建=定义.get('buildViewNode') is not None
    if 有目标!=有构建:
        raise 对话错误('conversation Definition "'+定义['kind']+'" must declare target and buildViewNode together')

class 会话事件注册表(会话定义注册表):
    '按事件类型预计算候选'
    def __init__(自身,上下文):
        '空路由'
        super().__init__(上下文)
        自身.回退=None
        自身.路由={}
        自身.不限=[]
        自身.表={}

    def register(自身,定义):
        '登记一份有唯一名字的业务定义'
        断言目标成对(定义)
        return 自身.登记定义(
            定义['kind'],
            自身.解析(定义),
            'conversation Definition "'+定义['kind']+'" is already registered',
            'uiConversation.events.register('+repr(定义['kind'])+')',
        )

    def registerFallback(自身,输入):
        '只在没有普通定义命中时使用的唯一回退'
        断言目标成对(输入)
        if 输入.get('target') is None:
            raise 对话错误('conversation fallback Definition must declare a target')
        if 自身.回退 is not None:
            raise 对话错误('conversation fallback Definition is already registered')
        定义=自身.解析(输入)
        def 挂上():
            '放上回退，拆除时若仍是这一份就拿掉'
            自身.回退=定义
            自身.刷新()
            def 拆():
                '不是这一份就不动'
                if 自身.回退 is not 定义:
                    return
                自身.回退=None
                自身.刷新()
            return 拆
        拆除=自身.ctx.effect(挂上,'uiConversation.events.registerFallback('+repr(定义['kind'])+')')
        def 再拆():
            '幂等拆除'
            if callable(拆除):
                拆除()
        return 再拆

    def fallbackEntry(自身):
        '当前回退'
        return 自身.回退

    def forEvent(自身,类型):
        '这个事件类型的候选。没有专门路由时用不受限集合'
        if 类型 in 自身.路由:
            return 自身.路由[类型]
        return 自身.不限

    def 解析(自身,输入):
        '函数形式原样。表形式收成按类型查找'
        if callable(输入.get('match')):
            return 输入
        表={}
        for 类型,匹配 in 输入['match'].items():
            表[类型]=匹配
        定义=dict(输入)
        def 匹配(事件,定义=定义,表=表):
            '表里没有这个类型就是不匹配'
            函=表.get(事件['type'])
            if 函 is None:
                return None
            return 函(事件)
        定义['match']=匹配
        自身.表[id(定义)]=表
        return 定义

    def 刷新(自身):
        '按注册顺序重建路由'
        路由={}
        不限=[]
        for 定义 in 自身.定义表.values():
            表=自身.表.get(id(定义))
            if 表 is None:
                路由项={'definition':定义,'match':定义['match']}
                不限.append(路由项)
                for 候选 in 路由.values():
                    候选.append(路由项)
            else:
                for 类型,匹配 in 表.items():
                    候选=路由.get(类型)
                    if 候选 is None:
                        候选=list(不限)
                        路由[类型]=候选
                    候选.append({'definition':定义,'match':匹配})
        自身.路由=路由
        自身.不限=不限
        会话定义注册表.刷新(自身)
