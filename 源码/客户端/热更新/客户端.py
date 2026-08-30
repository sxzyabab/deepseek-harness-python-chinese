"""client-hmr 的浏览器半边：客户端插件条目的热重载驱动。

对齐上游 `hmr/src/client/index.ts`。公开面仅中文名。监听宿主的系统 SSE 通道；收到 `rebuilt` 帧时重载该条目的打包产物，并原地替换 cordis 光纤。
"""
from ...依赖 import cordis#外部依赖胶水
import threading#重载串行链
from concurrent.futures import Future as _原生Future#单次操作结果
from .事件 import 插件事件帧,事件端点#再导出 SSE 帧与路径

class 操作任务:#单次异步结果
    def __init__(自身):#构造未决任务
        自身._future=_原生Future()#底层 Future
    def 兑现(自身,值=None):#成功结算
        if not 自身._future.done():#尚未结算
            自身._future.set_result(值)#写入结果
        return 值#返回兑现值
    def 拒绝(自身,错误):#失败结算
        if not 自身._future.done():#尚未结算
            if isinstance(错误,BaseException):#已是异常
                自身._future.set_exception(错误)#原样拒绝
            else:#非异常
                自身._future.set_exception(Exception(错误))#包装拒绝
    def wait(自身,超时=None):#阻塞等待
        return 自身._future.result(timeout=超时)#取结果或抛错
    def 等待(自身,超时=None):#兼容外来调用
        return 自身.wait(超时)#转发

def _等待(值):#统一阻塞到结算
    if callable(getattr(值,'wait',None)):#Future 风格
        return 值.wait()#等待
    return 值.等待()#本库或外来 thenable

def 已兑现(值=None):#立刻兑现的操作任务
    任务=操作任务()#新任务
    任务.兑现(值)#立刻成功
    return 任务#已完成

__all__=['名称','注入','应用','插件事件帧','事件端点']#仅中文公开名

名称='client-hmr'#插件名（字面量）
注入=['loader','modules']#依赖 loader 与 modules

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待承诺
    return 值#同步值

def 找条目(加载器,标识):#按包名找条目
    """找到模块说明符为 id 的 loader 条目。"""
    for 条目 in 加载器.entries():#遍历 loader 树
        if 取字段(取字段(条目,'options'),'name')==标识:#名字匹配
            return 条目#返回
    return None#图里没有该条目

def 去掉所拥样式(标识):#按 data-plugin 删样式
    """去掉 id 所拥有的每一个 style[data-plugin] 标签。"""
    文档=getattr(__import__('builtins'),'document',None)#浏览器 document
    if 文档 is None:#无 DOM
        文档=globals().get('document')#全局 document
    if 文档 is None:#仍无
        return#跳过
    for 元素 in 文档.querySelectorAll('style[data-plugin]'):#所有带该属性的 style
        if 元素.getAttribute('data-plugin')==标识:#属性值等于 id 才删
            元素.remove()#删除

def 应用(上下文):#安装浏览器半边 HMR
    """挂上 HMR 驱动：订阅系统 SSE 通道并热替换已重建条目。"""
    模块加载器=上下文.modules#客户端模块系统
    加载器=上下文.loader#条目治理 Loader
    队列=已兑现(None)#重载串行队列

    def 重载(标识):#热替换一条图条目
        """热替换一条图条目。"""
        条目=找条目(加载器,标识)#按包名找条目
        if 条目 is None:#不在 loader 树里
            上下文.logger.warn('client-hmr: rebuilt frame for unknown entry "'+标识+'" (not in the loader tree)')#未知条目，只警告
            return#无法重载
        模块加载器.invalidate(标识)#丢掉过期工厂与记录
        解开(模块加载器.prefetch(标识))#加载并登记新工厂
        旧光纤=取字段(条目,'fiber')#记下旧光纤
        if 旧光纤 is not None:#有旧光纤才拆
            运行时=取字段(旧光纤,'runtime')#取出 runtime
            if 运行时 is not None:#有 runtime
                条目.ctx.registry.delete(取字段(运行时,'callback'))#先从注册表删除
            while 取字段(旧光纤,'inertia') is not None:#等到惯性卸载结束
                解开(旧光纤.inertia)#等待
            if hasattr(条目,'fiber'):#可清 fiber
                try:#清掉 fiber
                    delattr(条目,'fiber')#让 refresh 能再走 _init
                except Exception:#属性锁
                    条目.fiber=None#置空
        去掉所拥样式(标识)#删掉本插件的 style 标签
        解开(条目.refresh())#物化新工厂并再插件
        新光纤=取字段(条目,'fiber')#新光纤
        if 新光纤 is not None:#有新光纤
            解开(新光纤.await_()) if hasattr(新光纤,'await_') else 解开(getattr(新光纤,'await',lambda:None)())#等新光纤落到稳定状态

    def 处理帧(帧):#按帧类型处理
        """按帧类型处理。"""
        种类=取字段(帧,'type')#判别标签
        nonlocal 队列#串行队列
        if 种类=='rebuilt':#某行打包已重建
            标识=取字段(帧,'id')#条目 id
            def 下一步(_前=None):#接到队列尾
                """执行一次重载。"""
                try:#重载
                    重载(标识)#热替换
                except Exception as 错误:#失败只记日志
                    上下文.logger.error('client-hmr: reload of "'+标识+'" failed')#重载失败标题
                    上下文.logger.error(错误)#失败详情
            链尾=队列#当前队列尾

            本次=操作任务()#本次重载

            新尾=操作任务()#新队列尾

            队列=新尾#先挂新尾

            def 跑链():#接到链尾后跑下一步

                try:#等前一重载

                    try:#前一失败也继续

                        _等待(链尾)#等链尾

                    except BaseException:#吞掉

                        pass#链尾必须挺过失败

                    下一步()#执行重载

                    本次.兑现(None)#成功

                except BaseException as 错误:#重载失败

                    本次.拒绝(错误)#记失败

                finally:#无论成败都放行链

                    新尾.兑现(None)#放行

            threading.Thread(target=跑链,daemon=True).start()#串行
            return#rebuilt 处理完
        if 种类=='graph':#连接时快照，未使用
            return#忽略
        return#未知类型按设计忽略

    def 拆除源():#拆除时关闭 EventSource
        """关闭 EventSource。"""
        源.close()#关闭

    源=None#EventSource 实例
    try:#打开系统 SSE
        EventSource=getattr(__import__('builtins'),'EventSource',None)#浏览器 EventSource
        if EventSource is None:#可能在 globals
            EventSource=globals().get('EventSource')#全局
        if EventSource is not None:#有 EventSource
            源=EventSource(事件端点)#打开系统 SSE
            def 收消息(事件):#每条 message 一帧
                """解析并处理一帧。"""
                try:#开发通道帧可能畸形
                    帧=json解析(取字段(事件,'data'))#按线协议解析
                except Exception:#畸形开发通道帧大声丢掉
                    上下文.logger.warn('client-hmr: unparseable event frame: '+str(取字段(事件,'data')))#记下原文
                    return#忽略本帧
                处理帧(帧)#按类型处理
            源.addEventListener('message',收消息)#监听 message
            上下文.effect(拆除源,'client-hmr: event source')#生命周期
    except Exception as 错误:#无法打开通道
        上下文.logger.warn(错误)#记警告

def json解析(文本):#JSON 解析
    """把 SSE data 文本解析成帧。"""
    import json#JSON
    return json.loads(文本)#解析
