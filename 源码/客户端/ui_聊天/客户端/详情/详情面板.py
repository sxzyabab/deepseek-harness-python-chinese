import json#美化与序列化
from .工具节点读取 import 查找工具调用#按 callId 查找

__all__=['详情面板','美化','原始结果文本']#仅中文公开名

def 恒等翻译(键,参数=None):
    """无文案表时返回键本身。"""
    return 键#键即文案

def 美化(原文):
    """非 JSON 原样。"""
    try:
        return json.dumps(json.loads(原文),ensure_ascii=False,separators=(',',':'),allow_nan=False,indent=2)#缩进
    except (json.JSONDecodeError,TypeError,ValueError):
        return 原文#原样

def 原始结果文本(块):
    """展平已结算结果。块为 dict。"""
    if 'kind' not in 块:#进行中
        return ''#无
    部=[]#片段
    内容=块['content'] if 'content' in 块 and 块['content'] is not None else []#内容
    for 项 in 内容:#内容
        种=项['type'] if 'type' in 项 else None#种
        if 种=='text':#文本
            文=项['text'] if 'text' in 项 and 项['text'] is not None else ''#文
            部.append(文)#收
        else:#其它
            部.append(json.dumps(项,ensure_ascii=False,separators=(',',':'),allow_nan=False,indent=2))#收
    if len(部)==0 and 'error' in 块 and 块['error'] is not None:#错误回退
        错=块['error']#错
        名=错['name'] if 'name' in 错 else None#名
        码=错['code'] if 'code' in 错 else None#码
        部.append(str(名)+': '+str(码))#错文
    return '\n'.join(部)#拼接

def 调用材料(快照,调用标识):
    """窗口内无则 None。"""
    找到=查找工具调用(快照,调用标识)#查找
    if 找到 is None:#无
        return None#空
    if 'kind' in 找到:#已结算
        调用=找到['call'] if 'call' in 找到 and 找到['call'] is not None else {}#调用
        名=调用['name'] if 'name' in 调用 and 调用['name'] is not None else 调用标识#名
        参=调用['argsRaw'] if 'argsRaw' in 调用 else None#参
        return {'name':名,'argsRaw':参,'block':找到}#材料
    名=找到['name'] if 'name' in 找到 else None#名
    参=找到['argsRaw'] if 'argsRaw' in 找到 else None#参
    return {'name':名,'argsRaw':参,'block':找到}#进行中

def 取选中(态):
    """store selection。态为 dict。"""
    return 态['selection'] if 'selection' in 态 else None#选

class 详情面板:
    """选中工具调用详情。"""
    def __init__(自身,属性=None):
        """记下 props。"""
        自身.属性=属性 if 属性 is not None else {}#合成

    def 更新(自身,属性):
        """刷新 props。"""
        自身.属性=属性 if 属性 is not None else {}#新

    def 渲染(自身):
        """标题栏 + 正文。"""
        属性=自身.属性#props
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        用存储=属性['useStore'] if 'useStore' in 属性 else None#存储
        选中=用存储(取选中) if 用存储 is not None else None#选中
        调用标识=选中['callId'] if 选中 is not None and 'callId' in 选中 else None#callId
        用聊天=属性['useChat'] if 'useChat' in 属性 else None#useChat
        材料=None#材料
        if 用聊天 is not None and 调用标识 is not None:#有
            def 取材料(快):
                """按 callId 取材料。"""
                return 调用材料(快,调用标识)#材料
            材料=用聊天(取材料)#材料
        标题=翻译('details.title')#默认
        if 选中 is not None:#有选
            if 材料 is not None and 'name' in 材料:#材料名
                标题=材料['name']#标题
            elif 'toolName' in 选中 and 选中['toolName'] is not None:#工具名
                标题=选中['toolName']#标题
        正文=None#正文
        if 选中 is None or 调用标识 is None:#无选
            正文={'type':'empty','text':翻译('details.empty')}#空态
        elif 材料 is None:#窗口外
            正文={'type':'empty','text':翻译('details.notInWindow')}#外
        else:#有材料
            段=[]#段
            参=材料['argsRaw'] if 'argsRaw' in 材料 else None#参数
            if 参 is not None:#有输入
                段.append({'type':'input','title':翻译('details.input'),'code':美化(参)})#输入
            块=材料['block'] if 'block' in 材料 else None#块
            if 块 is not None and 'kind' in 块:#已结算
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

    def __call__(自身,属性=None):
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
