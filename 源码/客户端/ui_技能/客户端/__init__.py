'登记 / 技能源、词表，以及按 skill 键的工具行和引用芯片'
from ...模块.客户端.通告 import 取握手窗口
import threading
from ....api.网关.网关 import 中止控制器#skills/list 的取消通道
from ....基础设施.通用工具 import 获取内部数据#remote.on
from ....工具.工作区路径 import 文件地址为#技能文件地址
from ...ui_基础界面组件.按名排序 import 按名排序#与命令菜单同一套排序
from . import (
    文案,
    技能行,
    技能引用,
    用户文本规则,
)
from .用户文本规则 import 技能引用规则#原文技能规则

__all__=['文案','技能行','技能引用','用户文本规则','依赖','应用']

中止事件=threading.Event#会话持留认 is_set
依赖=['inputTriggers','sessions','slots','locale','remote','remote.skills','sidebarRight','uiConversation']#触发源、会话、槽位、文案、远程、skills、侧栏、对话

def 应用(上下文,配置=None):
    '登记中英文案、/ 技能源，以及技能芯片和工具行'
    def 登记词典():
        '登记本插件中英文案表。页面显示不走英文表'
        return 上下文.locale.register(文案.命名空间,{'zh':文案.中文,'en':文案.英文})#登记
    上下文.副作用(登记词典,'ui-skill: dictionaries')#词典随插件拆掉
    上下文.uiConversation.userText.register(技能引用规则)#原文技能规则
    def 登记工具行():
        '等 tool.call.toolview 出现后登记 skill 行'
        return 上下文.slots.register({#按 skill 键
            'name':'tool.call.toolview',#槽位
            'key':'skill',#键
            'locale':文案.命名空间,#文案命名空间
        },技能行.技能行)#技能行
    上下文.slots.inject('tool.call.toolview',登记工具行)#等槽出现
    技能接口=上下文.remote.skills#登记时捕获的 skills
    会话服务=上下文.sessions#会话
    拉取表={}#会话 → 目录条目
    监听表={}#会话 → 词表监听

    def 已中止(信号):
        '取消通道已置位。没有信号视为未中止'
        if 信号 is None:#无
            return False#未中止
        return 信号.is_set()#置位

    def 通知词表(会话标识):
        '通知这一场的词表监听。一个监听失败不挡住其余'
        副本=list(监听表[会话标识]) if 会话标识 in 监听表 else []#快照
        for 监听 in 副本:#逐个
            try:#一个失败不挡住其余
                监听()#通知
            except Exception as 错误:#监听自己抛的
                取握手窗口().console.error('[ui-skill] lexicon listener failed:',错误)#留下

    def 拉目录(会话标识):
        '按会话拉一次技能目录。失败不留下这个键'
        已有=拉取表.get(会话标识)#已有
        if 已有 is not None and 'settled' in 已有:#已经落定
            return 已有#复用
        控制器=中止控制器()#远程取消
        持留中止=中止事件()#会话持留取消
        def 中止拉取():
            '失效或拆除时取消这份目录'
            持留中止.set()#持留
            控制器.中止配套信号()#远程
        条目={'abort':中止拉取,'signal':持留中止}#这一份
        拉取表[会话标识]=条目#先占住这个键
        try:#拉完才落定
            if 会话服务.binding(会话标识) is None:#没有持留
                raise Exception('skill catalog requires a retained session "'+str(会话标识)+'"')#拒绝
            def 读取(引用):
                '历史打开之后再列技能'
                if 已中止(持留中止):#拉取期间被取消
                    raise Exception('The operation was aborted.')#不再列
                状态=引用.binding['session'].getSnapshot()#会话快照
                if 状态['openState']!='open':#历史没打开
                    if 状态['openError'] is not None:#有打开错误
                        raise 状态['openError']#原样抛出
                    raise Exception('session "'+str(会话标识)+'" is not open')#没打开
                结果=技能接口.list({'sessionId':会话标识},控制器.信号)#skills/list
                if 已中止(持留中止):#返回前被取消
                    raise Exception('The operation was aborted.')#丢掉结果
                if 结果['ok'] is not True:#业务失败
                    错误体=结果['error']#错误
                    raise Exception('skills/list failed: '+str(错误体['code'])+': '+str(错误体['message']))#转抛
                return 结果['value']['skills']#目录
            列表=会话服务.using(会话标识,{'source':'skillCatalog','signal':持留中止},读取)#持留到回调结束
            if 已中止(持留中止):#持留结束后被取消
                raise Exception('The operation was aborted.')#不落定
            条目['settled']=列表#同步词表快照
            通知词表(会话标识)#通知监听
            return 条目#已落定
        except BaseException as 错误:#失败不得毒化这个键
            if 拉取表.get(会话标识) is 条目:#仍是这一份
                del 拉取表[会话标识]#摘掉
            if isinstance(错误,Exception):#给预览判断要不要记日志
                错误.目录信号=持留中止#取消通道
            raise#原样抛出

    def 失效(键,*位置参数):
        '丢掉这一场的目录并通知词表'
        条目=拉取表.get(键)#这一份
        if 条目 is None:#没有
            return#无需做
        del 拉取表[键]#摘掉
        条目['abort']()#取消在飞拉取
        通知词表(键)#通知

    def 清空全部(*位置参数):
        '清空全部会话的目录'
        for 键 in list(拉取表.keys()):#快照键
            失效(键)#逐个

    def 候选(会话,选项):
        '按查询过滤这一场的技能。子智能体没有用户技能目录'
        if 会话服务.subagentAddress(会话['sessionId']) is not None:#子智能体
            return []#空
        技能列表=拉目录(会话['sessionId'])['settled']#共享目录
        if 已中止(选项['signal']):#这次按键已被取代
            return []#让出
        结果=[]#候选
        for 技能 in 按名排序(技能列表,选项['query']):#前缀优先
            if 技能['modelInvocable']:#模型可调
                次要=技能['description']#原文描述
            else:#仅用户
                次要=文案.中文['menu.userOnly']+' · '+技能['description']#仅用户
            结果.append({'name':技能['name'],'description':次要})#一行
        return 结果#候选

    def 预热(会话):
        '作用域诞生时预热这一场。失败不往外抛'
        if 会话服务.subagentAddress(会话['sessionId']) is not None:#子智能体
            return#不预热
        try:#点火
            拉目录(会话['sessionId'])#预热
        except Exception as 预热错误:#失败留给下一次候选再拉
            return#不外抛

    def 词表(会话):
        '已落定目录的技能名。还没落定或失败则缺席'
        条目=拉取表.get(会话['sessionId'])#缓存
        if 条目 is None or 'settled' not in 条目:#没有快照
            return None#缺席
        return [技能['name'] for 技能 in 条目['settled']]#技能名

    def 订阅词表(会话,监听):
        '登记这一场的词表失效监听，返回退订'
        键=会话['sessionId']#会话键
        集合=监听表[键] if 键 in 监听表 else None#已有
        if 集合 is None:#新建
            集合=set()#空集合
            监听表[键]=集合#写回
        集合.add(监听)#加入
        def 退订():
            '从这一场摘掉这个监听'
            集合.discard(监听)#摘掉
            if len(集合)==0 and 键 in 监听表 and 监听表[键] is 集合:#空了
                del 监听表[键]#摘掉会话键
        return 退订#拆除器

    def 打开引用(会话,引用):
        '子智能体不预览。目录已落定则立刻打开，否则拉完再打开'
        会话标识=会话['sessionId']#会话键
        if 会话服务.subagentAddress(会话标识) is not None:#子智能体
            return False#不预览
        列表=会话服务.list.getSnapshot()['byId']#会话列表
        摘要=列表[会话标识] if 会话标识 in 列表 else None#这一场
        工作目录=None if 摘要 is None else 摘要.get('cwd')#工作目录
        目标=引用['ref']#mention
        def 打开(目录):
            '按 /名字 找到路径后在侧栏打开'
            路径=None#命中路径
            for 技能 in 目录:#逐条
                if '/'+技能['name']==目标:#命中
                    路径=技能['path'] if 'path' in 技能 else None#路径
                    break#找到
            if 路径 is None:#没有路径
                return False#未打开
            上下文.sidebarRight.打开资源(文件地址为(会话标识,工作目录,路径))#侧栏打开
            return True#已打开
        已有=拉取表.get(会话标识)#缓存
        if 已有 is not None and 'settled' in 已有:#已经落定
            return 打开(已有['settled'])#同步打开
        try:#还没有目录就先拉
            条目=拉目录(会话标识)#拉目录
            if not 已中止(条目['signal']):#仍有效
                打开(条目['settled'])#打开
        except Exception as 错误:#预览失败
            信号=错误.目录信号 if hasattr(错误,'目录信号') else None#取消通道
            if not 已中止(信号):#不是取消
                取握手窗口().console.error('[ui-skill] reference preview failed:',错误)#留下
        return True#已受理

    def 选定(载荷):
        '选定后插入字面 /名字 和尾空格'
        return {'text':'/'+载荷['candidate']['name']+' '}#字面文本

    源={#「/」技能触发源
        'trigger':'/',#触发字符
        'name':'skill',#来源名
        'order':2,#菜单分组顺序
        'candidates':候选,#候选
        'warm':预热,#预热
        'lexicon':词表,#词表
        'subscribeLexicon':订阅词表,#订阅
        'openReference':打开引用,#打开技能源
        'onPick':选定,#选定
    }
    def 登记文本节点():
        '等用户文本节点槽出现后登记技能芯片'
        def 注入技能(会话标识):
            '按这一条消息的会话准备预览'
            def 打开技能(名):
                '这一场还在才打开 /名字'
                if 会话服务.scope(会话标识) is None:#作用域已经没了
                    return#不打开
                源['openReference']({'sessionId':会话标识},{'ref':'/'+名})#交给技能源
            return {'openSkill':打开技能}#注入面
        return 上下文.slots.register({#技能芯片
            'name':'conversation.user.text.node',#槽位
            'key':'skill',#键
            'priority':100,#优先级
            'inject':注入技能,#按会话预览
        },技能引用.技能引用)#技能引用
    上下文.slots.inject('conversation.user.text.node',登记文本节点)#等槽出现
    触发服务=上下文.获取服务('inputTriggers')#斜杠触发服务
    getattr(上下文.remote,'$on')('agent-preset/selected',失效)#预设切换丢掉这一场
    上下文.监听('connection/reset',清空全部)#连接重置清空全部
    def 挂源():
        '把 / 技能源写入花名册'
        注销=触发服务.registerSource(源)#登记源
        def 拆除():
            '从花名册摘掉本源并清掉全部目录'
            注销()#摘源
            清空全部()#清缓存
        return 拆除#拆除器
    上下文.副作用(挂源,'ui-skill: source')#生命周期

inject=依赖#框架槽
apply=应用#框架槽
