import threading#单飞拉取与预热等待
from concurrent.futures import Future as 原生结果#单次操作结果
from urllib.parse import quote as 百分编码#URI 段编码
from .文案 import 命名空间,中文,英文#词典（同目录厚叶）
from ...ui_基础界面组件.按名排序 import 按名排序#按名与标签排序
from ..技能行 import 技能行,技能错误#技能工具行与本包异常

__all__=['依赖','应用']#仅中文公开名

依赖=['inputTriggers','sessions','slots','locale','remote','remote.skills','sidebarRight']#触发源、会话、槽位、文案、远程、skills 与右侧边栏

class 操作任务:#本文件内单次操作结果
    """单次操作的 Future 包装，只留 等待。"""
    def __init__(自身):#构造未决任务
        """构造未决任务。"""
        自身._结果=原生结果()#底层 Future

    def 兑现(自身,值=None):#成功结算
        """成功结算。"""
        if not 自身._结果.done():#尚未结算
            自身._结果.set_result(值)#写入结果
        return 值#返回兑现值

    def 拒绝(自身,错误):#失败结算
        """失败结算。"""
        if not 自身._结果.done():#尚未结算
            if isinstance(错误,BaseException):#已是异常
                自身._结果.set_exception(错误)#原样拒绝
            else:#非异常
                自身._结果.set_exception(技能错误(str(错误)))#包装拒绝

    def 等待(自身,超时=None):#阻塞等待
        """阻塞等到结算。"""
        return 自身._结果.result(timeout=超时)#取结果或抛错

def 已中止(信号):#读 threading.Event
    """无信号视为未中止。"""
    if 信号 is None:#无
        return False#未中止
    return 信号.is_set()#置位即中止

def 若已中止则抛出(信号):#已取消则抛
    """已中止则抛技能错误。"""
    if 已中止(信号):#已取消
        raise 技能错误('已中止')#中止

def 编码段(段):
    """百分编码一段，冒号保持字面量。"""
    return 百分编码(段,safe='').replace('%3A',':').replace('%3a',':')#冒号原样

def 编码路径(路径):
    """按斜杠分段编码。"""
    return '/'.join(编码段(段) for 段 in 路径.split('/'))#分段

def 是否绝对工作区路径(路径):
    """POSIX 根、Windows 盘符或 UNC。"""
    if 路径.startswith('/'):
        return True#POSIX 绝对
    if 路径.startswith('\\\\'):
        return True#UNC
    if len(路径)>=3 and 路径[0].isalpha() and 路径[1]==':' and 路径[2] in '/\\':
        return True#盘符
    return False#相对

def 会话文件地址(会话标识,路径):
    """编成 dsh-resource://file/session/<id>/<path>。"""
    规范化=路径.replace('\\','/')#统一斜杠
    while 规范化.startswith('./'):
        规范化=规范化[2:]#剥前导 ./
    return 'dsh-resource://file/session/'+编码段(会话标识)+'/'+编码路径(规范化)#会话作用域

def 文件资源地址(会话标识,cwd,路径):
    """相对或工作区内绝对走会话作用域；工作区外绝对仍写进同一会话地址。"""
    规范化=路径.replace('\\','/')#统一斜杠
    if not 是否绝对工作区路径(规范化):
        return 会话文件地址(会话标识,规范化)#相对
    根='' if cwd is None else cwd.replace('\\','/').rstrip('/')#工作区根
    if 根!='' and 规范化==根:
        return 会话文件地址(会话标识,'')#根本身
    if 根!='' and 规范化.startswith(根+'/'):
        return 会话文件地址(会话标识,规范化[len(根)+1:])#剥根
    return 会话文件地址(会话标识,规范化)#工作区外仍会话作用域

