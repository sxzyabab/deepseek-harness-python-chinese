__all__=[#仅中文公开名
    '设置分区行','设置引导步骤','设置根注入面','设置根组件属性',
]#公开面结束

#settings.section 注册 options 投影出的一行导航
设置分区行={'id':'','order':0,'label':''}#分区身份、排序、导航标签

#槽注册投影出的一步有序引导
设置引导步骤={'id':'','order':0}#步骤身份与排序

#设置外壳的注册方私有注入份额：桌面更新/连接态与账本投影为 hooks 隔间源
设置根注入面={#注入面
    'openDesktopUpdate':None,#请求当前壳层拥有的更新动作
    'reconnect':None,#立即重连
    'hooks':{#hooks 隔间
        'desktopUpdate':None,#两侧栏共用 Electron 状态（HostObservable）
        'connectionState':None,#当前宿主连接态（HostObservable）
        'sections':None,#分区账本投影成有序导航行（HostObservable）
        'onboardingSteps':None,#引导账本投影成协调器顺序
    },#hooks结束
}#注入面结束

#设置外壳根组件完整 props 字段约定（侧栏主人份额 + 渲染份额 + 注入面）
设置根组件属性={#完整 props 字段名约定
    'wide':True,#侧栏宽/窄轨
    'renderSlot':None,#声明的渲染份额
    'inject':设置根注入面,#注入面
}#属性结束
