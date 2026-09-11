"""产出物插件的浏览器半边。

对齐上游 `ui-deliverables/src/client/index.ts`。公开面仅中文名。
把交付物行登记进聊天视图的回合尾链，并提供 chatFileMentions 服务。
"""
from .文案 import 命名空间,中文,英文#词表
from .回合产出 import 交付物定义,选出产出文件,产出文件提及,收口产出,收口已呈现#节点与选取
from .产出文件 import 产出文件行#产出文件行组件（旧面保留）
from .产出清单 import 产出清单,选出交付物#交付物行
from .呈现行 import 呈现行#present 工具视图
from .呈现打开控制器 import 已呈现打开控制器#原生打开

__all__=['注入','应用','产出文件行','产出清单','呈现行','选出交付物','收口产出','选出产出文件','交付物定义','命名空间','中文','英文','已呈现打开控制器']#仅中文公开名

注入=['slots','locale','uiConversation','remote','remote.session']#槽位、文案、会话 UI、远程

def 应用(上下文):#安装产出物浏览器半边
    """登记词表、打开控制器与回合尾条目。"""
    打开器=已呈现打开控制器()#打开控制器
    def 拆除打开器():#拆除
        """销毁打开器。"""
        打开器.拆除()#拆除
    上下文.副作用(lambda:拆除打开器,'ui-deliverables: present-open controller')#寿命
    def 连接重置():#连接重置
        """作废宿主元数据。"""
        打开器.重置宿主()#重置
    上下文.监听('connection/reset',连接重置)#连接重置
    上下文.uiConversation.events.register(交付物定义)#登记产出物会话节点定义
    def 登记词表():#登记本包词典
        """把中英文词表交给 locale。"""
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})#登记
    上下文.副作用(登记词表,'ui-deliverables: dictionaries')#登记词表
    def 注入交付():#交付物注入面
        """打开与宿主可观察。"""
        def 重载宿主():#重载
            """loadHost。"""
            return 打开器.加载宿主()#加载
        def 打开已呈现(会话标识,序号,下标,动作='open'):#打开
            """openPresented。"""
            return 打开器.打开(会话标识,序号,下标,动作)#打开
        return {#注入
            'hooks':{'presentedOpen':打开器.状态,'presentedHost':打开器.宿主},#可观察
            'reloadPresentedHost':重载宿主,#重载
            'openPresented':打开已呈现,#打开
        }#注入结束
    def 注入回合尾():#等槽出现再登记
        """登记交付物行。"""
        return 上下文.slots.register({#登记
            'name':'conversation.chat.turnTail',#回合尾槽名
            'select':选出交付物,#选出交付
            'locale':命名空间,#文案
            'inject':注入交付,#注入
        },产出清单)#交付物行
    上下文.slots.inject('conversation.chat.turnTail',注入回合尾)#结束 turnTail 注入
    def 注入工具视图():#present 工具视图
        """登记呈现行。"""
        return 上下文.slots.register({#登记
            'name':'tool.call.toolview',#工具视图槽
            'key':'present',#present 键
            'locale':命名空间,#文案
        },呈现行)#呈现行
    上下文.slots.inject('tool.call.toolview',注入工具视图)#结束 toolview
    翻译=上下文.locale.bind(命名空间)#绑定本插件词表
    def 收口提及(所有者,_会话标识=None):#收口散文里的产出与已交付提及
        """与回合尾行同一套认领测试。属主为 dict。多余会话标识被忽略。"""
        路径表=选出产出文件(所有者)#选出本回合产出路径
        已呈现表=收口已呈现(所有者)#收口前已呈现
        if 路径表 is None and len(已呈现表)==0:#两面皆空
            return None#不提供提及
        合并=list(dict.fromkeys([*(路径表 if 路径表 is not None else []),*(项['path'] for 项 in 已呈现表)]))#去重保序
        def 打开标签(路径):#无障碍打开文案
            """一律侧栏预览文案。"""
            return 翻译('presented.previewButton',{'name':路径})#文案
        return 产出文件提及(合并,所有者['openFile'],打开标签)#匹配提及
    上下文.提供服务('chatFileMentions',{'forClosing':收口提及})#提供收口散文提及服务

inject=注入#框架槽
apply=应用#框架槽
