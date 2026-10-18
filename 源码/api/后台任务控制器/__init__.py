'宿主作业 Remote：把一个会话看得到的名册和一条作业的保留输出流给浏览器，并代人类停止作业'
from ...依赖.schemastery import 自然数字段#配置字段
from ...类型化远程调用.协议 import 远程服务,远程 as _远程#宿主 Remote
from ...基础设施.通用工具 import utf8字节数,是否非负安全整数,紧凑json编码#帧预算与偏移校验
from ..网关.流协议 import 已中止,若中止则抛 as 若已中止则抛出#流的取消
from .异常 import 远程错误#看不见的作业
from .唤醒 import 输出等待者,休眠#合并窗口
from . import (#同目录模块，导入即执行顶层
    唤醒,#唤醒旗
    类型,#线路类型
    异常,#线路失败
    客户端,#客户端半边
)

__all__=['包名','名称','依赖','默认','配置','后台任务控制器','唤醒','类型','异常','客户端']

包名='@deepseek-ai/dsh-api-job-controller'#包名
名称='job-controller'#插件名
依赖=['jobs','typert']#作业登记表与类型化远程
观察冲洗缺省毫秒=100#两次读取之间的合并窗口
观察最大帧缺省字节=64*1024#一帧输出的软预算

配置={#部署政策
    'observeFlushMs':自然数字段(最小=1,默认值=观察冲洗缺省毫秒),#合并窗口
    'observeMaxFrameBytes':自然数字段(最小=1,默认值=观察最大帧缺省字节),#帧预算
}

