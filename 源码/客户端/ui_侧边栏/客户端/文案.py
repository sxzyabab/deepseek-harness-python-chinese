"""`sidebar` 命名空间词典：外壳控件（品牌行、新建会话、折叠开关）。

对齐上游 `ui-sidebar/src/client/locales.ts`。公开面仅中文名；词典键与英文字面量保持上游。
"""

__all__=['中文','英文','侧栏文案键']#仅中文公开名

中文={#简体中文词条（键集合的权威源）
    'session.new':'新会话',#新会话按钮
    'session.new.label':'新建会话',#新建会话标签
    'toggle.open':'打开侧边栏',#打开侧边栏
    'toggle.collapse':'收起侧边栏',#收起侧边栏
}#中文词典结束

英文={#英文词条，键与中文权威源一致
    'session.new':'New Session',#新会话按钮
    'session.new.label':'New session',#新建会话标签
    'toggle.open':'Open sidebar',#打开侧边栏
    'toggle.collapse':'Collapse sidebar',#收起侧边栏
}#英文词典结束

侧栏文案键=tuple(中文.keys())#由中文词典键推导的键域
