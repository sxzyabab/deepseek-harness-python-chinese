import threading#后台清理
from ....依赖.cordis import 服务#服务基类
from ....内核.作用域 import 操作任务#关闭任务
from ....工具.加密 import 随机uuid#新终端身份
from ..类型 import 远程错误,取远程错误#Remote 失败
from .模型 import 终端视图,快照存储#视图与通知
from .外壳偏好 import 首选外壳,记住外壳#偏好
from .关闭请求 import 终端关闭请求#未完成关闭

__all__=['注入','应用','客户端终端','终端视图']#仅中文公开名

注入=['remote','remote.terminal']#Gateway 与 terminal 命名空间

def 取码(错误):#结构识别
    """看 code。"""
    本=取远程错误(错误)#本包
    if 本 is not None:#是
        return 本.code#码
    if isinstance(错误,dict):#信封
        return 错误['code'] if 'code' in 错误 else None#码
    return getattr(错误,'code',None)#对象

def 取消息(错误):#失败文案
    """Error.message 或 str。"""
    if isinstance(错误,BaseException) and len(错误.args)>0:#异常
        return str(错误.args[0])#第一参
    if isinstance(错误,dict) and 'message' in 错误:#信封
        return 错误['message']#消息
    return str(错误)#串

class 客户端终端(服务):#侧栏出现与后台清理
    """标签键独立于 Host 终端身份。"""
    def __init__(自身,上下文,远程):#构造
        """挂拆除并重试未完成关闭。"""
        super().__init__(上下文,'webTerminals')#登记
        自身._远程=远程#terminal 面
        自身.closeFailures=快照存储([])#失败通知
        自身._请求=终端关闭请求()#存储
        自身._关闭中={}#id → 任务
        自身._已关=set()#本页已关 id
        for 请求 in 自身._请求.未完成():#已保存
            自身._已关.add(请求['id'])#记
        自身._已拆除=False#插件
        自身._视图={}#会话 → 键 → 视图
        def 拆除效果():#fiber
            """卸视图，等关闭。"""
            def 清理():#拆除器
                """不关 Host。"""
                自身._已拆除=True#记下
                待拆=[]#视图
                for 会话表 in list(自身._视图.values()):#各会话
                    for 视图 in list(会话表.values()):#各出现
                        待拆.append(视图)#收
                自身._视图.clear()#清
                for 视图 in 待拆:#拆
                    视图.释放()#放流
                for 任务 in list(自身._关闭中.values()):#关闭
                    try:#等
                        任务.等待()#等
                    except BaseException:#关闭失败已记
                        pass#吞
            return 清理#拆除器
        上下文.副作用(拆除效果,'terminal-controller.client.views')#登记
        for 请求 in 自身._请求.未完成():#启动重试
            自身._清理(请求)#后台

    def 视图(自身,会话标识,键,终端标识=None,壳路径=None):#稳定模型
        """一次侧栏出现。"""
        会话表=自身._视图.get(会话标识)#表
        if 会话表 is None:#新建
            会话表={}#空
            自身._视图[会话标识]=会话表#登记
        视图=会话表.get(键)#已有
        if 视图 is None:#新建
            标识=终端标识 if 终端标识 is not None else 随机uuid()#身份
            视图=终端视图(会话标识,自身._远程,自身.所属上下文.remote,标识,终端标识 is None,壳路径)#视图
            会话表[键]=视图#登记
            threading.Thread(target=视图.刷新,daemon=True).start()#void refresh
        return 视图#模型

    def 启动外壳(自身,会话标识,信号):#按需探测
        """不分配 PTY。"""
        结果=自身._远程.shells(会话标识,信号)#探测
        if not 结果['ok']:#失败
            raise RuntimeError(结果['error']['message'])#消息
        壳列=结果['value']#列表
        上次=首选外壳()#偏好
        选中=None#路径
        for 壳 in 壳列:#找偏好
            if 壳['path']==上次:#可用
                选中=壳['path']#用
                break#停
        if 选中 is None and len(壳列)>0:#回落
            选中=壳列[0]['path']#第一
        return {'shells':壳列,'selectedShell':选中}#菜单

    def 选择外壳(自身,路径):#引导选择
        """打开标签前记住。"""
        记住外壳(路径)#记下

    def 关闭(自身,会话标识,键,终端标识=None):#立刻放标签
        """清理活过 DOM 卸挂与刷新。"""
        会话表=自身._视图.get(会话标识)#表
        视图=None if 会话表 is None else 会话表.get(键)#出现
        标识=视图.id if 视图 is not None else 终端标识#身份
        if 标识 is None:#无从关
            return#跳
        标题=键#回落
        if 视图 is not None:#有模型
            快照=视图.状态.getSnapshot()#状态
            if 'title' in 快照 and 快照['title'] is not None:#有标题
                标题=快照['title']#用
        请求={'sessionId':会话标识,'id':标识,'title':标题}#意图
        自身._已关.add(标识)#本页
        自身._请求.保存(请求)#持久
        if 会话表 is not None:#有表
            会话表.pop(键,None)#摘标签
            if len(会话表)==0:#空会话
                自身._视图.pop(会话标识,None)#摘
        自身._清理(请求,视图)#后台

    def 恢复(自身,会话标识):#Host 保留且本页未持有
        """可开成恢复标签的终端。"""
        结果=自身._远程.list(会话标识)#列表
        if not 结果['ok']:#失败
            raise RuntimeError(结果['error']['message'])#消息
        持有=set()#本页标签
        会话表=自身._视图.get(会话标识)#表
        if 会话表 is not None:#有
            for 视图 in 会话表.values():#出现
                持有.add(视图.id)#记下
        关闭中=set()#未完成关闭
        for 请求 in 自身._请求.未完成():#请求
            关闭中.add(请求['id'])#记下
        可恢复=[]#结果
        for 信息 in 结果['value']:#逐个
            标识=信息['id']#id
            if 标识 in 持有 or 标识 in 关闭中 or 标识 in 自身._已关:#占用
                continue#跳
            可恢复.append(信息)#收
        return 可恢复#列表

    def 重试关闭(自身,标识):#失败通知
        """不重开标签。"""
        记录=None#命中
        for 项 in 自身._请求.未完成():#查找
            if 项['id']==标识:#命中
                记录=项#记下
                break#停
        if 记录 is not None:#有
            自身._清理(记录)#再试

    def _清理(自身,记录,视图=None):#后台 Host 清理
        """成功与进行中无通知。"""
        if 记录['id'] in 自身._关闭中 or 自身._已拆除:#已在做
            return#跳
        失败列=[项 for 项 in 自身.closeFailures.getSnapshot() if 项['id']!=记录['id']]#摘旧失败
        自身.closeFailures.set(失败列)#写回
        任务=操作任务()#本轮
        自身._关闭中[记录['id']]=任务#登记
        def 跑():#线程
            """关进程或远程 close。"""
            try:#清理
                try:#主路径
                    if 视图 is not None:#有模型
                        视图.关闭()#关
                    else:#仅身份
                        结果=自身._远程.close(记录['sessionId'],记录['id'])#远程
                        if not 结果['ok']:#失败
                            失败=结果['error']#载荷
                            raise 远程错误(失败['code'],失败['message'],失败['details'] if 'details' in 失败 else {})#包装
                    自身._请求.移除(记录['id'])#确认
                except BaseException as 错误:#失败
                    if 取码(错误)=='session/not-found':#会话没了
                        自身._请求.移除(记录['id'])#丢掉
                    elif not 自身._已拆除:#仍可见
                        自身.closeFailures.set(自身.closeFailures.getSnapshot()+[{
                            'id':记录['id'],#身份
                            'title':记录['title'],#标题
                            'message':取消息(错误),#消息
                        }])#追加
                if 视图 is not None:#放流
                    视图.释放()#释放
            finally:#摘进行
                自身._关闭中.pop(记录['id'],None)#摘
                任务.兑现(None)#完
        threading.Thread(target=跑).start()#后台

def 应用(上下文):#安装
    """Client 终端模型。"""
    客户端终端(上下文,上下文.remote.terminal)#构造即登记

inject=注入#框架槽
apply=应用#框架槽
