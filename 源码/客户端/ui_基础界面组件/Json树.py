"""只读、令牌主题的 JSON 树。

对齐上游 `ui-primitives/src/JsonTree.tsx`。公开面仅中文名。
包无 cordis；文案经 props 注入，缺省字段保留内置默认。
"""
import json#序列化
from .剪贴板 import 写剪贴板#复制
from .菜单 import 菜单#复制菜单

__all__=['Json树','默认标签','对象预览上限','数组预览上限','预览深度上限']#仅中文公开名

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

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 可展开值(值):#对象或数组（非 Date）
    """排除 None 与非容器。"""
    if 值 is None:#空
        return False#不可
    if isinstance(值,(dict,list,tuple)):#容器
        return True#可
    return False#其余不可

def 条目们(值):#键值对列表
    """数组下标作键；对象取键。"""
    if isinstance(值,(list,tuple)):#数组
        return [(str(下标),项) for 下标,项 in enumerate(值)]#下标键
    if isinstance(值,dict):#对象
        return [(键,值[键]) for 键 in 值.keys()]#自有键
    return []#非容器

def 括号对(值):#开闭括号
    """数组 []，对象 {}。"""
    return ('[',']') if isinstance(值,(list,tuple)) else ('{','}')#括号

def 原始预览(值):#叶子预览节点
    """结构化叶子视图。"""
    if 值 is None:#null
        return {'kind':'keyword','text':'null'}#关键字
    if isinstance(值,str):#字符串
        return {'kind':'string','text':json.dumps(值,ensure_ascii=False)}#引号串
    if isinstance(值,bool):#布尔
        return {'kind':'keyword','text':'true' if 值 else 'false'}#关键字
    if isinstance(值,(int,float)) and not isinstance(值,bool):#数字
        return {'kind':'number','text':str(值)}#数字
    if isinstance(值,bytes):#字节
        return {'kind':'other','text':repr(值)}#其它
    return {'kind':'other','text':str(值)}#其它

def 预览值(值,深度):#折叠预览
    """深度触顶则省略。"""
    if not 可展开值(值):#叶子
        return 原始预览(值)#叶子
    是数组=isinstance(值,(list,tuple))#数组
    项们=条目们(值)#条目
    上限=数组预览上限 if 是数组 else 对象预览上限#上限
    开,闭=括号对(值)#括号
    if 深度>=预览深度上限:#触顶
        return {'kind':'preview','open':开,'close':闭,'parts':[{'kind':'ellipsis','text':'…'}]}#省略
    部件=[]#可见段
    for 下标,(键,项) in enumerate(项们[:上限]):#可见
        if 下标>0:#逗号
            部件.append({'kind':'punct','text':', '})#分隔
        if not 是数组:#对象键
            部件.append({'kind':'previewProperty','text':键})#键
            部件.append({'kind':'punct','text':': '})#冒号
        部件.append(预览值(项,深度+1))#递归
    if len(项们)>上限:#截断
        部件.append({'kind':'ellipsis','text':', …'})#省略尾
    return {'kind':'preview','open':开,'close':闭,'parts':部件}#预览

def 叶子值(值):#展开行叶子
    """结构化叶子。"""
    if 值 is None:#null
        return {'kind':'keyword','text':'null'}#关键字
    if isinstance(值,str):#字符串
        return {'kind':'string','text':json.dumps(值,ensure_ascii=False)}#串
    if isinstance(值,bool):#布尔
        return {'kind':'keyword','text':'true' if 值 else 'false'}#关键字
    if isinstance(值,(int,float)) and not isinstance(值,bool):#数字
        return {'kind':'number','text':str(值)}#数字
    return {'kind':'other','text':str(值)}#其它

def 字段文(字段):#空键显示
    """空串显示为引号空。"""
    return '""' if 字段=='' else 字段#字段

def 路径标识(路径):#稳定 id
    """数字与字符串分段。"""
    段们=[]#段
    for 段 in 路径:#逐段
        if isinstance(段,int):#数字
            段们.append('n'+str(段))#n 段
        else:#字符串
            文=str(段)#文
            段们.append('s'+str(len(文))+':'+文)#s 段
    return '/'.join(段们)#拼接

def 格式路径(路径):#展示路径
    """$ 起；合法标识符用点，否则下标。"""
    结果='$'#根
    for 段 in 路径:#逐段
        if isinstance(段,int):#数组下标
            结果+='['+str(段)+']'#下标
        elif 段 and (段[0].isalpha() or 段[0] in '_$') and all((c.isalnum() or c in '_$') for c in 段):#合法标识符
            结果+='.'+段#点访问
        else:#需引号下标
            结果+='['+json.dumps(段,ensure_ascii=False)+']'#下标
    return 结果#路径

def 复制文本(目标,模式):#按模式取复制串
    """path/prettyJson/json/value。"""
    if 模式=='path':#路径
        return 格式路径(目标['path'])#路径
    if 模式=='prettyJson':#美化
        return json.dumps(目标['value'],ensure_ascii=False,indent=2)#美化
    if 模式=='json':#紧凑
        return json.dumps(目标['value'],ensure_ascii=False)#紧凑
    值=目标['value']#原值
    if isinstance(值,str):#字符串原样
        return 值#原
    if 值 is None:#null
        return 'null'#字面
    return json.dumps(值,ensure_ascii=False)#其余 JSON

