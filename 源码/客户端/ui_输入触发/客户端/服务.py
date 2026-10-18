'根上的触发服务。只登记源，并按会话找出控制器'
from ...模块.客户端.通告 import 取握手窗口
from ....依赖.cordis.服务 import 服务#服务基类
from ..内核.菜单归约 import 源字段#源上的字段
from .控制器 import 触发控制器#每会话控制器

__all__=['触发服务']

依赖=['sessions']#要等会话服务

class 触发服务(服务):
    '根登记表，以及按会话解析控制器'
    inject=依赖
    def __init__(自身,上下文,配置=None):
        '以 inputTriggers 挂上。文案一变就重拉已经打开的菜单'
        super().__init__(上下文,'inputTriggers')#服务名
        自身.活={'sources':[],'controllers':{}}#源按登记顺序，控制器按绑定身份

        def 文案变更(*位置参数):
            '每场会话的开放菜单再拉一次候选'
            for 控制器 in list(自身.活['controllers'].values()):#当前还在的控制器
                控制器.refreshOpenMenu()#不改命中

        上下文.监听('locale/change',文案变更)#文案切换

    def registerSource(自身,源):
        '登记一个触发源。同一个触发字符加同一个名字只能有一个'
        活=自身.活#变更都走这一份
        触发符=源字段(源,'trigger')#触发字符
        名字=源字段(源,'name')#源名
        for 已有 in 活['sources']:#已经登记的
            if 源字段(已有,'trigger')==触发符 and 源字段(已有,'name')==名字:#重复
                raise Exception('slash source "'+str(触发符)+str(名字)+'" is already registered')#拒绝
        活['sources'].append(源)#按登记顺序放进
        for 控制器 in list(活['controllers'].values()):#已经在的会话
            try:#一个源的预热失败不能拆掉登记
                控制器.sourceAdded(源)#预热并加入词表
            except Exception as 错误:#预热或订阅失败
                取握手窗口().console.error('[ui-input-trigger] source "'+str(触发符)+str(名字)+'" late-registration setup failed:',错误)#留下

        def 拆除():
            '从名册拿掉，并让还开着它的菜单丢掉这一组'
            位置=-1#按身份找
            下标=0#扫描
            while 下标<len(活['sources']):#登记表
                if 活['sources'][下标] is 源:#就是这一份
                    位置=下标#记下
                    break#停止
                下标+=1#下一个
            if 位置<0:#已经不在
                return#不用再拆
            活['sources'].pop(位置)#拿掉
            for 控制器 in list(活['controllers'].values()):#还在的会话
                控制器.sourceRemoved(源)#丢掉菜单组和词表

        return 拆除#交给调用方放进副作用

    def sessionOf(自身,作用域):
        '这场会话的控制器。作用域必须还指着保留中的那一代'
        会话面=自身.会话面()#会话服务
        会话=会话面.sessionOf(作用域)#这一代会话
        绑定=None if 会话 is None else 会话面.binding(会话.sessionId)#稳定绑定
        if 绑定 is None or 绑定['session'] is not 会话:#不是还留着的那一代
            raise Exception('slash.sessionOf requires a retained Session scope')#拒绝
        活=自身.活#变更都走这一份
        键=id(绑定)#绑定是字典，按身份做键
        已有=活['controllers'].get(键)#已经有控制器
        if 已有 is not None:#还在
            return 已有#原样
        def 排序键(项):
            '没有 order 时按 0。小的排在上面'
            序=源字段(项,'order')#可选顺序
            if 序 is None:#缺省
                return 0#默认
            return 序#源自己的顺序

        def 按触发(触发符):
            '这个字符的源，按 order 排，登记顺序保留'
            筛=[]#这个字符的
            for 项 in 活['sources']:#登记表
                if 源字段(项,'trigger')==触发符:#这个字符
                    筛.append(项)#留下
            筛.sort(key=排序键)#稳定排序
            return 筛#菜单顺序

        def 全部():
            '全部源，保持登记顺序'
            return 活['sources']#同一份列表

        控制器=触发控制器({#这一场
            'actx':绑定['ctx'],#会话作用域
            'sessionId':绑定['sessionId'],#会话号
            'roster':{'sources':按触发,'all':全部},#名册
        })
        活['controllers'][键]=控制器#记下

        def 随作用域拆():
            '作用域结束时拆掉控制器'
            def 摘掉():
                '拆控制器，并从表里拿掉'
                控制器.dispose()#关上并停拉取
                if 活['controllers'].get(键) is 控制器:#还是这一份
                    del 活['controllers'][键]#拿掉

            return 摘掉#拆除器

        绑定['ctx'].副作用(随作用域拆,'slash: session controller')#跟作用域走
        return 控制器#交给调用方

    def 会话面(自身):
        '取会话服务。还没有就抛出'
        会话=自身.ctx.获取服务('sessions')#会话
        if 会话 is None:#没挂上
            raise Exception('ui-input-trigger: sessions service unavailable')#不能解析会话
        return 会话#会话服务
