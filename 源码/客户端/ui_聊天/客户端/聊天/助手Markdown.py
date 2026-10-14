from .推理行 import 推理行#Think 披露
from .消息项 import 打开列,收起列,图地址

__all__=['助手Markdown']#仅中文公开名

from nicegui import ui as 界面

def 恒等翻译(键,参数=None):
    '无文案表时返回键本身'
    return 键#键即文案

class 助手Markdown:
    '流式/定稿/中断共用；仅 tool-call 时不画壳'
    def __init__(自身,属性=None):
        '记下合成 props'
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.推理缓存={}#按块索引
        自身.根=None#列

    def 更新(自身,属性):
        '刷新 props'
        自身.属性=属性 if 属性 is not None else {}#新

    def 取推理行(自身,索引):
        '同索引复用'
        if 索引 not in 自身.推理缓存:#新
            自身.推理缓存[索引]=推理行()#建
        return 自身.推理缓存[索引]#行

    def 渲染(自身):
        '按块 kind 分发'
        属性=自身.属性#props
        块列表=属性['blocks'] if 'blocks' in 属性 and 属性['blocks'] is not None else []#块
        流式=属性['streaming'] if 'streaming' in 属性 else False#流式
        中断=属性['interrupted'] if 'interrupted' in 属性 else False#中断
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        有可见=流式 is True or 中断 is True#流式或中断必画
        if 有可见 is False:#尚无
            for 块 in 块列表:#扫块
                种=块['kind'] if 'kind' in 块 else None#种
                if 种!='tool-call':#非工具
                    有可见=True#可见
                    break
        if 有可见 is False:#仅工具
            收起列(自身)
            return
        末=len(块列表)-1#末索引
        with 打开列(自身,'助手Markdown'):
            if 中断 is True:
                界面.label(翻译('message.stopped')).classes('中断')
            for 索引,块 in enumerate(块列表):#遍历
                种=块['kind'] if 'kind' in 块 else None#种
                if 种=='text':#正文
                    文=块['text'] if 'text' in 块 and 块['text'] is not None else ''#文
                    if 文=='':
                        界面.label('')
                    else:
                        界面.markdown(文)
                    continue
                if 种=='reasoning':#推理
                    文=块['text'] if 'text' in 块 and 块['text'] is not None else ''#文
                    行=自身.取推理行(索引)
                    行.更新({'text':文,'running':流式 is True and 索引==末,'t':翻译})
                    行.渲染()
                    continue
                if 种=='image':#图
                    附=块['attachment'] if 'attachment' in 块 else None#附
                    地址=图地址({'attachment':附})
                    if 地址 is None:
                        界面.label(翻译('message.extraBlock'))
                    else:
                        界面.image(地址).classes('消息图')
                    continue
                if 种=='tool-call':#工具头由流分组
                    continue
                界面.label(翻译('message.unknownBlock'))

    def __call__(自身,属性=None):
        '对齐'
        if 属性 is not None:
            自身.更新(属性)#刷
        自身.渲染()#画
