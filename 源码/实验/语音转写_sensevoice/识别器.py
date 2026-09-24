import json,os,secrets,sys,threading,time
import requests
from ...工具.超时 import 中止控制器,合成信号,截止,若已中止则抛出,已中止
from .输入 import 语音输入错误
from .下载错误 import 语音下载错误
from .运行时准备 import 检查运行时,准备运行时

__all__=['读就绪','读转写','sensevoice工作者']

def 读就绪(句柄,上限,信号):
    """读一条有界就绪帧；退出早于就绪则失败。"""
    若已中止则抛出(信号)
    标准输出=句柄.stdout
    if 标准输出 is None:
        raise RuntimeError('Speech worker stdout is unavailable')
    文本=''
    while True:
        若已中止则抛出(信号)
        块=标准输出.read(1)
        if not 块:
            错=句柄.collected.stderr.readFrom(0).text if 句柄.collected.stderr else ''
            raise RuntimeError('Speech worker exited before readiness: '+错)
        if isinstance(块,bytes):
            文本+=块.decode('utf-8')
        else:
            文本+=块
        if len(文本.encode('utf-8'))>上限:
            raise RuntimeError('Speech worker readiness exceeded its byte limit')
        if '\n' in 文本:
            行=文本.split('\n',1)[0]
            值=json.loads(行)
            端口=值['port']
            if not isinstance(端口,int) or 端口<1 or 端口>65535:
                raise RuntimeError('Invalid speech worker readiness')
            return 端口

def 读转写(应答,上限):
    """有界 HTTP 响应；畸形输出使本次失败。"""
    体=应答.content
    if len(体)>上限:
        raise RuntimeError('Speech transcript exceeded its byte limit')
    值=json.loads(体.decode('utf-8'))
    if not 应答.ok:
        if 应答.status_code in (400,413) and 值.get('code')=='invalid-input':
            raise 语音输入错误(值['error'])
        raise RuntimeError(值.get('error') or 'speech worker failed')
    return {
        'text':值['text'],
        'audioSeconds':值['audioSeconds'],
        'inferenceSeconds':值['inferenceSeconds'],
    }

