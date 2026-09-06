"""助手块有序渲染：正文、Think 行、图组；工具头由聊天流分组。

对齐上游 `ui-conversation/src/client/chat/AssistantMarkdown.tsx`。公开面仅中文名。
流式/定稿/中断共用；仅 tool-call 时不画壳。
属性与块为 dict。
"""
from ..服务 import 对话错误#本包异常
from .推理行 import 推理行#Think 披露
from .图像标签 import 消息图像标签 as 消息图标签#图廊标签

__all__=['助手Markdown']#仅中文公开名

def 恒等翻译(键,参数=None):
    """无文案表时返回键本身。"""
    return 键#键即文案

class 助手Markdown:
    """流式/定稿/中断共用；仅 tool-call 时不画壳。"""

    def __init__(自身,属性=None):
        """记下合成 props 与推理行缓存。"""
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.推理缓存={}#按块索引保展开态

    def 更新(自身,属性):
        """刷新 props。"""
        自身.属性=属性 if 属性 is not None else {}#新

    def 取推理行(自身,索引):
        """同索引复用，保住展开。"""
        if 索引 not in 自身.推理缓存:#新
            自身.推理缓存[索引]=推理行()#建
        return 自身.推理缓存[索引]#行

    def 渲染(自身):
        """按块 kind 分发。"""
        属性=自身.属性#props
        块列表=属性['blocks'] if 'blocks' in 属性 and 属性['blocks'] is not None else []#块
        流式=属性['streaming'] is True if 'streaming' in 属性 else False#流式
        中断=属性['interrupted'] is True if 'interrupted' in 属性 else False#中断
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        加载图=属性['loadImage'] if 'loadImage' in 属性 else None#图
        提及=属性['mentions'] if 'mentions' in 属性 else None#提及
        def 缺省加载(_标识):
            """会话图服务不可用。"""
            raise 对话错误(翻译('image.serviceUnavailable'))#拒
        图加载器=加载图 if 加载图 is not None else 缺省加载#加载器
        图标签=消息图标签(翻译)#标签
        def 截断标(总数,钉翻译=翻译):
            """超界文案。"""
            return 钉翻译('json.truncated',{'total':总数})#文
        有可见=流式 is True or 中断 is True#流式或中断必画
        if 有可见 is False:#尚无
            for 块 in 块列表:#扫块
                种=块['kind'] if 'kind' in 块 else None#种
                if 种!='tool-call':#非工具
                    有可见=True#可见
                    break#停
        if 有可见 is False:#仅工具头
            return None#空壳跳过
        渲染列表=[]#段
        末=len(块列表)-1#末索引
        索引=0#游标
        while 索引<len(块列表):#遍历
            块=块列表[索引]#块
            种=块['kind'] if 'kind' in 块 else None#kind
            if 种=='text':#正文
                文=块['text'] if 'text' in 块 else None#文
                渲染列表.append({#Markdown
                    'type':'MarkdownText',#种
                    'key':索引,#键
                    'text':文,#文
                    'streaming':流式,#流式
                    'codeLabels':{'copyLabel':翻译('copy'),'copiedLabel':翻译('copied')},#复制
                    'fileMentions':提及,#提及
                })#结束
            elif 种=='reasoning':#Think
                文=块['text'] if 'text' in 块 else None#文
                渲染列表.append(自身.取推理行(索引)({#推理行
                    'text':文,#文
                    'running':流式 is True and 索引==末,#末块流式
                    't':翻译,#文案
                }))#渲
            elif 种=='image':#图组
                起点=索引#组首
                组=[块]#组
                while 索引+1<len(块列表):#连续图
                    下种=块列表[索引+1]['kind'] if 'kind' in 块列表[索引+1] else None#下种
                    if 下种!='image':#断
                        break#停
                    索引+=1#进
                    组.append(块列表[索引])#加
                渲染列表.append({#图廊
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
                载荷=块['block'] if 'block' in 块 else None#载荷
                渲染列表.append({#JSON
                    'type':'JsonBlock',#种
                    'key':索引,#键
                    'label':翻译('message.unknownBlock'),#标签
                    'payload':载荷,#载荷
                    'truncatedLabel':截断标,#截
                })#结束
            索引+=1#下一
        return {#根
            'type':'assistant-markdown',#类型
            'className':'root',#类
            'data-streaming':True if 流式 is True else None,#流式标
            'body':渲染列表,#体
            'stopped':翻译('message.stopped') if 中断 is True else None,#中断标
            'cssModule':'聊天/助手Markdown.module.css',#样式
        }#结束

    def __call__(自身,属性=None):
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
