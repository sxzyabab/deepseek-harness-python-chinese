import importlib.resources as 包资源
from nicegui import ui as 界面
from ...ui_基础界面组件.icons import 图标下chevron14
from ..异常 import 预设错误,页面失败文案#命令失败与页面失败句
from .呈现 import 完全权限预设,自动审查预设,展示权限预设#呈现层

__all__=['权限选择','样式表','权限字形']#仅中文公开名

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

样式表=挂到根(_读样式('权限选择.module.css'),'权限选择根')
界面.add_css(样式表,shared=True)

盾轮廓路径='M8.20554 0.899994L14.7901 3.36857V7.01026C14.7901 12 11.0466 14.2103 8.20554 15.3C5.36446 14.2103 1.62012 12 1.62012 7.01026V3.36857L8.20554 0.899994Z'#盾轮廓
盾轮廓线宽='1.31831'#盾描边

权限字形={#预设机值 → 路径
    'read-only':[#只读勾
        {'d':盾轮廓路径,'stroke':'currentColor','strokeWidth':盾轮廓线宽,'strokeLinejoin':'round'},
        {'d':'M12.1654 5.7552L8.9447 9.41475C8.73044 9.65816 8.53628 9.8804 8.35774 10.0423C8.1713 10.2114 7.94235 10.3717 7.64016 10.4254C7.48207 10.4535 7.32 10.4552 7.16151 10.4294C6.85843 10.3801 6.62728 10.2223 6.43836 10.0559C6.25752 9.89653 6.06037 9.67732 5.84264 9.43705L4.72925 8.20897L5.63557 7.38707L6.74897 8.61594C6.98603 8.87755 7.12974 9.03533 7.24673 9.13839C7.31033 9.19443 7.34485 9.21476 7.35823 9.22122C7.38068 9.22484 7.40352 9.22515 7.42593 9.22122C7.40522 9.22502 7.42893 9.23294 7.53583 9.136C7.65132 9.03126 7.79316 8.87139 8.02643 8.60638L11.2479 4.94763L12.1654 5.7552Z','fill':'currentColor'},
    ],
    'workspace-write':[#工作区写笔
        {'d':'M8.08887 0.251709C8.20479 0.23085 8.32486 0.241168 8.43652 0.282959L15.0215 2.75171C15.2787 2.84819 15.4492 3.09414 15.4492 3.3689V7.0105C15.4492 7.10986 15.4441 7.2081 15.4414 7.30542C15.0285 7.07175 14.5905 6.87695 14.1309 6.73022V3.82495L8.20508 1.60327L2.2793 3.82495V7.0105C2.27936 9.7171 3.4745 11.5379 5.02734 12.7947C5.01025 12.9942 5 13.1962 5 13.4001C5.00001 13.7617 5.02722 14.1169 5.08008 14.4636C2.91555 13.0393 0.961014 10.752 0.960938 7.0105V3.3689C0.960938 3.09417 1.13146 2.84821 1.38867 2.75171L7.97461 0.282959L8.08887 0.251709Z','fill':'currentColor'},
        {'d':'M11.3525 5.64688V6.85688H5V5.64688H11.3525Z','fill':'currentColor'},
        {'d':'M9.5824 8.29376V9.50376H5V8.29376H9.5824Z','fill':'currentColor'},
        {'d':'M14.6647 15.6852H10.0338C10.3878 15.3751 10.7567 15.0517 11.0772 14.7706C11.2531 14.6164 11.4144 14.4746 11.5511 14.3547H14.6647V15.6852Z','fill':'currentColor'},
        {'d':'M8.14852 14.1308L7.33925 15.4976C7.22458 15.6912 7.42245 15.9194 7.63037 15.8333L9.09785 15.2254L15.0399 10.0719L14.0905 8.97733L8.14852 14.1308Z','fill':'currentColor'},
    ],
    完全权限预设:[#完全访问叹号
        {'d':盾轮廓路径,'stroke':'currentColor','strokeWidth':盾轮廓线宽,'strokeLinejoin':'round'},
        {'d':'M9.10094 4.5V8.75939H7.59888V4.5H9.10094Z','fill':'currentColor'},
        {'d':'M9.10094 9.8114V11.5H7.59888V9.8114H9.10094Z','fill':'currentColor'},
    ],
}#字形结束

def 权限标签(值,名称,翻译):
    '自动审查走专用标签，否则产品标签'
    if 值==自动审查预设:#自动审查
        return 翻译('auto.label')#专用
    return 展示权限预设(值,名称,翻译)#产品标签

def 选项徽标(值,翻译):
    '仅自动审查有徽标'
    if 值==自动审查预设:#自动审查
        return 翻译('auto.badge')#徽标
    return None#无

