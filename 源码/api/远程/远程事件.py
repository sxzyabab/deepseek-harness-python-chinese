"""本应用转发宿主事件白名单的唯一出处。

配置键、事件名字面量保持线协议。mode 同时是宿主派发策略与 `ctx.remote.$on` 合法键面。
"""
远程转发事件=(#宿主事件转发白名单：event 为线名，mode 为 emit 或 waterfall
    {'event':'agent-preset/selected','mode':'emit'},#智能体预设已选定
    {'event':'approval/request','mode':'waterfall'},#审批请求瀑布
    {'event':'api-session/activity','mode':'emit'},#会话活动
    {'event':'api-session/added','mode':'emit'},#会话已添加
    {'event':'api-session/error','mode':'emit'},#会话错误
    {'event':'api-session/removed','mode':'emit'},#会话已移除
    {'event':'api-session/status','mode':'emit'},#会话状态
    {'event':'commands/change','mode':'emit'},#命令表已变更
    {'event':'credentials/reference-updated','mode':'emit'},#凭证引用已更新
    {'event':'goal/activation-changed','mode':'emit'},#目标激活已变更
    {'event':'cordis/request-run','mode':'emit'},#请求运行动态包
    {'event':'cordis/request-run-resolved','mode':'emit'},#动态包运行请求已决议
    {'event':'cordis/dynamic-package','mode':'emit'},#动态包清单
    {'event':'cordis/dynamic-retract','mode':'emit'},#动态包撤回
    {'event':'cordis/inspect-query','mode':'emit'},#动态包探查查询
    {'event':'cordis/inspect-query-resolved','mode':'emit'},#动态包探查查询已决议
    {'event':'llm/adapters-updated','mode':'emit'},#大模型适配器已更新
    {'event':'permission-presets/catalog-changed','mode':'emit'},#权限预设目录已变更
    {'event':'plugin-manager/changed','mode':'emit'},#插件装载已变更
    {'event':'plugin-manager/install-log','mode':'emit'},#插件安装日志
    {'event':'plugin-manager/install-state','mode':'emit'},#插件安装状态
    {'event':'settings/document-updated','mode':'emit'},#设置文档已更新
    {'event':'user-questions/request','mode':'waterfall'},#用户提问瀑布
)#只读元组

__all__=['远程转发事件']#公开面
