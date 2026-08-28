"""三张出厂插件卡片视图：终端 / Agent 循环 / 网页搜索。

对齐上游 BashCard / AgentLoopCard / WebSearchCard。公开面仅中文名。
"""
from .分区视图 import 插件卡片#卡片壳
from .字段 import 取值字段,密钥字段#字段控件

__all__=['终端卡片','智能体循环卡片','网页搜索卡片']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 读卡片状态(属性,钩名):#从 hooks 快照读卡片状态
    """优先 useXxxCard 选择器，否则 hooks 仓库。"""
    键表={'bashCard':'useBashCard','agentLoopCard':'useAgentLoopCard','webSearchCard':'useWebSearchCard'}#钩名→选择器
    选择器名=键表.get(钩名)#选择器属性名
    选择器=取字段(属性,选择器名) if 选择器名 else None#选择器
    if 选择器 is not None:#有
        return 选择器(lambda 快照:快照) or {}#快照
    钩=取字段(属性,'hooks') or {}#hooks
    仓=取字段(钩,钩名)#仓库
    if 仓 is None:#无
        return {}#空
    return 仓.getSnapshot() if hasattr(仓,'getSnapshot') else 仓#快照

def 投影取值(翻译,字段名,字段态,编辑,复位,禁用=False,数字=False):#投影取值字段视图
    """用字段控件渲染一行。"""
    return 取值字段({#控件
        'id':字段名,#id
        'label':取字段(字段态,'label'),#标签
        'hint':取字段(字段态,'hint'),#提示
        'text':取字段(字段态,'text',''),#草稿
        'overridden':bool(取字段(字段态,'overridden')),#覆盖
        'invalid':bool(取字段(字段态,'invalid')),#非法
        'overriddenLabel':翻译('overridden'),#徽章
        'resetLabel':翻译('reset'),#复位
        'invalidLabel':翻译('invalidNumber'),#非法
        'disabled':禁用,#禁用
        'numeric':数字,#数字键盘
        'onEdit':(lambda 文,某=字段名:编辑(某,文) if 编辑 else None),#编辑
        'onReset':(lambda 某=字段名:复位(某) if 复位 else None),#复位
    })()#渲染

def 投影密钥(翻译,字段态,编辑,已配,已配文案,未配文案,禁用=False):#投影密钥字段
    """只写凭证。"""
    return 密钥字段({#控件
        'id':'apiKey',#id
        'label':取字段(字段态,'label'),#标签
        'hint':取字段(字段态,'hint'),#提示
        'text':取字段(字段态,'text',''),#草稿
        'disabled':禁用 or 取字段(字段态,'writable') is False,#不可写则禁
        'configured':bool(已配),#已配
        'stateLabel':已配文案 if 已配 else 未配文案,#状态
        'onEdit':(lambda 文:编辑('apiKey',文) if 编辑 else None),#编辑
    })()#渲染

