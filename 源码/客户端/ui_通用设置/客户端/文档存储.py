from ...存储 import 创建快照存储

__all__=['设置文档存储']

class 设置文档存储:
    '本机回环才跟着设置镜像，判断有没有可打开的配置文件'
    def __init__(自身,上下文,描述面):
        '空闲快照。描述面是 configForms.describe() 交回的镜像'
        自身.上下文=上下文
        自身.描述面=描述面
        自身.存储=创建快照存储({'status':'idle','opening':False,'error':None})
        自身.跟随=None

    def 加载(自身):
        '开始跟随镜像，并把当前有没有文档写进快照'
        if 自身.跟随 is None:
            自身.跟随=自身.描述面.subscribe(自身.派生)
        def 写加载(状态):
            '先标加载，清掉上一次错误'
            状态['status']='loading'
            状态['error']=None
        自身.存储.update(写加载)
        自身.描述面.确保()
        自身.派生()

    def 打开(自身):
        '就绪且没在打开时，请求宿主打开配置文件。并发点击并进同一次'
        当前=自身.存储.getSnapshot()
        if 当前['status']!='ready' or 当前['opening']:
            return
        def 写打开(状态):
            '标正在打开并清错误'
            状态['opening']=True
            状态['error']=None
        自身.存储.update(写打开)
        try:
            结果=自身.上下文.remote.settings.openSettingsDocument()
            if 结果['ok'] is not True:
                消息=结果['error']['message']
                def 写错误(状态):
                    '留下宿主拒绝的原文，界面另显示固定中文'
                    状态['error']=消息
                自身.存储.update(写错误)
        finally:
            def 写结束(状态):
                '这次打开结束'
                状态['opening']=False
            自身.存储.update(写结束)

    def 拆除(自身):
        '停止跟随镜像'
        if 自身.跟随 is not None:
            自身.跟随()
            自身.跟随=None

    def 派生(自身):
        '镜像还没有答案时维持加载。有错误且没有视图则不可用'
        镜像=自身.描述面.getSnapshot()
        视图=镜像.get('view')
        if 视图 is None:
            if 镜像.get('error') is not None:
                错误=镜像.get('error')
                def 写不可用(状态):
                    '文档定位失败'
                    状态['status']='unavailable'
                    状态['error']=错误
                自身.存储.update(写不可用)
            return
        有文档=视图.get('hasDocument') is True
        def 写就绪(状态):
            '有文档才可打开，并清掉定位错误'
            if 有文档:
                状态['status']='ready'
            else:
                状态['status']='unavailable'
            状态['error']=None
        自身.存储.update(写就绪)
