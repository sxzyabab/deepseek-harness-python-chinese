"""助手块有序渲染：正文、Think 行、图组。

对齐上游 `ui-chat/src/client/chat/AssistantMarkdown.tsx`。公开面仅中文名。
"""
from .推理行 import 推理行#Think 披露

__all__=['助手Markdown']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """映射或对象。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 助手Markdown:#助手块体
    """流式/定稿/中断共用；仅 tool-call 时不画壳。"""

    def __init__(自身,属性=None):#记下
        """记下合成 props。"""
        自身.属性=属性 or {}#合成
        自身.推理缓存={}#按块索引

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=属性 or {}#新

    def 取推理行(自身,索引):#缓存实例
        """同索引复用。"""
        if 索引 not in 自身.推理缓存:#新
            自身.推理缓存[索引]=推理行()#建
        return 自身.推理缓存[索引]#行

    def 渲染(自身):#结构
        """按块 kind 分发。"""
        属性=自身.属性#props
        块们=取字段(属性,'blocks') or []#块
        流式=取字段(属性,'streaming',False)#流式
        中断=取字段(属性,'interrupted',False)#中断
        翻译=取字段(属性,'t',lambda 键,_=None:键)#文案
        有可见=流式 or 中断 is True or any(取字段(块,'kind')!='tool-call' for 块 in 块们)#可见
        if not 有可见:#仅工具
            return None#空
        渲染们=[]#段
        for 索引,块 in enumerate(块们):#遍历
            种=取字段(块,'kind')#种
            if 种=='text':#正文
                渲染们.append({'type':'text','text':取字段(块,'text') or '','streaming':流式 and 索引==len(块们)-1})#文
            elif 种=='reasoning':#推理
                渲染们.append(自身.取推理行(索引)({'text':取字段(块,'text') or '','running':流式 and 索引==len(块们)-1,'t':翻译}))#Think
            elif 种=='image':#图
                渲染们.append({'type':'image','attachment':取字段(块,'attachment')})#图
            elif 种=='tool-call':#工具头由流分组
                continue#跳
            else:#未知
                渲染们.append({'type':'unknown','label':翻译('message.unknownBlock')})#未知
        return {'type':'assistant-markdown','interrupted':中断,'streaming':流式,'children':渲染们,'cssModule':'助手Markdown.module.css'}#壳

    def __call__(自身,属性=None):#调用形
        """对齐。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
