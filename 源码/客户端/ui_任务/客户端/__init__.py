from . import 文案
from .文案 import 中文,命名空间,英文
from .任务列表动作 import 任务列表动作

__all__=['依赖','应用','文案','任务列表动作','命名空间','中文','英文']

依赖=['jobs','slots','locale']

def 应用(上下文,配置=None):
    '登记词典，并在会话头部挂上这一会话的后台任务'
    def 登记词典():
        '登记 job 词典。显示不读这张表'
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})
    上下文.副作用(登记词典,'ui-jobs: dictionaries')
    def 登记动作():
        '等头部动作槽出现再登记'
        def 注入面():
            '名册、观察和停止。钩子名保持上游英文'
            模型=上下文.jobs.状态
            def 取快照():
                '名册与观察'
                return 模型.获取快照()
            def 订阅(监听):
                '快照变化时通知'
                return 模型.订阅(监听)
            def 监视行(会话标识):
                '挂载期间保持这一会话的名册'
                return 上下文.jobs.监视表行(会话标识)
            def 观测(会话标识,标识):
                '开始观察一条作业的实时输出'
                return 上下文.jobs.观察(会话标识,标识)
            def 停止作业(会话标识,作业标识):
                '登记表接纳这次停止则为真'
                结果=上下文.jobs.终止(会话标识,作业标识).等待()
                return 结果['ok']
            return {
                'hooks':{'jobs':{'getSnapshot':取快照,'subscribe':订阅}},
                'watchRows':监视行,
                'observe':观测,
                'killJob':停止作业,
            }
        return 上下文.slots.register({
            'name':'conversation.session.header.actions',
            'id':'job-list',
            'order':20,
            'locale':命名空间,
            'inject':注入面,
        },任务列表动作)
    上下文.slots.inject('conversation.session.header.actions',登记动作)

inject=依赖
apply=应用
