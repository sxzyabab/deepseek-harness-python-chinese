'有界 Node 程序：宿主拥有绑定、输出上限与受管进程清理'
import codecs,math,os,sys,threading#增量解码、有限数、路径、冻结探测与后台线程
from ...依赖.schemastery import 数字字段,字符串字段#配置字段
from ...工具.超时 import (#截止
    定时器延迟上限毫秒,#定时器上限
    夹取超时,#钳截止
    等待中止,#中止类已禁用
)#超时结束
from ...工具.值 import 快照json值#绑定返回值
from ...沙盒.沙盒.异常 import 沙箱不可用错误#沙箱失败
from ...沙盒.沙盒 import 分类运行器失败,是否运行器派生失败#沙箱失败
from ..ptc运行时 import ptc运行时#缝上服务
from .异常 import 节点ptc错误#本包异常
from .绑定 import 校验绑定#绑定名
from ...基础设施.js特性 import PromiseEX as 期约#期约
from .通道 import json通道#控制通道
from .启动 import 引导参数#argv 尾
from .输出账本 import 输出账本#外层账本
from .输出流 import 排空输出#排空
from .环境 import 启动环境名#启动环境
from .json线 import 解码ptcjson线,编码ptcjson线#线格式
from . import (
    协议,
    引导,
    输出json,
    进程,
    进程入口,
)

__all__=[#仅中文公开名
    '节点ptc运行时','名称','依赖','配置',
]#公开面结束

名称='ptc-runtime-node'#Cordis 插件名
依赖=['fs','subprocess','sandbox','sandboxPolicy']#所需服务
配置={#部署可变界限与启动选择
    'timeoutMs':数字字段(默认值=120_000),#默认经过时间截止
    'maxTimeoutMs':数字字段(默认值=600_000),#解析器上限
    'maxOutputBytes':数字字段(默认值=67_108_864),#合计输出预算
    'maxOldGenerationSizeMb':数字字段(默认值=512),#V8 老生代 MiB
    'maxMessageBytes':数字字段(默认值=134_217_728),#控制帧上限
    'maxPendingCalls':数字字段(默认值=128),#同时绑定调用上限
    'graceMs':数字字段(默认值=3_000),#终止与排空宽限
    'nodeExecutable':字符串字段(),#子进程世界可执行
    'bootstrapPath':字符串字段(),#预装引导绝对路径
}#配置结束

执行说明文案=('Each call runs in a fresh Node process. Node APIs are available through await import(...). '
    +'Relative paths use the supplied working directory; process.env starts empty. '
    +'Direct filesystem access follows this execution\'s sandbox policy.')#面向模型的执行说明

def 消息于(错误):#错误英文消息
    '异常取消息，其它强制转字符串'
    if isinstance(错误,BaseException) and len(错误.args)>0:#有消息
        return str(错误.args[0]) if type(错误.args[0]) is str else str(错误)#消息
    return str(错误)#强制转

def 是否记录(值):#非数组对象
    '是否为非空且非 list 的 dict'
    return type(值) is dict#只要 dict

def 读管道(流,接纳,失败):#一路 UTF-8 管道
    '阻塞读到结束，增量解码后交给接纳'
    解码器=codecs.getincrementaldecoder('utf-8')()#增量 UTF-8
    try:#读
        while True:#直到 EOF
            块=流.read(65536)#一块
            if not 块:#结束
                break#停
            文本=解码器.decode(块)#增量
            if len(文本)>0:#有文本
                接纳(文本)#接纳
        文本=解码器.decode(b'',True)#收尾
        if len(文本)>0:#有文本
            接纳(文本)#接纳
    except (OSError,ValueError,UnicodeDecodeError) as 错误:#传输
        失败(错误)#失败

