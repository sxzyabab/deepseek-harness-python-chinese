from ..异常 import 对话错误#本包异常
from .推理行 import 推理行#Think 披露
from .图像标签 import 消息图像标签 as 消息图标签#图廊标签

__all__=['助手Markdown']#仅中文公开名

from nicegui import ui as 界面
from .文案 import 中文 as 对话文案
from ..异常 import 页面失败文案,贴出失败

def 恒等翻译(键,参数=None):
    '无宿主文案时用本包中文词典，没有则返回键本身。'
    if 键 not in 对话文案:#词典没有
        return 键#键
    文本=对话文案[键]#词条
    if 参数 is None:#无参数
        return 文本#原文
    for 名 in 参数:#替换占位
        文本=文本.replace('{'+名+'}',str(参数[名]))#替换
    return 文本#译完

class 助手Markdown:
    '流式/定稿/中断共用；仅 tool-call 时不画壳'

    def __init__(自身,属性=None):
        '记下合成 props 与推理行缓存'
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.推理缓存={}#按块索引保展开态
        自身.画面=None#可反复清空的画面

    def 更新(自身,属性):
        '刷新 props'
        自身.属性=属性 if 属性 is not None else {}#新

    def 取推理行(自身,索引):
        '同索引复用，保住展开'
        if 索引 not in 自身.推理缓存:#新
            自身.推理缓存[索引]=推理行()#建
        return 自身.推理缓存[索引]#行

    def 渲染(自身):
        '按块 kind 分发'
        属性=自身.属性#props
        块列表=属性['blocks'] if 'blocks' in 属性 and 属性['blocks'] is not None else []#块
        流式=属性['streaming'] is True if 'streaming' in 属性 else False#流式
        中断=属性['interrupted'] is True if 'interrupted' in 属性 else False#中断
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        加载图=属性['loadImage'] if 'loadImage' in 属性 else None#图
        提及=属性['mentions'] if 'mentions' in 属性 else None#提及
        def 缺省加载(_标识):
            '会话图服务不可用'
            raise 对话错误(翻译('image.serviceUnavailable'))#拒
        图加载器=加载图 if 加载图 is not None else 缺省加载#加载器
        图标签=消息图标签(翻译)#标签
        def 截断标(总数,钉翻译=翻译):
            '超界文案'
            return 钉翻译('json.truncated',{'total':总数})#文
        有可见=流式 is True or 中断 is True#流式或中断必画
        if 有可见 is False:#尚无
            for 块 in 块列表:#扫块
                种=块['kind'] if 'kind' in 块 else None#种
                if 种!='tool-call':#非工具
                    有可见=True#可见
                    break#停
        if 有可见 is False:#仅工具头
            return#不画
        自身.画面失败=None
        if 自身.画面 is not None:
            try:
                自身.画面.clear()
            except Exception as 错误:
                自身.画面=None
                自身.画面失败=页面失败文案(错误)
        if 自身.画面 is None:#新建
            自身.画面=界面.column().classes('root')#正文
        自身.画面.clear()#清空
        末=len(块列表)-1#末索引
        索引=0#游标
        with 自身.画面:#正文
            贴出失败(自身)
            while 索引<len(块列表):#遍历
                块=块列表[索引]#块
                种=块['kind'] if 'kind' in 块 else None#kind
                if 种=='text':#正文
                    文=块['text'] if 'text' in 块 and 块['text'] is not None else ''#文
                    if 文=='':#空
                        pass#不画空段
                    else:#Markdown
                        界面.markdown(文)#正文
                elif 种=='reasoning':#Think
                    文=块['text'] if 'text' in 块 and 块['text'] is not None else ''#文
                    行=自身.取推理行(索引)#保住展开
                    行.更新({'text':文,'running':流式 is True and 索引==末,'t':翻译})#灌入
                    行.渲染()#自己画
                elif 种=='image':#图组
                    组=[块]#组
                    while 索引+1<len(块列表):#连续图
                        下种=块列表[索引+1]['kind'] if 'kind' in 块列表[索引+1] else None#下种
                        if 下种!='image':#断
                            break#停
                        索引+=1#进
                        组.append(块列表[索引])#加
                    界面.label(图标签['image']+' ×'+str(len(组)))#图
                    界面.label(图标签['loading'])#加载说明
                elif 种=='tool-call':#工具头
                    pass#聊天流分组
                else:#未知块
                    载荷=块['block'] if 'block' in 块 else None#载荷
                    界面.label(翻译('message.unknownBlock'))#标签
                    if 载荷 is not None:#载荷
                        界面.label(str(载荷))#载荷
                索引+=1#下一
            if 中断 is True:#中断
                界面.label(翻译('message.stopped'))#停止
        del 图加载器#图服务仍由宿主持有，这里只标出图片
        del 提及#提及留在宿主，正文不把返回值当树
        del 截断标#截断文案改由未知块标签承担

    def __call__(自身,属性=None):
        '对齐 React'
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
