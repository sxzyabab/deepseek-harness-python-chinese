from . import 上传偏好
from . import 上传行
from . import 文案

__all__=['依赖','应用','文案','上传偏好','上传行']

依赖=['slots','locale','configForms']

def 应用(上下文,配置=None):
    '宿主配置在时登记偏好行和保存提示'
    文案名='settings.sessionLog'
    名字空间='session-log-deepseek'
    def 登记词典():
        '登记中英文案表。显示不走英文表。'
        return 上下文.locale.register(文案名,{'en':文案.英文,'zh':文案.中文})
    上下文.副作用(登记词典)
    表单=上下文.configForms.get(名字空间)
    偏好=上传偏好.上传偏好(表单)
    def 注入面():
        '行和提示共用的钩子与写入'
        return {
            'hooks':{'upload':表单,'mutation':偏好.状态},
            'setEnabled':偏好.设置启用,
            'dismiss':偏好.关掉提示,
        }
    def 监视():
        '宿主提供会话日志配置期间登记这一行'
        def 挂行(已提供):
            '命名空间出现时注入设置行。已提供是当前已被服务的命名空间集合。'
            def 登记行():
                '登记通用设置底部一行'
                return 上下文.slots.register({
                    'name':'settings.general.item',
                    'id':名字空间,
                    'order':90,
                    'locale':文案名,
                    'inject':注入面,
                },上传行.上传行)
            return 上下文.slots.inject('settings.general.item',登记行)
        return 上下文.configForms.在已提供期间([名字空间],挂行)
    上下文.副作用(监视)
    def 登记提示():
        '登记关掉设置后仍在的保存提示'
        return 上下文.slots.register({
            'name':'shell.overlay',
            'id':'session-log-upload-toast',
            'locale':文案名,
            'inject':注入面,
        },上传行.上传提示)
    上下文.slots.inject('shell.overlay',登记提示)

inject=依赖
apply=应用
