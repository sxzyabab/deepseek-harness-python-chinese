"""Cordis 动态插件 UI 词表。

对齐上游 `ui-cordis/src/client/locales.ts`。公开面仅中文名；键与英文字面量保持上游。
"""

__all__=['命名空间','中文','英文','文案键']#仅中文公开名

命名空间='cordis'#本界面命名空间

中文={#简体中文
    'row.defineTitle':'注册 Cordis 插件',#定义行标题
    'row.runTitle':'运行 Cordis 插件',#运行行标题
    'row.updateTitle':'更新 Cordis 插件',#更新行标题
    'row.stopTitle':'停止 Cordis 插件',#停止行标题
    'row.removeTitle':'移除 Cordis 插件',#移除行标题
    'purpose.missing':'(未填写用途)',#用途缺省
    'status.idle':'待激活',#空闲
    'status.awaitingApproval':'待审批',#等审批
    'status.failed':'运行失败',#失败
    'status.clientPending':'Client 待激活',#客户端待激活
    'status.running':'运行中',#在跑
    'status.removed':'已移除',#已移除
    'status.superseded':'已有更新',#已被更新覆盖
    'run.removed':'包已不存在',#运行卡片：包没了
    'run.superseded':'已有更新的运行卡片，请查看下方',#运行卡片：有更新
    'panel.hint':'运行控制在左下角设置上方的 Cordis 面板',#面板提示
    'panel.plugins.aria':'Cordis 插件',#插件列表无障碍名
    'panel.approvals.aria':'Cordis 审批',#审批列表无障碍名
    'panel.trigger':'Cordis Plugin',#面板触发器标签
    'panel.runningCount':'{count} running',#运行计数模板
    'panel.title':'Cordis 插件',#面板标题
    'panel.empty':'还没有定义任何插件',#空状态
    'panel.loading':'读取中…',#读取中
    'panel.readFailed':'读取插件清单失败：{message}',#读取失败
    'panel.group.current':'当前会话',#本组
    'panel.group.others':'其他会话',#其他组
    'panel.version':'版本',#版本标签
    'panel.current':'当前：{packageId}',#当前包
    'panel.next':'待切换：{packageId}',#待切换包
    'action.approve':'允许',#允许
    'action.approveOnce':'仅允许此版本',#只批这个包
    'action.approvePlugin':'允许此插件的后续版本',#批后续版本
    'action.decline':'拒绝',#拒绝
    'action.run':'运行',#运行
    'action.stop':'停止',#停止
    'action.remove':'移除',#移除
    'action.retry':'重试',#重试
    'action.rollback':'回退',#回退
    'render.failedAbdicated':'{slot} 渲染失败，已恢复默认界面：',#渲染失败并摘掉入口
    'render.failedHeld':'{slot} 渲染失败：',#渲染失败仍占座
    'a11y.defining':'正在定义插件',#定义中无障碍
    'a11y.failed':'定义失败',#定义失败无障碍
    'a11y.stopped':'定义已中断',#定义中断无障碍
    'body.source':'插件代码',#源码区标题
    'body.hostCode':'Host',#宿主半标签
    'body.clientCode':'Client',#客户端半标签
    'body.output':'结果',#结果区标题
    'body.copy':'复制',#复制
    'body.copied':'已复制',#已复制
}#中文结束

英文={#英文
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
    'body.source':'Plugin code',
    'body.hostCode':'Host',
    'body.clientCode':'Client',
    'body.output':'Result',
    'body.copy':'Copy',
    'body.copied':'Copied',
}#英文结束

文案键=tuple(中文.keys())#键域
