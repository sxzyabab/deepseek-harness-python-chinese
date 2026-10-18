import json#序列化
from ...基础设施.通用工具 import 紧凑json编码
from .剪贴板 import 写剪贴板#复制
from .菜单 import 菜单,处理菜单#复制菜单

样式表='''
.Json树{--json-tree-property:#881391;--json-tree-string:#c41a16;--json-tree-number:#1c00cf;--json-tree-keyword:#1c00cf;--json-tree-punctuation:#202124;min-width:0;overflow:auto;position:relative;color:var(--dsw-alias-label-primary);background:var(--dsw-alias-bg-layer-1);font:12px/16px var(--ds-font-family-code);display:flex;flex-direction:column}
body[data-ds-dark-theme] .Json树{--json-tree-property:#5db0d7;--json-tree-string:#f28b82;--json-tree-number:#99c8ff;--json-tree-keyword:#99c8ff;--json-tree-punctuation:#e8eaed}
.Json树行{position:relative;box-sizing:border-box;min-height:16px;padding:0 0 0 10px;white-space:pre-wrap;overflow-wrap:anywhere;display:flex;flex-direction:column}
.Json树行 .本行{display:flex;flex-direction:row;gap:4px}
'''

def 确保样式(文档):
    'Json 树样式按文档只插一次'
    if 文档.getElementById('Json树样式') is None:
        样式=文档.createElement('style')
        样式.id='Json树样式'
        样式.textContent=样式表
        文档.head.appendChild(样式)

__all__=['Json树','处理Json树','处理Json树节点','默认标签','对象预览上限','数组预览上限','预览深度上限','样式表']#仅中文公开名

对象预览上限=4#对象折叠预览键数
数组预览上限=5#数组折叠预览项数
预览深度上限=2#预览递归深度

默认标签={#内置文案
    'copyValue':'Copy value',#复制原值
    'copyJson':'Copy JSON',#复制紧凑 JSON
    'copyPath':'Copy property path',#复制路径
    'copyPrettyJson':'Copy pretty JSON',#复制美化 JSON
    'copyCompactJson':'Copy compact JSON',#对象紧凑 JSON
    'copied':'Copied',#已复制
    'copyFailed':'Copy failed',#失败
    'collapseNode':'Collapse JSON node',#收起
    'expandNode':'Expand JSON node',#展开
}#结束默认

def 可展开值(值):#对象或数组（非 Date）
    '排除 None 与非容器'
    if 值 is None:#空
        return False#不可
    if isinstance(值,(dict,list,tuple)):#容器
        return True#可
    return False#其余不可

def 列出条目(值):#键值对列表
    '数组下标作键；对象取键'
    if isinstance(值,(list,tuple)):#数组
        return [(str(下标),项) for 下标,项 in enumerate(值)]#下标键
    if isinstance(值,dict):#对象
        return [(键,值[键]) for 键 in 值.keys()]#自有键
    return []#非容器

def 括号对(值):#开闭括号
    '数组 []，对象 {}'
    return ('[',']') if isinstance(值,(list,tuple)) else ('{','}')#括号

def 原始预览(值):#叶子预览节点
    '结构化叶子视图'
    if 值 is None:#null
        return {'kind':'keyword','text':'null'}#关键字
    if isinstance(值,str):#字符串
        return {'kind':'string','text':紧凑json编码(值)}#引号串
    if isinstance(值,bool):#布尔
        return {'kind':'keyword','text':'true' if 值 else 'false'}#关键字
    if isinstance(值,(int,float)) and not isinstance(值,bool):#数字
        return {'kind':'number','text':str(值)}#数字
    if isinstance(值,bytes):#字节
        return {'kind':'other','text':repr(值)}#其它
    return {'kind':'other','text':str(值)}#其它

