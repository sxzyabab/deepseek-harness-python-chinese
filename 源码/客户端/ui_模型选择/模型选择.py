import importlib.resources as 包资源
from nicegui import ui as 界面
from ..ui_基础界面组件.icons import 图标下chevron14,图标右chevron14,图标勾16,图标关闭填14,图标数据16
from .异常 import 页面失败文案

__all__=['模型选择','样式表']#仅中文公开名

def _读样式(文件名):
    '读当前包内样式。失败时异常文案只有样式读不到，不含路径'
    try:
        return 包资源.files(__package__).joinpath(文件名).read_text(encoding='utf-8')
    except OSError:
        raise OSError('样式读不到') from None

def _去注释(原文):
    '去掉块注释，避免注释里的花括号打断规则'
    出=[]
    下标=0
    长度=len(原文)
    while 下标<长度:
        if 原文.startswith('/*',下标):
            止=原文.find('*/',下标+2)
            if 止<0:
                break
            下标=止+2
            continue
        出.append(原文[下标])
        下标+=1
    return ''.join(出)

def _前缀一片(片,根):
    '同一元素与后代都能命中'
    片=片.strip()
    if 片=='':
        return ''
    return '.'+根+' '+片+', .'+根+片

def _前缀选择器(选择器,根):
    '逗号分隔的每一段都挂上根'
    条=[]
    for 片 in 选择器.split(','):
        已=_前缀一片(片,根)
        if 已!='':
            条.append(已)
    return ', '.join(条)

def _挂规则(文,根):
    '普通规则挂根；媒体查询递归；关键帧保持原样'
    出=[]
    下标=0
    长度=len(文)
    while 下标<长度:
        while 下标<长度 and 文[下标].isspace():
            下标+=1
        if 下标>=长度:
            break
        起=下标
        while 下标<长度 and 文[下标]!='{':
            下标+=1
        if 下标>=长度:
            break
        选择器=文[起:下标].strip()
        下标+=1
        深度=1
        体起=下标
        while 下标<长度 and 深度>0:
            if 文[下标]=='{':
                深度+=1
            elif 文[下标]=='}':
                深度-=1
            下标+=1
        体=文[体起:下标-1]
        if 选择器.startswith('@keyframes') or 选择器.startswith('@font-face'):
            出.append(选择器+'{'+体+'}')
        elif 选择器.startswith('@media') or 选择器.startswith('@container') or 选择器.startswith('@supports'):
            出.append(选择器+'{'+_挂规则(体,根)+'}')
        elif 选择器!='':
            出.append(_前缀选择器(选择器,根)+'{'+体+'}')
    return '\n'.join(出)

def 挂到根(原文,根):
    '共享样式只作用在本组件根下'
    return _挂规则(_去注释(原文),根)

样式表=挂到根(_读样式('模型选择.module.css'),'模型选择根')
界面.add_css(样式表,shared=True)

