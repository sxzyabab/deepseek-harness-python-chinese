"""类型由 PTY 后端、按所有者作用域的注册表与工具消费方共用。运行时服务代码在 `__init__.py`。"""
from cordis import 聚合错误#搭建与清理双失败的聚合基类

终端会话标识值=str#PTY会话身份品牌基底（运行时即字符串）

class 终端后端清理错误(聚合错误):#后端搭建与清理双失败
    """未发布的搭建失败后，后端报告清理部分资源失败。"""
    def __init__(自身,搭建错误,清理错误):#同时携带搭建失败与清理失败
        """记下原始搭建失败与清理失败。"""
        super().__init__([搭建错误,清理错误],'PTY backend startup and cleanup both failed')#两条失败聚合成一条
        自身.spawnError=搭建错误#原始搭建或取消失败
        自身.cleanupError=清理错误#可能让后端拥有的资源仍活着的失败
        自身.搭建错误=搭建错误#中文别名
        自身.清理错误=清理错误#中文别名
        自身.name='TerminalBackendCleanupError'#固定类名

终端等待原因=('stdin_read','inferred_idle','timeout','session_exit')#读到输入、推断空闲、超时、会话退出
终端信号=('SIGINT','SIGTERM','SIGKILL','SIGTSTP','SIGHUP')#允许的POSIX信号；与subprocess成员相同，无跨seam依赖
终端会话状态种类=('running','exited')#顶层PTY进程状态种类；exited另带exitCode与signal
终端创建请求字段=('type','name','cwd')#创建请求：后端类型，可选显示名与工作目录
终端后端创建规格字段=('sessionId','owner','type','name','cwd','signal')#注册表交给后端的完全标识请求
终端发送请求字段=('text','submit','signal')#面向行的交互输入：文本、是否提交、可选取消
终端发送增量字段=('delta','truncated')#自上次操作读取以来的增量与是否截断
终端发送结果字段=('viewport','waitReason','sessionStatus','truncated')#结算视口、等待原因、会话状态、是否截断
终端发送操作字段=('done','readOutput','cancel')#活动发送：结算承诺、增量读取、请求中断
终端回滚读取请求字段=('offset','count')#相对最新偏移与请求行数
终端回滚读取结果字段=('text','totalLines','lineBegin','lineEnd','truncated')#有界回滚页与分页元数据
终端信号结果字段=('delivered','targetPgid')#已投递真值与目标进程组
终端会话快照字段=('sessionId','name','type','pid','status')#所有者可见摘要
终端后端会话字段=('motd','pid','startSend','read','signal','status','close')#后端拥有的活动会话
终端后端字段=('type','spawn')#可替换PTY后端：稳定类型与创建入口
终端创建结果字段=('sessionId','name','type','pid','status','motd')#成功发布快照外加开机信息