class 权限选择:
    '无投影或缺目录不渲染；满权与自动审查需确认'
    def __init__(自身,属性):
        '记下 props 与本地态'
        自身.属性=属性#合成
        自身.挑选=None#乐观值
        自身.已开=False#菜单
        自身.确认中=None#待确认机值
        自身.已知情=False#风险勾选
        自身.画面=None#可反复清空的容器
        自身.画面失败=None
        if isinstance(属性,dict) and 't' in 属性 and 'useProjection' in 属性 and 'usePermissionCatalog' in 属性:
            自身.渲染()#槽位只调用构造

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性#最新
        自身.复位若失效()#失效则关

    def 读选取(自身):
        '会话 permissions 投影'
        return 自身.属性['useProjection']('permissions')#选取

    def 读目录(自身):
        '完整目录；缺席 None'
        def 取值(态):
            '目录值'
            return 态['value']#值
        return 自身.属性['usePermissionCatalog'](取值)#目录

    def 复位若失效(自身):
        '锁定、无选取、无目录或确认项已不在目录时关菜单'
        锁定=自身.属性['locked'] is True if 'locked' in 自身.属性 else False#锁
        选取=自身.读选取()#投影
        目录=自身.读目录()#目录
        确认仍在=自身.确认中 is None#无确认则视为在
        if 自身.确认中 is not None and 目录 is not None:#有确认项
            确认仍在=False#先否
            for 项 in 目录['options']:#扫
                if 项['value']==自身.确认中:#仍在
                    确认仍在=True#在
                    break
        if (锁定 is False and 选取 is not None and 目录 is not None
            and 确认仍在 is True):#仍有效
            return#不动
        自身.已开=False#关菜单
        自身.已知情=False
        自身.确认中=None#清确认

    def 关菜单(自身):
        '关掉下拉'
        自身.已开=False#关

    def 切换菜单(自身):
        '翻转菜单'
        自身.已开=not 自身.已开#翻

    def 提交(自身,标识):
        '经命令写入路径切换'
        自身.挑选=标识#乐观
        try:#提交
            自身.属性['select'](标识)#命令路径
        except 预设错误 as 错误:#投影不会确认，页面留下失败句
            自身.画面失败=页面失败文案(错误)
        else:#提交没抛
            自身.画面失败=None
        自身.挑选=None#清乐观

    def 选择(自身,标识):
        '同值忽略；满权与自动审查走确认'
        自身.已开=False#关菜单
        选取=自身.读选取()#投影
        if 选取 is None:#无
            return#无事
        if 标识==选取['currentValue']:#同
            return#无事
        if 标识==完全权限预设 or 标识==自动审查预设:#风险门
            自身.已知情=False
            自身.确认中=标识#待确认
            return#等确认
        自身.提交(标识)#直接提交

    def 关确认(自身):
        '清确认态'
        自身.已知情=False
        自身.确认中=None#清确认

    def 设知情(自身,开):
        '确认勾选'
        自身.已知情=开 is True#勾

    def 确认选定(自身):
        '确认后提交'
        标识=自身.确认中#机值
        自身.关确认()#关确认
        if 标识 is not None:#仍有
            自身.提交(标识)#提交

    def 画字形(自身,路径列表):#权限图标
        '把预设路径画成随文字着色的 svg'
        段=[]#path
        for 段描 in 路径列表:#逐条
            属性=' '.join(str(键)+'="'+str(值)+'"' for 键,值 in 段描.items())#属性
            段.append('<path '+属性+'/>')#一条
        图='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="14" height="14" fill="none" aria-hidden="true">'+''.join(段)+'</svg>'#标记
        界面.html(图,sanitize=False)#画出

    def 渲染(自身):
        '无投影或缺目录返回 None'
        if 't' not in 自身.属性 or 'useProjection' not in 自身.属性 or 'usePermissionCatalog' not in 自身.属性:#槽位属性未齐
            return None#不画
        自身.复位若失效()#快照驱动关菜单
        锁定=自身.属性['locked'] is True if 'locked' in 自身.属性 else False#锁
        翻译=自身.属性['t']#文案
        选取=自身.读选取()#投影
        目录=自身.读目录()#目录
        if 选取 is None or 目录 is None:#能力或缺目录
            return None#不渲染
        挑选有效=False#乐观值是否仍在目录
        if 自身.挑选 is not None:#有乐观
            for 项 in 目录['options']:#扫
                if 项['value']==自身.挑选:#在
                    挑选有效=True#有效
                    break
        当前值=自身.挑选 if 挑选有效 is True else 选取['currentValue']#当前
        当前=None#当前选项
        for 项 in 目录['options']:#找
            if 项['value']==当前值:#命中
                当前=项
                break
        if 当前 is None:#目录里没有
            当前标签=权限标签(当前值,当前值,翻译)#用机值当名
        else:
            当前标签=权限标签(当前['value'],当前['name'],翻译)#产品标签
        忙=自身.挑选 is not None or 自身.确认中 is not None#提交中或确认中
        条目=[]#菜单行
        for 项 in 目录['options']:#各预设
            项值=项['value']#机值
            字形=权限字形[项值] if 项值 in 权限字形 else None#字形
            标签=权限标签(项值,项['name'],翻译)#标签
            徽标=选项徽标(项值,翻译)#徽标
            行={'id':项值,'label':标签}#基础
            if 徽标 is not None:#有徽标
                行['badge']=徽标#徽标
            if 字形 is not None:#有字形
                行['glyph']=字形#字形
            条目.append(行)#收下
        自动=自身.确认中==自动审查预设#自动审查确认
        if 自身.确认中 is None:#无确认
            确认=None#无
        else:#有确认
            确认={#风险确认
                'open':True,
                'title':翻译('auto.confirm.title' if 自动 is True else 'confirm.title'),#标题
                'description':翻译('auto.confirm.description' if 自动 is True else 'confirm.description'),#说明
                'acknowledgeLabel':翻译('auto.confirm.acknowledge' if 自动 is True else 'confirm.acknowledge'),#已知
                'cancelLabel':翻译('confirm.cancel'),#取消
                'closeLabel':翻译('close'),#关闭
                'confirmLabel':翻译('auto.confirm.enable' if 自动 is True else 'confirm.enable'),#启用
                'acknowledged':自身.已知情,#勾
                'disabled':锁定,#锁定则禁
                'onAcknowledgedChange':自身.设知情,#勾选
                'onCancel':自身.关确认,#取消
                'onConfirm':自身.确认选定,#启用
            }#确认结束
        当前徽标=选项徽标(当前值,翻译)#当前徽标
        if 当前徽标 is None:#无徽标
            无障碍=当前标签#纯标签
        else:
            无障碍=当前标签+' '+当前徽标#标签加徽标
        if 当前 is None:#无当前选项
            说明=None#无 title
        elif 当前['value']==自动审查预设:#自动审查
            说明=翻译('auto.description')#专用说明
        else:#宿主
            说明=当前['description'] if 'description' in 当前 else None#宿主说明
        旧=getattr(自身,'画面',None)#已有容器
        if 旧 is not None:
            try:
                旧.clear()
            except Exception as 错误:#父级清掉容器后，把失败留在页面上
                自身.画面=None
                自身.画面失败=页面失败文案(错误)
        if 自身.画面 is None:#新建
            自身.画面=界面.column().classes('权限选择根')#根
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
            '确认后提交并重画'
            自身.确认选定()#提交
            自身.渲染()#重画
        with 自身.画面:#根
            if isinstance(自身.画面失败,str) and 自身.画面失败!='':
                界面.label(自身.画面失败)
            当前字形=权限字形[当前值] if 当前值 in 权限字形 else None#触发器字形
            with 界面.row().classes('trigger'):#触发器
                if 当前字形 is not None:#有字形
                    自身.画字形(当前字形)#权限图标
                钮=界面.button(当前标签, on_click=切换).props('aria-label='+无障碍)#标签
                if 锁定 is True or 忙 is True:#锁或忙
                    钮.disable()#禁
                if 说明 is not None and 说明!='':#说明
                    钮.tooltip(说明)#提示
                if 当前徽标 is not None:#徽标单独成签
                    界面.label(当前徽标).classes('badge')#徽标
                图标下chevron14()#下拉箭头
            if 自身.已开:#菜单
                for 项 in 条目:#各预设
                    def 点(标识=项['id']):
                        '选定该权限后重画'
                        自身.选择(标识)#选
                        自身.渲染()#重画
                    with 界面.row():#一行
                        if 'glyph' in 项:#有字形
                            自身.画字形(项['glyph'])#行图标
                        界面.button(项['label'], on_click=点)#标签
                        if 'badge' in 项:#徽标单独成签
                            界面.label(项['badge']).classes('badge')#徽标
            if 确认 is not None:#风险确认
                with 界面.dialog() as 对话框:#确认框
                    with 界面.card():#卡
                        界面.label(确认['title'])#标题
                        界面.label(确认['description'])#说明
                        勾=界面.checkbox(确认['acknowledgeLabel'], value=确认['acknowledged'], on_change=改知情)#已知
                        if 确认['disabled'] is True:#锁定
                            勾.disable()#禁
                        界面.button(确认['cancelLabel'], on_click=取消确认)#取消
                        界面.button(确认['closeLabel'], on_click=取消确认)#关闭
                        启用=界面.button(确认['confirmLabel'], on_click=启用确认)#启用
                        if 确认['disabled'] is True or 确认['acknowledged'] is not True:#未勾或锁定
                            启用.disable()#禁
                对话框.open()#打开

    def __call__(自身,属性=None):
        '对齐 React 调用'
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()