class 模型选择:#composer 模型座位
    '两级下拉：根行钻入模型表或力度表'
    def __init__(自身,属性):#构造
        '记下 props'
        自身.属性=属性#合成
        自身.打开=False#菜单开
        自身.面板='root'#root/model/effort
        自身.上次动作='load'#load/select
        自身.吐司=None#瞬时错误
        自身.吐司序号=0#吐司序号
        自身.查询=''#模型搜索
        自身.画面=None#可反复清空的容器
        自身.画面失败=None
        if isinstance(属性,dict) and 'available' in 属性 and 'directory' in 属性 and 't' in 属性:
            自身.渲染()#槽位只调用构造

    def 更新(自身,属性):#刷新
        '刷新 props'
        自身.属性=属性#最新

    def 切面板(自身,面):#切面板
        '记下当前面板'
        自身.面板=面#覆盖

    def 读状态(自身):#目录快照
        '经 directory store'
        目录存储=自身.属性['directory'] if 'directory' in 自身.属性 else None#存储
        if 目录存储 is None:#无
            return {'current':None,'groups':[],'failures':[],'status':'idle','error':None}#空
        return 目录存储.getSnapshot()#快照

    def 展平行(自身,状态):#分组展平为选择行
        'group+model+selection'
        行列表=[]#累积
        组列表=状态['groups'] if 'groups' in 状态 and 状态['groups'] is not None else []#各组
        for 组 in 组列表:#各组
            模型列表=组['models'] if 'models' in 组 and 组['models'] is not None else []#各模型
            for 模型 in 模型列表:#各模型
                选={'provider':组['id'],'model':模型['id']}#选定
                推理=模型['reasoning'] if 'reasoning' in 模型 else None#推理
                默认=推理['defaultEffort'] if 推理 is not None and 'defaultEffort' in 推理 else None#默认力度
                if 默认 is not None:
                    选['reasoningEffort']=默认#带上
                行列表.append({'group':组,'model':模型,'selection':选})#行
        return 行列表#全部

    def 关闭(自身):#关菜单
        '回到根面板'
        自身.打开=False#关
        自身.面板='root'#根

    def 名称命中(自身,名称,查询):#有序子序列
        '空查询命中全部；大小写不敏感'
        名=str(名称).casefold()#名
        问=查询.casefold()#查询
        位=0#扫描位
        for 字 in 问:#逐字
            找到=名.find(字,位)#从此处
            if 找到<0:#断了
                return False#不中
            位=找到+1#前进
        return True#命中

    def 打开菜单(自身):#开菜单并刷新
        '没有当前模型时直接进入模型表，否则停在根行'
        状态=自身.读状态()#快照
        当前=状态['current'] if 'current' in 状态 else None#当前
        自身.面板='model' if 当前 is None else 'root'#无当前则钻入
        自身.查询=''#清搜索
        自身.打开=True
        自身.上次动作='load'#load
        加载=自身.属性['load'] if 'load' in 自身.属性 else None#加载
        if 加载 is not None:
            加载()#拉

    def 重载(自身):#菜单内重载
        '标 load 再拉'
        自身.上次动作='load'#load
        加载=自身.属性['load'] if 'load' in 自身.属性 else None#加载
        if 加载 is not None:
            加载()#拉

    def 选定模型(自身,选定):#选模型
        '同路由则关；否则 select'
        状态=自身.读状态()#快照
        当前=状态['current'] if 'current' in 状态 else None#当前
        if (当前 is not None
            and 当前['provider']==选定['provider']
            and 当前['model']==选定['model']):#同
            自身.关闭()#关
            return
        自身.上次动作='select'#select
        提交=自身.属性['select'] if 'select' in 自身.属性 else None#提交
        if 提交 is None:#无
            return
        接受=提交(选定)#提交返回 bool
        if 接受:#成功
            自身.关闭()#关
            return
        失败快照=自身.读状态()#失败后快照
        错=失败快照['error'] if 'error' in 失败快照 else None#错误
        翻译=自身.属性['t'] if 't' in 自身.属性 else None#翻译
        if 错 is not None and 翻译 is not None:
            自身.吐司序号+=1#序号
            自身.吐司={'seq':自身.吐司序号,'text':翻译('error.action',{'message':页面失败文案(错)})}#吐司

    def 选定力度(自身,力度):#选推理力度
        '改当前选定的 reasoningEffort'
        状态=自身.读状态()#快照
        当前=状态['current'] if 'current' in 状态 else None#当前
        if 当前 is None:#无
            return
        选={'provider':当前['provider'],'model':当前['model']}#选定
        if 力度 is not None:#有力度
            选['reasoningEffort']=力度#带上
        自身.选定模型(选)#走同一提交

    def 提供方序(自身,组):#账号与官方在前
        '其余保持原相对顺序'
        标识=组['id'] if 'id' in 组 else ''#提供方
        if 标识=='deepseek-account':#账号
            return 0#最前
        if 标识=='deepseek-official':#官方
            return 1#其次
        return 2#其余

    def 渲染(自身):#两级菜单
        '触发器常在；打开后按根行、模型表、力度表切换'
        可用=自身.属性['available'] if 'available' in 自身.属性 else None#可用
        if 可用 is not True:#不可用
            return None#不渲染
        翻译=自身.属性['t'] if 't' in 自身.属性 else None#翻译
        def 译(键,参数=None):#缺翻译时回退键
            '有翻译函数才调用'
            if 翻译 is None:#无
                return 键#键
            if 参数 is None:#无参数
                return 翻译(键)#译
            return 翻译(键,参数)#带参数
        状态=自身.读状态()#快照
        行列表=自身.展平行(状态)#行
        当前=状态['current'] if 'current' in 状态 else None#当前
        当前行=None#当前选择行
        for 行 in 行列表:#找
            选=行['selection']#选定
            if 当前 is not None and 当前['provider']==选['provider'] and 当前['model']==选['model']:#命中
                当前行=行
                break
        当前模型=当前行['model'] if 当前行 is not None else None#模型
        推理=当前模型['reasoning'] if 当前模型 is not None and 'reasoning' in 当前模型 else None#推理元
        有效力度=当前['reasoningEffort'] if 当前 is not None and 'reasoningEffort' in 当前 else None#当前力度
        if 有效力度 is None and 推理 is not None and 'defaultEffort' in 推理:#无则默认
            有效力度=推理['defaultEffort']#默认
        力度标签=None#力度文案
        if 当前行 is None:#未选定
            力度标签=None#无
        elif 推理 is None:#无推理元
            力度标签=状态['retainedEffort'] if 'retainedEffort' in 状态 else None#保留力度
        elif 有效力度 is None:#提供方默认
            力度标签=译('effort.providerDefault')#默认文
        else:#显式
            力度标签=有效力度#回退 id
            级列表=推理['efforts'] if 'efforts' in 推理 and 推理['efforts'] is not None else []#力度
            for 级 in 级列表:#找名
                if 级['id']==有效力度:#命中
                    名=级['name'] if 'name' in 级 else None#名
                    力度标签=名 if 名 else 有效力度#名
                    break
        态名=状态['status'] if 'status' in 状态 else None#状态
        等待=当前行 is None and 态名=='loading'#目录还在加载
        if 等待:#加载中
            模型标签=译('trigger.loading')#加载文
        else:#已有或回退
            模型标签=当前模型['name'] if 当前模型 is not None and 'name' in 当前模型 else None#模型名
            if 模型标签 is None:#回退
                模型标签=译('trigger.fallback')#回退
        失败=状态['failures'] if 'failures' in 状态 and 状态['failures'] is not None else []#分组失败
        锁定='locked' in 自身.属性 and 自身.属性['locked'] is True#显式锁定
        待定=状态['pending'] if 'pending' in 状态 else None#未结算选定
        忙=待定 is not None or 态名=='selecting'#选定进行中
        组列表=状态['groups'] if 'groups' in 状态 and 状态['groups'] is not None else []#各组
        组列表=sorted(组列表,key=自身.提供方序)#账号与官方在前
        显示搜索=len(行列表)>4#超过四条才搜索
        生效查询=自身.查询.strip() if 显示搜索 else ''#未开搜索则不过滤
        过滤组=[]#过滤后的组
        for 组 in 组列表:#各组
            模型列表=组['models'] if 'models' in 组 and 组['models'] is not None else []#模型
            命中=[]#命中模型
            for 模型 in 模型列表:#各模型
                名=模型['name'] if 'name' in 模型 else ''#名
                if 生效查询=='' or 自身.名称命中(名,生效查询):#命中
                    命中.append(模型)#收下
            if len(命中)>0:#本组还有
                过滤组.append({'id':组['id'],'name':组['name'] if 'name' in 组 else 组['id'],'models':命中})#组
        力度项=[]#力度行
        if 推理 is not None:#有推理
            if ('defaultEffort' not in 推理) or 推理['defaultEffort'] is None:#提供方默认
                力度项.append({'key':'provider-default','effort':None,'label':译('effort.providerDefault')})#默认行
            级列表=推理['efforts'] if 'efforts' in 推理 and 推理['efforts'] is not None else []#力度
            for 级 in 级列表:#各级
                级名=级['name'] if 'name' in 级 and 级['name'] else 级['id']#名
                力度项.append({'key':'effort:'+str(级['id']),'effort':级['id'],'label':级名})#行
        旧=getattr(自身,'画面',None)#已有容器
        if 旧 is not None:
            try:
                旧.clear()
            except Exception as 错误:#父级清掉容器后，把失败留在页面上
                自身.画面=None
                自身.画面失败=页面失败文案(错误)
        if 自身.画面 is None:#新建
            自身.画面=界面.column().classes('模型选择根 root')#根
        自身.画面.clear()#再清一次
        def 切换():#开或关
            '打开或关闭模型菜单'
            if 自身.打开:#已开
                自身.关闭()#关
            else:#未开
                自身.打开菜单()
            自身.渲染()#重画
        def 重载并画():#菜单内重载
            '标 load 再拉，然后重画'
            自身.重载()#拉
            自身.渲染()#重画
        def 改查询(事件):#搜索
            '写入查询并重画；同文不再重入'
            文=事件.value if 事件.value is not None else ''#文本
            if 文==自身.查询:#未变
                return
            自身.查询=文
            自身.渲染()#重画
        def 清查询():#清空搜索
            '回到完整列表'
            自身.查询=''#空
            自身.渲染()#重画
        def 去模型():#钻入模型表
            '清搜索后进入模型表'
            自身.查询=''
            自身.切面板('model')#模型
            自身.渲染()#重画
        def 去力度():#钻入力度表
            '进入力度表'
            自身.查询=''
            自身.切面板('effort')#力度
            自身.渲染()#重画
        def 回根():#回到根行
            '从钻入面板返回'
            自身.切面板('root')#根
            自身.渲染()#重画
        with 自身.画面:#根
            if isinstance(自身.画面失败,str) and 自身.画面失败!='':
                界面.label(自身.画面失败)
            with 界面.row().classes('trigger'):#触发器
                图标数据16()#数据图标
                钮=界面.button(模型标签 if isinstance(模型标签,str) else '',on_click=切换)#模型名
                if 锁定:#锁定则禁
                    钮.disable()#禁
                if isinstance(力度标签,str) and 力度标签!='':#有力度
                    界面.label(力度标签).classes('triggerEffort')#力度
                if 忙:#选定未结算
                    界面.spinner(size='sm')#忙碌转圈
                else:#箭头
                    图标下chevron14()#下拉箭头
            if 自身.打开 and 锁定 is not True:#菜单
                with 界面.column().classes('menu'):#菜单卡
                    if 自身.面板!='root' and 当前行 is not None:#钻入后可返回
                        界面.button(译('menu.aria'),on_click=回根)#返回根行
                    if 自身.面板=='root':#根行
                        with 界面.row().classes('cell'):#模型行
                            界面.label(译('menu.model'))#模型
                            界面.label(模型标签 if isinstance(模型标签,str) else '')#当前值
                            界面.button(on_click=去模型)#钻入
                            图标右chevron14()#右箭头
                        if 推理 is not None:#有力度行
                            with 界面.row().classes('cell'):#力度行
                                界面.label(译('menu.effort'))#推理
                                界面.label(力度标签 if isinstance(力度标签,str) else '')#当前力度
                                界面.button(on_click=去力度)#钻入
                                图标右chevron14()#右箭头
                    if 自身.面板=='model':#模型表
                        if 显示搜索:#搜索
                            界面.input(value=自身.查询,placeholder=译('search.placeholder'),on_change=改查询)#搜索框
                            if 自身.查询!='':#有查询
                                界面.button(译('search.clear'),on_click=清查询)#清除搜索
                                图标关闭填14()#清除图标
                        if 态名=='loading':#加载
                            界面.label(译('status.loading'))#加载状态
                        错文=状态['error'] if 自身.上次动作=='load' and 'error' in 状态 and 状态['error'] is not None else None#加载错误
                        if isinstance(错文,str) and 错文!='':
                            界面.label(译('error.action',{'message':页面失败文案(错文)}))#错误
                            界面.button(译('action.reload'),on_click=重载并画)#重试
                        for 条 in 失败:#分组失败
                            if isinstance(条,str) and 条!='':#纯文本
                                界面.label(页面失败文案(条))#原文
                                界面.button(译('action.reload'),on_click=重载并画)#重试
                            elif isinstance(条,dict) and 'message' in 条:#结构化
                                名=条['name'] if 'name' in 条 else ''#名
                                if 'id' in 条 and 条['id']=='deepseek-account':#账号
                                    名=译('provider.account')#账号名
                                界面.label(译('warning.groupLoad',{'name':名,'message':页面失败文案(条['message'])}))#警告
                                界面.button(译('action.reload'),on_click=重载并画)#分组重试
                        for 组 in 过滤组:#分组
                            标题=译('provider.account') if 组['id']=='deepseek-account' else 组['name']#标题
                            界面.label(str(标题)).classes('groupTitle')#分组标题
                            for 模型 in 组['models']:#各模型
                                选={'provider':组['id'],'model':模型['id']}#选定
                                已选=当前 is not None and 当前['provider']==组['id'] and 当前['model']==模型['id']#当前
                                def 点模型(选定=选):#闭包记住选定
                                    '选定该模型后重画'
                                    自身.选定模型(选定)#提交
                                    自身.渲染()#重画
                                名=模型['name'] if 'name' in 模型 and 模型['name'] else 译('trigger.fallback')#名
                                模型钮=界面.button(名,on_click=点模型)#模型
                                if 忙:#进行中
                                    模型钮.disable()#禁
                                if 已选:#当前
                                    图标勾16()#勾
                                elif 待定 is not None and 'provider' in 待定 and 待定['provider']==组['id'] and 'model' in 待定 and 待定['model']==模型['id']:#这一行在提交
                                    界面.spinner(size='sm')#行内转圈
                        if 态名=='ready' and len(过滤组)==0:#空
                            空键='empty.models' if len(行列表)==0 else 'search.empty'#无模型或无匹配
                            界面.label(译(空键))#空状态
                    if 自身.面板=='effort':#力度表
                        错文=状态['error'] if 自身.上次动作=='load' and 'error' in 状态 and 状态['error'] is not None else None#加载错误
                        if isinstance(错文,str) and 错文!='':
                            界面.label(译('error.action',{'message':页面失败文案(错文)}))#错误
                            界面.button(译('action.reload'),on_click=重载并画)#重试
                        if len(力度项)==0:#无力度
                            界面.label(译('empty.efforts'))#空力度
                        for 级 in 力度项:#各级
                            def 点力度(力度=级['effort']):#闭包记住力度
                                '选定推理力度后重画'
                                自身.选定力度(力度)#提交
                                自身.渲染()#重画
                            已选=有效力度==级['effort']#当前力度
                            级钮=界面.button(str(级['label']),on_click=点力度)#力度
                            if 忙:#进行中
                                级钮.disable()#禁
                            if 已选:#当前
                                图标勾16()#勾
            if 自身.吐司 is not None and 'text' in 自身.吐司:#拒绝选定
                界面.notify(自身.吐司['text'])#吐司

    def __call__(自身,属性=None):#组件调用
        '对齐 React 组件调用'
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()
