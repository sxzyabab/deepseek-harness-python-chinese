"""可编脚本 mock LLM 服务器的独立进程包装。

对齐上游 `llm-mock-server/src/bin.ts`。公开面仅中文名。
"""
import json,sys,time,signal#JSON、标准流、延迟与信号
from .命令行 import 模拟LLM命令用法,解析模拟LLM命令参数#CLI 解析
from . import 启动模拟LLM服务器#服务器启动

__all__=['主入口']#仅中文公开名

def 主入口(参数向量=None):#进程入口
    """解析 CLI 并启动或打印帮助。"""
    if 参数向量 is None:#缺省 argv
        参数向量=sys.argv[1:]#去掉程序名
    try:#主路径
        解析=解析模拟LLM命令参数(参数向量)#解析 CLI
        if 解析['kind']=='help':#帮助
            sys.stdout.write(模拟LLM命令用法)#打印用法
            return#结束
        配置=解析['config']#拆配置
        服务器选项=配置['server']#服务器选项
        监听延迟=配置['listenDelayMs']#监听延迟
        先不可用=配置['startsUnavailable']#是否先不可用
        主机=服务器选项.get('host') or '127.0.0.1'#主机
        端口=服务器选项.get('port') if 'port' in 服务器选项 else 8000#端口
        if 先不可用:#先不可用
            sys.stdout.write(json.dumps({#宣布不可用
                'type':'unavailable',#事件类型
                'baseURL':f'http://{主机}:{端口}/v1',#基址
                'listenDelayMs':监听延迟,#延迟
            },ensure_ascii=False)+'\n')#宣布不可用窗口
            time.sleep(监听延迟/1000)#延迟绑定
        def 写事件(事件):#事件写 stdout
            """把遥测写成 JSONL。"""
            sys.stdout.write(json.dumps(事件,ensure_ascii=False)+'\n')#写行
            sys.stdout.flush()#冲刷
        服务器=启动模拟LLM服务器({**服务器选项,'onEvent':写事件})#启动服务器
        sys.stdout.write(json.dumps({#宣布就绪
            'type':'ready',#事件类型
            'baseURL':f"{服务器['baseURL']}/v1",#基址
            'randomSeed':服务器['randomSeed'],#随机种子
        },ensure_ascii=False)+'\n')#宣布就绪
        sys.stdout.flush()#冲刷
        关闭中=[False]#是否正在关闭
        def 关闭(码):#关闭并退出
            """幂等关闭服务器后退出。"""
            if 关闭中[0]:#幂等
                return#结束
            关闭中[0]=True#标记关闭
            服务器['close']()#关闭
            raise SystemExit(码)#退出
        signal.signal(signal.SIGINT,lambda *_:关闭(130))#Ctrl-C
        if hasattr(signal,'SIGTERM'):#有 SIGTERM
            signal.signal(signal.SIGTERM,lambda *_:关闭(143))#终止信号
        while not 关闭中[0]:#保持进程
            time.sleep(0.5)#短睡
    except Exception as 错误:#解析或启动失败
        消息=错误.args[0] if 错误.args else str(错误)#错误消息
        sys.stderr.write(f'{消息}\n\n{模拟LLM命令用法}')#错误与用法
        raise SystemExit(1)#失败退出码

if __name__=='__main__':#脚本入口
    主入口()#运行
