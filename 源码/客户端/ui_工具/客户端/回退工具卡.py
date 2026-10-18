from ...ui_基础界面组件.icons import (
    图标代码16,图标接口14,图标星闪16,图标浏览16,图标编辑16,图标检索16,
)
from .文案 import 中文文案
from .自动拒绝 import 本地化自动拒绝
from .读卡模型 import 读卡模型
from .差异卡模型 import 差异卡模型
from .检索卡模型 import 检索卡模型
from .终端卡模型 import 终端卡模型,终端已失败
from .网页卡模型 import 网页卡模型
from .调用模型 import 工具行模型
from .工具行 import 工具行

__all__=['回退工具卡']

def 变体图标(窗口,变体):
    '14 像素的变体前导图标'
    属性={'window':窗口,'size':14}
    if 变体=='search':
        return 图标检索16(属性)
    if 变体=='read':
        return 图标浏览16(属性)
    if 变体=='bash':
        return 图标接口14(属性)
    if 变体=='write' or 变体=='edit':
        return 图标编辑16(属性)
    if 变体=='code':
        return 图标代码16(属性)
    return 图标星闪16(属性)

class 回退工具卡:
    '没有按键视图时的通用卡。自动拒绝换掉普通失败输出'
    def __new__(类,属性):
        '派生各卡材料后交给工具行'
        模型=工具行模型(属性['toolName'],属性['block'],属性.get('cwd'),属性.get('home'))
        if 模型['autoReviewDenial'] is None:
            拒绝=None
        else:
            拒绝=本地化自动拒绝(模型['autoReviewDenial'])
        终端=终端卡模型(属性['block'],属性.get('cwd'))
        if 模型['state']=='ok' and 终端 is not None and 终端已失败(终端):
            状态='error'
        else:
            状态=模型['state']
        单文件=模型['filePath'] is not None
        return 工具行({
            'window':属性['window'],
            'useDisclosure':属性['useDisclosure'],
            'variant':模型['variant'],
            'toolName':属性['toolName'],
            'icon':变体图标(属性['window'],模型['variant']),
            'title':中文文案(模型['titleKey']),
            'summary':模型['summary'],
            'bodyRaw':None if 单文件 or 拒绝 is not None else 模型['bodyRaw'],
            'output':模型['output'] if 拒绝 is None else 拒绝['output'],
            'errorSummary':模型['errorSummary'] if 拒绝 is None else 拒绝['summary'],
            'terminal':终端,
            'diff':差异卡模型(属性['block']),
            'read':读卡模型(属性['block'],属性.get('cwd'),属性.get('home')),
            'search':检索卡模型(属性['block']),
            'web':网页卡模型(属性['block']),
            'state':状态,
            'filePath':模型['filePath'],
            'onOpenFile':属性.get('openFile') if 单文件 else None,
            'inspect':属性.get('inspect'),
        })
