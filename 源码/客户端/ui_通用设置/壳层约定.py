"""设置外壳约定——`sidebar.settings` 占位者的类型。

对齐上游 `ui-settings-general/src/client/shell-contract.ts`。公开面仅中文名。
放在本包而不是 ui_settings：引用侧栏槽类型；底座不得依赖任何 ui-* 展示包。
"""

__all__=[#仅中文公开名
    '设置分区行','设置引导步骤','设置根注入面','设置根组件属性',
]#公开面结束

#settings.section 注册 options 投影出的一行导航
设置分区行={'id':'','order':0,'label':''}#分区身份、排序、导航标签

#槽注册投影出的一步有序引导
设置引导步骤={'id':'','order':0}#步骤身份与排序

#设置外壳的注册方私有注入份额：账本投影为 hooks 隔间源
设置根注入面={'hooks':{#hooks 隔间
    'sections':None,#分区账本投影成有序导航行（HostObservable）
    'onboardingSteps':None,#引导账本投影成协调器顺序
}}#注入面结束

#设置外壳根组件完整 props 字段约定（侧栏主人份额 + 渲染份额 + 注入面）
设置根组件属性={#完整 props 字段名约定
    'wide':True,#侧栏宽/窄轨
    'renderSlot':None,#声明的渲染份额
    'inject':设置根注入面,#注入面
}#属性结束