def 预览值(值,深度):#折叠预览
    '深度触顶则省略'
    if not 可展开值(值):#叶子
        return 原始预览(值)#叶子
    是数组=isinstance(值,(list,tuple))#数组
    项列表=列出条目(值)#条目
    上限=数组预览上限 if 是数组 else 对象预览上限#上限
    开,闭=括号对(值)#括号
    if 深度>=预览深度上限:#触顶
        return {'kind':'preview','open':开,'close':闭,'parts':[{'kind':'ellipsis','text':'…'}]}#省略
    部件=[]#可见段
    for 下标,(键,项) in enumerate(项列表[:上限]):#可见
        if 下标>0:#逗号
            部件.append({'kind':'punct','text':', '})#分隔
        if not 是数组:#对象键
            部件.append({'kind':'previewProperty','text':键})#键
            部件.append({'kind':'punct','text':': '})#冒号
        部件.append(预览值(项,深度+1))#递归
    if len(项列表)>上限:#截断
        部件.append({'kind':'ellipsis','text':', …'})#省略尾
    return {'kind':'preview','open':开,'close':闭,'parts':部件}#预览

def 叶子值(值):#展开行叶子
    '结构化叶子'
    if 值 is None:#null
        return {'kind':'keyword','text':'null'}#关键字
    if isinstance(值,str):#字符串
        return {'kind':'string','text':紧凑json编码(值)}#串
    if isinstance(值,bool):#布尔
        return {'kind':'keyword','text':'true' if 值 else 'false'}#关键字
    if isinstance(值,(int,float)) and not isinstance(值,bool):#数字
        return {'kind':'number','text':str(值)}#数字
    return {'kind':'other','text':str(值)}#其它

def 字段文(字段):#空键显示
    '空串显示为引号空'
    return '""' if 字段=='' else 字段#字段

def 路径标识(路径):#稳定 id
    '数字与字符串分段'
    段列表=[]#段
    for 段 in 路径:#逐段
        if isinstance(段,int):#数字
            段列表.append('n'+str(段))#n 段
        else:#字符串
            文=str(段)#文
            段列表.append('s'+str(len(文))+':'+文)#s 段
    return '/'.join(段列表)#拼接

def 格式路径(路径):#展示路径
    '$ 起；合法标识符用点，否则下标'
    结果='$'#根
    for 段 in 路径:#逐段
        if isinstance(段,int):#数组下标
            结果+='['+str(段)+']'#下标
        elif 段 and (段[0].isalpha() or 段[0] in '_$') and all((c.isalnum() or c in '_$') for c in 段):#合法标识符
            结果+='.'+段#点访问
        else:#需引号下标
            结果+='['+紧凑json编码(段)+']'#下标
    return 结果#路径

def 复制文本(目标,模式):#按模式取复制串
    'path/prettyJson/json/value'
    if 模式=='path':#路径
        return 格式路径(目标['path'])#路径
    if 模式=='prettyJson':#美化
        return json.dumps(目标['value'],ensure_ascii=False,separators=(',',':'),allow_nan=False,indent=2)#美化
    if 模式=='json':#紧凑
        return 紧凑json编码(目标['value'])#紧凑
    值=目标['value']#原值
    if isinstance(值,str):#字符串原样
        return 值#原
    if 值 is None:#null
        return 'null'#字面
    return 紧凑json编码(值)#其余 JSON

def 合并标签(覆盖):#合并文案
    '缺省字段保留内置'
    出=dict(默认标签)#拷贝
    if 覆盖 is not None:#有覆盖；空 dict 仍可合并
        出.update(覆盖)#合并
    return 出#标签

def 值复制菜单项(标签):#叶子复制菜单
    'value/json/path'
    return [#三项
        {'id':'value','label':标签['copyValue']},#原值
        {'id':'json','label':标签['copyJson']},#JSON
        {'id':'path','label':标签['copyPath']},#路径
    ]#结束

def 对象复制菜单项(标签):#对象复制菜单
    'prettyJson/json/path'
    return [#三项
        {'id':'prettyJson','label':标签['copyPrettyJson']},#美化
        {'id':'json','label':标签['copyCompactJson']},#紧凑
        {'id':'path','label':标签['copyPath']},#路径
    ]#结束

