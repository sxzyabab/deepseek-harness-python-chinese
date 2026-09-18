"""与客户端共享的插件装载公开记录；线协议键保持英文。"""

__all__=[#仅中文说明名；记录本身是 dict 形态
    '只读理由','装载错误码','插件信息','组合包行信息','组合包信息',
    '安装失败种类','包结果','变更结果','安装请求标识','安装组合包选项',
    '安装规格种类','检查问题','规格检查','安装进度','安装取消','安装日志块','插件变更',
]#公开面结束

#只读理由：management-required | unaddressable
#装载错误码：只读理由 | unknown-plugin | invalid-spec | ambiguous-install | not-bundle | not-removable | stop-profile | bundle-in-use | stale-approval | operation-error
#安装失败种类：pnpm-missing | timeout | not-found | no-matching-version | network | disk-full | permission | build-blocked | integrity | unknown
#变更应用态：applied | restart-required | overridden | failed | cancelled
#变更阶段：install | enable | remove
#安装规格种类：registry | path | git | tarball
#检查问题：invalid-spec | already-installed | not-found | not-a-package | not-a-bundle | network | unknown
#安装阶段：installing | cancelling | applying
#取消状态：cancelled | too-late | not-running
#变更原因：plugin | bundle | install | remove

#事件名（线协议不译）：
# plugin-manager/changed
# plugin-manager/install-log
# plugin-manager/install-state
