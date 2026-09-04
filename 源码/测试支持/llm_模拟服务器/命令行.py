"""独立 mock LLM 服务器的无依赖 CLI 解析。

对齐上游 `llm-mock-server/src/cli.ts`。公开面仅中文名。
"""
import argparse#参数解析
from . import (#导入行为与延迟上限
    模拟LLM行为名表,模拟LLM定时器延迟上限毫秒,
)#模块导入

__all__=[#仅中文公开名
    '连接拒绝行为','模拟LLM命令用法','解析模拟LLM命令参数',
]#公开面结束

连接拒绝行为='connection_refused'#连接拒绝行为名
行为集合=set(模拟LLM行为名表)#合法行为集
默认监听延迟毫秒=750#默认监听延迟
模拟LLM命令用法="""Usage: dsh-llm-mock-server [options]

Required:
  --sequence <a,b,...>       Ordered behaviors; connection_refused is allowed first

Listener:
  --host <host>              Default 127.0.0.1
  --port <port>              Default 8000; required and nonzero for connection_refused
  --api-key <token>          Validate exact Bearer token when present
  --listen-delay-ms <ms>     Unavailable interval (default 750 with connection_refused)
  --repeat-last              Repeat the final request behavior after exhaustion
  --seed <uint32>            Reproduce random selections
  --random-weights <a=n,...> Relative weights for concrete behaviors

Response:
  --success-text <text>
  --partial-text <text>
  --reasoning-text <text>
  --chunk-size <count>
  --chunk-delay-ms <ms>
  --disconnect-delay-ms <ms>
  --retry-after-ms <ms>
  --request-id <id>
  --tool-name <name>
  --tool-arguments <json>

Other:
  --help
"""#用法文案
Error=Exception#错误别名

def 数值(选项,值):#解析有限数
    """解析有限数。"""
    try:#解析
        解析=float(值)#解析数字
    except Exception:#失败
        raise Error(f'dsh-llm-mock-server: {选项} must be a finite number')#非有限
    if 解析!=解析 or 解析 in (float('inf'),float('-inf')):#非有限
        raise Error(f'dsh-llm-mock-server: {选项} must be a finite number')#非有限
    return 解析#返回数值

def 有界整数(选项,值,最小,最大):#解析有界整数
    """解析有界整数。"""
    解析=数值(选项,值)#先解析
    if 解析!=int(解析) or 解析<最小 or 解析>最大:#越界
        raise Error(f'dsh-llm-mock-server: {选项} must be an integer between {最小} and {最大}')#越界
    return int(解析)#返回有界整数

def 解析序列(原始):#解析行为序列
    """解析行为序列，允许首项 connection_refused。"""
    条目=[项.strip() for 项 in 原始.split(',')]#拆分条目
    if any(项=='' for 项 in 条目):#空条目
        raise Error('dsh-llm-mock-server: --sequence must contain non-empty comma-separated behaviors')#空条目
    先不可用=条目[0]==连接拒绝行为#是否先拒绝
    if 连接拒绝行为 in 条目[1:]:#位置非法
        raise Error('dsh-llm-mock-server: connection_refused is allowed only as the first behavior')#位置非法
    请求条目=条目[1:] if 先不可用 else 条目#请求级行为
    if len(请求条目)==0:#缺少后续
        raise Error('dsh-llm-mock-server: connection_refused must be followed by a request behavior')#缺少后续
    for 项 in 请求条目:#校验每个行为
        if 项 not in 行为集合:#未知行为
            raise Error(f'dsh-llm-mock-server: unknown behavior {项!r}')#未知行为
    return {'startsUnavailable':先不可用,'sequence':请求条目}#返回解析结果

def 解析随机权重(原始):#解析随机权重
    """解析 behavior=weight 逗号表。"""
    权重={}#权重表
    for 项 in 原始.split(','):#逐项
        段=项.split('=')#拆行为与权重
        if len(段)!=2 or 段[0]=='' or 段[1]=='':#格式非法
            raise Error('dsh-llm-mock-server: --random-weights expects behavior=weight comma-separated entries')#格式非法
        行为,原始权重=段#拆开
        if 行为 not in 行为集合 or 行为=='random':#必须具体行为
            raise Error(f'dsh-llm-mock-server: random weight requires a concrete behavior, got {行为!r}')#必须具体行为
        if 行为 in 权重:#重复
            raise Error(f'dsh-llm-mock-server: duplicate random weight for {行为!r}')#重复
        权重[行为]=数值('--random-weights',原始权重)#写入权重
    return 权重#返回权重

