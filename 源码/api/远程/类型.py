'转发宿主事件白名单的类型面：消费方键投影，以及它填进协议的选择席位'
from typing import Literal,TypedDict#字面量真值与结构类型
from .远程事件 import 远程转发事件#转发事件白名单常量

远程转发事件名=tuple(项['event'] for 项 in 远程转发事件)#白名单事件名

远程事件选择席位=TypedDict('远程事件选择席位',{#选择席位：键为真才允许 $on
    'agent-preset/selected':Literal[True],#智能体预设已选定
    'approval/request':Literal[True],#审批请求瀑布
    'api-session/activity':Literal[True],#会话活动
    'api-session/added':Literal[True],#会话已添加
    'api-session/error':Literal[True],#会话错误
    'api-session/removed':Literal[True],#会话已移除
    'api-session/status':Literal[True],#会话状态
    'commands/change':Literal[True],#命令表已变更
    'deepseek-account/session-expired':Literal[True],#账号会话已过期
    'deepseek-account/model-sign-in-required':Literal[True],#模型登录仍需要
    'credentials/record-updated':Literal[True],#凭证记录已更新
    'credentials/reference-updated':Literal[True],#凭证引用已更新
    'goal/activation-changed':Literal[True],#目标激活已变更
    'cordis/request-run':Literal[True],#请求运行动态包
    'cordis/request-run-resolved':Literal[True],#动态包运行请求已决议
    'cordis/dynamic-package':Literal[True],#动态包清单
    'cordis/dynamic-retract':Literal[True],#动态包撤回
    'cordis/inspect-query':Literal[True],#动态包探查查询
    'cordis/inspect-query-resolved':Literal[True],#动态包探查查询已决议
    'llm/adapters-updated':Literal[True],#大模型适配器已更新
    'permission-presets/catalog-changed':Literal[True],#权限预设目录已变更
    'plugin-manager/changed':Literal[True],#插件装载已变更
    'plugin-manager/install-log':Literal[True],#插件安装日志
    'plugin-manager/install-state':Literal[True],#插件安装状态
    'plugin-market/changed':Literal[True],#插件市场已变更
    'settings/document-updated':Literal[True],#设置文档已更新
    'schedule/changed':Literal[True],#日程已变更
    'user-questions/request':Literal[True],#用户提问瀑布
})#席位结束

__all__=['远程转发事件名','远程事件选择席位']#公开面