def 合并标签(覆盖):#合并文案
    """缺省字段保留内置。"""
    出=dict(默认标签)#拷贝
    if 覆盖:#有覆盖
        出.update(覆盖)#合并
    return 出#标签

def 值复制菜单项(标签):#叶子复制菜单
    """value/json/path。"""
    return [#三项
        {'id':'value','label':标签['copyValue']},#原值
        {'id':'json','label':标签['copyJson']},#JSON
        {'id':'path','label':标签['copyPath']},#路径
    ]#结束

def 对象复制菜单项(标签):#对象复制菜单
    """prettyJson/json/path。"""
    return [#三项
        {'id':'prettyJson','label':标签['copyPrettyJson']},#美化
        {'id':'json','label':标签['copyCompactJson']},#紧凑
        {'id':'path','label':标签['copyPath']},#路径
    ]#结束

class Json树节点:#树内一行
    """展开态本地持有；产出结构化行。"""
    def __init__(自身,字段,值,路径,标签,末项,初始展开,制表标识,认领制表,行悬停):#构造
        """记下行参数。"""
        自身.字段=字段#字段名或 None
        自身.值=值#节点值
        自身.路径=list(路径)#路径
        自身.标签=标签#文案
        自身.末项=末项#是否末项
        自身.已展开=初始展开#展开
        自身.制表标识=制表标识#当前制表 id
        自身.认领制表=认领制表#认领回调
        自身.行悬停=行悬停#悬停回调

    def 切换(自身):#展开/收起
        """翻转展开。"""
        自身.已展开=not 自身.已展开#翻

    def 渲染(自身):#结构化行
        """产出 treeitem 视图。"""
        容器=可展开值(自身.值)#容器
        项们=条目们(自身.值) if 容器 else []#条目
        可展=len(项们)>0#可展
        节点标识=路径标识(自身.路径)#id
        字段视图=None#字段
        if 自身.字段 is not None:#有字段
            字段视图={#字段
                'text':字段文(自身.字段)+':',#文
                'clickable':可展,#可点
                'onToggle':自身.切换 if 可展 else None,#切换
            }#结束
        if not 容器:#叶子
            return {#行
                'kind':'row','pathId':节点标识,'path':list(自身.路径),'value':自身.值,#身份
                'field':字段视图,'leaf':叶子值(自身.值),'comma':not 自身.末项,#叶子
                'expandable':False,'expanded':False,'children':None,#无子
            }#结束
        开,闭=括号对(自身.值)#括号
        if not 可展:#空容器
            return {#行
                'kind':'row','pathId':节点标识,'path':list(自身.路径),'value':自身.值,#身份
                'field':字段视图,'empty':{'open':开,'close':闭},'comma':not 自身.末项,#空
                'expandable':False,'expanded':False,'children':None,#无子
            }#结束
        子们=None#子树
        if 自身.已展开:#展开
            子们=[]#子
            for 下标,(键,项) in enumerate(项们):#逐项
                子路径=自身.路径+[下标 if isinstance(自身.值,(list,tuple)) else 键]#路径
                子=Json树节点(#子节点
                    键,项,子路径,自身.标签,下标==len(项们)-1,False,#参数
                    自身.制表标识,自身.认领制表,自身.行悬停,#制表与悬停
                )#结束
                子们.append(子.渲染())#渲
        return {#行
            'kind':'row','pathId':节点标识,'path':list(自身.路径),'value':自身.值,#身份
            'field':字段视图,'preview':预览值(自身.值,0),'comma':not 自身.末项,#预览
            'expandable':True,'expanded':自身.已展开,#展开
            'expander':{#展开钮
                'aria':自身.标签['collapseNode'] if 自身.已展开 else 自身.标签['expandNode'],#aria
                'tabStop':自身.制表标识==节点标识,#制表
                'onToggle':自身.切换,#切换
                'onFocus':lambda:自身.认领制表(节点标识),#认领
            },#结束
            'children':子们,#子
            'onHover':lambda:自身.行悬停(自身.路径,自身.值),#悬停
        }#结束

