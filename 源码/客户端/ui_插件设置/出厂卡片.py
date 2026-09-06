"""三张出厂插件卡片视图：终端 / Agent 循环 / 网页搜索。

对齐上游 BashCard / AgentLoopCard / WebSearchCard。公开面仅中文名。
"""
from .分区视图 import 插件卡片#卡片壳
from .字段 import 取值字段,密钥字段#字段控件

__all__=['终端卡片','智能体循环卡片','网页搜索卡片']#仅中文公开名

def 读卡片状态(属性,钩名):
    """注入面提供 hooks.<钩名>；快照是 dict。"""
    return 属性['hooks'][钩名].getSnapshot()#快照

def 投影取值(翻译,字段名,字段态,编辑,复位,禁用=False,数字=False):#投影取值字段视图
    """用字段控件渲染一行。"""
    def 点编辑(文,某=字段名):#编辑
        """把键入交给表单。"""
        if 编辑 is not None:#有
            编辑(某,文)#编辑
    def 点复位(某=字段名):#复位
        """把清除手势交给表单。"""
        if 复位 is not None:#有
            复位(某)#复位
    return 取值字段({#控件
        'id':字段名,#id
        'label':字段态['label'] if 'label' in 字段态 else None,#标签
        'hint':字段态['hint'] if 'hint' in 字段态 else None,#提示
        'text':字段态['text'] if 'text' in 字段态 else '',#草稿
        'overridden':bool(字段态['overridden']) if 'overridden' in 字段态 else False,#覆盖
        'invalid':bool(字段态['invalid']) if 'invalid' in 字段态 else False,#非法
        'overriddenLabel':翻译('overridden'),#徽章
        'resetLabel':翻译('reset'),#复位
        'invalidLabel':翻译('invalidNumber'),#非法
        'disabled':禁用,#禁用
        'numeric':数字,#数字键盘
        'onEdit':点编辑,#编辑
        'onReset':点复位,#复位
    })()#渲染

def 投影密钥(翻译,字段态,编辑,已配,已配文案,未配文案,禁用=False):#投影密钥字段
    """只写凭证。"""
    def 点编辑(文):#编辑
        """把密钥草稿交给表单。"""
        if 编辑 is not None:#有
            编辑('apiKey',文)#编辑
    可写=字段态['writable'] if 'writable' in 字段态 else None#可写
    return 密钥字段({#控件
        'id':'apiKey',#id
        'label':字段态['label'] if 'label' in 字段态 else None,#标签
        'hint':字段态['hint'] if 'hint' in 字段态 else None,#提示
        'text':字段态['text'] if 'text' in 字段态 else '',#草稿
        'disabled':禁用 or 可写 is False,#不可写则禁
        'configured':bool(已配),#已配
        'stateLabel':已配文案 if 已配 else 未配文案,#状态
        'onEdit':点编辑,#编辑
    })()#渲染

