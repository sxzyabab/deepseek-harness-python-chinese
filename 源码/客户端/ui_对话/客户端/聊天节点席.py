__all__=['聊天节点席']#仅中文公开名

from nicegui import ui as 界面
from .文案 import 中文 as 对话文案
from ..异常 import 页面失败文案,贴出失败

def 恒等翻译(键,参数=None):
    '无文案表时返回键本身'
    return 键#键即文案

def 空渲染槽(*位置参数,**关键字参数):
    '未注入槽渲染时不画'
    return None#不画

class 聊天节点席:
    '订阅一 Node 键；兄弟更新不重挂'

    def __init__(自身,属性=None):
        '记下 props'
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.画面=None#可反复清空的画面
        自身.渲染()#槽位只调用构造，这里就要画

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性 if 属性 is not None else {}#新

    def 渲染(自身):
        '锚点包装 + 槽分发或 JSON 回退'
        属性=自身.属性#props
        节点键=属性['nodeKey'] if 'nodeKey' in 属性 else None#键
        用会话=属性['useSession'] if 'useSession' in 属性 else None#会话
        渲染槽=属性['renderSlot'] if 'renderSlot' in 属性 else 空渲染槽#槽
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        节点=None#节点
        if 用会话 is not None and 节点键 is not None:#可读
            def 选(快照,钉键=节点键):
                'chat.nodes.get'
                聊天=快照['chat'] if 快照 is not None and 'chat' in 快照 else None#聊天
                表=聊天['nodes'] if 聊天 is not None and 'nodes' in 聊天 else None#仓
                if 表 is None:#无
                    return None#无
                return 表['get'](钉键)#仓 get
            节点=用会话(选)#投影
        if 节点 is None:#未物化
            return#不画
        原译=翻译 if 翻译 is not 恒等翻译 else None#宿主文案
        def 取文案(键,参数=None):
            '属性上的 t 优先，否则用本包中文词典。'
            if 原译 is not None:#宿主
                if 参数 is None:#无参数
                    return 原译(键)#译
                return 原译(键,参数)#带参数
            if 键 not in 对话文案:#词典没有
                return 键#键
            文本=对话文案[键]#词条
            if 参数 is None:#无参数
                return 文本#原文
            for 名 in 参数:#替换占位
                文本=文本.replace('{'+名+'}',str(参数[名]))#替换
            return 文本#译完
        翻译=取文案#词典
        属主={#属主份额
            'selectedCallId':属性['selectedCallId'] if 'selectedCallId' in 属性 else None,#选中调用
            'cwd':属性['cwd'] if 'cwd' in 属性 else None,#工作目录
            'openFile':属性['openFile'] if 'openFile' in 属性 else None,#打开文件
            'inspectCall':属性['inspectCall'] if 'inspectCall' in 属性 else None,#检视
            'forkAt':属性['forkAt'] if 'forkAt' in 属性 else None,#分叉
            'loadImage':属性['loadImage'] if 'loadImage' in 属性 else None,#载图
            'fileMentions':属性['fileMentions'] if 'fileMentions' in 属性 else None,#提及
            'node':节点,#节点
        }#结束
        种=节点['kind'] if 'kind' in 节点 else None#kind
        载荷=节点['data'] if 'data' in 节点 else None#载荷
        锚=节点['key'] if 'key' in 节点 else None#锚
        自身.画面失败=None
        if 自身.画面 is not None:
            try:
                自身.画面.clear()
            except Exception as 错误:
                自身.画面=None
                自身.画面失败=页面失败文案(错误)
        if 自身.画面 is None:#新建
            自身.画面=界面.column().classes('聊天节点')#席
        自身.画面.clear()#清空
        if 锚 is not None:#锚
            自身.画面.props('data-chat-anchor-key='+str(锚))#锚
        with 自身.画面:#席
            贴出失败(自身)
            结果=渲染槽('conversation.chat.node',属主,{'entryKey':种,'hookContext':节点键})#槽内组件自己画
            if 结果 is None:#没有登记
                界面.label(翻译('message.unknownSurface',{'type':种}))#未知面
                if 载荷 is not None:#载荷
                    界面.label(str(载荷))#载荷

    def __call__(自身,属性=None):
        '对齐 React'
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