class 后台任务控制器(远程服务):
    '宿主 job 命名空间的拥有者。流是登记表的投影，不移动模型游标'
    inject=依赖#框架槽
    Config=配置#框架槽
    def __init__(自身,上下文,配置值):
        '登记 job 命名空间。缺的配置键用与字段相同的默认'
        super().__init__(上下文,'jobController',{'namespace':'job'})#绑定
        if 配置值 is None:#没有配置对象
            配置值={}#按缺省
        if 'observeFlushMs' in 配置值 and 配置值['observeFlushMs'] is not None:#已给出
            自身._冲洗毫秒=配置值['observeFlushMs']#用给出的
        else:#缺省
            自身._冲洗毫秒=观察冲洗缺省毫秒#100
        if 'observeMaxFrameBytes' in 配置值 and 配置值['observeMaxFrameBytes'] is not None:#已给出
            自身._最大帧字节=配置值['observeMaxFrameBytes']#用给出的
        else:#缺省
            自身._最大帧字节=观察最大帧缺省字节#65536

    @_远程({'mode':'stream'})
    def list(自身,request,signal):
        '开口交一帧整表，之后每次合并过的生命周期提交再交一帧。输出追加不刷新名册'
        若已中止则抛出(signal)#生成已经取消
        等待者=输出等待者()#不丢唤醒
        def 监听(事件):
            '输出追加不刷新。无主或属于本会话的生命周期才唤醒'
            if 事件['type']=='output':#只是写输出
                return#名册不变
            作业=事件['job']#投影
            拥有者=作业['owner'] if 'owner' in 作业 else None#无主则没有这个键
            if 拥有者 is None or 拥有者==request['sessionId']:#本会话看得见
                等待者.唤醒()#记一笔
        注册表=自身.ctx.jobs#活的登记表
        退订=注册表.事件['subscribe']({'owners':'all'},监听)#先订阅再读，中间的提交不会丢
        try:#结束时退订
            yield {'type':'rows','jobs':注册表.列出(request['sessionId'])}#开口整表
            while True:#没有自然结束，载体来关
                等待者.等待(signal)#下一笔或中止
                休眠(自身._冲洗毫秒,signal)#把一阵提交收成一帧
                if 已中止(signal):#取消则不再读
                    return#结束
                yield {'type':'rows','jobs':注册表.列出(request['sessionId'])}#新的整表
        finally:#无论生成怎样停
            退订()#卸监听

    @_远程({'mode':'stream'})
    def follow(自身,request,signal):
        '从绝对偏移交保留输出：开口锚、合并后的输出帧，终态排空后交 status 并结束'
        if 'from' in request:#调用方给了偏移，null 也算给了
            起点=request['from']#原值
            if not 是否非负安全整数(起点):#不是非负安全整数
                raise ValueError('invalid observe offset: expected a non-negative safe integer, got '+紧凑json编码(起点))#拒绝
        若已中止则抛出(signal)#生成已经取消
        标识=str(request['jobId'])#登记表键
        等待者=输出等待者()#不丢唤醒
        已移除=None#拆掉时宣布的那份投影
        def 监听(事件):
            '只响应这一条作业。移除时记下投影，窗口过后的读取只会得到未知 id'
            nonlocal 已移除
            if 事件['type']=='output':#输出事件带 id
                变更=事件['id']#作业 id
            else:#生命周期事件带投影
                变更=事件['job']['id']#作业 id
            if 变更!=标识:#不是这一条
                return#忽略
            if 事件['type']=='removed':#所有者拆掉了
                已移除=事件['job']#最后一份投影
            等待者.唤醒()#去读
        注册表=自身.ctx.jobs#活的登记表
        退订=注册表.事件['subscribe']({'owners':'all'},监听)#先订阅再读
        try:#结束时退订
            会话=request['sessionId'] if 'sessionId' in request else None#无主作业不带会话
            作业=注册表.获取(标识,会话)#围栏读取，看不见就抛
            if 'from' in request:#从调用方的偏移续
                游标=request['from']#绝对偏移
            else:#从还留着的最早字节
                游标=作业['output']['earliest']#环的头
            yield {'type':'opened','job':作业,'from':游标}#锚
            while not 已中止(signal):#取消则停在当前帧之后
                if 已移除 is not None:#拆掉已经宣布
                    yield {'type':'status','job':已移除}#用那份投影收尾
                    return#正常结束
                读=注册表.按偏移读取(标识,游标,会话)#不移动模型游标
                if len(读['chunks'])>0 or 读['lossy']:#有字节或有损
                    批次=[]#当前帧的块
                    批次字节=0#当前帧的 UTF-8 字节
                    标有损=bool(读['lossy'])#只标在第一帧上
                    for 块 in 读['chunks']:#按环的顺序
                        批次.append(块)#收进这一帧
                        批次字节=批次字节+utf8字节数(块['text'])#加上这块
                        if 批次字节>=自身._最大帧字节:#软预算已满，单块更大也整块送出
                            末块=批次[len(批次)-1]#这一帧的最后一块
                            结束=末块['at']+utf8字节数(末块['text'])#这块结尾的绝对偏移
                            帧={'type':'output','chunks':批次,'next':结束}#续读点
                            if 标有损:#头被丢掉
                                帧['lossy']=True#只在有损时带这个键
                            yield 帧#送出
                            标有损=False#后面的帧不再标
                            批次=[]#下一帧
                            批次字节=0#清零
                    if len(批次)>0 or 标有损:#尾上还有块，或整次读取只有有损标记
                        帧={'type':'output','chunks':批次,'next':读['next']}#整次读取的续读点
                        if 标有损:#有损还没标出去
                            帧['lossy']=True#带上
                        yield 帧#送出
                游标=读['next']#下一次从这里读
                作业=注册表.获取(标识,会话)#再取投影
                if 作业['status']!='running' and 作业['status']!='stopping' and 游标>=作业['output']['total']:#已结算且环已排空
                    yield {'type':'status','job':作业}#终态
                    return#正常结束
                等待者.等待(signal)#等下一次写入或中止
                休眠(自身._冲洗毫秒,signal)#把一阵写入收成有界的帧
        finally:#无论生成怎样停
            退订()#卸监听

    @_远程('kill')
    def kill(自身,request):
        '代人类停止一条看得见的作业。原因不是模型请求的，拥有者仍会收到完成通知'
        作业表=自身.ctx.jobs#登记表
        try:#看不见的 id 与别的会话都是同一件事
            作业表.获取(request['jobId'],request['sessionId'])#围栏确认还在名册里
        except Exception as 错误:#未知或属于别的会话
            raise 远程错误('job/not-found',str(错误),{'sessionId':request['sessionId'],'jobId':request['jobId']},错误)#客户端只讲一件事
        结局=作业表.终止(request['jobId'],request['sessionId'],'cancelled by the user')#同一同步段里停止
        return {'outcome':结局}#requested 或 already-finished

默认=后台任务控制器#默认导出
Config=配置#框架槽
name=名称#框架槽
inject=依赖#框架槽
default=默认#框架槽