def 应用(上下文):#安装技能引用浏览器半边
    """登记「/」源、词表，以及按键的工具行。"""
    def 登记词典():#登记中英文案
        """登记本插件词典。"""
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})#登记
    上下文.副作用(登记词典,'ui-skill: dictionaries')#词典生命周期
    def 登记工具行():#登记 skill toolview
        """等 toolview 槽出现再登记 skill 行。"""
        return 上下文.slots.register({#按 skill 键的 toolview 条目
            'name':'tool.call.toolview','key':'skill','locale':命名空间,#条目选项
        },技能行)#技能工具行组件
    上下文.slots.inject('tool.call.toolview',登记工具行)#等槽出现
    技能接口=上下文.remote.skills#登记时捕获的根 Remote 上的 skills
    会话服务=上下文.获取服务('sessions')#会话服务
    拉取表={}#会话 → 在飞/已落定目录拉取
    词表监听={}#会话 → 词表监听者集合

    def 通知词表(会话标识):#通知该会话的词表监听者
        """通知该会话的词表监听者。"""
        for 监听 in list(词表监听[会话标识] if 会话标识 in 词表监听 else set()):#快照后逐个通知
            try:#单个监听者失败不得饿死其余
                监听()#触发
            except Exception as 错误:#订阅者异常契约未定，故不能换成更窄的 except
                print('[ui-skill] 词表监听失败:',错误)#记日志

    def 拉目录(会话标识):#按会话单飞拉取技能目录
        """按会话单飞拉取技能目录，返回共享条目。"""
        已有=拉取表[会话标识] if 会话标识 in 拉取表 else None#已有拉取
        if 已有 is not None:#同键复用
            return 已有#共享条目
        中止器=threading.Event()#自有中止旗
        def 中止拉取():#中止在飞拉取
            """仅失效/拆除时触发。"""
            中止器.set()#标中止
        def 解包目录(包装):#从 list 响应取出 skills
            """解包 skills/list 业务结果。"""
            若已中止则抛出(中止器)#拉取期间失效则抛
            结果=包装['result']#业务结果
            if not 结果['ok']:#业务失败转成抛错
                错误=结果['error'] if 'error' in 结果 else None#错误
                码=错误['code'] if 错误 is not None and 'code' in 错误 else None
                消息=错误['message'] if 错误 is not None and 'message' in 错误 else None#消息
                raise 技能错误('skills/list 失败: '+str(码)+': '+str(消息))#转抛
            return 结果['value']['skills']#目录条目
        任务=操作任务()#本键共享拉取
        条目={'任务':任务,'abort':中止拉取,'signal':中止器}#本键共享条目
        拉取表[会话标识]=条目#写入缓存
        def 执行拉取():#单飞拉取体
            """持留会话至历史打开后再调 skills/list。"""
            try:#拉取并解包
                if 会话服务.binding(会话标识) is None:#未持留
                    raise 技能错误('skill catalog requires a retained session "'+str(会话标识)+'"')
                def 在持有内拉取(引用):#打开后拉目录
                    """等历史打开再 RPC。"""
                    若已中止则抛出(中止器)#拉取期间失效则抛
                    状态=引用.binding.session.getSnapshot()#会话快照
                    打开态=状态['openState'] if isinstance(状态,dict) else getattr(状态,'openState',None)
                    if 打开态!='open':#未打开
                        错误=状态['openError'] if isinstance(状态,dict) and 'openError' in 状态 else getattr(状态,'openError',None)
                        if 错误 is not None:
                            raise 错误
                        raise 技能错误('session "'+str(会话标识)+'" is not open')
                    包装=技能接口.list({'sessionId':会话标识},中止器).等待()#唯一一次 list
                    若已中止则抛出(中止器)#RPC 后仍有效
                    return 解包目录(包装)#业务解包
                技能列表=会话服务.using(会话标识,{'source':'skillCatalog','signal':中止器},在持有内拉取)
                条目['settled']=技能列表#同步词表快照
                任务.兑现(技能列表)#交给等待方
                通知词表(会话标识)#通知词表监听者
            except BaseException as 错误:#失败不得毒化该键
                if (拉取表[会话标识] if 会话标识 in 拉取表 else None) is 条目:#仍是本条目
                    del 拉取表[会话标识]#摘掉
                任务.拒绝(错误)#共享失败
        线=threading.Thread(target=执行拉取)#后台拉取
        线.daemon=True#不挡退出
        线.start()
        return 条目#共享条目

    def 失效(键):#丢掉一键缓存
        """丢掉一键缓存并中止在飞拉取。"""
        条目=拉取表[键] if 键 in 拉取表 else None#该键条目
        if 条目 is None:#没有缓存
            return#无需做
        del 拉取表[键]#摘掉
        条目['abort']()#中止
        通知词表(键)#通知

    def 清空全部():#清空全部会话目录缓存
        """清空全部会话的目录缓存。"""
        for 键 in list(拉取表.keys()):#快照键
            失效(键)#逐个失效

    翻译=上下文.locale.bind(命名空间)#绑定翻译

    def 候选(会话,选项):#按查询过滤本会话技能候选
        """按查询过滤本会话技能候选。"""
        查询=选项['query'] if 'query' in 选项 else ''#查询串
        信号=选项['signal'] if 'signal' in 选项 else None#中止信号
        if 会话服务.subagentAddress(会话['sessionId']) is not None:#子智能体会话
            return []#无用户技能目录
        技能列表=拉目录(会话['sessionId'])['任务'].等待()#共享目录
        if 已中止(信号):#被取代的按键：共享拉取仍热着，本调用方让出
            return []#早退
        结果=[]#候选列表
        for 技能 in 按名排序(技能列表,查询):#前缀优先的有序子序列
            名=技能['name'] if 'name' in 技能 else ''#技能名
            描述=技能['description'] if 'description' in 技能 else ''#描述
            if 'modelInvocable' in 技能 and 技能['modelInvocable']:#模型可调则原文
                次要=描述#原文
            else:#仅用户
                次要=翻译('menu.userOnly')+' · '+描述#加前缀
            结果.append({'name':名,'description':次要})#候选
        return 结果#候选列表

    def 预热(会话):#作用域诞生预热
        """点火即忘的作用域诞生预热。"""
        if 会话服务.subagentAddress(会话['sessionId']) is not None:#子智能体
            return#不预热
        任务=拉目录(会话['sessionId'])['任务']#预热
        def 忽略():#吞掉成败
            """预热失败由 candidates 再报。"""
            try:#等待
                任务.等待()#等待
            except BaseException:#失败
                pass#忽略
        线=threading.Thread(target=忽略)#后台
        线.daemon=True#不挡退出
        线.start()

    def 词表(会话):#同步词表
        """已落定目录的技能名。"""
        条目=拉取表[会话['sessionId']] if 'sessionId' in 会话 and 会话['sessionId'] in 拉取表 else None#缓存
        if 条目 is None:#无
            return None#缺席
        已落定=条目['settled'] if 'settled' in 条目 else None#快照
        if 已落定 is None:#在飞或失败
            return None#缺席
        return [技能['name'] for 技能 in 已落定]#技能名列表

    def 订阅词表(会话,监听):#登记词表失效监听者
        """登记该会话的词表失效监听者。"""
        键=会话['sessionId']#会话键
        集合=词表监听[键] if 键 in 词表监听 else None#已有集合
        if 集合 is None:#新建
            集合=set()#空集合
            词表监听[键]=集合#写回
        集合.add(监听)#加入
        def 退订():#退订
            """从该会话集合摘掉。"""
            集合.discard(监听)#摘掉
            if len(集合)==0 and 键 in 词表监听:#空了
                del 词表监听[键]#摘掉会话键
        return 退订#拆除器

    def 打开引用(会话,引用):#打开技能源文件预览
        """子智能体拒绝；已落定目录立刻打开，否则拉目录后打开。"""
        会话标识=会话['sessionId']#会话键
        if 会话服务.subagentAddress(会话标识) is not None:#子智能体
            return False#不预览
        列表=会话服务.list.getSnapshot().byId#会话列表
        摘要=列表[会话标识] if 会话标识 in 列表 else None#当前会话
        cwd=摘要['cwd'] if 摘要 is not None and 'cwd' in 摘要 else None#工作目录
        目标=引用['ref'] if 'ref' in 引用 else ''#mention
        def 打开(目录):#目录就绪后打开
            """按 mention 找路径并打开。"""
            路径=None#命中路径
            for 技能 in 目录:#逐条
                名=技能['name'] if 'name' in 技能 else ''#技能名
                if '/'+名==目标:#命中
                    路径=技能['path'] if 'path' in 技能 else None#路径
                    break#找到
            if 路径 is None:#目录里没有
                return False#未打开
            地址=文件资源地址(会话标识,cwd,路径)#会话作用域地址
            上下文.sidebarRight.openResource(地址)#侧栏打开
            return True#已受理
        条目=拉取表[会话标识] if 会话标识 in 拉取表 else None#缓存
        已落定=条目['settled'] if 条目 is not None and 'settled' in 条目 else None#快照
        if 已落定 is not None:#已落定
            return 打开(已落定)#同步打开
        条目=拉目录(会话标识)#加入或发起拉取
        def 到达后打开():#目录到达后打开
            """仍有效才打开。"""
            try:#等待目录
                目录=条目['任务'].等待()#目录
                if not 已中止(条目['signal']):#仍有效
                    打开(目录)#打开
            except BaseException as 错误:#预览失败
                if not 已中止(条目['signal']):#仍有效才记
                    print('[ui-skill] 引用预览失败:',错误)#记日志
        线=threading.Thread(target=到达后打开)#后台打开
        线.daemon=True#不挡退出
        线.start()
        return True#已受理

    def 选定(载荷):#选定：插入字面 /name 加空格
        """纯文本引用决策。"""
        候选项=载荷['candidate']#候选
        return {'text':'/'+候选项['name']+' '}#字面 /name 加尾空格

    源={#「/」技能触发源
        'trigger':'/',#触发字符
        'name':'skill',#来源名
        'order':2,#菜单分组顺序
        'candidates':候选,#候选
        'warm':预热,#预热
        'lexicon':词表,#词表
        'subscribeLexicon':订阅词表,#订阅词表
        'openReference':打开引用,#打开技能源
        'onPick':选定,#选定
    }#源结束
    触发服务=上下文.获取服务('inputTriggers')#斜杠触发服务
    上下文.remote.$on('agent-preset/selected',失效)#预设切换丢掉该会话目录键
    上下文.监听('connection/reset',清空全部)#连接重置清空全部
    def 挂源():#登记源；拆除时卸源并清缓存
        """把「/」技能源写入花名册。"""
        注销=触发服务.registerSource(源)#登记源
        def 拆除():#fiber 拆除
            """从花名册摘掉本源并清缓存。"""
            注销()#摘源
            清空全部()#清缓存
        return 拆除#拆除器
    上下文.副作用(挂源,'ui-skill: source')#生命周期

inject=依赖#框架槽
apply=应用#框架槽
