"""cordis_stop / cordis_undefine 本地化卡：嵌套 JSX 结构树。

对齐上游 `ui-cordis/src/client/CordisActionRow.tsx`。公开面仅中文名。
复用运行行样式表；图标半需浏览器。无法 JS·vm 执行：图标原语像素。
"""
from .卡片模型 import 动作卡片#卡模型
from .运行行 import 样式表#共用样式

__all__=['动作行','样式表','前导图标']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 前导图标(态,移除):#icon 槽
    """error/stopped 用 StateDot；否则 Trash 或 Stop。"""
    if 态=='error':#失败
        return {'type':'StateDot','state':'error'}#红点
    if 态=='stopped':#中断
        return {'type':'StateDot','state':'warning'}#琥珀
    if 移除:#移除
        return {'type':'IconTrashOutline16','size':14}#垃圾桶
    return {'type':'IconStopFill16','size':14}#停止

def 滤子(子们):#去掉 None
    """保留真值子节点。"""
    return [子 for 子 in 子们 if 子 is not None]#过滤

class 动作行:#stop/undefine 结构树
    """组装停止或移除卡嵌套 JSX 树。"""

    def __init__(自身,属性=None):#记下
        """记下 props。"""
        自身.属性=属性 or {}#合成

    def 更新(自身,属性):#刷新
        """刷新 props。"""
        自身.属性=属性 or {}#新

    def 渲染(自身):#结构树
        """与上游 JSX 同构。"""
        p=自身.属性#props
        卡=动作卡片(取字段(p,'block'))#卡
        翻译=取字段(p,'t') or (lambda 键,*_a,**_k:键)#文案
        工具名=取字段(p,'toolName')#工具
        移除=工具名=='cordis_undefine'#移除
        摘要=卡.get('errorSummary') or 卡.get('pluginId') or 取字段(p,'callId')#摘要
        行子=滤子([#css.row 子
            {'type':'span','class':'icon','children':[前导图标(卡.get('state'),移除)]},#图标
            {'type':'span','class':'title','children':[翻译('row.removeTitle' if 移除 else 'row.stopTitle')]},#标题
            {'type':'span','class':'separator','aria-hidden':True},#分隔
            {'type':'span','class':'error' if 卡.get('errorSummary') else 'summary','children':[摘要]},#摘要
            {'type':'button','class':'inspect','aria-label':'Inspect','onClick':'inspect',
             'children':[{'type':'IconInspectOutline12'}]} if 取字段(p,'inspect') is not None else None,#巡检
        ])#行子结束
        卡子=[{'type':'div','class':'row','children':行子}]#顶行
        if 卡.get('output') is not None:#输出
            卡子.append({'type':'pre','class':'output','children':[卡.get('output')]})#输出
        return {#根
            'type':'div','class':'card','data-tool':工具名,'data-state':卡.get('state'),
            'children':卡子,'css':样式表,
            'handlers':{'inspect':取字段(p,'inspect')},#动作
            'note':'图标半需浏览器；无法 Python·vm 执行图标原语',#缺口
        }#结束

    def __call__(自身,属性=None):#调用形
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
