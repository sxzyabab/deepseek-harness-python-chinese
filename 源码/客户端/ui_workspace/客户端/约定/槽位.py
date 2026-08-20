"""ui-workspace 槽约定：浏览区与挑选器注入面、目录流孔主人份额。

对齐上游 `ui-workspace/src/client/contract/slots.ts`。公开面仅中文名。
"""

__all__=[#仅中文公开名
    '目录流槽名',
    '目录流槽名表',
    '侧栏目录流槽',
    '英雄目录流槽',
    '添加工作区令牌',
]#公开面结束

英雄目录流槽='conversation.hero.workspace.directoryFlow'#会话空态目录流孔
侧栏目录流槽='sidebar.workspaces.directoryFlow'#侧栏浏览区目录流孔
目录流槽名=(#两个目录流孔名
    英雄目录流槽,#会话空态目录流孔
    侧栏目录流槽,#侧栏浏览区目录流孔
)#孔名结束
目录流槽名表=目录流槽名#别名，供登记面再导出
添加工作区令牌='::add-workspace'#菜单添加工作区条目 id
