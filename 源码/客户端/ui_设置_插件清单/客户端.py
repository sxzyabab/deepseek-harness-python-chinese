from .文案 import 命名空间,中文,英文#词表
from .清单页签 import 插件清单页签,插件清单错误#页签组件

__all__=['依赖','应用','插件清单页签','命名空间','中文','英文']#仅中文公开名

依赖=['slots','locale','remote','remote.pluginInventory','modules']#槽位、文案、远程、清单远程面、模块

def 应用(上下文):#安装只读清单页签
    """把惰性清单页签贡献给插件设置分区。"""
    def 登记词典():#登记中英文案
        """把清单词表写进 locale。"""
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})#登记词表
    上下文.副作用(登记词典,'ui-settings-plugin-inventory: dictionaries')#登记词表
    翻译=上下文.locale.bind(命名空间)#绑定本插件词表
    def 列表():#拉取当前宿主清单快照
        """调用清单远程面；失败抛错。"""
        应答=上下文.remote.pluginInventory.list().等待()#远程 list
        结果=应答['result'] if 'result' in 应答 else 应答#信封或业务
        if not 结果['ok']:#业务失败
            错误=结果['error'] if 'error' in 结果 and 结果['error'] is not None else {}#错误
            码=错误['code'] if 'code' in 错误 else None
            消息=错误['message'] if 'message' in 错误 else None#消息
            raise 插件清单错误(f"pluginInventory.list failed: {码}: {消息}")#诊断
        return 结果['value'] if 'value' in 结果 else None#快照
    def 预设名(预设):#解析预设显示名
        """优先元数据 name，否则 id。"""
        if 'name' in 预设 and 预设['name'] is not None and 预设['name']!='':#有 name
            return 预设['name']#显示名
        if 'id' in 预设:#有 id
            return 预设['id']#回退 id
        return ''#空
    def 重试本页():#重试本页同步
        """modules.entries.retry；失败记日志。"""
        try:#重试
            上下文.modules.entries.retry()#本页同步
        except Exception as 错:#失败
            上下文.logger.error(错)#记日志
    def 注入面():#页签注入面
        """清单、预设名、本页同步钩子。"""
        return {#注入
            'list':列表,#清单
            'presetName':预设名,#预设显示名
            'hooks':{'clientSync':上下文.modules.entries.state},#本页同步状态
            'retryClient':重试本页,#重试本页
        }
    def 页签标签():#页签文案
        """全部清单页签标签。"""
        return 翻译('tab')#标签
    def 登记页签():#登记全部清单页签
        """登记 settings.plugins.tab 条目。"""
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
