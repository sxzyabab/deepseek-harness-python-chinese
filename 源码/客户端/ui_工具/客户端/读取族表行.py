from ...ui_基础界面组件.icons import 图标浏览16
from .文案 import 中文文案
from .调用模型 import 工具行模型
from .工具行 import 工具行

__all__=['读族行']

def 读族行(属性,卡片):
    '读和读图像共用的单文件行。卡片材料由调用方给'
    模型=工具行模型(属性['toolName'],属性['block'],属性.get('cwd'),属性.get('home'))
    材料={
        'window':属性['window'],
        'useDisclosure':属性['useDisclosure'],
        'variant':模型['variant'],
        'toolName':属性['toolName'],
        'icon':图标浏览16({'window':属性['window'],'size':14}),
        'title':中文文案(模型['titleKey']),
        'summary':模型['summary'],
        'bodyRaw':None,
        'output':模型['output'],
        'errorSummary':模型['errorSummary'],
        'state':模型['state'],
        'filePath':模型['filePath'],
        'onOpenFile':属性.get('openFile'),
        'inspect':属性.get('inspect'),
    }
    材料.update(卡片)
    return 工具行(材料)
