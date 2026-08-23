"""从 cordis.yml 启动 ACP stdio 服务器；用法是 dsh-acp-demo [--config path]，默认 ./cordis.yml。

对齐上游 `示例/acp-demo/src/bin.ts`。公开面仅中文名。
共享的 env 加载、Loader 守卫、快照配置选择与结算树启动都在 app_boot。
EOF 拆除并 flush 快照运行；调用方自动化拥有进程寿命。stdout 留给 JSON-RPC，诊断只走 stderr。
"""
import os,sys,argparse,threading#环境、进程、参数与 EOF 监视
from ...启动.app启动 import 启动,安装大声失败,加载环境,解析配置路径#启动粘合层
from ...依赖 import cordis#外部依赖胶水
是否thenable=cordis.工具.是否thenable#可等待

名称='dsh-acp-demo'#二进制诊断名前缀

安装大声失败(名称)#安装大声失败的 Loader 守卫
快照模式=os.environ.get('DSH_SNAPSHOT')#读取快照模式
if 快照模式!='replay':#回放不加载 .env
    加载环境(名称)#加载 .env
解析器=argparse.ArgumentParser(prog=名称,add_help=True)#参数解析
解析器.add_argument('-c','--config',default='./cordis.yml',help='cordis.yml 路径')#配置路径
参数=解析器.parse_args()#解析
上下文对象=启动(名称,解析配置路径(参数.config,快照模式))#启动结算树
if 快照模式 is not None:#快照运行由本进程在 EOF 退出
    def 标准输入结束():#stdin EOF
        """拆除 fiber 后以 0 退出。"""
        try:#读尽 stdin
            sys.stdin.read()#阻塞到 EOF
        except Exception:#读失败
            pass#忽略
        结果=上下文对象.fiber.dispose()#拆除
        if 是否thenable(结果):#可等待
            结果.等待()#等待
        sys.exit(0)#以 0 退出
    threading.Thread(target=标准输入结束,daemon=True).start()#后台监视 EOF
