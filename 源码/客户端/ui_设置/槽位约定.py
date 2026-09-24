__all__=[
    '通用条目主人份额',
    '插件页签主人份额',
    '触发器主人份额',
    '页眉主人份额',
    '分区主人份额',
    '引导主人份额',
    '启动器主人份额',
]

通用条目主人份额={'children':None}#故意为空标记
插件页签主人份额={'children':None}#故意为空标记
触发器主人份额={'wide':True}#宽轨为真；窄轨仅图标
页眉主人份额={'children':None}#故意为空标记
分区主人份额={'close':None}#关闭设置面板回调
引导主人份额={'stepId':'','explicit':False,'complete':None,'openSection':None}#步骤 id 与协调器动作
启动器主人份额={'wide':True,'openSettings':None,'openOnboarding':None}#侧栏启动器
