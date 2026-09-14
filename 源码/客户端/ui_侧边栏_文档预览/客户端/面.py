import threading#读取线程与中止监视
from .远程过程调用 import 文档文件字节#字节解码

__all__=['已中止','文本面']#仅中文公开名


def 已中止(信号):
    """信号是否已中止。无信号视为未中止。信号为 threading.Event。"""
    if 信号 is None:#无
        return False#未中止
    return 信号.is_set()#Event 置位


def 文本面(读取,完整读取):
    """把预览面绑到一份分页读与一份完整字节读。

    返回槽位 `inject` 工厂：会话标识与已绑定动作进，注入面出。
    """

    def 工厂(_会话标识,动作):
        """构造 loadPage / reloadPages / loadAll / reloadAll。"""
        标签表={}#标签标识 → {generation, version, mode}

        def 读取簿(标签标识,信号):
            """取或建簿记；首次武装中止监听。"""
            if 标签标识 in 标签表:#已有
                return 标签表[标签标识]#复用
            簿={'generation':0,'version':None,'mode':'text-pages'}#新建
            标签表[标签标识]=簿#挂上

            def 清理():
                """记录结束：清簿记与桶。"""
                if 标签标识 in 标签表:#仍在
                    del 标签表[标签标识]#清
                动作['forget'](标签标识)#清桶

            if 信号 is not None:#有信号
                def 监视():
                    """等中止后清理。"""
                    信号.wait()#阻塞至置位
                    清理()#清
                threading.Thread(target=监视,daemon=True).start()#守护
            return 簿#簿记

        def 模式簿(标签标识,信号,模式):
            """换模式时晋代并重置桶。"""
            簿=读取簿(标签标识,信号)#簿记
            if 簿['mode']!=模式:#换模式
                簿['mode']=模式#记下
                簿['generation']+=1#晋代
                簿['version']=None#清版本
                动作['reset'](标签标识)#重置
            return 簿#簿记

        def 加载页(标签标识,文件,偏移,信号,观察版本=None):
            """把一页读进存储。"""
            if 已中止(信号):#已中止
                return#停
            簿=模式簿(标签标识,信号,'text-pages')#文本页
            代次=簿['generation']#本代
            动作['loading'](标签标识,'text-pages',观察版本)#标加载

            def 结算():
                """分页读结算。"""
                if 已中止(信号) or 簿['generation']!=代次:#过期
                    return#丢
                结果=读取(文件['sessionId'],文件['path'],偏移,信号)#RemoteResult
                if 已中止(信号) or 簿['generation']!=代次:#过期
                    return#丢
                if not 结果['ok']:#失败
                    动作['failed'](标签标识,结果['error'])#失败
                    return#停
                值=结果['value']#页
                if 偏移!=1 and 簿['version'] is not None and 值['version']!=簿['version']:#换版
                    重启(标签标识,文件,信号,观察版本,'text-pages')#重启
                    return#停
                簿['version']=值['version']#记下
                动作['page'](标签标识,值)#写入

            threading.Thread(target=结算,daemon=True).start()#守护

        def 加载全部(标签标识,文件,信号,观察版本=None):
            """为整文件渲染器读取完整文件。"""
            if 已中止(信号):#已中止
                return#停
            簿=模式簿(标签标识,信号,'bytes-complete')#完整字节
            代次=簿['generation']#本代
            动作['loading'](标签标识,'bytes-complete',观察版本)#标加载

            def 结算():
                """完整读结算。"""
                if 已中止(信号) or 簿['generation']!=代次:#过期
                    return#丢
                结果=完整读取(文件,信号)#RemoteResult
                if 已中止(信号) or 簿['generation']!=代次:#过期
                    return#丢
                if not 结果['ok']:#失败
                    动作['failed'](标签标识,结果['error'])#失败
                    return#停
                try:
                    文件字节=文档文件字节(结果['value'])#解码
                except Exception as 错:#畸形 base64
                    动作['failed'](标签标识,{#远程错误形
                        'name':'RemoteError',
                        'message':'document file byte response has malformed base64 data',
                        'isDSHRemoteError':True,
                        'code':'gateway/internal',
                        'details':{},
                        'cause':错,
                    })
                    return#停
                簿['version']=文件字节['version']#记下
                动作['complete'](标签标识,文件字节)#写入

            threading.Thread(target=结算,daemon=True).start()#守护

        def 重启(标签标识,文件,信号,观察版本=None,模式='text-pages'):
            """丢掉页并按模式重读。"""
            if 已中止(信号):#已中止
                return#停
            簿=读取簿(标签标识,信号)#簿记
            簿['generation']+=1#晋代
            簿['version']=None#清版本
            动作['reset'](标签标识)#重置
            if 模式=='text-pages':#文本页
                加载页(标签标识,文件,1,信号,观察版本)#首页
            else:#完整字节
                加载全部(标签标识,文件,信号,观察版本)#完整

        def 重载全部(标签标识,文件,信号,观察版本=None):
            """丢掉旧完整结果并重读。"""
            重启(标签标识,文件,信号,观察版本,'bytes-complete')#完整模式

        return {#注入面
            'loadPage':加载页,
            'reloadPages':重启,
            'loadAll':加载全部,
            'reloadAll':重载全部,
        }#面结束

    return 工厂#inject 工厂
