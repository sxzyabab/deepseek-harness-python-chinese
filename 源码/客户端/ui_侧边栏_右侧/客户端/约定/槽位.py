
__all__=[#仅中文公开名
    '右侧侧栏词表命名空间',
    '席名右栏会话',
    '席名右侧签正文',
    '席名右侧签标题',
    '席名右侧向导',
    '席名右侧签菜单项',
    '右侧侧栏子槽',
]#公开面结束

右侧侧栏词表命名空间='sidebarRight'#文案命名空间（线路字面量）
席名右栏会话='rightbar.session'#会话右栏席
席名右侧签正文='sidebar.right.pane.tab'#键控正文席
席名右侧签标题='sidebar.right.pane.tab.title'#键控标题席
席名右侧向导='sidebar.right.tab.guide'#向导链席
席名右侧签菜单项='sidebar.right.tab.menu.item'#菜单列表席

右侧侧栏子槽={#右栏会话席声明的子槽
    席名右侧签正文:{'kind':'keyed','scope':'session'},#正文
    席名右侧签标题:{'kind':'keyed','scope':'session'},#标题
    席名右侧签菜单项:{'kind':'list','scope':'session'},#菜单
}#子槽结束
