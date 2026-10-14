from nicegui import ui as 界面
from ..异常 import 页面失败文案,贴出失败
from .文案 import 命名空间,中文 as 对话文案
from ...ui_聊天.客户端.聊天.消息项 import 模型重试行,回合错行,回合顶格行
from .压缩项 import 压缩项#压缩
from .上下文注入行 import 上下文注入行#上下文
from .命令节点视图 import 命令节点视图,手动压缩节点视图#命令
from .回合尾节点视图 import 回合尾节点视图#回合尾

__all__=['登记聊天节点渲染器','未知节点视图','上下文消息节点视图','压缩节点视图','重试节点视图','回合错误节点视图','回合满令牌节点视图']#仅中文公开名

def 恒等翻译(键,参数=None):
    '无文案表时返回键本身'
    return 键#键即文案

class 上下文消息节点视图:
    '委托注入行，复用实例保展开'

    def __init__(自身,属性=None):
        '记下 props 与行'
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.行=上下文注入行()#行
        自身.画面=None#可反复清空的画面
        自身.渲染()#槽位只调用构造，这里就要画

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性 if 属性 is not None else {}#新

    def 渲染(自身):
        '抽 data 交注入行'
        属性=自身.属性#props
        节点=属性['node'] if 'node' in 属性 and 属性['node'] is not None else {}#节点
        数据=节点['data'] if 'data' in 节点 and 节点['data'] is not None else 节点#数据
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        自身.画面失败=None
        if 自身.画面 is not None:
            try:
                自身.画面.clear()
            except Exception as 错误:
                自身.画面=None
                自身.画面失败=页面失败文案(错误)
        if 自身.画面 is None:#新建
            自身.画面=界面.column().classes('上下文消息')#行
        自身.画面.clear()#清空
        with 自身.画面:#行
            贴出失败(自身)
            自身.行.更新({#注入
                'content':数据['content'] if 'content' in 数据 else None,#内容
                'source':数据['source'] if 'source' in 数据 else None,#源
                'provenance':数据['provenance'] if 'provenance' in 数据 else None,#出处
                'form':数据['form'] if 'form' in 数据 else None,#形态
                't':翻译,#文案
            })#更新
            自身.行.渲染()#自己画

    def __call__(自身,属性=None):
        '对齐 React'
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲

class 压缩节点视图:
    '复用压缩项保展开'

    def __init__(自身,属性=None):
        '记下'
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.项=压缩项()#项
        自身.画面=None#可反复清空的画面
        自身.渲染()#槽位只调用构造，这里就要画

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性 if 属性 is not None else {}#新

    def 渲染(自身):
        '压缩项'
        属性=自身.属性#props
        节点=属性['node'] if 'node' in 属性 and 属性['node'] is not None else {}#节点
        数据=节点['data'] if 'data' in 节点 and 节点['data'] is not None else 节点#数据
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        自身.画面失败=None
        if 自身.画面 is not None:
            try:
                自身.画面.clear()
            except Exception as 错误:
                自身.画面=None
                自身.画面失败=页面失败文案(错误)
        if 自身.画面 is None:#新建
            自身.画面=界面.column().classes('压缩节点')#项
        自身.画面.clear()#清空
        with 自身.画面:#项
            贴出失败(自身)
            自身.项.更新({'node':数据,'t':翻译})#更新
            自身.项.渲染()#自己画

    def __call__(自身,属性=None):
        '对齐'
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲

class 重试节点视图:
    '当前环'

    def __init__(自身,属性=None):
        '记下'
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.行=模型重试行()#行
        自身.画面=None#可反复清空的画面
        自身.渲染()#槽位只调用构造，这里就要画

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性 if 属性 is not None else {}#新

    def 渲染(自身):
        '重试行'
        属性=自身.属性#props
        节点=属性['node'] if 'node' in 属性 and 属性['node'] is not None else {}#节点
        数据=节点['data'] if 'data' in 节点 and 节点['data'] is not None else {}#数据
        当前=数据['current'] if 'current' in 数据 and 数据['current'] is not None else 数据#当前
        态=当前['retryState'] if 'retryState' in 当前 else None#态
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        自身.画面失败=None
        if 自身.画面 is not None:
            try:
                自身.画面.clear()
            except Exception as 错误:
                自身.画面=None
                自身.画面失败=页面失败文案(错误)
        if 自身.画面 is None:#新建
            自身.画面=界面.column().classes('重试节点')#行
        自身.画面.clear()#清空
        with 自身.画面:#行
            贴出失败(自身)
            自身.行.更新({'node':当前,'active':态=='scheduled','t':翻译})#更新
            自身.行.渲染()#自己画

    def __call__(自身,属性=None):
        '对齐'
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲

class 回合错误节点视图:
    '错误行'

    def __init__(自身,属性=None):
        '记下'
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.行=回合错行()#行
        自身.画面=None#可反复清空的画面
        自身.渲染()#槽位只调用构造，这里就要画

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性 if 属性 is not None else {}#新

    def 渲染(自身):
        '错行'
        属性=自身.属性#props
        节点=属性['node'] if 'node' in 属性 and 属性['node'] is not None else {}#节点
        数据=节点['data'] if 'data' in 节点 and 节点['data'] is not None else 节点#数据
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        自身.画面失败=None
        if 自身.画面 is not None:
            try:
                自身.画面.clear()
            except Exception as 错误:
                自身.画面=None
                自身.画面失败=页面失败文案(错误)
        if 自身.画面 is None:#新建
            自身.画面=界面.column().classes('回合错误')#行
        自身.画面.clear()#清空
        with 自身.画面:#行
            贴出失败(自身)
            自身.行.更新({'node':数据,'t':翻译})#更新
            自身.行.渲染()#自己画

    def __call__(自身,属性=None):
        '对齐'
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲

class 回合满令牌节点视图:
    '满令牌'

    def __init__(自身,属性=None):
        '记下'
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.行=回合顶格行()#行
        自身.画面=None#可反复清空的画面
        自身.渲染()#槽位只调用构造，这里就要画

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性 if 属性 is not None else {}#新

    def 渲染(自身):
        '顶格'
        翻译=自身.属性['t'] if 't' in 自身.属性 else 恒等翻译#文案
        自身.画面失败=None
        if 自身.画面 is not None:
            try:
                自身.画面.clear()
            except Exception as 错误:
                自身.画面=None
                自身.画面失败=页面失败文案(错误)
        if 自身.画面 is None:#新建
            自身.画面=界面.column().classes('满令牌')#行
        自身.画面.clear()#清空
        with 自身.画面:#行
            贴出失败(自身)
            自身.行.更新({'t':翻译})#更新
            自身.行.渲染()#自己画

    def __call__(自身,属性=None):
        '对齐'
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲

class 未知节点视图:
    'JSON 回退'

    def __init__(自身,属性=None):
        '记下'
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.画面=None#可反复清空的画面
        自身.渲染()#槽位只调用构造，这里就要画

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性 if 属性 is not None else {}#新

    def 渲染(自身):
        '画出未知表面的标签和载荷。'
        属性=自身.属性#props
        原译=属性['t'] if 't' in 属性 and 属性['t'] is not None else None#宿主文案
        def 翻译(键,参数=None):
            '属性上的 t 优先，否则用本包中文词典。'
            if 原译 is not None:#宿主
                if 参数 is None:#无参数
                    return 原译(键)#译
                return 原译(键,参数)#带参数
            if 键 not in 对话文案:#词典没有
                return 键#键
            文本=对话文案[键]#词条
            if 参数 is None:#无参数
                return 文本#原文
            for 名 in 参数:#替换占位
                文本=文本.replace('{'+名+'}',str(参数[名]))#替换
            return 文本#译完
        节点=属性['node'] if 'node' in 属性 and 属性['node'] is not None else {}#节点
        数据=节点['data'] if 'data' in 节点 and 节点['data'] is not None else {}#数据
        载荷=数据['data'] if 'data' in 数据 else 数据#载荷
        面种=数据['type'] if 'type' in 数据 else (节点['kind'] if 'kind' in 节点 else None)#种
        自身.画面失败=None
        if 自身.画面 is not None:
            try:
                自身.画面.clear()
            except Exception as 错误:
                自身.画面=None
                自身.画面失败=页面失败文案(错误)
        if 自身.画面 is None:#新建
            自身.画面=界面.column().classes('未知节点')#视图
        自身.画面.clear()#清空
        with 自身.画面:#视图
            贴出失败(自身)
            界面.label(翻译('message.unknownSurface',{'type':面种}))#标签
            if 载荷 is not None:#有载荷
                界面.label(str(载荷))#载荷

    def __call__(自身,属性=None):
        '对齐'
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲

def 登记聊天节点渲染器(上下文):
    'inject 各 kind 渲染器，含命令子席与回合尾链/动作席'
    槽=上下文.slots#槽
    def 挂(键,组件,子=None):
        'inject+register；默认参钉死本轮选项，防闭包晚绑定'
        选项={'name':'conversation.chat.node','key':键,'locale':命名空间}#选项
        if 子 is not None:#有子席
            选项['children']=子#子
        def 注入(钉选项=选项,钉组件=组件):
            'register 本键'
            return 槽.register(钉选项,钉组件)#挂
        槽.inject('conversation.chat.node',注入)#注入
    挂('context',上下文消息节点视图)#上下文
    挂('command',命令节点视图,{'conversation.chat.commandview':{'kind':'keyed','scope':'session'}})#命令+子席
    挂('manual-compaction',手动压缩节点视图)#手动压缩
    挂('compaction',压缩节点视图)#压缩
    挂('model-retry',重试节点视图)#重试
    挂('turn-error',回合错误节点视图)#错误
    挂('turn-max-tokens',回合满令牌节点视图)#满令牌
    挂('turn-tail',回合尾节点视图,{#回合尾+子席
        'conversation.chat.turnTail':{'kind':'chain','scope':'session'},#尾链
        'conversation.chat.assistant-actions':{'kind':'list','scope':'session'},#动作列表
    })#尾
    挂('unknown',未知节点视图)#未知