def 处理Json树节点(window,属性):
    '画出字段、值或括号。有 parent 就挂上去'
    文档=window.document
    确保样式(文档)
    组件=属性['组件']
    盒=文档.createElement('div')
    盒.className='Json树行'
    def 清空(节点):
        while 节点.firstElementChild is not None:
            节点.firstElementChild.remove()
    def 预览文(节点):
        '预览收成一段文字'
        if 节点['kind']=='preview':
            中=''.join(预览文(部) for 部 in 节点['parts'])
            return 节点['open']+中+节点['close']
        return 节点['text'] if 'text' in 节点 else ''
    def 进入(事件):
        '记复制目标'
        组件.悬停本行()
    盒.addEventListener('mouseenter',进入)
    def 加重(父,文):
        标=文档.createElement('span')
        标.textContent=文
        父.appendChild(标)
    def 重画():
        '按展开态重画这一行和子行'
        容器=可展开值(组件.值)
        项列表=列出条目(组件.值) if 容器 else []
        可展=len(项列表)>0
        清空(盒)
        本行=文档.createElement('div')
        本行.className='本行'
        if 可展:
            文=组件.标签['collapseNode'] if 组件.已展开 else 组件.标签['expandNode']
            def 点切换(事件):
                组件.切换()
                重画()
            def 聚焦(事件):
                组件.认领本制表()
            钮=文档.createElement('button')
            钮.type='button'
            钮.textContent=文
            钮.addEventListener('click',点切换)
            钮.addEventListener('focus',聚焦)
            本行.appendChild(钮)
        if 组件.字段 is not None:
            加重(本行,字段文(组件.字段)+':')
        if 容器 is False:
            加重(本行,叶子值(组件.值)['text'])
        elif 可展 is False:
            开,闭=括号对(组件.值)
            加重(本行,开+闭)
        elif 组件.已展开 is False:
            加重(本行,预览文(预览值(组件.值,0)))
        else:
            加重(本行,括号对(组件.值)[0])
        if 组件.末项 is False:
            加重(本行,',')
        盒.appendChild(本行)
        if 可展 and 组件.已展开:
            开,闭=括号对(组件.值)
            for 下标,(键,项) in enumerate(项列表):
                子路径=组件.路径+[下标 if isinstance(组件.值,(list,tuple)) else 键]
                子=Json树节点(键,项,子路径,组件.标签,下标==len(项列表)-1,False,组件.制表标识,组件.认领制表,组件.行悬停,window)
                子节点=子.渲染()
                if 子节点 is not None:
                    盒.appendChild(子节点)
            加重(盒,闭)
    重画()
    if 'parent' in 属性:
        属性['parent'].appendChild(盒)
    return 盒

class Json树节点:#树内一行
    '展开态本地持有；产出结构化行'
    def __init__(自身,字段,值,路径,标签,末项,初始展开,制表标识,认领制表,行悬停,window=None):#构造
        '记下行参数。构造不画'
        自身.字段=字段#字段名或 None
        自身.值=值#节点值
        自身.路径=list(路径)#路径
        自身.标签=标签#文案
        自身.末项=末项#是否末项
        自身.已展开=初始展开#展开
        自身.制表标识=制表标识#当前制表 id
        自身.认领制表=认领制表#认领回调
        自身.行悬停=行悬停#悬停回调
        自身.窗口=window
        自身.根=None

    def 切换(自身):#展开/收起
        '翻转展开'
        自身.已展开=not 自身.已展开#翻

    def 认领本制表(自身):
        '展开钮获焦时认领制表'
        自身.认领制表(路径标识(自身.路径))#认领

    def 悬停本行(自身):
        '行悬停记复制目标'
        自身.行悬停(自身.路径,自身.值)#悬停

    def 渲染(自身):#画出一行
        '拆掉旧行，再画一次'
        if 自身.根 is not None:
            自身.根.remove()
        自身.根=处理Json树节点(自身.窗口,{'组件':自身})
        return 自身.根

