"""工具行视图：提问 / 待办 专属 toolview 登记。

对齐上游 `ask-question-row.tsx` / `todo-row.tsx`。公开面仅中文名。
通用 ToolRow 铬仍见上游；本模块落盘摘要派生与登记 apply。
"""
import json#解析结果/参数
from .调用模型 import 派生工具行,取字段#行模型

__all__=['提问行','待办行','已答摘要','待办摘要','提问工具视图','待办工具视图']#仅中文公开名

会话命名空间='conversation'#会话词典命名空间

def 是答案(值):#答案条目形
    """对象即为答案条目候选。"""
    return isinstance(值,dict) and 值 is not None#对象

def 已答摘要(文本,翻译):#已答计数摘要
    """从结果 JSON 计已答数；无效则 None。"""
    try:#解析
        解析=json.loads(文本)#JSON
    except Exception:#失败
        return None#无效
    if not isinstance(解析,dict):#非对象
        return None#无效
    答案们=解析.get('answers')#答案表
    if not isinstance(答案们,list) or not all(是答案(a) for a in 答案们):#形不对
        return None#无效
    已答=0#计数
    for a in 答案们:#逐题
        选=a.get('selected')#选中
        自=a.get('custom')#自定义
        if (isinstance(选,list) and len(选)>0) or (isinstance(自,str) and 自!=''):#已答
            已答+=1#加
    return 翻译('ask.answered',{'answered':已答,'total':len(答案们)})#摘要

def 计划摘要(条目们):#待办计数
    """done/total/activeContent/activeExtra。"""
    完成=0#完成
    活跃内容=None#活跃正文
    活跃额外=0#并行活跃额外
    for 项 in 条目们:#逐项
        态=取字段(项,'status')#状态
        if 态=='completed':#完成
            完成+=1#加
        elif 态=='in_progress':#进行
            if 活跃内容 is None:#首个
                活跃内容=取字段(项,'content')#内容
            else:#并行
                活跃额外+=1#额外
    return {'done':完成,'total':len(条目们),'activeContent':活跃内容,'activeExtra':活跃额外}#摘要

def 待办摘要(参数原文,翻译):#待办行摘要拆分
    """text 可截断；extra 为并行活跃数。"""
    try:#解析
        解析=json.loads(参数原文)#JSON
    except Exception:#失败
        return None#回退
    if not isinstance(解析,dict):#非对象
        return None#回退
    表=解析.get('todos')#todos
    if not isinstance(表,list) or not all(isinstance(i,dict) for i in 表):#形
        return None#回退
    计=计划摘要(表)#计数
    头=翻译('todo.completed',{'done':计['done'],'total':计['total']})#头
    if 计['activeContent'] is None:#无活跃
        return {'text':头,'extra':计['activeExtra']}#仅头
    return {'text':头+' · '+str(计['activeContent']),'extra':计['activeExtra']}#带头+活跃

