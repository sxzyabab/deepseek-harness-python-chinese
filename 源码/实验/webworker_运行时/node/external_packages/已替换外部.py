"""Worker 整体替换的外部 npm 包名。放在无导入的模块中，供两个消费者读取：
运行时内置表（`./内建.py`）与构建期 VFS 镜像收集器——后者必须把这些包
完全排除出镜像：加载器在到达 `node_modules` 之前就从包内应答它们。

对齐上游 `webworker-runtime/src/node/external_packages/replaced-externals.ts`。
公开面仅中文名。
"""
__all__=['替换外部包清单']#仅中文公开名

替换外部包清单=(#替换包清单
    '@earendil-works/pi-ai',#pi-ai
    '@vscode/ripgrep',#ripgrep路径包
    'koffi',#FFI
    'node-pty',#伪终端
    'sharp',#图像转码
    'ws',#WebSocket
)#替换外部包清单结束
