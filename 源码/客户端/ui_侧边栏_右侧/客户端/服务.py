from uuid import uuid4 as 生成随机UUID#多开页面地址后缀
from ...ui_停靠套件.引擎 import (#树只读
    活动停靠窗格标识,
    可分割,
    停靠窗格标识列表,
    查找标签窗格,
    查找内容标签,
    取窗格,
)#引擎
from ...存储 import 创建快照存储
from .约定.种子 import 页面地址
from .约定.槽位 import 右侧侧栏错误
from .存储 import 可关闭标签
from .标签域 import 标签域
from .标签清单 import 侧栏标签清单

__all__=['右侧侧栏错误','创建右侧侧栏控制器','右侧侧栏控制器','资源方案前缀']

资源方案前缀='dsh-resource://'


def 创建右侧侧栏控制器(注册表,钉住):
    """造控制器与认领、遗忘回调。返回 {controller, adopt, forget}。"""
    已认={}#session → {store, unsubscribe}
    清单=侧栏标签清单()
    控制器=右侧侧栏控制器(注册表,钉住,已认,清单.源)

    def 遗忘(会话标识):
        """永久清空的作用域。"""
        清单.移除(会话标识)

    def 认领(会话标识,存储):
        """认领会话存储实例；返回释放器。"""
        旧=已认[会话标识] if 会话标识 in 已认 else None#旧
        if 旧 is not None:#先退旧
            旧['unsubscribe']()#退
        def 同步():
            """提交后同步清单与标签域。"""
            表面表=存储['getSnapshot']()['bySession']#表
            表面=表面表[会话标识] if 会话标识 in 表面表 else None#表面
            签表=()
            if 表面 is not None:
                布局=表面['layout']
                原表=布局['tabs'] if 'tabs' in 布局 else None
                签表=原表.values() if 原表 is not None else ()
            清单.更新(会话标识,list(签表))
            if 表面 is not None:#有
                控制器.标签域.同步(会话标识,表面['layout'])#同步
        本次={'store':存储,'unsubscribe':存储['subscribe'](同步)}#认领
        已认[会话标识]=本次#写
        def 释放():
            """仅释放本次。"""
            本次['unsubscribe']()#退
            if 会话标识 in 已认 and 已认[会话标识] is 本次:#仍是本次
                del 已认[会话标识]#删
        return 释放#释放器

    return {'controller':控制器,'adopt':认领,'forget':遗忘}


