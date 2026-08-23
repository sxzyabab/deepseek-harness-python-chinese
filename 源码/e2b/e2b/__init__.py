"""共享拥有一个 E2B 沙箱。能力适配器都等待同一份 SDK 句柄，因此文件系统与进程操作落在同一个远端 Linux 世界。

对齐上游 `e2b/src/index.ts`。公开面仅中文名。配置键与诊断英文字面量保持上游。
"""
import math,os,threading,uuid#有限判定、环境密钥、后台创建与控制面 HOME 随机段
from ...依赖 import cordis,schemastery,e2b#外部依赖胶水
服务=cordis.服务#Cordis 服务基类
模式=schemastery.模式#配置校验
沙箱=e2b.Sandbox#沙箱句柄
沙箱未找到错误=e2b.SandboxNotFoundError#沙箱已消失
文件类型=e2b.FileType#目录项类型
命令退出错误=e2b.CommandExitError#命令非零退出
文件未找到错误=e2b.FileNotFoundError#远端文件不存在

__all__=(#仅中文公开名
    '引用E2B壳参数','e2b控制环境','E2B运行时','默认',
    '沙箱','沙箱未找到错误','文件类型','命令退出错误','文件未找到错误',
)#公开面结束

def 引用E2B壳参数(值):#POSIX 单引号转义
    """把一个不透明参数引用给 SDK 无法绕开的 `/bin/bash -l -c` 层。"""
    return "'"+值.replace("'","'\"'\"'")+"'"#把内部单引号切成 '"'"' 再包回单引号

def e2b控制环境(覆盖=None):#控制面命令的隔离环境
    """用一份新的随机 HOME 路径隔离 E2B 写死的登录壳。"""
    环境=dict(覆盖 or {})#调用方可叠加的显式项
    环境['HOME']='/.dsh-e2b-control-'+str(uuid.uuid4())#每次新 HOME，避免登录壳读用户配置
    return 环境#SDK 可再扩展的可变映射

配置模式=模式.对象({#schemastery 配置模式
    'apiKey':模式.字符串(),#可选字符串密钥
    'cwd':模式.字符串().默认('/home/user/workspace'),#默认远端工作目录
    'timeoutMs':模式.数字().默认(300000),#默认 5 分钟寿命
})#配置模式结束