class 提问行:#ask_user_question 行
    """提问交互一行摘要。"""
    def __init__(自身,属性=None):#可选 props
        """记下 props。"""
        自身.属性=属性 or {}#合成

    def 更新(自身,属性):#刷新
        """刷新 props。"""
        自身.属性=属性 or {}#新

    def 渲染(自身):#结构树
        """派生摘要与状态。"""
        p=自身.属性#props
        块=取字段(p,'block')#块
        翻译=取字段(p,'t') or (lambda 键,*_a,**_k:键)#文案
        工具名=取字段(p,'toolName') or 'ask_user_question'#名
        模型=派生工具行(块 if isinstance(块,dict) else {'toolName':工具名,**dict(块 or {})})#模型
        # 修补：派生工具行用 toolName 在块上
        if not isinstance(块,dict):#对象
            模型=派生工具行({'toolName':工具名,'argsRaw':取字段(块,'argsRaw'),'kind':取字段(块,'kind'),'content':取字段(块,'content'),'error':取字段(块,'error'),'isError':取字段(块,'isError'),'call':取字段(块,'call')})#重建
        码=取字段(取字段(块,'error'),'code') if 取字段(块,'kind') is not None or (isinstance(块,dict) and 'kind' in 块) else None#错误码
        摘要=模型['summary']#摘要
        状态=模型['state']#状态
        if 码=='ASK_CANCELLED':#取消
            摘要=翻译('ask.cancelled')#取消文案
        elif 码=='ASK_ABORTED':#中断
            摘要=翻译('ask.interrupted')#中断
            状态='stopped'#停止
        elif 模型['state']=='running':#等待
            摘要=翻译('ask.waiting')#等待
        elif (isinstance(块,dict) and 'kind' in 块) and 模型['state']=='ok':#已答
            文本=''.join(取字段(b,'text','') for b in (取字段(块,'content') or []) if 取字段(b,'type')=='text')#拼文本
            摘要=已答摘要(文本,翻译) or 模型['summary']#已答或回退
        return {#结构树
            'type':'ask-question-row',#类型
            'variant':模型.get('variant'),#变体
            'title':翻译('ask.rowTitle'),#标题
            'summary':摘要,#摘要
            'body':模型.get('body'),#正文
            'output':模型.get('output'),#输出
            'state':状态,#状态
            'inspect':取字段(p,'inspect'),#检查
        }#结束

    def __call__(自身,属性=None):#调用形
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷新
        return 自身.渲染()#渲

class 待办行:#todo_write 行
    """计划更新一行摘要。"""
    def __init__(自身,属性=None):#可选 props
        """记下 props。"""
        自身.属性=属性 or {}#合成

    def 更新(自身,属性):#刷新
        """刷新 props。"""
        自身.属性=属性 or {}#新

    def 渲染(自身):#结构树
        """派生摘要。"""
        p=自身.属性#props
        块=取字段(p,'block')#块
        翻译=取字段(p,'t') or (lambda 键,*_a,**_k:键)#文案
        工具名=取字段(p,'toolName') or 'todo_write'#名
        已结算=isinstance(块,dict) and 'kind' in 块#已结算
        参数原文=(取字段(取字段(块,'call'),'argsRaw') if 已结算 else 取字段(块,'argsRaw')) or ''#参数
        模型=派生工具行({'toolName':工具名,'argsRaw':参数原文,'kind':取字段(块,'kind'),'content':取字段(块,'content'),'error':取字段(块,'error'),'isError':取字段(块,'isError'),'call':取字段(块,'call')})#模型
        摘要=待办摘要(参数原文,翻译) or {'text':模型['summary'],'extra':0}#摘要
        return {#结构树
            'type':'todo-row',#类型
            'variant':模型.get('variant'),#变体
            'title':翻译('todo.rowTitle'),#标题
            'summary':摘要['text'],#摘要
            'summarySuffix':('+'+str(摘要['extra'])) if 摘要['extra']>0 else None,#后缀
            'body':模型.get('body'),#正文
            'output':模型.get('output'),#输出
            'errorSummary':模型.get('errorSummary'),#错误
            'state':模型.get('state'),#状态
            'inspect':取字段(p,'inspect'),#检查
        }#结束

    def __call__(自身,属性=None):#调用形
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷新
        return 自身.渲染()#渲

def 提问工具视图应用(上下文):#登记提问行
    """登记 ask_user_question toolview。"""
    上下文.slots.inject('tool.call.toolview',lambda:上下文.slots.register({#登记
        'name':'tool.call.toolview','key':'ask_user_question','locale':会话命名空间,#选项
    },提问行))#组件

提问工具视图={'name':'ask-question-toolview','inject':['slots'],'apply':提问工具视图应用}#插件形

def 待办工具视图应用(上下文):#登记待办行
    """登记 todo_write toolview。"""
    上下文.slots.inject('tool.call.toolview',lambda:上下文.slots.register({#登记
        'name':'tool.call.toolview','key':'todo_write','locale':会话命名空间,#选项
    },待办行))#组件

待办工具视图={'name':'todo-toolview','inject':['slots'],'apply':待办工具视图应用}#插件形