class Json树:#只读 JSON 检查树
    """可选顶层固定展开与复制动作。"""
    def __init__(自身,属性=None,**关键字参数):#构造
        """合并 props 与本地复制态。"""
        自身.属性=dict(属性 or {})#基础
        自身.属性.update(关键字参数)#覆盖
        自身.复制目标=None#当前复制行
        自身.复制态='idle'#idle/copied/failed
        自身.复制菜单开=False#菜单
        自身.制表标识=自身.初制表()#制表

    def 更新(自身,属性):#刷新
        """刷新 props；数据变则重置复制与制表。"""
        旧=取字段(自身.属性,'data')#旧数据
        自身.属性=dict(属性)#最新
        if 取字段(自身.属性,'data') is not 旧:#数据换
            自身.复制目标=None#清
            自身.复制态='idle'#清
            自身.复制菜单开=False#关
            自身.制表标识=自身.初制表()#重算

    def 标签(自身):#合并文案
        """Partial 覆盖。"""
        return 合并标签(取字段(自身.属性,'labels'))#标签

    def 初制表(自身):#初始制表 id
        """顶层展开取首可展项；否则根。"""
        数据=取字段(自身.属性,'data')#数据
        顶展=取字段(自身.属性,'expandTopLevel',True)#顶展
        if 数据 is None:#无
            return None#无
        根项=条目们(数据)#根条目
        if 顶展:#顶层展开
            for 下标,(键,值) in enumerate(根项):#找首可展
                if 可展开值(值) and len(条目们(值))>0:#可展
                    段=下标 if isinstance(数据,(list,tuple)) else 键#段
                    return 路径标识([段])#id
            return None#无
        if 可展开值(数据) and len(根项)>0:#根可展
            return 路径标识([])#根
        return None#无

    def 认领制表(自身,标识):#认领制表
        """记下。"""
        自身.制表标识=标识#写

    def 行悬停(自身,路径,值):#悬停行
        """可复制且菜单未开时记目标。"""
        if not 取字段(自身.属性,'copyable',True) or 自身.复制菜单开:#不可
            return#跳
        自身.复制目标={'path':list(路径),'value':值}#目标
        自身.复制态='idle'#重置反馈

    def 清复制(自身):#清复制目标
        """关菜单并清。"""
        自身.复制目标=None#清
        自身.复制态='idle'#清
        自身.复制菜单开=False#关

    def 复制(自身,模式):#执行复制
        """写剪贴板并反馈。"""
        if 自身.复制目标 is None:#无目标
            return#跳
        文=复制文本(自身.复制目标,模式)#文本
        if 写剪贴板(文):#成功
            自身.复制态='copied'#成功
        else:#失败
            自身.复制态='failed'#失败

    def 渲染(自身):#结构化视图
        """产出树 + 可选复制锚。"""
        属性=自身.属性#props
        数据=取字段(属性,'data')#数据
        if 数据 is None:#无数据
            return None#空
        标签=自身.标签()#文案
        顶展=bool(取字段(属性,'expandTopLevel',True))#顶展
        可复制=bool(取字段(属性,'copyable',True))#可复制
        根项=条目们(数据)#根条目
        子视图=[]#子
        if 顶展:#顶层展开：根括号 + 子项
            for 下标,(键,值) in enumerate(根项):#逐项
                路径=[下标 if isinstance(数据,(list,tuple)) else 键]#路径
                节点=Json树节点(#节点
                    键,值,路径,标签,下标==len(根项)-1,False,#参数
                    自身.制表标识,自身.认领制表,自身.行悬停,#回调
                )#结束
                子视图.append(节点.渲染())#渲
            开,闭=括号对(数据)#括号
            主体={#顶展体
                'mode':'expanded-top',#模式
                'openBracket':开,#开
                'closeBracket':闭,#闭
                'children':子视图,#子
                'rootValue':数据,#根值
                'onRootHover':lambda:自身.行悬停([],数据),#根悬停
            }#结束
        else:#单根节点
            节点=Json树节点(#根
                None,数据,[],标签,True,True,#参数
                自身.制表标识,自身.认领制表,自身.行悬停,#回调
            )#结束
            主体={'mode':'tree','root':节点.渲染()}#单树
        复制锚=None#复制
        if 可复制 and 自身.复制目标 is not None:#有目标
            是对象=可展开值(自身.复制目标['value'])#对象
            默认模式='prettyJson' if 是对象 else 'value'#默认
            标题=标签['copied'] if 自身.复制态=='copied' else (#标题
                标签['copyFailed'] if 自身.复制态=='failed' else (
                    标签['copyPrettyJson'] if 是对象 else 标签['copyValue']
                )
            )#结束
            菜单项=对象复制菜单项(标签) if 是对象 else 值复制菜单项(标签)#项
            复制锚={#锚
                'state':自身.复制态,#态
                'title':标题,#标题
                'defaultMode':默认模式,#默认
                'items':菜单项,#菜单
                'onCopy':lambda 模式=默认模式:自身.复制(模式),#点按
                'onMenu':lambda:setattr(自身,'复制菜单开',True),#右键
                'onSelect':自身.复制,#选定
                'onClose':自身.清复制,#关
                'menu':菜单,#菜单组件
            }#结束
        return {#视图
            'type':'json-tree',#类型
            'label':取字段(属性,'label','JSON'),#aria
            'className':取字段(属性,'className'),#定位类
            'body':主体,#主体
            'copyAnchor':复制锚,#复制
            'onLeave':自身.清复制 if not 自身.复制菜单开 else None,#离开清
            'cssModule':'Json树.module.css',#样式
        }#结束

    def __call__(自身,属性=None,**关键字参数):#调用形
        """对齐 React。"""
        if 属性 is not None or 关键字参数:#有
            合并=dict(属性 or {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()#渲