class 终端卡片:#Shell 卡片
    """timeoutMs / maxOutputBytes。"""
    def __init__(自身,属性):#构造
        """记下 props。"""
        自身.属性=属性#合成 props
        自身.壳=插件卡片({#内嵌壳
            't':属性['t'] if 't' in 属性 else None,#文案
            'titleKey':'bashTitle',#标题键
            'descriptionKey':'bashDescription',#说明键
            'state':{},#稍后填
            'onSave':属性['save'] if 'save' in 属性 else None,#保存
            'onDiscard':属性['discard'] if 'discard' in 属性 else None,#丢弃
            'children':None,#稍后填
        })#壳结束

    def 更新(自身,属性):#props 变更
        """刷新。"""
        自身.属性=属性#最新

    def 渲染(自身):#结构化视图
        """投影字段控件。"""
        翻译=自身.属性['t']#文案
        状态=读卡片状态(自身.属性,'bashCard')#状态
        编辑=自身.属性['edit'] if 'edit' in 自身.属性 else None#编辑
        复位=自身.属性['resetField'] if 'resetField' in 自身.属性 else None#复位
        可写='writable' in 状态 and 状态['writable']#可写
        禁用=not bool(可写)#只读
        超时=状态['timeoutMs'] if 'timeoutMs' in 状态 and 状态['timeoutMs'] is not None else {}#超时字段
        上限=状态['maxOutputBytes'] if 'maxOutputBytes' in 状态 and 状态['maxOutputBytes'] is not None else {}#上限字段
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
            'onSave':自身.属性['save'] if 'save' in 自身.属性 else None,#保存
            'onDiscard':自身.属性['discard'] if 'discard' in 自身.属性 else None,#丢弃
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
        自身.壳=插件卡片({'t':属性['t'] if 't' in 属性 else None,'titleKey':'agentLoopTitle','descriptionKey':'agentLoopDescription','state':{},'onSave':属性['save'] if 'save' in 属性 else None,'onDiscard':属性['discard'] if 'discard' in 属性 else None,'children':None})#壳

    def 更新(自身,属性):#props 变更
        """刷新。"""
        自身.属性=属性#最新

    def 渲染(自身):#结构化视图
        """投影并行上限字段。"""
        翻译=自身.属性['t']#文案
        状态=读卡片状态(自身.属性,'agentLoopCard')#状态
        编辑=自身.属性['edit'] if 'edit' in 自身.属性 else None#编辑
        复位=自身.属性['resetField'] if 'resetField' in 自身.属性 else None#复位
        可写='writable' in 状态 and 状态['writable']#可写
        禁用=not bool(可写)#只读
        字段=状态['maxParallelToolCalls'] if 'maxParallelToolCalls' in 状态 and 状态['maxParallelToolCalls'] is not None else {}#字段
        字段面={**字段,'label':翻译('agentLoopMaxParallel'),'hint':翻译('agentLoopMaxParallelHint')}#补文案
        控件=[投影取值(翻译,'maxParallelToolCalls',字段面,编辑,复位,禁用,True)]#控件
        return 自身.壳({'t':翻译,'titleKey':'agentLoopTitle','descriptionKey':'agentLoopDescription','state':状态,'onSave':自身.属性['save'] if 'save' in 自身.属性 else None,'onDiscard':自身.属性['discard'] if 'discard' in 自身.属性 else None,'children':{'fields':控件}})#壳

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
        自身.壳=插件卡片({'t':属性['t'] if 't' in 属性 else None,'titleKey':'webSearchTitle','descriptionKey':'webSearchDescription','state':{},'onSave':属性['save'] if 'save' in 属性 else None,'onDiscard':属性['discard'] if 'discard' in 属性 else None,'children':None})#壳

    def 更新(自身,属性):#props 变更
        """刷新。"""
        自身.属性=属性#最新

    def 渲染(自身):#结构化视图
        """投影搜索字段与密钥徽章。"""
        翻译=自身.属性['t']#文案
        状态=读卡片状态(自身.属性,'webSearchCard')#状态
        编辑=自身.属性['edit'] if 'edit' in 自身.属性 else None#编辑
        复位=自身.属性['resetField'] if 'resetField' in 自身.属性 else None#复位
        可写='writable' in 状态 and 状态['writable']#可写
        禁用=not bool(可写)#只读
        地址=状态['baseURL'] if 'baseURL' in 状态 and 状态['baseURL'] is not None else {}#端点
        次数=状态['maxUses'] if 'maxUses' in 状态 and 状态['maxUses'] is not None else {}#次数
        密钥=状态['apiKey'] if 'apiKey' in 状态 and 状态['apiKey'] is not None else {}#密钥
        地址面={**地址,'label':翻译('webSearchBaseUrl'),'hint':翻译('webSearchBaseUrlHint')}#补文案
        次数面={**次数,'label':翻译('webSearchMaxUses'),'hint':翻译('webSearchMaxUsesHint')}#补文案
        密钥面={**密钥,'label':翻译('webSearchApiKey'),'hint':翻译('webSearchApiKeyHint'),'writable':状态['apiKeyWritable'] if 'apiKeyWritable' in 状态 else None}#补文案
        已配=状态['apiKeyConfigured'] if 'apiKeyConfigured' in 状态 else None#已配
        控件=[#字段
            投影密钥(翻译,密钥面,编辑,已配,翻译('webSearchApiKeySet'),翻译('webSearchApiKeyUnset'),禁用),#密钥
            投影取值(翻译,'baseURL',地址面,编辑,复位,禁用),#端点
            投影取值(翻译,'maxUses',次数面,编辑,复位,禁用,True),#次数
        ]#控件结束
        return 自身.壳({'t':翻译,'titleKey':'webSearchTitle','descriptionKey':'webSearchDescription','state':状态,'onSave':自身.属性['save'] if 'save' in 自身.属性 else None,'onDiscard':自身.属性['discard'] if 'discard' in 自身.属性 else None,'children':{'fields':控件}})#壳

    def __call__(自身,属性=None):#组件调用形
        """对齐 React 调用。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
