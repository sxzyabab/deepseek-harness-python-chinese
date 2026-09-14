import json,threading#JSON 解析与重载串行链
from concurrent.futures import Future as 原生结果#单次操作结果
from .事件 import 插件事件帧,事件端点,热更新错误#再导出 SSE 帧、路径与本包错误

class 操作任务:
    """单次操作的 Future 包装，只留 等待。"""
    def __init__(自身):
        """构造未决任务。"""
        自身._结果=原生结果()#底层 Future

    def 兑现(自身,值=None):
        """成功结算。"""
        if not 自身._结果.done():#尚未结算
            自身._结果.set_result(值)#写入结果
        return 值#返回兑现值

    def 拒绝(自身,错误):
        """失败结算。"""
        if not 自身._结果.done():#尚未结算
            if isinstance(错误,BaseException):#已是异常
                自身._结果.set_exception(错误)#原样拒绝
            else:#非异常
                包装=热更新错误('task rejected')#包装拒绝
                包装.原因=错误#附加信息做成属性
                自身._结果.set_exception(包装)#包装拒绝

    def 等待(自身,超时=None):
        """阻塞等到结算。"""
        return 自身._结果.result(timeout=超时)#取结果或抛错

__all__=['名称','注入','应用','拆除条目光纤','插件事件帧','事件端点','热更新错误']#仅中文公开名

名称='client-hmr'#插件名（字面量）
注入=['loader','modules']#依赖 loader 与 modules

def 找条目(加载器,标识):
    """找到模块说明符为 id 的 loader 条目。选项是配置文件 dict。"""
    for 条目 in 加载器.列出插件配置():#遍历 loader 树
        选项=条目.选项#配置文件选项
        if 'name' in 选项 and 选项['name']==标识:#名字匹配
            return 条目#返回
    return None#图里没有该条目

def 去掉所拥样式(标识):
    """去掉 id 所拥有的每一个 style[data-plugin] 标签。"""
    if 'document' not in globals():#非浏览器
        return#跳过
    文档=globals()['document']#浏览器 document
    for 元素 in 文档.querySelectorAll('style[data-plugin]'):#所有带该属性的 style
        if 元素.getAttribute('data-plugin')==标识:#属性值等于 id 才删
            元素.remove()#删除

def 拆除条目光纤(条目):
    """注册表优先拆除条目正在跑的光纤，好让 刷新 重建它。"""
    旧光纤=条目.纤程#记下旧光纤
    if 旧光纤 is None:#无光纤则不动
        return#跳过
    运行时=旧光纤.运行时#取出 runtime
    if 运行时 is not None:#有 runtime
        条目.所属上下文.注册表.删除(运行时.插件)#先从注册表删除
    条目.纤程=None#清掉 fiber，让 刷新 能再走初始化

def 应用(上下文):
    """挂上 HMR 驱动：订阅系统 SSE 通道并热替换已重建条目。"""
    模块加载器=上下文.modules#客户端模块系统
    加载器=上下文.loader#条目治理 Loader
    队列=操作任务()#重载串行队列
    队列.兑现(None)#起始已完成

    def 重载(标识,修订):
        """热替换一条图条目。prefetch 在模块系统内阻塞到工厂登记。"""
        条目=找条目(加载器,标识)#按包名找条目
        if 条目 is None:#不在 loader 树里
            上下文.日志.警告('client-hmr: rebuilt frame for unknown entry "'+标识+'" (not in the loader tree)')#未知条目，只警告
            return#无法重载
        模块加载器.invalidate(标识,修订)#丢掉过期工厂与记录并带上新 rev
        模块加载器.prefetch(标识)#加载并登记新工厂；内部阻塞
        拆除条目光纤(条目)#注册表优先拆除旧光纤
        去掉所拥样式(标识)#删掉本插件的 style 标签
        条目.刷新()#物化新工厂并再插件
        新光纤=条目.纤程#新光纤
        if 新光纤 is not None:#有新光纤
            新光纤.等待()#等新光纤落到稳定状态，启动失败则抛出

    def 处理帧(帧):
        """按帧类型处理。帧是 JSON 解析出的 dict。"""
        nonlocal 队列#串行队列
        if 'type' not in 帧:#缺判别标签
            return#未知类型按设计忽略
        种类=帧['type']#判别标签
        if 种类=='rebuilt':#某行打包已重建
            标识=帧['id']#条目 id
            修订=帧['rev']#内容修订
            def 下一步():
                """执行一次重载。"""
                try:#重载
                    重载(标识,修订)#热替换
                except BaseException as 错误:#失败只记日志
                    上下文.日志.错误('client-hmr: reload of "'+标识+'" failed')#重载失败标题
                    上下文.日志.错误(错误)#失败详情
            链尾=队列#当前队列尾
            本次=操作任务()#本次重载
            新尾=操作任务()#新队列尾
            队列=新尾#先挂新尾
            def 执行串行链():
                """接到链尾后跑下一步。"""
                try:#等前一重载
                    try:#前一失败也继续
                        链尾.等待()#等链尾
                    except BaseException:#吞掉链尾失败
                        pass#链尾必须挺过失败
                    下一步()#执行重载
                    本次.兑现(None)#成功
                except BaseException as 错误:#重载失败
                    本次.拒绝(错误)#记失败
                finally:#无论成败都放行链
                    新尾.兑现(None)#放行
            threading.Thread(target=执行串行链,daemon=True).start()#串行
            return#rebuilt 处理完
        if 种类=='graph':#连接时快照，未使用
            return#忽略
        return#未知类型按设计忽略

    def 拆除源():
        """关闭 EventSource。"""
        源.close()#关闭

    源=globals()['EventSource'](事件端点)#打开系统 SSE
    def 收消息(事件):
        """解析并处理一帧。事件是 DOM MessageEvent。"""
        try:#开发通道帧可能畸形
            帧=json.loads(事件.data)#按线协议解析
        except json.JSONDecodeError:#畸形 JSON
            上下文.日志.警告('client-hmr: unparseable event frame: '+str(事件.data))#记下原文
            return#忽略本帧
        处理帧(帧)#按类型处理
    源.addEventListener('message',收消息)#监听 message
    上下文.副作用(拆除源,'client-hmr: event source')#生命周期

name=名称#框架槽
inject=注入#框架槽
apply=应用#框架槽