def 处理Json树(window,属性):
    '画出括号和节点，悬停时画出复制。无数据返回 None。有 parent 就挂上去'
    文档=window.document
    确保样式(文档)
    组件=属性['组件']
    数据=属性['data'] if 'data' in 属性 else None
    if 数据 is None:
        return None
    标签=组件.标签()
    顶展=属性['expandTopLevel'] is not False if 'expandTopLevel' in 属性 else True
    可复制=属性['copyable'] is not False if 'copyable' in 属性 else True
    根项=列出条目(数据)
    根=文档.createElement('div')
    根.className='Json树'
    类名=属性['className'] if 'className' in 属性 else None
    if isinstance(类名,str) and 类名!='':
        根.className=根.className+' '+类名
    无障碍=属性['label'] if 'label' in 属性 else 'JSON'
    if 无障碍 is None:
        无障碍='JSON'
    根.setAttribute('aria-label',str(无障碍))
    复制区=文档.createElement('div')
    复制区.className='Json复制'
    def 清空(节点):
        while 节点.firstElementChild is not None:
            节点.firstElementChild.remove()
    def 造钮(文,点):
        钮=文档.createElement('button')
        钮.type='button'
        钮.textContent=文
        def 点击(事件,回调=点):
            回调()
        钮.addEventListener('click',点击)
        return 钮
    def 刷新复制():
        '有复制目标时画出按钮和菜单'
        清空(复制区)
        if 可复制 is False or 组件.复制目标 is None:
            return
        是对象=可展开值(组件.复制目标['value'])
        if 组件.复制态=='copied':
            标题=标签['copied']
        elif 组件.复制态=='failed':
            标题=标签['copyFailed']
        elif 是对象:
            标题=标签['copyPrettyJson']
        else:
            标题=标签['copyValue']
        def 点默认():
            组件.点按复制()
            刷新复制()
        复制区.appendChild(造钮(标题,点默认))
        def 点菜单():
            组件.打开复制菜单()
            刷新复制()
        复制区.appendChild(造钮('…',点菜单))
        if 组件.复制菜单开 is False:
            return
        def 选定(模式):
            组件.复制(模式)
            组件.复制菜单开=False
            刷新复制()
        菜单节点=处理菜单(window,{
            'open':True,
            'items':对象复制菜单项(标签) if 是对象 else 值复制菜单项(标签),
            'onSelect':选定,
            'window':window,
            '菜单':菜单({
                'open':True,
                'items':对象复制菜单项(标签) if 是对象 else 值复制菜单项(标签),
                'onSelect':选定,
                'window':window,
            }),
        })
        if 菜单节点 is not None:
            复制区.appendChild(菜单节点)
    def 悬停并刷新(路径,值):
        组件.行悬停(路径,值)
        刷新复制()
    根.appendChild(复制区)
    if 顶展:
        开,闭=括号对(数据)
        括号=文档.createElement('span')
        括号.textContent=开
        def 进入根(事件):
            悬停并刷新([],数据)
        括号.addEventListener('mouseenter',进入根)
        根.appendChild(括号)
        for 下标,(键,值) in enumerate(根项):
            路径=[下标 if isinstance(数据,(list,tuple)) else 键]
            节点=Json树节点(键,值,路径,标签,下标==len(根项)-1,False,组件.制表标识,组件.认领制表,悬停并刷新,window)
            画出=节点.渲染()
            if 画出 is not None:
                根.appendChild(画出)
        闭标=文档.createElement('span')
        闭标.textContent=闭
        根.appendChild(闭标)
    else:
        节点=Json树节点(None,数据,[],标签,True,True,组件.制表标识,组件.认领制表,悬停并刷新,window)
        画出=节点.渲染()
        if 画出 is not None:
            根.appendChild(画出)
    def 离开(事件):
        if 组件.复制菜单开 is False:
            组件.清复制()
            刷新复制()
    根.addEventListener('mouseleave',离开)
    刷新复制()
    if 'parent' in 属性:
        属性['parent'].appendChild(根)
    return 根

