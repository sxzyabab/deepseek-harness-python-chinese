from ...预设.智能体预设注册表.展示 import 预设展示文本#出厂预设名
from .文案 import 命名空间,中文,英文#词表
from .清单页签 import 插件清单页签#页签组件
from .异常 import 插件清单错误,页面失败文案

__all__=['依赖','应用','插件清单页签','命名空间','中文','英文']#仅中文公开名

依赖=['slots','locale','remote','remote.pluginInventory','modules']#槽位、文案、远程、清单远程面、模块

def 应用(上下文):#安装只读清单页签
    '把惰性清单页签贡献给插件设置分区'
    def 登记词典():#登记中英文案
        '把清单词表写进 locale'
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})#登记词表
    上下文.副作用(登记词典,'ui-settings-plugin-inventory: dictionaries')#登记词表
    翻译=上下文.locale.bind(命名空间)#绑定本插件词表
    def 列表():#拉取当前宿主清单快照
        '调用清单远程面；失败抛错'
        应答=上下文.remote.pluginInventory.list().等待()#远程 list
        结果=应答['result'] if 'result' in 应答 else 应答#信封或业务
        if not 结果['ok']:#业务失败
            错误=结果['error'] if 'error' in 结果 and 结果['error'] is not None else {}#错误
            码=错误['code'] if 'code' in 错误 else None
            消息=错误['message'] if 'message' in 错误 else None
            raise 插件清单错误('pluginInventory.list failed: '+str(码)+': '+页面失败文案(消息))
        return 结果['value'] if 'value' in 结果 else None#快照
    def 解析包文案(文本):#当前语言下的包内文案
        '字符串原样；映射按当前语言覆盖，空串也算已有译文'
        方法=getattr(上下文.locale,'resolveText',None)#语言服务若已提供
        if callable(方法):#走服务
            return 方法(文本)#解析
        if isinstance(文本,str):#纯字符串
            return 文本#原样
        if not isinstance(文本,dict):#不是映射
            return ''#空
        快照=上下文.locale.getSnapshot()#当前语言快照
        活动=快照['active'] if isinstance(快照,dict) and 'active' in 快照 else 'zh'#活动语言
        活动=活动.lower() if isinstance(活动,str) else 'zh'#小写
        链=[]#由宽到窄
        for 语言 in (活动,活动.split('-')[0],'zh','en'):#精确、主标签、中文、英文
            if 语言 not in 链:#去重
                链.append(语言)#记入
        结果=文本['en'] if 'en' in 文本 and 文本['en'] is not None else ''#英文兜底
        for 语言 in reversed(链):#越具体越后写
            if 语言 in 文本 and 文本[语言] is not None:#该语言有译文
                结果=文本[语言]#覆盖
        return 结果#选定译文
    def 预设名(预设):#解析预设显示名
        '出厂预设走 Agent 预设词典，自写元数据保持原文'
        智能体文案=上下文.locale.bind('settings.agentPreset')#预设词典
        return 预设展示文本(预设,智能体文案)['name']#显示名
    def 重试本页():#重试本页同步
        'modules.entries.retry；失败只记去掉路径后的说明，不装载插件'
        try:#重试
            上下文.modules.entries.retry()#本页同步
        except Exception as 错:
            上下文.日志.错误(页面失败文案(错))#说明不含绝对路径
    def 注入面():#页签注入面
        '清单、预设名、本页同步钩子'
        return {#注入
            'list':列表,#清单
            'presetName':预设名,#预设显示名
            'resolveText':解析包文案,#包内标题与说明
            'hooks':{'clientSync':上下文.modules.entries.state},#本页同步状态，对象自带 getSnapshot/subscribe
            'retryClient':重试本页,#重试本页
        }
    def 页签标签():#页签文案
        '全部清单页签标签'
        return 翻译('tab')#标签
    def 登记页签():#登记全部清单页签
        '登记 settings.plugins.tab 条目'
        return 上下文.slots.register({#等插件页签槽出现
            'name':'settings.plugins.tab',#插件页签槽名
            'id':'all',#全部清单页签 id
            'order':10,#排在可配置页签之后
            'label':页签标签,#页签标签
            'locale':命名空间,#文案
            'inject':注入面,#注入
        },插件清单页签)#页签组件
    上下文.slots.inject('settings.plugins.tab',登记页签)#页签

inject=依赖#框架槽
apply=应用#框架槽