class sensevoice工作者:
    """一台串行工作者，请求拥有取消，空闲回收。"""
    def __init__(自身,上下文,配置):
        """记下部署配置并初始化准备步骤。"""
        自身.上下文=上下文
        自身.配置=配置
        自身.工作者=None
        自身.串行=threading.Lock()
        自身.待处理=0
        自身.寿命=中止控制器()
        自身.空闲定时器=None
        自身.运行时=None
        自身.最后进度=0
        自身.监听者=set()
        自身.准备任务=None
        if 配置['modelDirectory'] is not None and 配置['vadModelPath'] is not None:
            自身.downloadSources=()
        else:
            源表=配置['modelOrigins'] if 配置['modelOrigin'] is None else [配置['modelOrigin']]
            见=set()
            表=[]
            for 源 in 源表:
                from urllib.parse import urlparse
                原点=urlparse(源).scheme+'://'+urlparse(源).netloc
                if 原点 not in 见:
                    见.add(原点)
                    表.append(原点)
            自身.downloadSources=tuple(表)
        种类=['check']
        if 配置['modelDirectory'] is None:
            种类.append('model')
        if 配置['vadModelPath'] is None:
            种类.append('vad')
        种类.extend(['verify','load'])
        自身.状态={'phase':'unprepared','steps':[{'kind':项,'status':'pending'} for 项 in 种类]}

    def snapshot(自身):
        """当前 Host 拥有的准备态。"""
        return 自身.状态

    def subscribe(自身,监听):
        """观察就绪。"""
        自身.监听者.add(监听)
        def 退订():
            """取消。"""
            自身.监听者.discard(监听)
        return 退订

    def 发布(自身,状态):
        """合并步骤并节流下载进度。"""
        if 自身.准备任务 is not None and 状态['phase'] in ('ready','standby','unprepared','failed','cancelled'):
            自身.准备任务['completed']=True
        先前=自身.状态
        步骤=状态.get('steps')
        if 步骤 is None:
            新=[]
            for 项 in 先前['steps']:
                if 状态['phase']=='ready':
                    新.append({**项,'status':'complete'})
                    continue
                if 状态.get('step')=='check' and 项['kind']!='check':
                    新.append({'kind':项['kind'],'status':'pending'})
                    continue
                if 状态.get('step')==项['kind']:
                    if 项['status']=='running':
                        新.append(项)
                    else:
                        新.append({'kind':项['kind'],'status':'running','startedAt':int(time.time()*1000)})
                    continue
                if 项['status']!='running':
                    新.append(项)
                    continue
                if 状态['phase']=='standby':
                    新.append({**项,'status':'cancelled'})
                elif 状态['phase'] in ('failed','cancelled'):
                    新.append({**项,'status':状态['phase']})
                elif 状态.get('step') is None:
                    新.append(项)
                else:
                    新.append({**项,'status':'complete'})
            步骤=新
        自身.状态={**状态,'steps':步骤}
        现在=time.perf_counter()*1000
        if (
            状态['phase']=='downloading' and 先前.get('phase')=='downloading'
            and 状态.get('resource')==先前.get('resource')
            and 状态.get('completedBytes')!=状态.get('totalBytes')
            and 现在-自身.最后进度<自身.配置['progressIntervalMs']
        ):
            return
        自身.最后进度=现在
        for 监听 in list(自身.监听者):
            监听()

    def inspect(自身):
        """启用时检查磁盘缓存，完整则进入 standby。"""
        def 跑(信号):
            """检查。"""
            句柄=截止(信号,自身.配置['prepareTimeoutMs'],'SPEECH_PREPARE_TIMEOUT')
            自身.发布({'phase':'checking','step':'check','startedAt':int(time.time()*1000)})
            运行时=检查运行时(自身.配置,句柄.信号)
            若已中止则抛出(句柄.信号)
            自身.运行时=运行时
            步骤=[]
            for 项 in 自身.状态['steps']:
                完成=项['kind']=='check' or (运行时 is not None and 项['kind']!='load')
                步骤.append({'kind':项['kind'],'status':'complete' if 完成 else 'pending'})
            自身.发布({'phase':'standby' if 运行时 else 'unprepared','steps':步骤})
            句柄.释放()
        自身.跑准备(跑)

    def prepare(自身,选项=None):
        """启动或加入一次固定下载源的准备。"""
        if 选项 is None:
            选项={}
        源=选项.get('downloadSource')
        if 源 is not None and 源 not in 自身.downloadSources:
            raise RuntimeError('Speech download source is unavailable')
        配置=自身.配置 if 源 is None else {**自身.配置,'modelOrigin':源}
        def 跑(信号,用配置=配置):
            """启动工作者。"""
            自身.启动(信号,用配置)
        自身.跑准备(跑,源)

    def 跑准备(自身,跑,下载源=None):
        """同时只允许一个准备任务。"""
        if 自身.准备任务 is not None and 自身.准备任务['downloadSource']!=下载源:
            raise RuntimeError('Cancel preparation before changing its download source')
        if 自身.准备任务 is not None or 自身.工作者 is not None:
            return
        若已中止则抛出(自身.寿命.信号)
        中止=中止控制器()
        任务={'abort':中止,'completed':False,'downloadSource':下载源,'settled':threading.Event()}
        自身.准备任务=任务
        def 执行():
            """入队准备。"""
            try:
                自身.入队(跑,中止.信号)
            except Exception as 错误:
                if 已中止(自身.寿命.信号):
                    return
                if 已中止(中止.信号):
                    自身.发布({'phase':'cancelled'})
                else:
                    态={'phase':'failed','message':str(错误)}
                    if isinstance(错误,语音下载错误):
                        态['download']=错误.download
                    自身.发布(态)
            finally:
                任务['settled'].set()
                自身.准备任务=None
        threading.Thread(target=执行,daemon=True).start()

    def cancel(自身):
        """取消未完成准备；已完成就绪保留。"""
        任务=自身.准备任务
        if 任务 is None:
            return
        if not 任务['completed']:
            自身.发布({'phase':'cancelling','startedAt':int(time.time()*1000)})
            任务['abort'].中止(RuntimeError('Speech preparation cancelled'))
        任务['settled'].wait()

    def transcribe(自身,输入,信号):
        """有界排队；取消后不等推理残留。"""
        def 跑(合并):
            """执行。"""
            return 自身.执行(输入,合并)
        return 自身.入队(跑,信号)

    def 入队(自身,跑,信号):
        """串行队列。"""
        合并=合成信号(信号,自身.寿命.信号)
        若已中止则抛出(合并)
        if 自身.待处理>=自身.配置['maxPending']:
            raise RuntimeError('Speech transcription queue is full')
        if 自身.空闲定时器 is not None:
            自身.空闲定时器.cancel()
            自身.空闲定时器=None
        自身.待处理+=1
        try:
            with 自身.串行:
                若已中止则抛出(合并)
                return 跑(合并)
        finally:
            自身.待处理-=1
            if 自身.待处理==0 and not 已中止(自身.寿命.信号) and 自身.配置['idleTimeoutMs']>0:
                def 空闲():
                    """停工作者。"""
                    with 自身.串行:
                        自身.停止()
                自身.空闲定时器=threading.Timer(自身.配置['idleTimeoutMs']/1000.0,空闲)
                自身.空闲定时器.daemon=True
                自身.空闲定时器.start()

    def 启动(自身,信号,准备配置=None):
        """唤醒或新建工作者。"""
        if 准备配置 is None:
            准备配置=自身.配置
        if 自身.工作者 is not None and 自身.工作者['closed']:
            自身.停止()
        if 自身.工作者 is not None:
            return 自身.工作者
        句柄=截止(信号,自身.配置['prepareTimeoutMs'],'SPEECH_PREPARE_TIMEOUT')
        已缓存=自身.运行时 is not None
        if not 已缓存:
            自身.发布({'phase':'checking','step':'check','startedAt':int(time.time()*1000)})
        运行时=自身.运行时 or 准备运行时(自身.上下文,准备配置,句柄.信号,自身.发布)
        自身.运行时=运行时
        若已中止则抛出(句柄.信号)
        自身.发布({'phase':'waking' if 已缓存 else 'loading','step':'load','startedAt':int(time.time()*1000)})
        os.makedirs(自身.配置['dataRoot'],exist_ok=True)
        令牌=secrets.token_hex(32)
        载荷={**自身.配置,**运行时}
        进程=自身.上下文.subprocess.spawn({
            'argv':[sys.executable,运行时['worker'],json.dumps(载荷)],
            'cwd':自身.配置['dataRoot'],
            'graceMs':自身.配置['graceMs'],
            'env':{'DSH_SPEECH_TOKEN':令牌,'ELECTRON_RUN_AS_NODE':'1'},
            'stdio':{'stdin':'ignore','stdout':'pipe','stderr':{'maxBytes':自身.配置['maxLogBytes']}},
        })
        try:
            端口=读就绪(进程,自身.配置['maxLogBytes'],句柄.信号)
            工作者={'handle':进程,'url':'http://127.0.0.1:'+str(端口),'token':令牌,'closed':False}
            自身.工作者=工作者
            自身.发布({'phase':'ready'})
            def 退出():
                """进程退出进 standby。"""
                if not 工作者['closed']:
                    工作者['closed']=True
                    自身.发布({'phase':'standby'})
            def 等退出():
                """等 done。"""
                进程.done.等待() if hasattr(进程.done,'等待') else 进程.waitForExit()
                退出()
            threading.Thread(target=等退出,daemon=True).start()
            句柄.释放()
            return 工作者
        except Exception as 错误:
            进程.terminate()
            进程.waitForExit()
            句柄.释放()
            raise 错误

    def 执行(自身,输入,信号):
        """就绪或待唤醒才转写。"""
        阶段=自身.状态['phase']
        if 阶段 not in ('ready','standby'):
            raise RuntimeError('Prepare the local speech provider before recording')
        try:
            工作者=自身.启动(信号)
            调用=截止(信号,自身.配置['inferenceTimeoutMs'],'SPEECH_INFERENCE_TIMEOUT')
            应答=requests.post(
                工作者['url']+'/transcribe?language='+requests.utils.quote(输入['language']),
                headers={'authorization':'Bearer '+工作者['token'],'content-type':'audio/wav'},
                data=bytes(输入['audio']),
                timeout=自身.配置['inferenceTimeoutMs']/1000.0,
            )
            try:
                结果=读转写(应答,自身.配置['maxResponseBytes'])
            except Exception as 错误:
                若已中止则抛出(调用.信号)
                raise 错误
            若已中止则抛出(调用.信号)
            调用.释放()
            return 结果
        except 语音输入错误:
            raise
        except Exception as 错误:
            自身.停止()
            自身.发布({'phase':'standby'})
            raise 错误

    def 停止(自身):
        """终止托管进程。"""
        工作者=自身.工作者
        if 工作者 is None:
            return
        工作者['closed']=True
        工作者['handle'].terminate()
        工作者['handle'].waitForExit()
        自身.工作者=None
        自身.发布({'phase':'standby'})

    def dispose(自身):
        """停识别器。"""
        自身.监听者.clear()
        自身.寿命.中止(RuntimeError('SenseVoice provider disposed'))
        if 自身.空闲定时器 is not None:
            自身.空闲定时器.cancel()
        with 自身.串行:
            自身.停止()
        任务=自身.准备任务
        if 任务 is not None:
            任务['settled'].wait()
