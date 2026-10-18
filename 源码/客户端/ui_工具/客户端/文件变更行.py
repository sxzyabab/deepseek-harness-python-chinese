from ...ui_基础界面组件.icons import 图标编辑16
from .文案 import 会话命名空间,中文文案
from .差异卡模型 import 差异卡模型
from .调用模型 import 工具行模型
from .工具行 import 工具行
from .槽 import 槽名工具调用视图

__all__=['文件变更行','文件变更工具视图']

内容字段=('content','old_string','new_string')
千字节=1024

class 文件变更行:
    '路径和已解码输入大小。结算后可以展开差异'
    def __new__(类,属性):
        '派生摘要和差异卡'
        自身=object.__new__(类)
        自身.属性=属性
        return 自身.渲染()

    def 内容千字节(自身):
        '各阶段已解码的输入。还没有任何内容字段则为 None'
        参数=自身.属性['block']['args']
        未完成=None
        for 键 in 内容字段:
            if 参数.has(键) and not 参数.complete(键):
                未完成=键
                break
        已完成=0
        for 键 in 内容字段:
            if 键!=未完成 and 参数.complete(键):
                长度=参数.stringLength(键,{'step':千字节})
                已完成=已完成+(0 if 长度 is None else 长度)
        if 未完成 is None:
            有字段=False
            for 键 in 内容字段:
                if 参数.has(键):
                    有字段=True
            if not 有字段:
                return None
            return (已完成+千字节-1)//千字节
        增量=参数.stringLength(未完成,{'step':千字节,'offset':已完成})
        字数=已完成+(0 if 增量 is None else 增量)
        return (字数+千字节-1)//千字节

    def 渲染(自身):
        '交给工具行'
        属性=自身.属性
        模型=工具行模型(属性['toolName'],属性['block'],属性.get('cwd'),属性.get('home'))
        千字=自身.内容千字节()
        大小=None if 千字 is None else 中文文案('tool.preparing.content',{'kilobytes':千字})
        后缀=大小 if 大小 is not None and 模型['summary']!='' else None
        return 工具行({
            'window':属性['window'],
            'useDisclosure':属性['useDisclosure'],
            'variant':模型['variant'],
            'toolName':属性['toolName'],
            'icon':图标编辑16({'window':属性['window'],'size':14}),
            'title':中文文案(模型['titleKey']),
            'summary':模型['summary'],
            'summarySuffix':后缀,
            'output':模型['output'],
            'errorSummary':模型['errorSummary'],
            'diff':差异卡模型(属性['block']),
            'state':模型['state'],
            'filePath':模型['filePath'],
            'onOpenFile':属性.get('openFile'),
            'inspect':属性.get('inspect'),
        })

def 应用文件变更工具视图(上下文,配置=None):
    '登记 edit 和 write'
    def 登记():
        '两个键一起登记，卸下时按相反顺序拆'
        yield 上下文.slots.register({
            'name':槽名工具调用视图,'key':'edit','locale':会话命名空间,
        },文件变更行)
        yield 上下文.slots.register({
            'name':槽名工具调用视图,'key':'write','locale':会话命名空间,
        },文件变更行)
    上下文.slots.inject(槽名工具调用视图,登记)

文件变更工具视图={
    'name':'file-mutation-toolview',
    'inject':['slots'],
    'apply':应用文件变更工具视图,
}