class 右侧侧栏控制器:#跨插件右侧侧栏面
    """挂载席绑定写路径；认领存储供出现次动作。"""

    def __init__(自身,注册表,钉住,已认=None,打开标签=None):
        """构造。"""
        自身.注册表=注册表#类型表
        自身.已认=已认 if 已认 is not None else {}#认领表
        自身.绑定席=None#挂载席绑定
        自身.关闭钩表={}#kind → 钩
        自身.标签域=标签域(自身,钉住)#标签域
        自身.打开标签=打开标签#跨会话打开签元数据
        自身.已挂载=创建快照存储(None)#挂载会话可观察源
        自身.mounted=自身.已挂载

    def 登记关闭钩(自身,种类,钩):
        """显式移除前登记资源清理；失败则保留标签。返回拆除器。"""
        if 种类 in 自身.关闭钩表:#已登记
            raise 右侧侧栏错误('关闭钩已登记：'+种类)
        自身.关闭钩表[种类]=钩#挂上

        def 拆除():
            """仅卸本钩。"""
            if 种类 in 自身.关闭钩表 and 自身.关闭钩表[种类] is 钩:#仍是
                del 自身.关闭钩表[种类]#卸

        return 拆除#拆除器

    def 绑定(自身,绑定):
        """采纳挂载席绑定。"""
        自身.绑定席=绑定#写
        自身._发布已挂载()
        def 释放():
            """仅清本绑定。"""
            if 自身.绑定席 is 绑定:#仍是
                自身.绑定席=None#清
                自身._发布已挂载()
        return 释放#释放器

    def _发布已挂载(自身):
        """会话未变则静默。"""
        次=None if 自身.绑定席 is None else 自身.绑定席['sessionId']
        if 自身.已挂载.getSnapshot()!=次:
            自身.已挂载.set(次)

    def 打开资源(自身,地址,选项=None):
        """开资源。"""
        选项=选项 if 选项 is not None else {}#默认
        绑=自身._要求()#绑定
        自身._在会话放置资源(绑['sessionId'],绑['actions'],地址,选项)#放

    def 打开标签(自身,种类,选项=None):
        """开页面种类。"""
        选项=选项 if 选项 is not None else {}#默认
        绑=自身._要求()#绑定
        自身._在会话放置标签(绑['sessionId'],绑['actions'],种类,选项)#放

    def 在会话打开资源(自身,会话标识,地址,选项=None):
        """会话定向开资源。"""
        选项=选项 if 选项 is not None else {}#默认
        动作=自身._动作于(会话标识)#动作
        if 动作 is not None:#有
            自身._在会话放置资源(会话标识,动作,地址,选项)#放

    def 在会话打开标签(自身,会话标识,种类,选项=None):
        """会话定向开页面。"""
        选项=选项 if 选项 is not None else {}#默认
        动作=自身._动作于(会话标识)#动作
        if 动作 is not None:#有
            自身._在会话放置标签(会话标识,动作,种类,选项)#放

    def 在会话关闭(自身,会话标识,标签标识):
        """会话定向关签；独一停靠向导保持打开。"""
        动作=自身._动作于(会话标识)#动作
        认=自身.已认[会话标识] if 会话标识 in 自身.已认 else None#认
        if 动作 is None or 认 is None:#无
            return#停
        表面表=认['store']['getSnapshot']()['bySession']#表
        表面=表面表[会话标识] if 会话标识 in 表面表 else None#表面
        if 表面 is None:#无
            return#停
        签表=表面['layout']['tabs']#签表
        if 标签标识 not in 签表 or not 可关闭标签(表面,标签标识):#不可关
            return#停
        签=签表[标签标识]#记录

        def 提交():
            """关签。"""
            动作['closeTab'](会话标识,标签标识)#关

        自身._清理后移除(会话标识,签,提交)#清后关

    def _清理后移除(自身,会话标识,签,提交):
        """先跑关闭钩再提交。"""
        钩=自身.关闭钩表[签['kind']] if 签['kind'] in 自身.关闭钩表 else None#钩
        if 钩 is not None:#有
            钩(会话标识,签)#跑
        提交()#提交

    def _在会话放置资源(自身,会话标识,动作,地址,选项):
        """认领并放置资源。"""
        if not 地址.startswith(资源方案前缀):#非资源
            raise 右侧侧栏错误('没有已登记标签类型认领 "'+地址+'"')
        种类=选项['kind'] if 'kind' in 选项 else None#点名
        自身._放置(会话标识,动作,自身.注册表.认领(地址,种类),地址,选项,选项['params'] if 'params' in 选项 else None)#放

    def _在会话放置标签(自身,会话标识,动作,种类,选项):
        """放置页面种类。"""
        定义=自身.注册表.取(种类)#定义
        if 定义 is None:#无
            raise 右侧侧栏错误('没有登记为 "'+种类+'" 的标签类型')
        if 定义.get('multiple') is True:#每次独立内容
            地址=页面地址(种类)+'/'+str(生成随机UUID())#带 UUID
        else:#每窗一页
            地址=页面地址(种类)#页面地址
        认领={'kind':种类,'contentId':地址,'title':定义['title'](地址)}#认领
        自身._放置(会话标识,动作,认领,地址,选项,选项['params'] if 'params' in 选项 else None)#放

    def _放置(自身,会话标识,动作,认领,地址,放置,参数):
        """共享开路径。"""
        认=自身.已认[会话标识] if 会话标识 in 自身.已认 else None#认
        表面=None#表面
        if 认 is not None:#有存储
            表面表=认['store']['getSnapshot']()['bySession']#表
            表面=表面表[会话标识] if 会话标识 in 表面表 else None#表面
        if 表面 is None and 自身.绑定席 is not None and 自身.绑定席['sessionId']==会话标识:#绑席表面
            表面表=自身.绑定席['surfaces']#表
            表面=表面表[会话标识] if 会话标识 in 表面表 else None#表面
        布局=表面['layout'] if 表面 is not None else None#布局
        目标窗=None#目标窗
        if 布局 is not None:#有布局
            目标窗=放置['paneId'] if 'paneId' in 放置 and 放置['paneId'] is not None else 活动停靠窗格标识(布局)#窗
        目标=布局['nodes'][目标窗] if 布局 is not None and 目标窗 is not None and 目标窗 in 布局['nodes'] else None#节点
        优先新窗=(放置.get('preferNewPane') is True
            and ('replaceTab' not in 放置 or 放置['replaceTab'] is None)
            and 表面 is not None
            and 目标 is not None
            and 目标.get('kind')=='pane'
            and 目标.get('host')=='dock'
            and len(目标.get('tabs') or [])>0
            and 可分割(布局)
            and len(停靠窗格标识列表(布局))<2
            and 自身.绑定席 is not None
            and 自身.绑定席['sessionId']==会话标识
            and 自身.绑定席['canSplitPane'](目标['id']))#可否优先新窗
        意图={'kind':认领['kind'],'contentId':认领['contentId'],'title':认领['title']}#意图
        if 'paneId' in 放置 and 放置['paneId'] is not None:#窗
            意图['paneId']=放置['paneId']#写
        if 优先新窗:#新窗
            意图['preferNewPane']=True#写
        if 'replaceTab' in 放置 and 放置['replaceTab'] is not None:#替
            意图['replaceTab']=放置['replaceTab']#写
        if 'revealIfOpened' in 放置:#揭示
            意图['revealIfOpened']=放置['revealIfOpened']#写

        def 提交():
            """开内容并记导航。"""
            def 落定(标签标识):
                """记导航。"""
                自身.标签域.导航(会话标识,标签标识,{'address':地址,'params':参数})#导航
            动作['openContent'](会话标识,意图,落定)#开

        被替=None#被替签
        if 布局 is not None and 'replaceTab' in 放置 and 放置['replaceTab'] is not None:#有替
            被替=布局['tabs'][放置['replaceTab']] if 放置['replaceTab'] in 布局['tabs'] else None#记录
        已开=None#已开签
        if 布局 is not None and 放置.get('revealIfOpened') is not False:#默揭示
            已开=查找内容标签(布局,认领['contentId'],认领['kind'])#已开
        if 被替 is None or (已开 is not None and 被替['id']==已开):#无需清
            提交()#开
            return#停
        自身._清理后移除(会话标识,被替,提交)#替前清

    def 关闭(自身,标签标识):
        """关挂载会话签；独一停靠向导保持打开。"""
        绑=自身._要求()#绑定
        if 绑['sessionId'] in 自身.已认:#经会话路径
            自身.在会话关闭(绑['sessionId'],标签标识)#关
            return#停
        绑['actions']['closeTab'](绑['sessionId'],标签标识)#关

    def 活动(自身):
        """活动窗活动签记录。"""
        表面=自身._挂载()#表面
        if 表面 is None:#无
            return None#无
        布局=表面['layout']#布局
        窗=取窗格(布局,布局['activePaneId'])#窗
        活动签=窗['activeTabId']#活动签
        for 签 in 布局['tabs'].values():#找
            if 签['id']==活动签:#命中
                return 签#记录
        return None#无

    def 是否展开(自身):
        """是否展开。"""
        表面=自身._挂载()#表面
        if 表面 is None:#无
            return False#否
        return 表面['layout']['expanded'] is True#展开

    def 切换展开(自身):
        """切换展开。"""
        绑=自身._要求()#绑定
        绑['actions']['toggleExpanded'](绑['sessionId'])#切

    def 聚焦(自身,标签标识):
        """焦签。"""
        绑=自身._要求()#绑定
        表面=自身._挂载()#表面
        if 表面 is None or 标签标识 not in 表面['layout']['tabs']:#无
            return#止
        绑['actions']['focusTab'](绑['sessionId'],标签标识)#焦

    def 分栏(自身,窗格标识=None):
        """分栏；返回新窗或 None。"""
        绑=自身._要求()#绑定
        表面=自身._挂载()#表面
        if 表面 is None:#无
            return None#无
        布局=表面['layout']#布局
        目标=活动停靠窗格标识(布局) if 窗格标识 is None else 窗格标识#目标
        节点=布局['nodes'][目标] if 目标 in 布局['nodes'] else None#节点
        if 节点 is None or 节点['kind']!='pane' or 节点['host']!='dock':#非法
            return None#无
        可分窗=绑['canSplitPane']#房间规则
        if not 可分割(布局) or len(停靠窗格标识列表(布局))>=2 or not 可分窗(目标):#否
            return None#无
        新建=[None]#盒
        def 落定(标识):
            """记新建。"""
            新建[0]=标识#写
        绑['actions']['splitPane'](绑['sessionId'],目标,落定)#分
        return 新建[0]#新窗

    def 浮出(自身,标签标识,矩形=None):
        """浮出。"""
        绑=自身._要求()#绑定
        表面=自身._挂载()#表面
        if 表面 is None or 标签标识 not in 表面['layout']['tabs']:#无
            return#止
        if 查找标签窗格(表面['layout'],标签标识)['host']!='dock':#已浮
            return#止
        绑['actions']['floatTab'](绑['sessionId'],标签标识,矩形)#浮

    def 收回(自身,窗格标识):
        """收回浮窗。"""
        绑=自身._要求()#绑定
        表面=自身._挂载()#表面
        if 表面 is None:#无
            return#止
        节点=表面['layout']['nodes'][窗格标识] if 窗格标识 in 表面['layout']['nodes'] else None#节点
        if 节点 is None or 节点['kind']!='pane' or 节点['host']!='float':#非浮
            return#止
        绑['actions']['unfloatPane'](绑['sessionId'],窗格标识)#收

    def _撤销(自身):
        """测试用撤销。"""
        绑=自身._要求()#绑定
        绑['actions']['undo'](绑['sessionId'])#撤

    def _重做(自身):
        """测试用重做。"""
        绑=自身._要求()#绑定
        绑['actions']['redo'](绑['sessionId'])#重

    def _挂载(自身):
        """挂载会话表面。"""
        绑=自身.绑定席#绑定
        if 绑 is None:#无
            return None#无
        表=绑['surfaces']#表面表
        return 表[绑['sessionId']] if 绑['sessionId'] in 表 else None#表面

    def _动作于(自身,会话标识):
        """认领存储动作。"""
        认=自身.已认[会话标识] if 会话标识 in 自身.已认 else None#认
        if 认 is None:#无
            return None#无
        return 认['store']['actions']#动作

    def _要求(自身):
        """须有挂载席。"""
        if 自身.绑定席 is None:#无
            raise 右侧侧栏错误('尚未挂载会话表面')
        return 自身.绑定席#绑定
