"""提问工具行：问句风味摘要行，替换通用 Tool call 卡。

对齐上游 `ui-tool/src/client/tool/toolviews/ask-question-row.tsx`。公开面仅中文名。
登记进按键 tool.call.toolview 洞；问题本身在撰写器接管面渲染。
"""
import json#解析答案 JSON
from ..文案 import 会话命名空间#conversation 词典席
from .调用模型 import 派生工具行,取字段#行模型
from .工具行 import 工具行#摘要行外壳

__all__=['提问行','提问工具视图','已答摘要','是否答案条目']#仅中文公开名

def 是否答案条目(值):#形检查一条答案
    """跨线 result JSON 的答案条目。"""
    return isinstance(值,dict) and 值 is not None#普通对象

def 已答摘要(文本,翻译):#从结果 JSON 派生已答计数摘要
    """跳过题 selected 空且无 custom；字段非法时 None。"""
    try:#解析
        解析=json.loads(文本)#JSON
    except Exception:#非 JSON
        return None#无效
    if not isinstance(解析,dict) or 解析 is None:#非对象
        return None#无效
    答案们=解析.get('answers')#答案数组
    if not isinstance(答案们,list) or not all(是否答案条目(项) for 项 in 答案们):#非法
        return None#无效
    已答=0#已答数
    for 项 in 答案们:#逐条
        已选=项.get('selected')#已选
        自定义=项.get('custom')#自定义
        if (isinstance(已选,list) and len(已选)>0) or (isinstance(自定义,str) and 自定义!=''):#已作答
            已答+=1#累计
    return 翻译('ask.answered',{'answered':已答,'total':len(答案们)}) if callable(翻译) else str(已答)+'/'+str(len(答案们))#摘要

class 提问行:#问句交互行
    """整行切换调用的 Input/Output；ToolRow 统一展开。"""

    def __init__(自身,属性=None):#记下 props
        """记下合成 props；内嵌工具行。"""
        自身.属性=属性 or {}#合成
        自身.行=工具行()#外壳

    def 更新(自身,属性):#刷新
        """刷新合成 props。"""
        自身.属性=属性#新

    def 渲染(自身):#结构树
        """派生摘要/态后交给工具行。"""
        属性=自身.属性#props
        工具名=取字段(属性,'toolName') or 'ask_user_question'#工具名
        块=取字段(属性,'block')#工具块
        翻译=取字段(属性,'t')#文案
        检查=取字段(属性,'inspect')#检查
        if isinstance(块,dict):#映射块补 toolName
            切片=dict(块)#拷贝
            if 'toolName' not in 切片 and 'name' not in 切片:#缺名
                切片['toolName']=工具名#写入
        else:#对象块
            切片=块#原样
        模型=派生工具行(切片)#行模型
        摘要=模型['summary']#默认摘要
        状态=模型['state']#默认态
        已结算=(isinstance(块,dict) and 'kind' in 块) or (not isinstance(块,dict) and hasattr(块,'kind'))#是否已结算
        码=取字段(取字段(块,'error'),'code') if 已结算 else None#错误码
        if 码=='ASK_CANCELLED':#用户取消整组
            摘要=翻译('ask.cancelled') if callable(翻译) else 'ask.cancelled'#取消文案
        elif 码=='ASK_ABORTED':#回合中断
            摘要=翻译('ask.interrupted') if callable(翻译) else 'ask.interrupted'#中断
            状态='stopped'#琥珀中止
        elif 模型['state']=='running':#等待中
            摘要=翻译('ask.waiting') if callable(翻译) else 'ask.waiting'#等待
        elif 已结算 and 模型['state']=='ok':#已答
            内容=取字段(块,'content') or []#内容块
            文本=''.join(取字段(b,'text') or '' for b in 内容 if 取字段(b,'type')=='text')#正文
            摘要=已答摘要(文本,翻译) or 模型['summary']#已答或回退
        行属性={#交给工具行
            't':翻译,#文案
            'variant':模型['variant'],#变体
            'toolName':工具名,#工具名
            'icon':'question',#提问图标
            'title':翻译('ask.rowTitle') if callable(翻译) else 'ask.rowTitle',#行标题
            'summary':摘要,#摘要
            'body':模型['body'],#输入
            'output':模型['output'],#输出
            'state':状态,#态
            'inspect':检查,#检查
        }#结束
        return 自身.行(行属性)#渲染外壳

    def __call__(自身,属性=None):#组件调用形
        """对齐 React 组件调用。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染

提问工具视图={#按键 toolview 登记插件
    'name':'ask-question-toolview',#插件名
    'inject':['slots'],#依赖槽位
}#插件描述

def 应用提问工具视图(上下文):#登记提问行
    """把提问行写入 Tool 拥有的按键视图槽。"""
    def 登记():#等槽出现再登记
        """登记 ask_user_question 键。"""
        return 上下文.slots.register({#按键条目
            'name':'tool.call.toolview','key':'ask_user_question','locale':会话命名空间,#选项
        },提问行)#组件
    上下文.slots.inject('tool.call.toolview',登记)#等槽

提问工具视图['apply']=应用提问工具视图#挂 apply
