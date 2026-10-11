'宿主会话日志上传配置的通用设置配套'
from .上传偏好 import 上传偏好
from .上传行 import 上传行,上传提示
from .文案 import 命名空间,英文,中文

__all__=['依赖','应用']

依赖=['slots','locale','configForms']

def 应用(上下文):
    '宿主配置在时登记偏好行和保存提示'
    名字空间='session-log-deepseek'
    def 登记词典():
        '登记文案'
        return 上下文.locale.register(命名空间,{'en':英文,'zh':中文})
    上下文.副作用(登记词典)
    表单=上下文.configForms.get(名字空间)
    偏好=上传偏好(表单)
    def 注入面():
        '行和提示共用的钩子'
        return {
            'hooks':{'upload':表单,'mutation':偏好.状态},
            'setEnabled':偏好.设置启用,
            'dismiss':偏好.关掉提示,
        }
    def 登记行():
        '通用设置底部的一行'
        return 上下文.slots.register({
            'name':'settings.general.item',
            'id':名字空间,
            'order':90,
            'locale':命名空间,
            'inject':注入面,
        },上传行)
    def 在提供时():
        '命名空间出现才登记这一行'
        return 上下文.slots.inject('settings.general.item',登记行)
    上下文.副作用(lambda:上下文.configForms.在已提供期间([名字空间],lambda 已提供:在提供时()))
    def 登记提示():
        '壳层上的保存提示'
        return 上下文.slots.register({
            'name':'shell.overlay',
            'id':'session-log-upload-toast',
            'locale':命名空间,
            'inject':注入面,
        },上传提示)
    上下文.slots.inject('shell.overlay',登记提示)

inject=依赖
apply=应用