class 节点ptc运行时(ptc运行时):#Node 提供方
    '直接文件效果与 Bash 共用同一沙箱服务'
    def __init__(自身,上下文,配置):#记下配置并挂清理
        '校验正有限界限，缺省节点可执行为 node'
        super().__init__(上下文)#登记 ptcRuntime
        已解析=dict(配置)#拷贝
        if 'nodeExecutable' not in 已解析 or 已解析['nodeExecutable'] is None or 已解析['nodeExecutable']=='':#缺省
            已解析['nodeExecutable']='node'#裸名
        自身.配置=已解析#记下
        for 键,值 in 自身.配置.items():#数值必须正有限
            if type(值) is bool:#布尔不是数
                continue#跳过
            if isinstance(值,(int,float)) and (not math.isfinite(值) or 值<=0):#非正或非有限
                raise 节点ptc错误('ptc-runtime-node: '+键+' must be positive and finite')#拒绝
        for 键 in ('timeoutMs','maxTimeoutMs','graceMs'):#定时器范围
            if 自身.配置[键]>定时器延迟上限毫秒:#超上限
                raise 节点ptc错误('ptc-runtime-node: '+键+' exceeds the supported timer range')#拒绝
        最大输出=自身.配置['maxOutputBytes']#输出上限
        if type(最大输出) is bool or type(最大输出) is not int or 最大输出<4:#至少 4
            raise 节点ptc错误('ptc-runtime-node: maxOutputBytes must be an integer of at least 4')#拒绝
        最大消息=自身.配置['maxMessageBytes']#消息上限
        if type(最大消息) is bool or type(最大消息) is not int or 最大消息>0xffffffff:#32 位帧
            raise 节点ptc错误('ptc-runtime-node: maxMessageBytes must fit an unsigned 32-bit frame length')#拒绝
        for 键 in ('maxPendingCalls','maxOldGenerationSizeMb'):#必须整数
            值=自身.配置[键]#取出
            if type(值) is bool or type(值) is not int:#非整数
                raise 节点ptc错误('ptc-runtime-node: '+键+' must be an integer')#拒绝
        if len(自身.配置['nodeExecutable'])==0:#空可执行
            raise 节点ptc错误('ptc-runtime-node: nodeExecutable must be non-empty')#拒绝
        if 'bootstrapPath' in 自身.配置 and 自身.配置['bootstrapPath'] is not None:#有预装
            if not os.path.isabs(自身.配置['bootstrapPath']):#必须绝对
                raise 节点ptc错误('ptc-runtime-node: bootstrapPath must be absolute')#拒绝
        自身.存活=[]#进行中的运行
        自身.已释放=False#是否已拆
        def 登记清理():#fiber 拆除登记
            '交出拆除器，中止并等进行中的运行'
            def 拆除():#插件拆除
                '中止并返回进行中运行的落定期约'
                自身.已释放=True#标记
                活动=list(自身.存活)#快照
                for 运行 in 活动:#逐个
                    运行['控制器'].中止(节点ptc错误('runtime disposed'))#中止
                return 期约.全部([运行['完成'] for 运行 in 活动])#全部落定
            return 拆除#拆除器
        上下文.副作用(登记清理,'Node ptc-runtime cleanup')#登记

    def 语言(自身):#源语言
        'run 期望的小写语言标识'
        return 'typescript'#TypeScript

    def 隔离(自身):#执行基底
        '小写执行基底标识'
        return 'process'#进程

    def 执行说明(自身):#程序用法
        '提供方拥有的用法说明'
        return 执行说明文案#固定英文

    def 沙箱模式(自身):#部署文件政策
        '文件政策模式'
        return 自身.ctx.sandboxPolicy.defaultMode#部署默认

    def 超时(自身):#数值截止描述
        '{defaultMs,maxMs}'
        默认=min(自身.配置['timeoutMs'],自身.配置['maxTimeoutMs'])#有效默认
        return {'defaultMs':默认,'maxMs':自身.配置['maxTimeoutMs']}#描述

    def 解析(自身,请求):#解析一次执行
        """补全 cwd、数值或空截止与执行策略。
        请求是 dict
        """
        if 自身.已释放:#已拆
            raise 节点ptc错误('ptc-runtime-node: resolve after disposal')#拒绝
        if 'sandboxPolicy' in 请求 and 请求['sandboxPolicy'] is not None:#请求自带
            政策=请求['sandboxPolicy']#用请求
        else:#部署解析
            政策=自身.ctx.sandboxPolicy.解析()#默认政策
        if 'cwd' in 请求 and 请求['cwd'] is not None:#请求目录
            目录=请求['cwd']#用请求
        else:#政策根
            目录=政策['workspaceRoot']#工作区根
        if not os.path.isabs(目录):#必须绝对
            raise 节点ptc错误('ptc-runtime-node: cwd must be absolute')#拒绝
        规格=dict(请求)#拷贝
        规格['cwd']=目录#绝对目录
        规格['sandboxPolicy']=政策#已解析政策
        if 'timeoutMs' in 请求 and 请求['timeoutMs'] is None:#显式不设截止
            规格['timeoutMs']=None#空截止
        else:#数值截止
            请求截止=请求['timeoutMs'] if 'timeoutMs' in 请求 else None#可选
            规格['timeoutMs']=夹取超时(请求截止,自身.配置['timeoutMs'],自身.配置['maxTimeoutMs'],'ptc-runtime-node: timeoutMs')#钳
        return 规格#已解析

    def 运行(自身,规格):#跑已解析程序
        """在全新受管隔离 Node 进程中跑。
        规格是 dict。
        返回期约，清理完成后解决为运行结果
        """
        if 自身.已释放:#已拆
            raise 节点ptc错误('ptc-runtime-node: run after disposal')#拒绝
        if 'sandboxPolicy' not in 规格 or 规格['sandboxPolicy'] is None:#缺政策
            raise 节点ptc错误('ptc-runtime-node: run requires a resolved sandbox policy')#拒绝
        截止=规格['timeoutMs']#截止
        if not os.path.isabs(规格['cwd']):#目录
            raise 节点ptc错误('ptc-runtime-node: run requires resolved cwd and timeout')#拒绝
        if 截止 is not None:#数值截止
            if type(截止) is bool or not isinstance(截止,(int,float)) or 截止<=0 or 截止>自身.配置['maxTimeoutMs']:#非法
                raise 节点ptc错误('ptc-runtime-node: run requires resolved cwd and timeout')#拒绝
        绑定=校验绑定(规格)#绑定表
        控制器=中止控制器()#本运行
        完成=期约()#运行落定
        存活={'控制器':控制器,'完成':完成}#登记项
        自身.存活.append(存活)#记下
        def 运行结束(结果值):#成功
            '摘掉存活并放开拆除，原样交还结果'
            if 存活 in 自身.存活:#仍在
                自身.存活.remove(存活)#移除
            if 完成.状态=='pending':#尚未放开
                完成.解决()#放开拆除
            return 结果值#原结果
        def 运行失败(错误):#失败
            '摘掉存活并放开拆除，再拒绝'
            if 存活 in 自身.存活:#仍在
                自身.存活.remove(存活)#移除
            if 完成.状态=='pending':#尚未放开
                完成.解决()#放开拆除
            失败=期约()#拒绝回执
            失败.拒绝(错误)#原错误
            return 失败#继续拒绝
        try:#执行
            执行结果=自身._执行(规格,规格['sandboxPolicy'],绑定,控制器)#结果期约
        except BaseException as 错误:#执行器自身抛出
            执行结果=期约()#失败回执
            执行结果.拒绝(错误)#拒绝
        return 执行结果.然后(运行结束,运行失败)#摘掉后交还原结果

    def _执行(自身,规格,政策,绑定,控制器):#一次受管执行
        '启动进程、分帧、绑定调用与清理'
        账本=输出账本(自身.配置['maxOutputBytes'])#外层账本
        日志=[]#已接纳日志
        沙箱={'mode':政策['mode'],'denied':False}#沙箱事实
        结果任务=期约()#调用方结果
        if 'signal' not in 规格 or 规格['signal'] is None:#无上游
            信号=控制器.信号#只用本运行
        else:#融合
            信号=合成信号(规格['signal'],控制器.信号)#先中止获胜
        句柄=None#子进程
        通道=None#控制通道
        已隔离=None#隔离 argv
        已结算=[False]#只结算一次
        已超时=[False]#墙钟
        输出溢出=[False]#外层上限
        溢出结果=[None]#预计算超限结果
        标准误=['']#尾部 stderr
        解析中=[True]#strip/解析阶段
        锁=threading.Lock()#结算锁
        墙钟=None#定时器
        def 收尾(失败=None,值=None):#结算一次运行
            '清理受管进程后解决结果'
            with 锁:#互斥
                if 已结算[0]:#已结算
                    return#忽略
                已结算[0]=True#标记
            if 墙钟 is not None:#有定时器
                墙钟.cancel()#取消
            if 通道 is not None:#有通道
                通道.关闭()#关
            失败盒=[失败]#清理期间可改写的失败
            def 交还结局(忽略=None):#写出沙箱事实并解决
                '按溢出、成功或失败解决调用方结果。忽略是然后传入的汇合值'
                if 输出溢出[0]:#输出上限优先
                    结局=溢出结果[0] if 溢出结果[0] is not None else 账本.超限(日志)#超限
                elif 失败盒[0] is None:#成功
                    结局=账本.成功(日志,值)#成功
                else:#失败
                    结局=账本.失败(日志,失败盒[0])#失败
                结局['sandbox']=dict(沙箱)#沙箱事实
                if 结果任务.状态=='pending':#尚未解决
                    结果任务.解决(结局)#解决
            def 关掉输出():#关掉两路管道
                '关掉标准输出与标准错误'
                if 句柄 is None:#无进程
                    return#无流
                for 流 in (句柄.stdout,句柄.stderr):#两路
                    if 流 is None:#无
                        continue#跳过
                    try:#关
                        流.close()#关
                    except (OSError,ValueError):#已关
                        pass#忽略
            def 清理出错(错误):#终止或等待失败
                '记清理失败后仍交还结局'
                失败盒[0]={'kind':'worker-exit','message':'managed process cleanup failed: '+消息于(错误)}#失败
                关掉输出()#关流
                交还结局()#解决
            if 句柄 is None:#没有进程
                交还结局()#直接解决
                return#无清理
            try:#开始终止
                句柄.终止()#升级终止
            except (节点ptc错误,OSError,ValueError) as 错误:#终止失败
                清理出错(错误)#记失败
                return#已交还
            def 忽略结局(错误):#孩子结局拒绝不挡清理
                '吞掉结局拒绝'
                return None#当成功
            def 进程已退出(落定值):#结局与整树都已结算
                '排空输出后交还结局。落定值是两路汇合值'
                try:#排空
                    出干净=排空输出(句柄.stdout,自身.配置['graceMs'])#stdout
                    错干净=排空输出(句柄.stderr,自身.配置['graceMs'])#stderr
                    if (not 出干净 or not 错干净) and 失败盒[0] is None:#未干净结束
                        失败盒[0]={'kind':'worker-exit','message':'Node process output did not close cleanly'}#失败
                except (节点ptc错误,OSError,ValueError) as 错误:#排空失败
                    失败盒[0]={'kind':'worker-exit','message':'managed process cleanup failed: '+消息于(错误)}#失败
                关掉输出()#关流
                交还结局()#解决
            期约.全部([句柄.done.捕获(忽略结局),句柄.等待退出()]).然后(进程已退出,清理出错)#结局与整树
        def 因中止():#中止回调
            '超时或取消'
            if 已超时[0]:#墙钟
                收尾({'kind':'timeout','message':'execution deadline reached ('+str(规格['timeoutMs'])+'ms)'})#超时
                return
            原因='The operation was aborted'#默认
            try:#取原因
                若已中止则抛出(信号)#抛原因
            except BaseException as 错误:#原因
                原因=消息于(错误)#文案
            收尾({'kind':'abort','message':原因})#取消
        def 监视中止():#后台等中止
            '阻塞到信号中止'
            等待中止(信号)#等待
            因中止()#收尾
        中止线程=threading.Thread(target=监视中止,daemon=True)#监视
        中止线程.start()
        if 已中止(信号):#已经中止
            因中止()#立刻
            return 结果任务#已结算
        if 规格['timeoutMs'] is not None:#有墙钟
            def 到期():#墙钟
                '标记超时并中止'
                已超时[0]=True#超时
                控制器.中止(节点ptc错误('execution deadline reached'))#中止
            墙钟=threading.Timer(规格['timeoutMs']/1000.0,到期)#定时器
            墙钟.daemon=True#守护
            墙钟.start()#武装
        try:#启动进程
            if 已结算[0]:#中止已结算
                return 结果任务#结果
            代码=规格['program']#程序体；Python 宿主不擦 TS 类型
            解析中[0]=False#进入启动
            空间列表=[]#boot 命名空间
            for 项 in 绑定.values():#按插入序
                一条={'global':项['global'],'names':list(项['functions'].keys())}#全局与名
                if 'errorClass' in 项 and 项['errorClass'] is not None:#有错误类
                    一条['errorClass']=项['errorClass']#带上
                空间列表.append(一条)#收下
            引导={'code':代码,'namespaces':空间列表,'maxOutputBytes':自身.配置['maxOutputBytes']}#boot
            可执行=自身.ctx.subprocess.解析可执行文件(自身.配置['nodeExecutable'],None,信号)#解析
            if 已结算[0]:#中止
                return 结果任务#结果
            打包=hasattr(sys,'frozen') and ('bootstrapPath' not in 自身.配置 or 自身.配置['bootstrapPath'] is None)#打包
            堆标志='--max-old-space-size='+str(自身.配置['maxOldGenerationSizeMb'])#堆上限
            参数表=[可执行]#argv0
            if not 打包:#非打包
                参数表.append(堆标志)#堆标志
            参数表.extend(引导参数(自身.ctx.fs,自身.配置,自身.配置['maxMessageBytes']))#引导
            if 政策['mode']!='danger-full-access':#需要隔离
                已隔离=自身.ctx.sandbox.隔离(参数表,政策)#包装 argv
            if 已结算[0]:#中止
                return 结果任务#结果
            if 已隔离 is not None and 'enforcement' in 已隔离:#强制能力
                沙箱['enforcement']=已隔离['enforcement']#记下
            环境={}#墓碑表
            for 键 in os.environ.keys():#父环境
                if 键.upper() not in 启动环境名 and 键.upper()!='ELECTRON_RUN_AS_NODE':#非启动名且非 Electron 选择器
                    环境[键]=None#删除墓碑
            if 打包:#打包可执行
                环境['DSH_PTC_RUNTIME_NODE']='1'#标记
                环境['NODE_OPTIONS']=堆标志#堆
            启动参数表=已隔离['argv'] if 已隔离 is not None else 参数表#最终 argv
            句柄=自身.ctx.subprocess.启动({'argv':启动参数表,'cwd':规格['cwd'],'env':环境,'stdio':{'stdin':'ignore','stdout':'pipe','stderr':'pipe','control':'pipe'},'graceMs':自身.配置['graceMs'],'signal':信号})#启动
            if 句柄.control is None or 句柄.stdout is None or 句柄.stderr is None:#缺管
                raise 节点ptc错误('subprocess provider did not supply the requested control and output pipes')#拒绝
            def 接纳(文本):#一条外层文本
                '接纳或触顶收尾'
                if 输出溢出[0]:#已溢出
                    return#忽略
                if not 账本.接纳(文本,日志):#越顶
                    输出溢出[0]=True#标记
                    溢出结果[0]=账本.超限(日志+[文本])#预计算
                    收尾({'kind':'output-limit','message':'outer output exceeded '+str(自身.配置['maxOutputBytes'])+' bytes'})#收尾
            def 管道失败(错误):#stdout/stderr
                '传输失败'
                收尾({'kind':'worker-exit','message':消息于(错误)})#失败
            出线程=threading.Thread(target=读管道,args=(句柄.stdout,接纳,管道失败),daemon=True)#stdout
            def 接纳标准误(文本):#stderr 另留尾
                '接纳并保留尾部'
                标准误[0]=(标准误[0]+文本)[-自身.配置['maxOutputBytes']:]#尾部
                if len(文本)>0:#有文本
                    接纳(文本)#入账
            错线程=threading.Thread(target=读管道,args=(句柄.stderr,接纳标准误,管道失败),daemon=True)#stderr
            出线程.start()#读出
            错线程.start()#读错
            已就绪=[False]#ready
            下一标识=[1]#调用 id
            未决数=[0]#同时调用
            未决字节=[0]#未决帧字节
            def 协议失败(消息):#畸形帧
                '协议失败收尾'
                收尾({'kind':'protocol','message':消息})#协议
            def 进程结束(结局):#孩子退出
                '提前退出分类'
                if 已结算[0]:#已结算
                    return#忽略
                if 已隔离 is not None and 分类运行器失败(结局['exitCode'],标准误[0],已隔离['runnerFailureRules']) is not None:#运行器
                    收尾({'kind':'sandbox-unavailable','message':标准误[0]})#沙箱
                    return
                收尾({'kind':'worker-exit','message':'Node process exited before completing ('+str(结局['exitCode'])+')'+(': '+标准误[0] if 标准误[0] else '')})#退出
            def 接收(原始,字节):#控制帧
                '分派 ready/log/done/call'
                if not 是否记录(原始):#非对象
                    协议失败('invalid control frame')#协议
                    return
                if not 已就绪[0]:#等 ready
                    if 原始.get('type')!='ready':#不是
                        协议失败('program frame arrived before bootstrap readiness')#协议
                        return
                    已就绪[0]=True#就绪
                    def 引导发送失败(错误):#boot 帧失败
                        '引导帧发送失败'
                        协议失败(消息于(错误))#协议
                    try:#发 boot
                        写出=通道.发送({'type':'boot','data':引导})#引导期约
                    except (节点ptc错误,OSError,ValueError,TypeError) as 错误:#编码失败
                        协议失败(消息于(错误))#协议
                        return#不再挂捕获
                    写出.捕获(引导发送失败)#传输失败
                    return
                种类=原始.get('type')#帧类
                if 种类=='log':#日志
                    if type(原始.get('text')) is not str:#必须字符串
                        协议失败('invalid log frame')#协议
                        return
                    接纳(原始['text'])#接纳
                    return
                if 种类=='output-limit':#程序侧触顶
                    输出溢出[0]=True#标记
                    收尾()#无失败字段，走超限结果
                    return
                if 种类=='done':#终态
                    if 'error' in 原始 and 原始['error'] is not None:#失败
                        错=原始['error']#错误
                        if (not 是否记录(错) or type(错.get('message')) is not str
                                or 错.get('kind') not in ('exception','invalid-output','output-limit')):#畸形
                            协议失败('invalid terminal error')#协议
                            return
                        失败={'kind':错['kind'],'message':错['message']}#失败
                        if 已隔离 is not None:#拒绝签名
                            小写=失败['message'].lower()#小写
                            for 签名 in 已隔离['denialSignatures']:#逐条
                                if 签名.lower() in 小写:#命中
                                    沙箱['denied']=True#拒绝
                                    break#停
                        if 失败['kind']=='output-limit':#输出上限
                            输出溢出[0]=True#标记
                        收尾(失败)#失败
                        return
                    if 'value' not in 原始 or 原始['value'] is None:#无完成值
                        收尾(None,None)#缺席完成
                        return
                    值=解码ptcjson线(原始['value'])#重建
                    if 值 is None:#有损
                        收尾({'kind':'invalid-output','message':'program completion must be lossless JSON'})#有损
                    else:#无损
                        收尾(None,值)#成功
                    return
                if 种类=='call':#绑定调用
                    标识=原始.get('id')#调用 id
                    if (type(标识) is bool or type(标识) is not int or 标识!=下一标识[0]
                            or type(原始.get('global')) is not str or type(原始.get('name')) is not str):#身份
                        协议失败('invalid binding call identity')#协议
                        return
                    下一标识[0]=标识+1#推进
                    函数表=绑定[原始['global']]['functions'] if 原始['global'] in 绑定 else None#函数
                    函数=函数表[原始['name']] if 函数表 is not None and 原始['name'] in 函数表 else None#取出
                    if not callable(函数):#未声明
                        协议失败('program requested an undeclared binding')#协议
                        return
                    参数=解码ptcjson线(原始['args'])#参数
                    if 参数 is None:#有损
                        协议失败('binding arguments must be lossless JSON')#协议
                        return
                    未决数[0]+=1#加一
                    未决字节[0]+=字节#加字节
                    if 未决数[0]>自身.配置['maxPendingCalls'] or 未决字节[0]>自身.配置['maxMessageBytes']:#超限
                        协议失败('pending binding calls exceed configured limits')#协议
                        return
                    def 跑绑定(调用标识=标识,调用函数=函数,调用参数=参数,帧字节=字节):#一次绑定
                        '执行绑定并回复'
                        try:#调用
                            try:#执行
                                值=快照json值(调用函数(调用参数))#快照
                                if 值 is None:#有损
                                    raise 节点ptc错误('binding resolution must be lossless JSON')#拒绝
                                回复={'type':'reply','id':调用标识,'ok':True,'value':编码ptcjson线(值)}#成功
                            except BaseException as 错误:#失败
                                回复={'type':'reply','id':调用标识,'ok':False,'message':消息于(错误)}#失败回复
                            finally:#名额
                                未决数[0]-=1#减一
                                未决字节[0]-=帧字节#减字节
                            if not 已结算[0]:#仍活
                                def 回复失败(错误):#回复帧失败
                                    '回复发送失败'
                                    协议失败(消息于(错误))#协议
                                通道.发送(回复).捕获(回复失败)#回复
                        except (节点ptc错误,OSError,ValueError,TypeError) as 错误:#回复失败
                            协议失败(消息于(错误))#协议
                    绑定线程=threading.Thread(target=跑绑定,daemon=True)#绑定线程
                    绑定线程.start()
                    return
                协议失败('unknown control message')#未知
            def 通道失败(错误,种类):#通道失败
                '协议或传输'
                if 种类=='protocol':#协议
                    协议失败(消息于(错误))#协议
                elif 已就绪[0]:#已握手
                    收尾({'kind':'worker-exit','message':消息于(错误)})#退出
                else:#握手前
                    def 握手前退出(结局):#孩子已退出
                        '握手前按结局分类'
                        进程结束(结局)#分类
                    def 握手前失败(失败值):#等结局失败
                        '握手前的退出失败'
                        收尾({'kind':'worker-exit','message':消息于(失败值)})#退出
                    句柄.done.然后(握手前退出,握手前失败)#等孩子
            通道=json通道(句柄.control,自身.配置['maxMessageBytes'],接收,通道失败)#分帧
            def 进程已退出(结局):#孩子退出
                '排队帧回调后再分类退出'
                def 稍后分类():#让已排队的帧回调先走
                    '分类退出'
                    进程结束(结局)#分类
                threading.Thread(target=稍后分类,daemon=True).start()#延后一拍
            def 进程等待失败(错误):#spawn 失败
                '启动或等待失败'
                if 已隔离 is not None and 是否运行器派生失败(错误,已隔离['argv'][0],规格['cwd']):#运行器
                    收尾({'kind':'sandbox-unavailable','message':消息于(错误)})#沙箱
                else:#普通
                    收尾({'kind':'worker-exit','message':消息于(错误)})#退出
            句柄.done.然后(进程已退出,进程等待失败)#监视退出
        except 沙箱不可用错误 as 错误:#沙箱不可用
            收尾({'kind':'sandbox-unavailable','message':消息于(错误)})#沙箱
        except BaseException as 错误:#其它
            收尾({'kind':'exception' if 解析中[0] else 'worker-exit','message':消息于(错误)})#阶段
        return 结果任务#清理完成后解决

default=节点ptc运行时#Cordis 默认导出
name=名称#Cordis 插件名
inject=依赖#Cordis 依赖槽
Config=配置#Cordis 配置槽
