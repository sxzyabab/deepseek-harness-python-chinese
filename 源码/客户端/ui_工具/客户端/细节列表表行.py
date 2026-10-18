from ...ui_基础界面组件.icons import (
    图标代码16,图标分支16,图标清单14,图标检索16,图标智能体预设16,图标目标16,图标用户16,
    图标Cordis插件14,描边图标,常规描边,
)
from .文案 import 会话命名空间,中文文案
from .原始工具调用 import 解析工具调用
from .详情卡片模型 import 详情卡片模型
from .调用模型 import 工具行模型
from .工具行 import 工具行
from .槽 import 槽名工具调用视图

__all__=['细节列表行','细节工具视图']

语言服务标题={
    'goToDefinition':'tool.title.findDefinition',
    'findReferences':'tool.title.findReferences',
    'goToImplementation':'tool.title.findImplementation',
    'hover':'tool.title.hoverSymbol',
}
队友工具=frozenset(['spawn_teammate','list_agents','send_message','interrupt_agent','wait_agent'])
细节键=(
    'create_goal','get_goal','update_goal',
    'schedule_create','schedule_list','schedule_delete','schedule_update',
    'cordis_inspect_list','cordis_inspect_query','cordis_inspect_self',
    'workflow','ralph',
    'session_event_read','session_event_search','session_event_trace',
    'session_search','session_trace',
    'list_subagent_models','subagent','list_agents','send_message','interrupt_agent',
    'job_list','job_output','job_kill',
    'terminal_open','terminal_read','terminal_list','terminal_signal','terminal_close',
    'lsp',
    'spawn_teammate','team_task_create','team_task_get','team_task_update','team_task_list',
    'wait_agent',
)

def 时钟图标(窗口):
    '基础界面组件还没有时钟字形，按上游路径画出'
    return 描边图标({'window':窗口,'size':14},'0 0 16 16',[
        'M8 14C11.3137 14 14 11.3137 14 8C14 4.68629 11.3137 2 8 2C4.68629 2 2 4.68629 2 8C2 11.3137 4.68629 14 8 14Z',
        'M8 4.31V8.46L11 10.08',
    ],14,常规描边)

def 细节图标(窗口,工具名):
    '按工具族选前导图标'
    if 工具名 in 队友工具:
        return 图标用户16({'window':窗口,'size':14})
    if 工具名.startswith('schedule_'):
        return 时钟图标(窗口)
    if 工具名.endswith('_goal'):
        return 图标目标16({'window':窗口,'size':14})
    if 工具名.startswith('cordis_'):
        return 图标Cordis插件14({'window':窗口})
    if 工具名.startswith('terminal_'):
        return 图标代码16({'window':窗口,'size':14})
    if 工具名.startswith('session_') or 工具名=='lsp':
        return 图标检索16({'window':窗口,'size':14})
    if 工具名.startswith('job_') or 工具名.startswith('team_task_'):
        return 图标清单14({'window':窗口})
    if 工具名=='workflow' or 工具名=='ralph':
        return 图标分支16({'window':窗口,'size':14})
    return 图标智能体预设16({'window':窗口,'size':14})

class 细节列表行:
    '把已记录的实体、回执和报告放进可展开行'
    def __new__(类,属性):
        '语言服务按操作换标题'
        窗口=属性['window']
        模型=工具行模型(属性['toolName'],属性['block'],属性.get('cwd'),属性.get('home'))
        语言=''
        文档=窗口.document
        if 文档.documentElement is not None:
            语言=文档.documentElement.lang or ''
        详情=详情卡片模型(属性['block'],窗口,语言)
        标题键=模型['titleKey']
        if 属性['toolName']=='lsp':
            已解析=解析工具调用(属性['block'])
            操作=None if 已解析 is None else 已解析['args'].get('operation')
            if isinstance(操作,str) and 操作 in 语言服务标题:
                标题键=语言服务标题[操作]
        if isinstance(详情,dict) and 详情.get('summary') is not None:
            摘要=详情['summary']
        elif isinstance(详情,dict) and len(详情.get('items') or [])>0 and 详情['items'][0].get('title') is not None:
            摘要=详情['items'][0]['title']
        elif isinstance(详情,dict) and 详情.get('empty') is not None:
            摘要=详情['empty']
        else:
            摘要=模型['summary']
        return 工具行({
            'window':窗口,
            'useDisclosure':属性['useDisclosure'],
            'variant':模型['variant'],
            'toolName':属性['toolName'],
            'icon':细节图标(窗口,属性['toolName']),
            'title':中文文案(标题键),
            'summary':摘要,
            'details':详情,
            'bodyRaw':模型['bodyRaw'],
            'output':模型['output'],
            'errorSummary':模型['errorSummary'],
            'state':模型['state'],
            'inspect':属性.get('inspect'),
            'onOpenFile':属性.get('openFile'),
        })

def 应用细节工具视图(上下文,配置=None):
    '把已记录结果登记进按键视图槽'
    def 登记():
        '每个工具名各登记一行'
        for 键 in 细节键:
            yield 上下文.slots.register({
                'name':槽名工具调用视图,
                'key':键,
                'locale':会话命名空间,
            },细节列表行)
    上下文.slots.inject(槽名工具调用视图,登记)

细节工具视图={
    'name':'details-toolview',
    'inject':['slots'],
    'apply':应用细节工具视图,
}
