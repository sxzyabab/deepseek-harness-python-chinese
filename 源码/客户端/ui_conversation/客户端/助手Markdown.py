"""助手块有序渲染：正文、Think 行、图组；工具头由聊天流分组。

对齐上游 `ui-conversation/src/client/chat/AssistantMarkdown.tsx`。公开面仅中文名。
流式/定稿/中断共用；仅 tool-call 时不画壳。
"""
from .推理行 import 推理行#Think 披露
from .图像标签 import 消息图像标签 as 消息图标签#图廊标签

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
        """记下合成 props 与推理行缓存。"""
        自身.属性=属性 or {}#合成
        自身.推理缓存={}#按块索引保展开态

    def 更新(自身,属性):#刷新
        """刷新 props。"""
        自身.属性=属性 or {}#新

    def 取推理行(自身,索引):#缓存实例
        """同索引复用，保住展开。"""
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
        加载图=取字段(属性,'loadImage')#图
        提及=取字段(属性,'mentions')#提及
        def 缺省加载(_):#无服务
            """会话图服务不可用。"""
            raise RuntimeError(翻译('image.serviceUnavailable'))#拒
        图加载器=加载图 if callable(加载图) else 缺省加载#加载器
        图标签=消息图标签(翻译)#标签
        def 截断标(总数):#JsonBlock truncatedLabel
            """超界文案。"""
            return 翻译('json.truncated',{'total':总数})#文
        有可见=流式 or 中断 is True or any(取字段(块,'kind')!='tool-call' for 块 in 块们)#可见
        if not 有可见:#仅工具头
            return None#空壳跳过
        渲染们=[]#段
        末=len(块们)-1#末索引
        索引=0#游标
        while 索引<len(块们):#遍历
            块=块们[索引]#块
            种=取字段(块,'kind')#kind
            if 种=='text':#正文
                渲染们.append({#Markdown
                    'type':'MarkdownText',#种
                    'key':索引,#键
                    'text':取字段(块,'text'),#文
                    'streaming':流式,#流式
                    'codeLabels':{'copyLabel':翻译('copy'),'copiedLabel':翻译('copied')},#复制
                    'fileMentions':提及,#提及
                })#结束
            elif 种=='reasoning':#Think
                渲染们.append(自身.取推理行(索引)({#推理行
                    'text':取字段(块,'text'),#文
                    'running':流式 and 索引==末,#末块流式
                    't':翻译,#文案
                }))#渲
            elif 种=='image':#图组
                起点=索引#组首
                组=[块]#组
                while 索引+1<len(块们) and 取字段(块们[索引+1],'kind')=='image':#连续图
                    索引+=1#进
                    组.append(块们[索引])#加
                渲染们.append({#图廊
                    'type':'ImageGallery',#种
                    'key':起点,#组键
                    'images':组,#图
                    'load':图加载器,#加载
                    'align':'start',#对齐
                    'labels':图标签,#标签
                })#结束
            elif 种=='tool-call':#工具头
                pass#聊天流分组
            else:#未知块
                渲染们.append({#JSON
                    'type':'JsonBlock',#种
                    'key':索引,#键
                    'label':翻译('message.unknownBlock'),#标签
                    'payload':取字段(块,'block'),#载荷
                    'truncatedLabel':截断标,#截
                })#结束
            索引+=1#下一
        return {#根
            'type':'assistant-markdown',#类型
            'className':'root',#类
            'data-streaming':流式 or None,#流式标
            'body':渲染们,#体
            'stopped':翻译('message.stopped') if 中断 else None,#中断标
            'cssModule':'聊天/助手Markdown.module.css',#样式
        }#结束

    def __call__(自身,属性=None):#调用形
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
