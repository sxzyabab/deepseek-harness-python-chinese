from nicegui import ui as 界面
from .异常 import 页面失败文案
from .文案 import 预设展示文案#展示文案
from .分区存储 import 草稿阻挡#客户端阻挡
from .预设指南 import 系统指南,预设指南#出厂帮助
from .预设行 import _读样式,挂到根#样式挂到本分区根

__all__=['预设分区']#仅中文公开名

界面.add_css(挂到根(_读样式('预设分区.module.css'),'预设分区根'),shared=True)

class 预设分区:
    '部署无名册时返回 None。属性与快照都是 dict'
    def __init__(自身,属性):
        '只接收合并后的属性字典，拉名册并画出'
        自身.属性=属性 if isinstance(属性,dict) else {}#属性
        自身.指南=None#打开的帮助
        自身.画面=None#可反复清空的容器
        自身.画面失败=None
        加载=自身.属性['load'] if 'load' in 自身.属性 else None#加载
        if 加载 is not None:
            加载()#拉
        if 't' in 自身.属性 and 'useAgentPresetSection' in 自身.属性:
            自身.渲染()#槽位只调用构造

    def 更新(自身,属性):
        '刷新 props'
        自身.属性=属性 if isinstance(属性,dict) else {}#最新

    def 关指南(自身):
        '关掉模式帮助并重画'
        自身.指南=None#关
        自身.渲染()#重画

    def 换指南页(自身,页):
        '切换说明或用法'
        if 自身.指南 is None:#未开
            return
        自身.指南={'content':自身.指南['content'],'page':页}#换页
        自身.渲染()#重画

    def 状态(自身):
        '经 useAgentPresetSection'
        def 恒等(快照):
            '整表'
            return 快照#快照
        return 自身.属性['useAgentPresetSection'](恒等)#快照

    def 取消删除(自身):
        '关掉删除确认'
        自身.属性['confirmDelete'](None)#取消

    def 渲染(自身):
        '产出分区；unavailable 则 None'
        属性=自身.属性#props
        态=自身.状态()#态
        翻译=属性['t']#翻译
        状态码=态['status']#生命周期
        if 状态码=='unavailable':#部署无预设
            return None#不画
        仅错误=状态码=='error'#整页失败
        if 仅错误:#错误页不分组
            行列表=[]#空
            组列表=[]#空
            草稿=None#无
            查看=None#无
            揭示={ }#无
        else:#名册
            行列表=态['rows'] if 'rows' in 态 and 态['rows'] is not None else []#名册
        组列表=[]#分组视图
        for 信任,标题键 in (('system','builtInGroup'),('user','customGroup')):#两组
            组行=[]#本组
            for 行 in 行列表:#过滤
                if 行['trust']!=信任:#不属
                    continue#跳
                文=预设展示文案(行,翻译)#展示
                述=文['description'] if 'description' in 文 else None#述
                if 述 is None:#无述
                    述=翻译('noDescription')#回退
                组行.append({#卡片
                    'row':行,#原行
                    'name':文['name'],#名
                    'description':述,#述
                })#结束
            尾=None#自定义组尾
            if 信任=='user' and 'startCreatorDraft' in 属性 and 属性['startCreatorDraft'] is not None:#有编写入口
                有创造=False#名册有 cordis
                for r in 行列表:#查
                    if r['id']=='cordis':#命中
                        有创造=True
                        break
                if 有创造:#名册有 cordis
                    启=属性['startCreatorDraft']#启动
                    关=属性['close'] if 'close' in 属性 else None#关设置
                    def 点编写(启动=启,关闭=关):
                        '暂存并关设置'
                        启动()#启动
                        if 关闭 is not None:#有关
                            关闭()#关设置
                    可写=态['authorable']#可写
                    尾={#编写按钮
                        'disabled':not 可写,#不可写则禁
                        'title':None if 可写 else 翻译('duplicateUnavailable'),#提示
                        'label':翻译('creatorDraft'),#文案
                        'onClick':点编写,
                    }#结束
            if len(组行)==0 and 尾 is None:#空组无尾；判 length
                continue#跳
            组列表.append({'trust':信任,'heading':翻译(标题键),'cards':组行,'tail':尾})#组
        if 仅错误:#失败页不打开对话框
            草稿=None#无复制
            查看=None#无查看
            揭示={ }#无路径
        else:#名册附带
            草稿=态['copy'] if 'copy' in 态 else None#复制草稿
            查看=态['view'] if 'view' in 态 else None#查看器
            揭示=态['revealedPaths'] if 'revealedPaths' in 态 and 态['revealedPaths'] is not None else {}#揭示路径
        阻挡=草稿阻挡(草稿,行列表) if 草稿 is not None else None#阻挡
        草稿消息=None#消息
        if 草稿 is not None:#开着
            草稿错=草稿['error'] if 'error' in 草稿 else None#错误
            if 草稿错 is not None:#优先错误
                草稿消息=页面失败文案(草稿错)#去掉绝对路径
            elif 阻挡 is not None:#客户端阻挡
                草稿消息=翻译(阻挡)#文案
            else:#无
                草稿消息=阻挡#空
        查看标题=''#标题
        if 查看 is not None:#开着
            命中=None#行
            for r in 行列表:#找
                if r['id']==查看['id']:#命中
                    命中=r
                    break
            if 命中 is not None:#有行
                查看标题=预设展示文案(命中,翻译)['name']#名
            else:#无
                查看标题=查看['title'] if 'title' in 查看 else ''#标题
        旧=getattr(自身,'画面',None)#已有容器
        if 旧 is not None:
            try:
                旧.clear()
            except Exception as 错误:#父级清掉容器后，把失败留在页面上
                自身.画面=None
                自身.画面失败=页面失败文案(错误)
        if 自身.画面 is None:#新建
            自身.画面=界面.column().classes('预设分区根 section')#根
        自身.画面.clear()#再清一次
        def 重试():
            '再拉名册并重画'
            if 'load' in 属性:
                属性['load']()#拉
            自身.渲染()#重画
        with 自身.画面:#根
            if isinstance(自身.画面失败,str) and 自身.画面失败!='':
                界面.label(自身.画面失败)
            if 仅错误:#失败页
                界面.label(翻译('error'))#标题
                错=态['error'] if 'error' in 态 else None#文案
                if 错 is not None:#有文
                    失败句=页面失败文案(错)#去掉绝对路径
                    if 失败句!='':
                        界面.label(失败句)#原因
                界面.button(翻译('retry'), on_click=重试)#重试
            界面.label(翻译('nav')).classes('title')#导航
            界面.label(翻译('sectionIntro')).classes('intro')#导语
            if (not 仅错误) and 态['error'] is not None:#行内错误
                行内失败=页面失败文案(态['error'])#去掉绝对路径
                if 行内失败!='':
                    界面.label(行内失败).classes('error')#错误
            for 组 in 组列表:#各组
                界面.label(组['heading'])#组标题
                for 卡 in 组['cards']:#各卡
                    行=卡['row']#原行
                    with 界面.card().classes('card'):#卡
                        界面.label(卡['name']).classes('cardName')#名称
                        破损=行['broken'] if 'broken' in 行 else None#加载失败
                        if 破损 is not None:#破损
                            界面.label(翻译('brokenBadge'))#失败徽标
                            破损句=页面失败文案(破损)#去掉绝对路径
                            if 破损句!='':
                                界面.label(破损句).classes('cardBrokenReason')#原因
                        默认中='isDefault' in 行 and 行['isDefault'] is True#显式默认
                        界面.label(翻译('inUse') if 默认中 else 组['heading'])#使用中或分组标签
                        界面.label(str(行['id']))#标识
                        界面.label(卡['description']).classes('cardDesc')#说明
                        帮助=系统指南(行['id'],行['trust'] if 'trust' in 行 else None)#出厂帮助
                        if 帮助 is not None:#有帮助
                            def 开说明(内容=帮助):
                                '打开模式说明'
                                自身.指南={'content':内容,'page':'explanation'}
                                自身.渲染()#重画
                            def 开用法(内容=帮助):
                                '打开如何使用'
                                自身.指南={'content':内容,'page':'usage'}
                                自身.渲染()#重画
                            界面.button(翻译('modeExplanation'), on_click=开说明)#模式说明
                            界面.button(翻译('howToUse'), on_click=开用法)#如何使用
                        def 点默认(标识=行['id']):
                            '设为默认'
                            属性['makeDefault'](标识)
                        def 点查看(标识=行['id']):
                            '查看预设'
                            属性['view'](标识)
                        def 点复制(标识=行['id']):
                            '开始复制'
                            属性['beginCopy'](标识)
                        def 点删除(标识=行['id']):
                            '请求删除'
                            属性['confirmDelete'](标识)
                        def 点位置(标识=行['id']):
                            '打开目录'
                            属性['openLocation'](标识)
                        with 界面.row():
                            界面.button(翻译('setDefault'), on_click=点默认)
                            界面.button(翻译('view'), on_click=点查看)
                            界面.button(翻译('duplicate'), on_click=点复制)
                            if 行['trust']=='user':
                                界面.button(翻译('delete'), on_click=点删除)
                            if 'hasDocument' in 态 and 态['hasDocument'] is True:#宿主有文档
                                界面.button(翻译('openLocation'), on_click=点位置)
                        if 行['id'] in 揭示:
                            界面.label(翻译('revealedPathLabel')+str(揭示[行['id']]))
                尾=组['tail']
                if 尾 is not None:
                    尾钮=界面.button(尾['label'], on_click=尾['onClick'])
                    if 尾['disabled']:
                        尾钮.disable()
                    if 尾['title'] is not None:
                        尾钮.tooltip(尾['title'])
            if 草稿 is not None:#复制框
                def 改标识(事件):
                    '写入复制标识'
                    属性['setCopyId'](事件.value)
                def 改名称(事件):
                    '写入复制名称'
                    属性['setCopyName'](事件.value)
                标识文=草稿['id'] if 'id' in 草稿 and 草稿['id'] is not None else ''
                名称文=草稿['name'] if 'name' in 草稿 and 草稿['name'] is not None else ''
                保存中='saving' in 草稿 and 草稿['saving'] is True#显式保存中
                with 界面.dialog() as 复制框:
                    with 界面.card():
                        界面.label(翻译('copyTitle'))
                        界面.label(翻译('copyIntro'))
                        界面.input(翻译('presetId'), value=标识文, placeholder=翻译('presetIdPlaceholder'), on_change=改标识)
                        界面.input(翻译('displayName'), value=名称文, placeholder=翻译('displayNamePlaceholder'), on_change=改名称)
                        if 草稿消息 is not None and 草稿消息!='':
                            界面.label(草稿消息)
                        with 界面.row():
                            界面.button(翻译('cancel'), on_click=属性['cancelCopy'])
                            建钮=界面.button(翻译('creating') if 保存中 else 翻译('create'), on_click=属性['confirmCopy'])
                            if 阻挡 is not None:
                                建钮.disable()
                复制框.open()
            if 查看 is not None:#查看框
                正文=查看['content'] if 'content' in 查看 and 查看['content'] is not None else ''
                with 界面.dialog() as 查看框:
                    with 界面.card():
                        界面.label(查看标题)
                        界面.label(翻译('composition'))
                        界面.textarea(value=正文).props('readonly')
                        界面.button(翻译('close'), on_click=属性['closeView'])
                查看框.open()
            待删=态['pendingDelete'] if 'pendingDelete' in 态 else None#待删
            删除中='deleting' in 态 and 态['deleting'] is True#显式删除中
            if 待删 is not None:#删除确认
                with 界面.dialog() as 删除框:
                    with 界面.card():
                        界面.label(翻译('deleteTitle'))
                        界面.label(翻译('deleteDescription'))
                        with 界面.row():
                            取消钮=界面.button(翻译('cancel'), on_click=自身.取消删除)
                            删钮=界面.button(翻译('deleting') if 删除中 else 翻译('deleteConfirm'), on_click=属性['remove'])
                            if 删除中:#进行中
                                取消钮.disable()
                                删钮.disable()
                删除框.open()
            if 自身.指南 is not None:#帮助层；父组件调用渲染
                预设指南({
                    't':翻译,#文案
                    'guide':自身.指南['content'],#键表
                    'page':自身.指南['page'],#当前页
                    'onClose':自身.关指南,#关闭
                    'onPage':自身.换指南页,#换页
                }).渲染()#画出帮助

    def __call__(自身,属性=None):
        '只接收一个属性字典'
        if 属性 is not None:
            自身.更新(属性)#刷
        return 自身.渲染()
