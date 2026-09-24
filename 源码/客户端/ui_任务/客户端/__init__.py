from .文案 import 命名空间,中文,英文#词典
from .任务列表动作 import 任务列表动作#头部作业列表

__all__=['依赖','应用','命名空间','中文','英文','任务列表动作']

依赖=['jobs','slots','locale']#作业名册、槽位、文案

def 应用(上下文):
    """登记词典与会话头部作业列表。"""
    def 登记词典():
        """登记作业词典。"""
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})
    上下文.副作用(登记词典,'ui-jobs: dictionaries')
    def 登记动作():
        """登记 header 作业列表。"""
        def 注入面():
            """作业名册、观测与停止。"""
            def 监视行(会话标识):
                """挂载期间保持名册流。"""
                return 上下文.jobs.watchRows(会话标识)
            def 观测(会话标识,标识):
                """观测一行实时输出。"""
                return 上下文.jobs.observe(会话标识,标识)
            def 停止作业(会话标识,作业标识):
                """人类停止；登记表接纳则 True。"""
                return 上下文.jobs.kill(会话标识,作业标识)['ok']
            return {
                'hooks':{'jobs':上下文.jobs.state},
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
