"""`question` 命名空间词典。

对齐上游 `ui-user-questions/src/client/locales.ts`。公开面仅中文名；词典键与英文字面量保持上游。
"""

__all__=['中文','英文','提问文案键']#仅中文公开名

中文={#简体中文词条（键集合的权威源）
    'error.incomplete':'请先完成这道问题。',#未答完时的错误
    'error.unanswered':'请选择一个选项或填写自定义答案。',#未作答时的错误
    'nav.prev':'上一题',#上一题导航
    'nav.next':'下一题',#下一题导航
    'nav.cancel':'放弃整组问题',#放弃整组
    'option.recommended':'推荐',#推荐选项标记
    'custom.placeholder':'输入你的答案',#自定义答案占位
    'action.skip':'跳过本题',#跳过本题
    'action.next':'下一题',#下一题动作
    'plan.header':'计划待审',#计划待审标题
    'plan.approve':'确认执行',#批准计划
    'plan.decline':'拒绝',#拒绝计划
    'plan.discuss':'去聊天里说',#改去聊天讨论
}#中文词典结束

英文={#英文词条，键与中文权威源一致
    'error.incomplete':'Please complete this question first.',#未答完时的错误
    'error.unanswered':'Please select an option or enter a custom answer.',#未作答时的错误
    'nav.prev':'Previous question',#上一题导航
    'nav.next':'Next question',#下一题导航
    'nav.cancel':'Dismiss all questions',#放弃整组
    'option.recommended':'Recommended',#推荐选项标记
    'custom.placeholder':'Type your answer',#自定义答案占位
    'action.skip':'Skip this question',#跳过本题
    'action.next':'Next',#下一题动作
    'plan.header':'Plan review',#计划待审标题
    'plan.approve':'Approve',#批准计划
    'plan.decline':'Refuse',#拒绝计划
    'plan.discuss':'Chat about it',#改去聊天讨论
}#英文词典结束

提问文案键=tuple(中文.keys())#由中文词典键推导的键域
