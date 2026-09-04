"""worker 束的模块代理表：宿主树的唯一平台分叉。每个条目替换一个 Node
内建或外部 npm 包；workspace 与 vendored 模块始终按原样挂载。

构建把这些变成打包器别名，`node/builtins.ts` 把同一批模块变成加载器的
静态表——一份列表，两个消费者。

对齐上游 `webworker-runtime/src/module-proxies.ts`。公开面仅中文名。
"""
__all__=['模块代理表','模块代理前缀表']#仅中文公开名

模块代理表={#精确说明符代理表
    #以VFS为后端的真实实现。
    'node:fs':'./node/builtin_modules/implemented/fs.ts',#fs实现
    'fs':'./node/builtin_modules/implemented/fs.ts',#fs裸名
    'node:fs/promises':'./node/builtin_modules/implemented/fs/promises.ts',#fs/promises实现
    'fs/promises':'./node/builtin_modules/implemented/fs/promises.ts',#fs/promises裸名
    'node:path':'./node/builtin_modules/implemented/path.ts',#path实现
    'path':'./node/builtin_modules/implemented/path.ts',#path裸名
    'node:path/posix':'./node/builtin_modules/implemented/path.ts',#path/posix同实现
    'node:os':'./node/builtin_modules/implemented/os.ts',#os实现
    'os':'./node/builtin_modules/implemented/os.ts',#os裸名
    'node:url':'./node/builtin_modules/implemented/url.ts',#url实现
    'node:module':'./node/builtin_modules/implemented/module.ts',#module实现
    'node:crypto':'./node/builtin_modules/implemented/crypto.ts',#crypto实现
    'crypto':'./node/builtin_modules/implemented/crypto.ts',#crypto裸名
    #`buffer`本身保持未别名：shim由该npm包支撑。
    'node:buffer':'./node/builtin_modules/implemented/buffer.ts',#buffer实现
    #隧道请求源：假bind，真路由面。`node:process`与`process`故意缺席——
    #worker宿主安装该全局（`./globals/process.ts`）。
    'node:http':'./node/builtin_modules/implemented/http.ts',#http实现
    #同步栈AsyncLocalStorage语义。
    'node:async_hooks':'./node/builtin_modules/implemented/async_hooks.ts',#async_hooks实现
    #基于浏览器原语的真实实现。
    'node:util':'./node/builtin_modules/implemented/util.ts',#util实现
    'node:util/types':'./node/builtin_modules/implemented/util/types.ts',#util/types实现
    'node:events':'./node/builtin_modules/implemented/events.ts',#events实现
    'node:timers/promises':'./node/builtin_modules/implemented/timers/promises.ts',#timers/promises实现
    'node:perf_hooks':'./node/builtin_modules/implemented/perf_hooks.ts',#perf_hooks实现
    'node:tty':'./node/builtin_modules/implemented/tty.ts',#tty实现
    'tty':'./node/builtin_modules/implemented/tty.ts',#tty裸名
    #真实zstd编解码器：会话日志追加在每次写入时压缩。
    'node:zlib':'./node/builtin_modules/implemented/zlib.ts',#zlib实现
    #worker自己的进程层：`bash -c`与命令表对着VFS跑，
    #因为浏览器worker没有可fork的进程。
    'node:child_process':'./node/builtin_modules/implemented/child_process.ts',#child_process实现
    #结构性mock：每个符号存在，每次调用抛出。
    'node:dns/promises':'./node/builtin_modules/mock/dns/promises.ts',#dns/promises mock
    'dns/promises':'./node/builtin_modules/mock/dns/promises.ts',#dns/promises裸名
    'node:net':'./node/builtin_modules/mock/net.ts',#net mock
    'node:stream':'./node/builtin_modules/implemented/stream.ts',#stream实现
    'node:vm':'./node/builtin_modules/mock/vm.ts',#vm mock
    'node:worker_threads':'./node/builtin_modules/mock/worker_threads.ts',#worker_threads mock
    'node:sqlite':'./node/builtin_modules/mock/sqlite.ts',#sqlite mock
    #外部npm替换，以各自所替代的包命名。
    'koffi':'./node/external_packages/koffi.ts',#koffi替换
    'sharp':'./node/external_packages/sharp.ts',#sharp替换
    'node-pty':'./node/external_packages/node-pty.ts',#node-pty替换
    '@vscode/ripgrep':'./node/external_packages/ripgrep.ts',#ripgrep替换
    '@earendil-works/pi-ai':'./node/external_packages/pi-ai.ts',#pi-ai替换
    #可构造的假对象，其方法从不被触及。
    'ws':'./node/external_packages/ws.ts',#ws替换
}#模块代理表结束

模块代理前缀表={#前缀代理表；pi-ai子路径共享同一个结构性stub
    '@earendil-works/pi-ai/':'./node/external_packages/pi-ai.ts',#pi-ai子路径
}#前缀表结束