def 解析模拟LLM命令参数(参数向量):#解析 CLI 参数
    """解析独立服务器参数，不启动进程或监听器。"""
    if '--help' in 参数向量:#帮助
        return {'kind':'help'}#帮助
    解析器=argparse.ArgumentParser(add_help=False)#严格解析器
    解析器.add_argument('--sequence')#行为序列
    解析器.add_argument('--host')#主机
    解析器.add_argument('--port')#端口
    解析器.add_argument('--api-key')#API 密钥
    解析器.add_argument('--listen-delay-ms')#监听延迟
    解析器.add_argument('--repeat-last',action='store_true')#重复末项
    解析器.add_argument('--seed')#随机种子
    解析器.add_argument('--random-weights')#随机权重
    解析器.add_argument('--success-text')#成功文本
    解析器.add_argument('--partial-text')#部分文本
    解析器.add_argument('--reasoning-text')#推理文本
    解析器.add_argument('--chunk-size')#分片大小
    解析器.add_argument('--chunk-delay-ms')#分片延迟
    解析器.add_argument('--disconnect-delay-ms')#断开延迟
    解析器.add_argument('--retry-after-ms')#重试等待
    解析器.add_argument('--request-id')#请求 id
    解析器.add_argument('--tool-name')#工具名
    解析器.add_argument('--tool-arguments')#工具参数
    值=解析器.parse_args(list(参数向量))#解析旗标
    端口=8000 if 值.port is None else 数值('--port',值.port)#端口
    监听延迟=None if 值.listen_delay_ms is None else 有界整数('--listen-delay-ms',值.listen_delay_ms,0,模拟LLM定时器延迟上限毫秒)#监听延迟
    随机种子=None if 值.seed is None else 数值('--seed',值.seed)#随机种子
    随机权重=None if 值.random_weights is None else 解析随机权重(值.random_weights)#随机权重
    分片大小=None if 值.chunk_size is None else 数值('--chunk-size',值.chunk_size)#分片大小
    分片延迟=None if 值.chunk_delay_ms is None else 数值('--chunk-delay-ms',值.chunk_delay_ms)#分片延迟
    断开延迟=None if 值.disconnect_delay_ms is None else 数值('--disconnect-delay-ms',值.disconnect_delay_ms)#断开延迟
    重试等待=None if 值.retry_after_ms is None else 数值('--retry-after-ms',值.retry_after_ms)#重试等待
    if 值.sequence is None:#缺序列
        raise Error('dsh-llm-mock-server: --sequence is required')#缺序列
    解析序列结果=解析序列(值.sequence)#解析序列
    if 解析序列结果['startsUnavailable'] and 端口==0:#拒绝需要显式端口
        raise Error('dsh-llm-mock-server: connection_refused requires an explicit nonzero --port')#拒绝需要显式端口
    if not 解析序列结果['startsUnavailable'] and 监听延迟 is not None:#延迟依赖拒绝
        raise Error('dsh-llm-mock-server: --listen-delay-ms requires connection_refused first in --sequence')#延迟依赖拒绝
    if 'random' not in 解析序列结果['sequence'] and (随机种子 is not None or 随机权重 is not None):#随机选项依赖 random
        raise Error('dsh-llm-mock-server: --seed and --random-weights require random in --sequence')#随机选项依赖 random
    服务器={#服务器选项
        'sequence':解析序列结果['sequence'],#行为序列
        'port':端口,#端口
        'repeatLast':bool(值.repeat_last),#重复末项
    }#server 结束
    if 随机种子 is not None:#可选种子
        服务器['randomSeed']=随机种子#写入
    if 随机权重 is not None:#可选权重
        服务器['randomWeights']=随机权重#写入
    if 值.host is not None:#可选主机
        服务器['host']=值.host#写入
    if 值.api_key is not None:#可选密钥
        服务器['apiKey']=值.api_key#写入
    if 值.success_text is not None:#可选成功文本
        服务器['successText']=值.success_text#写入
    if 值.partial_text is not None:#可选部分文本
        服务器['partialText']=值.partial_text#写入
    if 值.reasoning_text is not None:#可选推理文本
        服务器['reasoningText']=值.reasoning_text#写入
    if 分片大小 is not None:#可选分片大小
        服务器['chunkSize']=分片大小#写入
    if 分片延迟 is not None:#可选分片延迟
        服务器['chunkDelayMs']=分片延迟#写入
    if 断开延迟 is not None:#可选断开延迟
        服务器['disconnectDelayMs']=断开延迟#写入
    if 重试等待 is not None:#可选重试等待
        服务器['retryAfterMs']=重试等待#写入
    if 值.request_id is not None:#可选请求 id
        服务器['requestId']=值.request_id#写入
    if 值.tool_name is not None:#可选工具名
        服务器['toolName']=值.tool_name#写入
    if 值.tool_arguments is not None:#可选工具参数
        服务器['toolArguments']=值.tool_arguments#写入
    return {#返回运行配置
        'kind':'run',#运行
        'config':{#配置
            'server':服务器,#服务器选项
            'listenDelayMs':(监听延迟 if 监听延迟 is not None else 默认监听延迟毫秒) if 解析序列结果['startsUnavailable'] else 0,#监听延迟
            'startsUnavailable':解析序列结果['startsUnavailable'],#是否先不可用
        },#config 结束
    }#返回

CONNECTION_REFUSED_BEHAVIOR=连接拒绝行为#上游名
MOCK_LLM_CLI_USAGE=模拟LLM命令用法#上游名
parseMockLlmCliArgs=解析模拟LLM命令参数#上游名
