from . import 文案
from . import 呈现
from . import 目录
from . import 设置仓库
from . import 权限行
from . import 权限选择

__all__=['文案','呈现','目录','设置仓库','权限行','权限选择','依赖','应用']

依赖=[
    'commandUi','connection','sessions','slots','locale','remote',
    'remote.permissionPresets','remote.settings',
    'configForms','settingsSchema',
]

def 选取于(会话):
    '读会话 permissions 投影。能力缺席则 None'
    if 会话 is None:
        return None
    面=会话.projections.面('permissions')
    return 面['getSnapshot']()

def 应用(上下文,配置=None):
    '登记 /permission 弹出选择、通用设置行，以及进程权限目录'
    命令=上下文.获取服务('commandUi')
    会话面=上下文.sessions
    def 登记访问词典():
        '登记当前会话中英文案表。页面显示不走英文表'
        return 上下文.locale.register(文案.权限访问命名空间,{'zh':文案.访问中文,'en':文案.访问英文})
    上下文.副作用(登记访问词典,'ui-permission: current-session dictionaries')
    def 会话标识(会话上下文):
        '命令壳传来的会话上下文。dict 和对象都读 sessionId'
        if isinstance(会话上下文,dict):
            return 会话上下文['sessionId']
        return 会话上下文.sessionId
    def 会话于(会话上下文):
        '按 sessionId 取已经物化的会话'
        绑定=会话面.binding(会话标识(会话上下文))
        if 绑定 is None:
            return None
        return 绑定['session']
    def 提交(会话标识值,预设):
        '经 /permission 命令切换当前会话'
        绑定=会话面.binding(会话标识值)
        活=None if 绑定 is None else 绑定['session']
        if 活 is None:
            raise Exception('this session is not materialized yet')
        结果=活.command('/permission '+预设)
        if 结果['ok'] is not True:
            错=结果['error']
            if isinstance(错,dict):
                码=错['code']
                消息=错['message']
            else:
                码=错.code
                消息=错.message
            raise Exception('permission switch failed: '+str(码)+': '+str(消息))
        if 结果['value']['matched'] is not True:
            raise Exception('the host offers no /permission command')
        return True
    进程目录=目录.权限目录(上下文)
    def 拆目录():
        '拆除进程目录'
        def 拆():
            '停止订阅并作废在途读取'
            进程目录.拆除()
        return 拆
    上下文.副作用(拆目录,'ui-permission: process catalog directory')
    def 订失效():
        '目录失效时关掉已经打开的 /permission 弹出'
        def 关掉(*位置参数):
            '解散 permission 弹出'
            命令.dismiss('permission')
        return 进程目录.失效滴答.subscribe(关掉)
    上下文.副作用(订失效,'ui-permission: dismiss stale slash choices')
    def 登记设置词典():
        '登记设置行中英文案表。页面显示不走英文表'
        return 上下文.locale.register('settings.permission',{'zh':文案.中文,'en':文案.英文})
    上下文.副作用(登记设置词典,'ui-permission: settings row dictionaries')
    控制器=设置仓库.权限预设设置控制器(上下文.configForms.describe(),上下文,进程目录)
    def 行注入():
        '通用设置行的快照和读写'
        return {'hooks':{'permission':控制器.存储},'load':控制器.加载,'select':控制器.选定}
    def 拆控制器():
        '拆除设置行控制器'
        def 拆():
            '停止跟随镜像和目录'
            控制器.拆除()
        return 拆
    上下文.副作用(拆控制器,'ui-permission: settings row directory')
    def 登记设置行():
        '等通用设置条目槽出现再登记权限行'
        return 上下文.slots.register({
            'name':'settings.general.item',
            'id':'permission',
            'order':-20,
            'locale':'settings.permission',
            'inject':行注入,
        },权限行.权限行)
    上下文.slots.inject('settings.general.item',登记设置行)
    def 权限注入(会话标识值):
        '进程目录叠这一场会话的提交'
        def 选定(预设):
            '经 /permission 命令切换'
            return 提交(会话标识值,预设)
        return {'hooks':{'permissionCatalog':进程目录.存储},'select':选定}
    def 登记权限席():
        '撰写器当前会话权限席'
        return 上下文.slots.register({
            'name':'conversation.input.permission',
            'locale':文案.权限访问命名空间,
            'inject':权限注入,
        },权限选择.权限选择)
    上下文.slots.inject('conversation.input.permission',登记权限席)
    def 可用(会话上下文):
        '当前会话有权限投影才装饰这条命令'
        return 选取于(会话于(会话上下文)) is not None
    def 选项(会话上下文,信号):
        '弹出选项。命令壳会传入中止信号，这次读取不取消'
        选取=选取于(会话于(会话上下文))
        if 选取 is None:
            raise Exception('permission presets are not available on this host')
        目录值=进程目录.加载()
        当前值=选取['currentValue']
        def 访问文案(键):
            '当前会话权限中文表'
            return 文案.访问中文[键]
        表=[]
        for 项 in 目录值['options']:
            值=项['value']
            if 值==呈现.自动审查预设:
                标签=文案.访问中文['auto.label']
            else:
                标签=呈现.展示权限预设(值,项['name'],访问文案)
            选项项={'id':值,'label':标签}
            if 值==呈现.自动审查预设:
                选项项['badge']=文案.访问中文['auto.badge']
                选项项['detail']=文案.访问中文['auto.description']
            elif 'description' in 项 and 项['description'] is not None:
                选项项['detail']=项['description']
            if 值==当前值:
                选项项['active']=True
            if 值==呈现.完全权限预设 or 值==呈现.自动审查预设:
                自动=值==呈现.自动审查预设
                if 自动:
                    标题=文案.访问中文['auto.confirm.title']
                    说明=文案.访问中文['auto.confirm.description']
                    已知=文案.访问中文['auto.confirm.acknowledge']
                    启用=文案.访问中文['auto.confirm.enable']
                else:
                    标题=文案.访问中文['confirm.title']
                    说明=文案.访问中文['confirm.description']
                    已知=文案.访问中文['confirm.acknowledge']
                    启用=文案.访问中文['confirm.enable']
                选项项['confirmation']={
                    'title':标题,
                    'description':说明,
                    'acknowledgeLabel':已知,
                    'cancelLabel':文案.访问中文['confirm.cancel'],
                    'confirmLabel':启用,
                }
            表.append(选项项)
        return 表
    def 选中(选项项,会话上下文):
        '提交切换。没有额外返回'
        提交(会话标识(会话上下文),选项项['id'])
        return None
    def 挂装饰():
        '装饰宿主 /permission 的裸调用'
        return 命令.decorate({
            'name':'permission',
            'available':可用,
            'ui':{'kind':'popupSelect','options':选项,'onSelect':选中},
        })
    上下文.副作用(挂装饰,'ui-permission: /permission decoration')

inject=依赖
apply=应用