class 终端卡片:#Shell 卡片
    """timeoutMs / maxOutputBytes。"""
    def __init__(自身,属性):#构造
        """记下 props。"""
        自身.属性=属性#合成 props
        自身.壳=插件卡片({#内嵌壳
            't':取字段(属性,'t'),#文案
            'titleKey':'bashTitle',#标题键
            'descriptionKey':'bashDescription',#说明键
            'state':{},#稍后填
            'onSave':取字段(属性,'save'),#保存
            'onDiscard':取字段(属性,'discard'),#丢弃
            'children':None,#稍后填
        })#壳结束

    def 更新(自身,属性):#props 变更
        """刷新。"""
        自身.属性=属性#最新

    def 渲染(自身):#结构化视图
        """投影字段控件。"""
        翻译=取字段(自身.属性,'t',lambda 键,_=None:键)#文案
        状态=读卡片状态(自身.属性,'bashCard')#状态
        编辑=取字段(自身.属性,'edit')#编辑
        复位=取字段(自身.属性,'resetField')#复位
        禁用=not bool(取字段(状态,'writable'))#只读
        超时=取字段(状态,'timeoutMs') or {}#超时字段
        上限=取字段(状态,'maxOutputBytes') or {}#上限字段
        超时面={**超时,'label':翻译('bashTimeoutMs'),'hint':翻译('bashTimeoutMsHint')}#补文案
        上限面={**上限,'label':翻译('bashMaxOutputBytes'),'hint':翻译('bashMaxOutputBytesHint')}#补文案
        控件=[#字段行
            投影取值(翻译,'timeoutMs',超时面,编辑,复位,禁用,True),#超时
            投影取值(翻译,'maxOutputBytes',上限面,编辑,复位,禁用,True),#上限
        ]#控件结束
        return 自身.壳({#经壳渲染
            't':翻译,#文案
            'titleKey':'bashTitle',#标题
            'descriptionKey':'bashDescription',#说明
            'state':状态,#外壳状态
            'onSave':取字段(自身.属性,'save'),#保存
            'onDiscard':取字段(自身.属性,'discard'),#丢弃
            'children':{'fields':控件},#控件
        })#壳调用

    def __call__(自身,属性=None):#组件调用形
        """对齐 React 调用。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染

class 智能体循环卡片:#Agent 循环卡片
    """maxParallelToolCalls。"""
    def __init__(自身,属性):#构造
        """记下 props。"""
        自身.属性=属性#合成 props
        自身.壳=插件卡片({'t':取字段(属性,'t'),'titleKey':'agentLoopTitle','descriptionKey':'agentLoopDescription','state':{},'onSave':取字段(属性,'save'),'onDiscard':取字段(属性,'discard'),'children':None})#壳

    def 更新(自身,属性):#props 变更
        """刷新。"""
        自身.属性=属性#最新

    def 渲染(自身):#结构化视图
        """投影并行上限字段。"""
        翻译=取字段(自身.属性,'t',lambda 键,_=None:键)#文案
        状态=读卡片状态(自身.属性,'agentLoopCard')#状态
        编辑=取字段(自身.属性,'edit')#编辑
        复位=取字段(自身.属性,'resetField')#复位
        禁用=not bool(取字段(状态,'writable'))#只读
        字段=取字段(状态,'maxParallelToolCalls') or {}#字段
        字段面={**字段,'label':翻译('agentLoopMaxParallel'),'hint':翻译('agentLoopMaxParallelHint')}#补文案
        控件=[投影取值(翻译,'maxParallelToolCalls',字段面,编辑,复位,禁用,True)]#控件
        return 自身.壳({'t':翻译,'titleKey':'agentLoopTitle','descriptionKey':'agentLoopDescription','state':状态,'onSave':取字段(自身.属性,'save'),'onDiscard':取字段(自身.属性,'discard'),'children':{'fields':控件}})#壳

    def __call__(自身,属性=None):#组件调用形
        """对齐 React 调用。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染

class 网页搜索卡片:#网页搜索卡片
    """baseURL / maxUses / apiKey。"""
    def __init__(自身,属性):#构造
        """记下 props。"""
        自身.属性=属性#合成 props
        自身.壳=插件卡片({'t':取字段(属性,'t'),'titleKey':'webSearchTitle','descriptionKey':'webSearchDescription','state':{},'onSave':取字段(属性,'save'),'onDiscard':取字段(属性,'discard'),'children':None})#壳

    def 更新(自身,属性):#props 变更
        """刷新。"""
        自身.属性=属性#最新

    def 渲染(自身):#结构化视图
        """投影搜索字段与密钥徽章。"""
        翻译=取字段(自身.属性,'t',lambda 键,_=None:键)#文案
        状态=读卡片状态(自身.属性,'webSearchCard')#状态
        编辑=取字段(自身.属性,'edit')#编辑
        复位=取字段(自身.属性,'resetField')#复位
        禁用=not bool(取字段(状态,'writable'))#只读
        地址=取字段(状态,'baseURL') or {}#端点
        次数=取字段(状态,'maxUses') or {}#次数
        密钥=取字段(状态,'apiKey') or {}#密钥
        地址面={**地址,'label':翻译('webSearchBaseUrl'),'hint':翻译('webSearchBaseUrlHint')}#补文案
        次数面={**次数,'label':翻译('webSearchMaxUses'),'hint':翻译('webSearchMaxUsesHint')}#补文案
        密钥面={**密钥,'label':翻译('webSearchApiKey'),'hint':翻译('webSearchApiKeyHint'),'writable':取字段(状态,'apiKeyWritable')}#补文案
        控件=[#字段
            投影密钥(翻译,密钥面,编辑,取字段(状态,'apiKeyConfigured'),翻译('webSearchApiKeySet'),翻译('webSearchApiKeyUnset'),禁用),#密钥
            投影取值(翻译,'baseURL',地址面,编辑,复位,禁用),#端点
            投影取值(翻译,'maxUses',次数面,编辑,复位,禁用,True),#次数
        ]#控件结束
        return 自身.壳({'t':翻译,'titleKey':'webSearchTitle','descriptionKey':'webSearchDescription','state':状态,'onSave':取字段(自身.属性,'save'),'onDiscard':取字段(自身.属性,'discard'),'children':{'fields':控件}})#壳

    def __call__(自身,属性=None):#组件调用形
        """对齐 React 调用。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
