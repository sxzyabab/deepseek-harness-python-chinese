import re#短横线名判定
from .文案 import 英文#内置英文标签

__all__=['完全权限预设','自动审查预设','展示预设名','展示权限预设']#仅中文公开名

完全权限预设='danger-full-access'#需 GUI 风险门的机值
自动审查预设='auto'#实验性当前会话审查预设

预设标签键={#机值 → 文案键
    'read-only':'preset.readOnly',#只读
    'workspace-write':'preset.workspaceWrite',#工作区写
    完全权限预设:'preset.fullAccess',#完全
}#键表结束

默认预设标签={#内置英文标签
    'preset.readOnly':英文['preset.readOnly'],#只读
    'preset.workspaceWrite':英文['preset.workspaceWrite'],#工作区写
    'preset.fullAccess':英文['preset.fullAccess'],#完全
}#默认结束

短横线名=re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*\Z',re.ASCII)#常规短横线键

def 展示预设名(名称):
    """把常规短横线名转成词首大写；非短横线原样。"""
    if 短横线名.match(名称) is None:#非常规
        return 名称#原样
    词表=名称.split('-')#词
    return ' '.join(词[0].upper()+词[1:] if len(词)>0 else 词 for 词 in 词表)#词首大写

def 展示权限预设(值,名称,翻译=None):
    """内置产品标签，否则常规展示名。"""
    if 值 not in 预设标签键:#非常规机值
        return 展示预设名(名称)#展示名
    键=预设标签键[值]#文案键
    if 名称==值 or 名称==默认预设标签[键]:#宿主未改名
        if 翻译 is not None:#有词典
            return 翻译(键)#本地化
        return 默认预设标签[键]#英文
    return 展示预设名(名称)#宿主名