class Json树:#只读 JSON 检查树
    '可选顶层固定展开与复制动作'
    def __init__(自身,属性=None,**关键字参数):#构造
        '合并 props 与本地复制态'
        自身.属性=dict(属性 if 属性 is not None else {})#基础
        自身.属性.update(关键字参数)#覆盖
        自身.复制目标=None#当前复制行
        自身.复制态='idle'#idle/copied/failed
        自身.复制菜单开=False#菜单
        自身.制表标识=自身.初制表()#制表
        自身.根=None

    def 更新(自身,属性):#刷新
        '刷新 props；数据变则重置复制与制表'
        旧=自身.属性['data'] if 'data' in 自身.属性 else None#旧数据
        自身.属性=dict(属性)#最新
        if (自身.属性['data'] if 'data' in 自身.属性 else None) is not 旧:#数据换；身份 is not
            自身.复制目标=None
            自身.复制态='idle'
            自身.复制菜单开=False#关
            自身.制表标识=自身.初制表()#重算

    def 标签(自身):#合并文案
        'Partial 覆盖'
        return 合并标签(自身.属性['labels'] if 'labels' in 自身.属性 else None)#标签

    def 初制表(自身):#初始制表 id
        '顶层展开取首可展项；否则根'
        数据=自身.属性['data'] if 'data' in 自身.属性 else None#数据
        顶展=自身.属性['expandTopLevel'] if 'expandTopLevel' in 自身.属性 else True#顶展缺省 True
        if 数据 is None:#无
            return None#无
        根项=列出条目(数据)#根条目
        if 顶展:#顶层展开
            for 下标,(键,值) in enumerate(根项):#找首可展
                if 可展开值(值) and len(列出条目(值))>0:#可展
                    段=下标 if isinstance(数据,(list,tuple)) else 键#段
                    return 路径标识([段])#id
            return None#无
        if 可展开值(数据) and len(根项)>0:#根可展
            return 路径标识([])#根
        return None#无

    def 认领制表(自身,标识):#认领制表
        '记下'
        自身.制表标识=标识#写

    def 行悬停(自身,路径,值):#悬停行
        '可复制且菜单未开时记目标'
        可复制=自身.属性['copyable'] if 'copyable' in 自身.属性 else True#缺省可复制
        if 可复制 is False or 自身.复制菜单开:#不可
            return#跳
        自身.复制目标={'path':list(路径),'value':值}#目标
        自身.复制态='idle'#重置反馈

    def 清复制(自身):
        '关菜单并清'
        自身.复制目标=None
        自身.复制态='idle'
        自身.复制菜单开=False#关

    def 悬停根(自身):
        '顶层括号悬停'
        数据=自身.属性['data'] if 'data' in 自身.属性 else None#根值
        自身.行悬停([],数据)#悬停

    def 点按复制(自身,模式=None):
        '无模式则按目标形态选默认'
        if 自身.复制目标 is None:#无目标
            return#跳
        if 模式 is None:#默认
            是对象=可展开值(自身.复制目标['value'])#对象
            模式='prettyJson' if 是对象 else 'value'#默认模式
        自身.复制(模式)#执行

    def 打开复制菜单(自身):
        '右键打开复制菜单'
        自身.复制菜单开=True#开

    def 复制(自身,模式):#执行复制
        '写剪贴板并反馈'
        if 自身.复制目标 is None:#无目标
            return#跳
        文=复制文本(自身.复制目标,模式)#文本
        if 写剪贴板(文):#成功
            自身.复制态='copied'#成功
        else:#失败
            自身.复制态='failed'#失败

    def 渲染(自身):#画出树
        '拆掉旧树，再画一次'
        if 自身.根 is not None:
            自身.根.remove()
        绘制=dict(自身.属性)
        绘制['组件']=自身
        自身.根=处理Json树(自身.属性['window'],绘制)
        return 自身.根

    def __call__(自身,属性=None,**关键字参数):#调用形
        '对齐 React'
        if 属性 is not None or len(关键字参数)>0:
            合并=dict(属性 if 属性 is not None else {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()