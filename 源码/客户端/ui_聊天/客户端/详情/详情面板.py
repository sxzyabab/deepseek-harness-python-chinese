"""所选工具调用的整块详情面板。

对齐上游 `ui-chat/src/client/details/DetailsPanel.tsx`。公开面仅中文名。
无真 React：结构树描述。
"""
from .工具节点读取 import 查找工具调用#按 callId 查找

__all__=['详情面板','美化','原始结果文本']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """映射或属性。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 美化(原文):#美化 JSON
    """非 JSON 原样。"""
    import json#解析
    try:#尝试
        return json.dumps(json.loads(原文),ensure_ascii=False,indent=2)#缩进
    except Exception:#非 JSON
        return 原文#原样

def 原始结果文本(块):#原始结果文本
    """展平已结算结果。"""
    if 'kind' not in 块 if isinstance(块,dict) else not hasattr(块,'kind'):#进行中
        return ''#无
    部=[]#片段
    for 项 in 取字段(块,'content') or []:#内容
        if 取字段(项,'type')=='text':#文本
            部.append(取字段(项,'text') or '')#收
        else:#其它
            import json#序列化
            部.append(json.dumps(项,ensure_ascii=False,indent=2))#收
    if not 部 and 取字段(块,'error') is not None:#错误回退
        错=取字段(块,'error')#错
        部.append(str(取字段(错,'name'))+': '+str(取字段(错,'code')))#错文
    return '\n'.join(部)#拼接

def 调用材料(快照,调用标识):#快照→材料
    """窗口内无则 None。"""
    找到=查找工具调用(快照,调用标识)#查找
    if 找到 is None:#无
        return None#空
    if isinstance(找到,dict) and 'kind' in 找到:#已结算
        调用=取字段(找到,'call') or {}#调用
        return {'name':取字段(调用,'name') or 调用标识,'argsRaw':取字段(调用,'argsRaw'),'block':找到}#材料
    return {'name':取字段(找到,'name'),'argsRaw':取字段(找到,'argsRaw'),'block':找到}#进行中

class 详情面板:#详情面板
    """选中工具调用详情。"""

    def __init__(自身,属性=None):#构造
        """记下 props。"""
        自身.属性=属性 or {}#合成

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=属性 or {}#新

    def 渲染(自身):#结构树
        """标题栏 + 正文。"""
        属性=自身.属性#props
        翻译=取字段(属性,'t',lambda 键,_=None:键)#文案
        仓=取字段(属性,'useStore')#store
        选中=None#选中
        if callable(仓):#钩子
            选中=仓(lambda 态:取字段(态,'selection'))#选
        elif isinstance(仓,dict):#映射
            选中=仓.get('selection')#选
        调用标识=取字段(选中,'callId') if 选中 else None#callId
        用聊天=取字段(属性,'useChat')#useChat
        材料=None#材料
        if callable(用聊天) and 调用标识 is not None:#有
            材料=用聊天(lambda 快:调用材料(快,调用标识))#材料
        标题=翻译('details.title')#默认
        if 选中 is not None:#有选
            标题=取字段(材料,'name') if 材料 else (取字段(选中,'toolName') or 标题)#标题
        正文=None#正文
        if 选中 is None or 调用标识 is None:#无选
            正文={'type':'empty','text':翻译('details.empty')}#空态
        elif 材料 is None:#窗口外
            正文={'type':'empty','text':翻译('details.notInWindow')}#外
        else:#有材料
            段=[]#段
            参=取字段(材料,'argsRaw')#参数
            if 参 is not None:#有输入
                段.append({'type':'input','title':翻译('details.input'),'code':美化(参)})#输入
            块=取字段(材料,'block')#块
            if isinstance(块,dict) and 'kind' in 块:#已结算
                段.append({'type':'output','title':翻译('details.output'),'text':原始结果文本(块)})#输出
            else:#进行中
                段.append({'type':'running','text':翻译('details.running')})#运行中
            正文={'type':'material','sections':段}#材料
        return {#面板
            'type':'details-panel',#类型
            'title':标题,#标题
            'closeLabel':翻译('details.close'),#关闭
            'body':正文,#正文
            'cssModule':'DetailsPanel.module.css',#样式
        }#结束

    def __call__(自身,属性=None):#调用形
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