class E2B运行时(服务):#共享沙箱所有者服务
    """创建一个可惰性消费的 E2B SDK 句柄，并在超时或拆除时删除沙箱。

    创建从插件构造开始；适配器第一次操作前等待 取沙箱。
    """
    Config=配置模式#schemastery 配置模式
    inject=[]#无服务依赖
    def __init__(自身,上下文对象,配置):#用上下文与配置构造所有者
        """登记为 ctx.e2b，校验配置，并开始创建沙箱。"""
        super().__init__(上下文对象,'e2b')#注册为 ctx.e2b
        密钥=配置.get('apiKey') if isinstance(配置,dict) else getattr(配置,'apiKey',None)#配置优先
        if 密钥 is None:#未给密钥
            密钥=os.environ.get('E2B_API_KEY')#读环境
        工作目录=配置['cwd'] if isinstance(配置,dict) else 配置.cwd#已填缺省的远端 cwd
        超时=配置['timeoutMs'] if isinstance(配置,dict) else 配置.timeoutMs#已填缺省的超时
        自身.配置={'apiKey':密钥 or '','cwd':工作目录,'timeoutMs':超时}#固化解析结果
        自身.校验()#加载时大声失败
        自身.cwd=自身.配置['cwd']#公开工作目录
        自身.runtimeRoot=自身.cwd.rstrip('/')+'/.dsh-e2b'#适配器私有根（POSIX）
        自身.运行时根=自身.runtimeRoot#中文别名
        自身.已拆除=False#拆除后拒绝再交出句柄
        自身.就绪=None#惰性完成的沙箱句柄；构造时填
        自身.就绪错误=None#创建失败原因
        自身.就绪事件=threading.Event()#创建结算事件
        def 打开沙箱():#后台创建
            """创建沙箱并准备目录。"""
            try:#创建与准备
                自身.就绪=自身.打开()#成功句柄
            except BaseException as 错误:#创建失败
                自身.就绪错误=错误#记下原因
            finally:#无论成败放行等待方
                自身.就绪事件.set()#结算
        threading.Thread(target=打开沙箱,daemon=True).start()#构造即开始创建
        def 装拆除():#登记拆除副作用
            """返回拆除器：先挡后续取沙箱，再等创建结束并删除。"""
            def 拆除():#拆除时杀沙箱
                """先挡后续取沙箱，再等创建结束并删除。"""
                自身.已拆除=True#先挡后续取沙箱
                自身.就绪事件.wait()#等到创建结束
                if 自身.就绪错误 is not None:#创建失败则无沙箱可杀
                    return#没有句柄
                沙箱句柄=自身.就绪#成功打开后才有句柄
                try:#杀远端沙箱
                    沙箱句柄.kill()#请求删除
                except 沙箱未找到错误:#已消失可忽略
                    return#完全停稳
            return 拆除#拆除器
        上下文对象.effect(装拆除,'e2b sandbox teardown')#effect 标签

    def 校验(自身):#加载时校验配置
        """密钥非空、cwd 绝对、超时正有限。"""
        if len(自身.配置['apiKey'])==0:#密钥为空
            raise Exception('dsh-e2b: configure apiKey or set E2B_API_KEY')#必须配置密钥
        工作目录=自身.配置['cwd']#远端 cwd
        if not 工作目录.startswith('/'):#cwd 必须是绝对 Linux 路径
            raise Exception('dsh-e2b: cwd must be an absolute Linux path: '+工作目录)#相对路径拒绝
        超时=自身.配置['timeoutMs']#超时
        if isinstance(超时,bool) or not isinstance(超时,(int,float)) or not math.isfinite(超时) or 超时<=0:#超时必须正有限
            raise Exception('dsh-e2b: timeoutMs must be a positive finite number')#非法超时

    def 取沙箱(自身):#适配器入口
        """返回共享的存活 SDK 句柄。配置的 cwd 已存在之后的已创建沙箱。"""
        if 自身.已拆除:#拆除中不再交出
            raise Exception('E2B sandbox service is disposing')#拆除中
        自身.就绪事件.wait()#等到创建
        if 自身.已拆除:#等待后再检一次
            raise Exception('E2B sandbox service is disposing')#拆除中
        if 自身.就绪错误 is not None:#创建失败
            raise 自身.就绪错误#原样上抛
        return 自身.就绪#交出共享句柄

    def 打开(自身):#创建沙箱并准备目录
        """向 E2B 申请沙箱并准备 cwd 与运行时根。"""
        沙箱句柄=沙箱.create(#向 E2B 申请沙箱；关键字对齐 Python SDK 与上游语义
            api_key=自身.配置['apiKey'],#宿主侧密钥，不进沙箱
            timeout=自身.配置['timeoutMs']/1000,#寿命（秒）
            secure=True,#安全模式
        )#create 结束
        try:#准备工作目录与运行时根
            沙箱句柄.files.make_dir(自身.cwd)#创建共享 cwd
            沙箱句柄.files.make_dir(自身.runtimeRoot)#创建适配器私有根
            根信息=沙箱句柄.files.get_info(自身.runtimeRoot)#核对根不是链接
            根类型=getattr(根信息,'type',None)#目录项类型
            链接目标=getattr(根信息,'symlink_target',None) or getattr(根信息,'symlinkTarget',None)#符号链接目标
            if 根类型!=文件类型.DIR or 链接目标 is not None:#必须是真实目录
                raise Exception('dsh-e2b: runtime root must be a real directory: '+自身.runtimeRoot)#拒绝链接或非目录
            沙箱句柄.commands.run(#收紧私有根权限
                'chmod 700 -- '+引用E2B壳参数(自身.runtimeRoot),#仅所有者可进
                envs=e2b控制环境(),#隔离登录壳 HOME
            )#chmod 结束
            return 沙箱句柄#准备完成，交出句柄
        except BaseException as 错误:#准备失败则回滚沙箱
            try:#尝试删除刚创建的沙箱
                沙箱句柄.kill()#回滚
            except BaseException:#二次失败先吞掉
                pass#由已配置超时约束存活
            raise 错误#原失败仍上抛

默认=E2B运行时#默认导出服务类
