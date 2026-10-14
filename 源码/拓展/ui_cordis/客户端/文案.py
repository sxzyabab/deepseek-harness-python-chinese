__all__=['命名空间','中文','英文','文案键']#仅中文公开名

命名空间='cordis'

中文={
    'row.defineTitle':'注册 Cordis 插件',
    'row.runTitle':'运行 Cordis 插件',#运行行标题
    'row.updateTitle':'更新 Cordis 插件',
    'row.stopTitle':'停止 Cordis 插件',#停止行标题
    'row.removeTitle':'移除 Cordis 插件',
    'purpose.missing':'(未填写用途)',
    'status.idle':'待激活',
    'status.awaitingApproval':'待审批',
    'status.failed':'运行失败',
    'status.clientPending':'Client 待激活',
    'status.running':'运行中',
    'status.removed':'已移除',
    'status.superseded':'已有更新',
    'run.removed':'包已不存在',#运行卡片：包没了
    'run.superseded':'已有更新的运行卡片，请查看下方',#运行卡片：有更新
    'panel.hint':'运行控制在左下角设置上方的 Cordis 面板',
    'panel.plugins.aria':'Cordis 插件',
    'panel.approvals.aria':'Cordis 审批',
    'panel.trigger':'Cordis Plugin',
    'panel.runningCount':'{count} running',#运行计数模板
    'panel.title':'Cordis 插件',
    'panel.empty':'还没有定义任何插件',
    'panel.loading':'读取中…',
    'panel.readFailed':'读取插件清单失败：{message}',
    'panel.group.current':'当前会话',
    'panel.group.others':'其他会话',
    'panel.version':'版本',
    'panel.current':'当前：{packageId}',
    'panel.next':'待切换：{packageId}',
    'action.approve':'允许',
    'action.approveOnce':'仅允许此版本',#只批这个包
    'action.approvePlugin':'允许此插件的后续版本',
    'action.decline':'拒绝',
    'action.run':'运行',
    'action.stop':'停止',
    'action.remove':'移除',
    'action.retry':'重试',
    'action.rollback':'回退',
    'render.failedAbdicated':'{slot} 渲染失败，已恢复默认界面：',#渲染失败并摘掉入口
    'render.failedHeld':'{slot} 渲染失败：',#渲染失败仍占座
    'a11y.defining':'正在定义插件',
    'a11y.failed':'定义失败',#定义失败无障碍
    'a11y.stopped':'定义已中断',
    'a11y.preparing':'准备调用 Cordis 工具',#参数未齐时的前缀行
    'body.source':'插件代码',
    'body.hostCode':'Host',#宿主半标签
    'body.clientCode':'Client',
    'body.output':'结果',
    'body.copy':'复制',
    'body.copied':'已复制',
}

英文={
    'row.defineTitle':'Register Cordis Plugin',
    'row.runTitle':'Run Cordis Plugin',
    'row.updateTitle':'Update Cordis Plugin',
    'row.stopTitle':'Stop Cordis Plugin',
    'row.removeTitle':'Remove Cordis Plugin',
    'purpose.missing':'(no purpose given)',
    'status.idle':'Ready',
    'status.awaitingApproval':'Awaiting approval',
    'status.failed':'Run failed',
    'status.clientPending':'Client ready to activate',
    'status.running':'Running',
    'status.removed':'Removed',
    'status.superseded':'Superseded',
    'run.removed':'Package no longer exists',
    'run.superseded':'A newer run card is below',
    'panel.hint':'Run controls live in the Cordis panel above Settings',
    'panel.plugins.aria':'Cordis plugins',
    'panel.approvals.aria':'Cordis approvals',
    'panel.trigger':'Cordis Plugin',
    'panel.runningCount':'{count} running',
    'panel.title':'Cordis plugins',
    'panel.empty':'No plugins defined yet',
    'panel.loading':'Loading…',
    'panel.readFailed':'Failed to read plugin inventory: {message}',
    'panel.group.current':'This session',
    'panel.group.others':'Other sessions',
    'panel.version':'Version',
    'panel.current':'Current: {packageId}',
    'panel.next':'Pending: {packageId}',
    'action.approve':'Allow',
    'action.approveOnce':'Allow this version only',
    'action.approvePlugin':'Allow future versions of this plugin',
    'action.decline':'Decline',
    'action.run':'Run',
    'action.stop':'Stop',
    'action.remove':'Remove',
    'action.retry':'Retry',
    'action.rollback':'Roll back',
    'render.failedAbdicated':'{slot} failed to render; restored the default UI: ',
    'render.failedHeld':'{slot} failed to render: ',
    'a11y.defining':'Defining plugin',
    'a11y.failed':'Definition failed',
    'a11y.stopped':'Definition interrupted',
    'a11y.preparing':'Preparing a Cordis tool call',
    'body.source':'Plugin code',
    'body.hostCode':'Host',
    'body.clientCode':'Client',
    'body.output':'Result',
    'body.copy':'Copy',
    'body.copied':'Copied',
}

文案键=tuple(中文.keys())
