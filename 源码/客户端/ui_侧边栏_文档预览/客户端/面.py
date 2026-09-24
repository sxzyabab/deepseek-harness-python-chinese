import threading#读取线程与中止监视
from .文档.资源组 import 资源组

__all__=['已中止','文本面']#仅中文公开名

def 已中止(信号):
    """信号是否已中止。无信号视为未中止。信号为 threading.Event。"""
    if 信号 is None:#无
        return False#未中止
    return 信号.is_set()#Event 置位

def 文本面(读取,完整读取,资源):
    """把预览面绑到一份分页读、完整字节读与资源组成员。"""
    def 工厂(_会话标识,动作):
        """构造 loadPage / reloadPages / loadAll / reloadAll / prepareRenderer / addResource / setResources。"""
        标签表={}#标签标识 → 簿记
        def 读取簿(标签标识,信号):
            """取或建簿记；首次武装中止监听。"""
            if 标签标识 in 标签表:#已有
                return 标签表[标签标识]#复用
            def 资源已变():
                动作['resourceChanged'](标签标识)
            簿={'generation':0,'version':None,'mode':'text-pages','group':资源组(资源,资源已变)}#新建
            标签表[标签标识]=簿#挂上
            def 清理():
                """记录结束：清簿记与桶。"""
                飞=簿.get('controller')#飞行
                if 飞 is not None:#有
                    飞.set()#中止
                簿['group'].close()
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
        def 模式簿(标签标识,信号,模式,渲染器标识=None):
            """换模式或渲染器时晋代并重置桶。"""
            簿=读取簿(标签标识,信号)#簿记
            if 簿['mode']!=模式 or 簿.get('rendererId')!=渲染器标识:#换
                飞=簿.get('controller')#旧飞
                if 飞 is not None:#有
                    飞.set()#中止
                if 渲染器标识 is None:#清
                    if 'rendererId' in 簿:#有
                        del 簿['rendererId']#删
                else:#记下
                    簿['rendererId']=渲染器标识#写
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
            旧飞=簿.get('controller')#旧飞
            if 旧飞 is not None:#有
                旧飞.set()#中止
            控制器=threading.Event()#本飞
            簿['controller']=控制器#记下
            动作['loading'](标签标识,'bytes-complete',观察版本)#标加载
            def 结算():
                """完整读结算。"""
                if 已中止(信号) or 控制器.is_set():#过期
                    return#丢
                结果=完整读取(文件,信号)#RemoteResult（已解码）
                if 已中止(信号) or 控制器.is_set():#过期
                    return#丢
                if not 结果['ok']:#失败
                    动作['failed'](标签标识,结果['error'])#失败
                    return#停
                文件字节=结果['value']#已解码
                簿['version']=文件字节['version']#记下
                动作['complete'](标签标识,文件字节)#写入
            threading.Thread(target=结算,daemon=True).start()#守护
        def 重启(标签标识,文件,信号,观察版本=None,模式='text-pages'):
            """丢掉页并按模式重读。"""
            if 已中止(信号):#已中止
                return#停
            簿=读取簿(标签标识,信号)#簿记
            飞=簿.get('controller')#旧飞
            if 飞 is not None:#有
                飞.set()#中止
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
        def 准备渲染器(标签标识,信号,渲染器标识,观察版本=None,重载=False):
            """开始渲染器自有加载，不读源字节。"""
            if 已中止(信号):#已中止
                return#停
            模式簿(标签标识,信号,'renderer',渲染器标识)#渲染器模式
            if 重载:#重载
                动作['reset'](标签标识)#清内容
            动作['loading'](标签标识,'renderer',观察版本,渲染器标识)#标加载
        def 加资源(标签标识,地址,信号):
            if not 已中止(信号):
                读取簿(标签标识,信号)['group'].add(地址)
        def 设资源(标签标识,地址表,信号):
            if not 已中止(信号):
                读取簿(标签标识,信号)['group'].set(地址表)
        return {#注入面
            'addResource':加资源,
            'setResources':设资源,
            'loadPage':加载页,
            'reloadPages':重启,
            'loadAll':加载全部,
            'reloadAll':重载全部,
            'prepareRenderer':准备渲染器,
        }#面结束
    return 工厂#inject 工厂
