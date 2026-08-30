"""不可信助手 Markdown 渲染面。

对齐上游 `ui-primitives/src/markdown/MarkdownText.tsx`。公开面仅中文名。
流式：增量解析器冻结除尾两块外的块；定稿：含数学全量解析+脚注区。
"""
from .解析 import 解析GFM,解析GFM含数学#两臂文法
from .增量 import 增量Markdown解析器#流式增量
from .渲染 import (#渲染管线
    建引用目标,收集引用目标,渲染块们,包块子节点,渲染脚注区,
)#渲染

__all__=['Markdown文本','定稿渲染','流式渲染器']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 定稿渲染(文本,代码文案=None,文件提及=None):#一次定稿全量渲染
    """含数学解析、引用收集、脚注区。"""
    根=解析GFM含数学(文本)#定稿臂
    子=取字段(根,'children') or []#顶层块
    目标=建引用目标()#空表
    收集引用目标(子,目标)#收定义
    上下文={#渲染上下文
        'streaming':False,#定稿
        'codeLabels':代码文案,#围栏文案
        'fileMentions':文件提及,#文件提及
        'targets':目标,#引用表
        'footnoteOrder':[],#脚注序
        'footnoteCounts':{},#脚注计数
    }#结束
    定位=[{'node':节点,'key':下标} for 下标,节点 in enumerate(子)]#带 key
    块=包块子节点(渲染块们(定位,上下文),False)#块+换行
    区=渲染脚注区(上下文)#脚注
    if 区 is None:#无脚注
        return 块#仅块
    return 块+['\n',区]#块+区

class 流式渲染器:#一份增长消息的流式态
    """冻结块缓存视图；尾部每帧重渲；脚注序号沿冻结延续。"""

    def __init__(自身,代码文案=None):#构造
        """文案变了要换实例（上游同）。"""
        自身.代码文案=代码文案#围栏文案
        自身.解析器=增量Markdown解析器(解析GFM)#流式臂
        自身.代际=-1#代
        自身.已冻计数=0#已缓存冻结数
        自身.冻结元素=[]#缓存视图
        自身.冻结目标=建引用目标()#冻结侧引用
        自身.冻结脚注序=[]#冻结脚注序
        自身.冻结脚注计={}#冻结脚注计
        自身.上次文本=None#幂等键
        自身.上次结果=[]#缓存结果

    def 渲染(自身,文本):#累计文本→视图列表
        """同文本幂等。"""
        if 文本==自身.上次文本:#相同
            return 自身.上次结果#缓存
        分割=自身.解析器.更新(文本)#增量分割
        冻结=分割['frozen']#已冻
        尾=分割['tail']#尾
        代=分割['generation']#代
        if 代!=自身.代际:#换代
            自身.代际=代#记
            自身.已冻计数=0#清
            自身.冻结元素=[]#清
            自身.冻结目标=建引用目标()#清
            自身.冻结脚注序=[]#清
            自身.冻结脚注计={}#清
        新冻=冻结[自身.已冻计数:]#本帧新冻
        收集引用目标([取字段(b,'node') for b in 新冻],自身.冻结目标)#收新冻定义
        帧目标={#本帧可见引用
            'definitions':dict(自身.冻结目标['definitions']),#拷定义
            'footnotes':dict(自身.冻结目标['footnotes']),#拷脚注
        }#结束
        收集引用目标([取字段(b,'node') for b in 尾],帧目标)#加尾定义
        if len(新冻)>0:#有新冻
            冻上下文={#冻结渲染上下文
                'streaming':True,#流式
                'codeLabels':自身.代码文案,#文案
                'fileMentions':None,#流式无提及
                'targets':帧目标,#引用
                'footnoteOrder':自身.冻结脚注序,#续序
                'footnoteCounts':自身.冻结脚注计,#续计
            }#结束
            批=list(自身.冻结元素)#拷
            for 元 in 渲染块们(新冻,冻上下文):#新冻块
                if len(批)>0:#间隔
                    批.append('\n')#换行
                批.append(元)#元素
            自身.冻结元素=批#写回
            自身.已冻计数=len(冻结)#推进
        尾上下文={#尾渲染上下文
            'streaming':True,#流式
            'codeLabels':自身.代码文案,#文案
            'fileMentions':None,#流式无提及
            'targets':帧目标,#引用
            'footnoteOrder':list(自身.冻结脚注序),#拷序（尾可增）
            'footnoteCounts':dict(自身.冻结脚注计),#拷计
        }#结束
        出=list(自身.冻结元素)#起
        for 元 in 渲染块们(尾,尾上下文):#尾块
            if len(出)>0:#间隔
                出.append('\n')#换行
            出.append(元)#元素
        区=渲染脚注区(尾上下文)#脚注（含冻结序号）
        if 区 is not None:#有
            if len(出)>0:#间隔
                出.append('\n')#换行
            出.append(区)#区
        自身.上次文本=文本#记
        自身.上次结果=出#记
        return 出#结果

class Markdown文本:#助手 Markdown
    """streaming 走流式渲染器；否则定稿。"""

    def __init__(自身,属性=None,**关键字参数):#构造
        """合并 props；流式器惰性建。"""
        自身.属性=dict(属性 or {})#基础
        自身.属性.update(关键字参数)#覆盖
        自身.流式器=None#惰性
        自身.流式文案键=None#文案指纹

    def 更新(自身,属性):#刷新
        """刷新 props。"""
        自身.属性=dict(属性)#最新

    def 渲染(自身):#结构树
        """产出 markdown 子树。"""
        属性=自身.属性#props
        文本=取字段(属性,'text') or ''#源
        流式=bool(取字段(属性,'streaming',False))#流式?
        文案=取字段(属性,'codeLabels')#围栏文案
        提及=取字段(属性,'fileMentions')#文件提及
        if 流式:#流式臂
            键=id(文案)#文案身份
            if 自身.流式器 is None or 自身.流式文案键!=键:#需重建
                自身.流式器=流式渲染器(文案)#新
                自身.流式文案键=键#记
            子=自身.流式器.渲染(文本)#渲
        else:#定稿
            自身.流式器=None#丢流式态
            自身.流式文案键=None#清
            子=定稿渲染(文本,文案,提及)#定稿
        return {#视图
            'type':'markdown-text',#类型
            'streaming':流式,#流式
            'children':子,#子树
            'cssModule':'Markdown文本.module.css',#样式
        }#结束

    def __call__(自身,属性=None,**关键字参数):#组件调用形
        """对齐 React。"""
        if 属性 is not None or 关键字参数:#有
            合并=dict(属性 or {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()#渲
