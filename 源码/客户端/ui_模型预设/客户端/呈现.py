import re
from .文案 import 英文

__all__=['完全权限预设','自动审查预设','展示预设名','展示权限预设']

完全权限预设='danger-full-access'
自动审查预设='auto'

预设标签键={
    'read-only':'preset.readOnly',
    'workspace-write':'preset.workspaceWrite',
    完全权限预设:'preset.fullAccess',
}

默认预设标签={
    'preset.readOnly':英文['preset.readOnly'],
    'preset.workspaceWrite':英文['preset.workspaceWrite'],
    'preset.fullAccess':英文['preset.fullAccess'],
}

短横线名=re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*$')

def 展示预设名(名称):
    '把常规短横线名转成词首大写。不是短横线则原样返回'
    if 短横线名.match(名称) is None:
        return 名称
    词表=[]
    for 词 in 名称.split('-'):
        词表.append(词[0].upper()+词[1:])
    return ' '.join(词表)

def 展示权限预设(值,名称,翻译=None):
    '内置预设用产品标签。宿主改过的名字用展示名'
    键=预设标签键[值] if 值 in 预设标签键 else None
    if 键 is not None and (名称==值 or 名称==默认预设标签[键]):
        if 翻译 is not None:
            return 翻译(键)
        return 默认预设标签[键]
    return 展示预设名(名称)
