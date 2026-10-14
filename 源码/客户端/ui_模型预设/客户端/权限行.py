import importlib.resources as 包资源
from nicegui import ui as 界面
from ...ui_基础界面组件.icons import 图标下chevron14
from ..异常 import 页面失败文案#页面失败句
from .呈现 import 完全权限预设,展示权限预设#产品标签与完全访问机值

__all__=['权限行','样式表']#仅中文公开名

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

样式表=挂到根(_读样式('权限行.module.css'),'权限行根')
界面.add_css(样式表,shared=True)

class 权限行:
    '后续新建会话的默认预设行'
    def __init__(自身,属性):
        '记下 props 并触发首读'
        自身.属性=属性#合成 props
        自身.已开=False#菜单
        自身.确认满权=False#待确认完全权限
        自身.已知情=False#确认勾选
        自身.画面=None#可反复清空的容器
        自身.画面失败=None
        if isinstance(属性,dict) and 't' in 属性 and 'usePermission' in 属性 and 'load' in 属性:
            属性['load']()#首读
            自身.渲染()#槽位只调用构造

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性#最新
        自身.复位若失效()#不可写则关

    def 读状态(自身):
        '经 usePermission 选择器'
        用权限=自身.属性['usePermission']#选择器
        def 原样(快照):
            '整表'
            return 快照#快照
        return 用权限(原样)#快照

    def 复位若失效(自身):
        '不可写或不可用时关菜单'
        状态=自身.读状态()#行快照
        if 状态['writable'] is True and 状态['status']!='unavailable':#仍有效
            return#不动
        自身.已开=False#关菜单
        自身.已知情=False
        自身.确认满权=False#清确认

    def 关菜单(自身):
        '关掉下拉'
        自身.已开=False#关

    def 切换菜单(自身):
        '翻转菜单'
        自身.已开=not 自身.已开#翻

    def 选择(自身,标识):
        '同值忽略；满权走确认'
        自身.已开=False#关菜单
        状态=自身.读状态()#行快照
        if 标识==状态['currentValue']:#同
            return#无事
        if 标识==完全权限预设:#满权
            自身.已知情=False
            自身.确认满权=True#待确认
            return#等确认
        自身.属性['select'](标识)#写入默认

    def 关确认(自身):
        '清确认态'
        自身.已知情=False
        自身.确认满权=False#清确认

    def 设知情(自身,开):
        '确认勾选'
        自身.已知情=开 is True#勾

    def 确认启用(自身):
        '关掉确认后写入完全权限'
        自身.已知情=False
        自身.确认满权=False#清确认
        自身.属性['select'](完全权限预设)#写入

    def 渲染(自身):
        '宿主未露出权限设置则 None'
        if 't' not in 自身.属性 or 'usePermission' not in 自身.属性:#槽位属性未齐
            return None#不画
        自身.复位若失效()#快照驱动关菜单
        翻译=自身.属性['t']#文案
        状态=自身.读状态()#行快照
        if 状态['status']=='unavailable':#未服务
            return None#不渲染
        选中=None#当前选项
        for 项 in 状态['options']:#找
            if 项['id']==状态['currentValue']:#命中
                选中=项
                break
        忙=(状态['status']=='loading' or 状态['status']=='saving'
            or 自身.确认满权 is True)#加载、保存或确认中
        if 选中 is not None:#有当前
            标签=展示权限预设(选中['id'],选中['label'],翻译)#产品标签
        elif 忙 is True:#尚未选出
            标签=翻译('loading')#加载
        else:#无选项
            标签=翻译('unavailable')#不可用
        说明=页面失败文案(状态['error']) if 状态['error'] is not None else 翻译('description')#错误或说明
        条目=[]#菜单项
        for 项 in 状态['options']:#各预设
            条目.append({#项
                'id':项['id'],#机值
                'label':展示权限预设(项['id'],项['label'],翻译),#产品标签
            })#项结束
        禁用=(忙 is True or 状态['writable'] is not True
            or len(状态['options'])==0)#忙、只读或空选项
        旧=getattr(自身,'画面',None)#已有容器
        if 旧 is not None:
            try:
                旧.clear()
            except Exception as 错误:#父级清掉容器后，把失败留在页面上
                自身.画面=None
                自身.画面失败=页面失败文案(错误)
        if 自身.画面 is None:#新建
            自身.画面=界面.column().classes('权限行根')#根
        自身.画面.clear()#再清一次
        def 改知情(事件):
            '勾选变化后重画；创建控件时的同值不再重入'
            开=事件.value is True#显式勾上
            if 开==自身.已知情:#未变
                return
            自身.设知情(开)#勾
            自身.渲染()#重画
        def 切换():
            '翻转菜单后重画'
            自身.切换菜单()#翻
            自身.渲染()#重画
        def 取消确认():
            '关掉确认后重画'
            自身.关确认()#关
            自身.渲染()#重画
        def 启用确认():
            '确认后写入并重画'
            自身.确认启用()#写入
            自身.渲染()#重画
        with 自身.画面:#根
            if isinstance(自身.画面失败,str) and 自身.画面失败!='':
                界面.label(自身.画面失败)
            with 界面.row().classes('row'):#标题与选择器
                with 界面.column().classes('rowText'):#文案
                    界面.label(翻译('title')).classes('title')#标题
                    说明签=界面.label(说明).classes('desc')#说明
                    if 状态['error'] is not None:#错误
                        说明签.props('role=alert')#警报
                with 界面.row().classes('selector'):#选择器
                    钮=界面.button(标签, on_click=切换)#当前值
                    if 禁用:#忙或只读
                        钮.disable()#禁
                    图标下chevron14()#下拉箭头
            if 自身.已开:#菜单
                for 项 in 条目:#各预设
                    def 点(标识=项['id']):
                        '选定该权限后重画'
                        自身.选择(标识)#选
                        自身.渲染()#重画
                    界面.button(项['label'], on_click=点)#项
            if 自身.确认满权 is True:#满权确认
                with 界面.dialog() as 对话框:#确认框
                    with 界面.card():#卡
                        界面.label(翻译('confirm.title'))#标题
                        界面.label(翻译('confirm.description'))#说明
                        勾=界面.checkbox(翻译('confirm.acknowledge'), value=自身.已知情, on_change=改知情)#已知
                        禁确认=状态['writable'] is not True or 状态['status']=='saving'#只读或保存中
                        if 禁确认:#禁勾
                            勾.disable()#禁
                        界面.button(翻译('confirm.cancel'), on_click=取消确认)#取消
                        界面.button(翻译('close'), on_click=取消确认)#关闭
                        启用=界面.button(翻译('confirm.enable'), on_click=启用确认)#启用
                        if 禁确认 or 自身.已知情 is not True:#未勾或锁定
                            启用.disable()#禁
                对话框.open()#打开

    def __call__(自身,属性=None):
        '对齐 React 调用'
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()
