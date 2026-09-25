"""浏览器命令服务；每个插件寿命一个键盘适配器。"""
import builtins#页面全局
from ....依赖.cordis.服务 import 服务#服务基类
from ..协议 import (#协议
    绑定问题,
    初始快捷键配置,
    规范化绑定,
    绑定重叠,
    呈现绑定,
)#协议
from .注册表 import 快捷键注册表#注册表
from .dom import 探测环境,安装键盘#DOM
from .存储 import Web快捷键存储,桌面快捷键存储#存储
from .原生 import 安装原生键盘#原生

__all__=[#仅中文公开名
    '依赖','快捷键服务',
]#公开面结束

依赖=['locale']#硬依赖本地化

class 快捷键服务(服务):
    """Cordis 键盘提供方；Desktop 启动需要原生键盘桥。"""
    inject=依赖#框架槽

    def __init__(自身,上下文):
        """探测环境、挂注册表与适配器。"""
        文档=builtins.document#文档
        导航=builtins.navigator#导航
        窗口=builtins.window#窗口
        环境=探测环境(文档,导航)#环境
        键盘=None#原生键盘桥
        if 环境['runtime']=='desktop':#桌面
            桌面=getattr(窗口,'dshDesktop',None)#preload
            键盘=getattr(桌面,'keyboard',None) if 桌面 is not None else None#键盘
            if 键盘 is None:#缺桥
                raise RuntimeError('Desktop 键盘桥不可用')#拒绝
        super().__init__(上下文,'shortcuts')#登记服务
        自身.keyboard=键盘#桥
        自身.runtime=环境['runtime']#壳
        自身.platform=环境['platform']#平台
        注入=getattr(builtins,'__DSH_SHORTCUTS_CONFIG__',None)#Host 注入
        表={} if 注入 is None else dict(注入)#表
        if 'stopSequenceMs' in 表 and 表['stopSequenceMs'] is not None:#有显式
            自身.stopSequenceMs=表['stopSequenceMs']#采用
        else:#缺省
            自身.stopSequenceMs=500#与 Host 默认一致
        自身.注册表=快捷键注册表(自身.runtime,自身.platform,初始快捷键配置())#注册表
        自身.catalog=自身.注册表.catalog#目录
        自身.config=自身.注册表.config#配置
        自身.fixedCatalog=自身.注册表.fixedCatalog#固定目录
        自身.固定监听=set()#固定输入监听
        自身.活跃=True#寿命
        自身.已连接=False#适配器已回
        def 发布(快照):
            """适配器推送已接受快照。"""
            if 自身.活跃 and 自身.已连接 and 快照['sequence']>=自身.config.getSnapshot()['sequence']:#有序
                自身.注册表.configure(快照)#配置
        Web面=None#Web 适配
        if 自身.runtime=='web':#Web
            Web面=Web快捷键存储(窗口,自身.platform,发布)#建
        自身.适配器=Web面 if Web面 is not None else 桌面快捷键存储(窗口)#适配器
        if 键盘 is not None:#原生键盘
            def 挂原生():
                """安装原生键盘。"""
                return 安装原生键盘(
                    窗口,键盘,自身.注册表,
                    lambda:自身.config.getSnapshot(),
                    lambda:自身.投递固定({'type':'reset'}),
                )#拆除器
            上下文.副作用(挂原生,'shortcuts: native keyboard')#寿命
        def 挂偏好():
            """订阅偏好并在拆除时停。"""
            卸=自身.适配器.subscribe(发布) if 自身.适配器 is not None else None#订阅
            def 拆除():
                """停活跃并卸。"""
                自身.活跃=False#停
                if 卸 is not None:#有
                    卸()#卸订阅
                if Web面 is not None:#Web
                    Web面.dispose()#拆除
            return 拆除#拆除器
        上下文.副作用(挂偏好,'shortcuts: preferences')#寿命
        自身.同步定义()#首同步
        def 挂键盘():
            """安装 DOM 键盘。"""
            用原生=键盘 is not None and (自身.platform=='macos' or 自身.platform=='windows')#原生拥有绑定
            卸=安装键盘(窗口,自身.注册表,lambda 输入:自身.投递固定(输入),用原生)#安装
            def 拆除():
                """卸键盘与固定监听。"""
                卸()#卸
                自身.固定监听.clear()#清
            return 拆除#拆除器
        上下文.副作用(挂键盘,'shortcuts: keyboard')#寿命
        def 挂语言():
            """语言变更刷新标签。"""
            return 上下文.locale.subscribe(lambda:自身.注册表.refreshLabels())#订阅
        上下文.副作用(挂语言,'shortcuts: locale')#寿命

    def register(自身,命令):
        """注册可编辑命令。"""
        卸=自身.注册表.register(命令)#登记
        自身.同步定义()#同步
        def 拆除():
            """拆除并再同步。"""
            卸()#卸
            自身.同步定义()#同步
        return 拆除#拆除器

    def registerFixed(自身,命令):
        """注册固定命令。"""
        卸=自身.注册表.registerFixed(命令)#登记
        自身.同步定义()#同步
        def 拆除():
            """拆除并再同步。"""
            卸()#卸
            自身.同步定义()#同步
        return 拆除#拆除器

    def observeFixedInput(自身,监听):
        """观察固定序列输入。"""
        自身.固定监听.add(监听)#加
        def 拆除():
            """退订。"""
            自身.固定监听.discard(监听)#删
        return 拆除#拆除器

    def 投递固定(自身,输入):
        """扇出固定输入；先消费者优先。"""
        已消费=False#是否已消费
        for 监听 in list(自身.固定监听):#复制后派发
            if 监听 not in 自身.固定监听:#中途退订
                continue#跳过
            try:#单监听
                if 输入['type']=='reset':#重置
                    监听(输入)#直传
                else:#keydown
                    def 消费(原消费=输入['consume']):
                        """包装消费。"""
                        nonlocal 已消费#写
                        已消费=True#记
                        原消费()#原
                    手势={**输入['gesture'],'defaultPrevented':输入['gesture']['defaultPrevented'] or 已消费}#手势
                    监听({'type':'keydown','gesture':手势,'context':输入['context'],'consume':消费})#投递
            except Exception as 错误:#处理器失败
                print('固定快捷键处理器失败',错误)#诊断

    def describeBinding(自身,绑定):
        """按设备物理键与预留规则描述候选。"""
        规范=None if 绑定 is None else 规范化绑定(绑定,自身.platform)#规范
        冲突=[]#冲突 id
        if 规范 is not None:#有候选
            for 行 in 自身.catalog.getSnapshot():#可编辑目录
                if 行['binding'] is not None and 绑定重叠(行['binding'],规范):#重叠
                    冲突.append(行['id'])#记
            for 行 in 自身.fixedCatalog.getSnapshot():#固定目录
                for 项 in 行['bindings']:#逐绑定
                    if 绑定重叠(项,规范):#重叠
                        冲突.append(行['id'])#记
                        break#止本行
        return {#描述
            'binding':规范,
            'keys':呈现绑定(规范,自身.platform)['keys'],
            'issue':None if 规范 is None else 绑定问题(规范,自身.runtime,自身.platform),
            'conflicts':冲突,
        }#描述结束

    def 同步定义(自身):
        """把当前目录交给适配器。"""
        if not 自身.活跃:#已拆
            return#跳过
        if 自身.适配器 is None:#无适配器
            自身.读失败()#失败
            return#止
        try:#获取
            快照=自身.适配器.get(自身.注册表.definitions())#同步获取
            自身.已连接=True#已连
            if 自身.活跃 and 快照['sequence']>=自身.config.getSnapshot()['sequence']:#有序
                自身.注册表.configure(快照)#配置
        except Exception:#读失败
            自身.读失败()#诊断

    def 读失败(自身):
        """标记不可读。"""
        if 自身.活跃:#仍活
            自身.注册表.configure({**自身.config.getSnapshot(),'status':'unreadable','error':'read'})#诊断

    def edit(自身,编辑,修订):
        """持久化一次已核对操作；失败保留已接受绑定。"""
        if 自身.适配器 is None:#无适配器
            return {'status':'unreadable','snapshot':自身.config.getSnapshot()}#不可读
        try:#保存
            结果=自身.适配器.edit(编辑,修订)#结果
        except Exception as 错误:#写失败
            if 自身.活跃:#仍活
                print('快捷键偏好保存失败',错误)#诊断
            return {'status':'write-failed','snapshot':自身.config.getSnapshot()}#写失败
        if 自身.活跃 and 结果['snapshot']['sequence']>=自身.config.getSnapshot()['sequence']:#有序
            自身.注册表.configure(结果['snapshot'])#配置
        return 结果#结果

    def recording(自身,活跃):
        """录制层占用键盘时抑制原生菜单加速器。"""
        if 自身.适配器 is None:#无
            raise RuntimeError('Desktop 快捷键桥不可用')#拒绝
        自身.适配器.recording(活跃)#同步完成

    def closeWindow(自身):
        """用当前已接受快捷键 revision 请求关闭 Desktop 窗口。"""
        if 自身.keyboard is None:#无桥
            raise RuntimeError('Desktop 键盘桥不可用')#拒绝
        自身.keyboard.closeWindow(自身.config.getSnapshot()['revision'])#关闭

inject=依赖#框架槽
default=快捷键服务#默认导出
快捷键服务.inject=依赖#框架槽
