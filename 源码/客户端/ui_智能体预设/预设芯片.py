from nicegui import ui as 界面
from ..ui_基础界面组件.icons import 图标下chevron14,图标智能体预设16,图标警告16
from .异常 import 页面失败文案
from .文案 import 预设展示文案#展示文案
from .预设菜单 import 预设菜单
from .预设行 import _读样式,挂到根#样式挂到芯片根

__all__=['预设芯片','介绍文字延迟毫秒','介绍字符错开毫秒','介绍文字揭开毫秒','介绍字符淡入毫秒']#仅中文公开名

界面.add_css(挂到根(_读样式('预设芯片.module.css'),'预设芯片根'),shared=True)

介绍文字延迟毫秒=150#图标入场后再揭字
介绍字符错开毫秒=40#每字起步间隔上限
介绍文字揭开毫秒=200#整段揭开窗
介绍字符淡入毫秒=400#单字淡入时长

def 介绍错开毫秒(字数):
    '短名按上限；长名压进同一揭开窗'
    if 字数<=1:#单字
        return 0#无错开
    return min(介绍字符错开毫秒,介绍文字揭开毫秒/(字数-1))#夹取

class 预设芯片:
    '部署无名册时返回 None。属性与快照都是 dict'
    def __init__(自身,属性):
        '只接收合并后的属性字典，拉名册并画出'
        自身.属性=属性 if isinstance(属性,dict) else {}#属性
        自身.打开=False#菜单
        自身.介绍中=False#介绍动画
        自身.画面=None#可反复清空的容器
        自身.画面失败=None
        加载=自身.属性['load'] if 'load' in 自身.属性 else None#加载
        if 加载 is not None:
            加载()#拉
        if 't' in 自身.属性 and 'useAgentPresetSeat' in 自身.属性:
            自身.渲染()#槽位只调用构造

    def 更新(自身,属性):
        '刷新 props'
        自身.属性=属性 if isinstance(属性,dict) else {}#最新

    def 状态(自身):
        '经 useAgentPresetSeat'
        def 恒等(快照):
            '整表'
            return 快照#快照
        return 自身.属性['useAgentPresetSeat'](恒等)#快照

    def 选定(自身,标识):
        '关菜单并 select'
        自身.打开=False#关
        自身.属性['select'](标识)#提交

    def 切换菜单(自身):
        '翻转菜单开闭'
        自身.打开=not 自身.打开#翻转

    def 关闭菜单(自身):
        '关菜单'
        自身.打开=False#关

    def 开始介绍(自身,标签):
        '减动效则立刻 acknowledge'
        态=自身.状态()#态
        if not 态['introduce']:#无提示
            return#跳过
        就绪=len(态['options'])>0 and 态['current']!=''#就绪；判 length 与空串
        if not 就绪:#未就绪
            return#跳过
        介绍完=自身.属性['introduced']#完结
        字列表=list(标签)#字符
        if len(字列表)==0:#空
            介绍完()#完
            return
        自身.介绍中=True#开动画
        错开=介绍错开毫秒(len(字列表))#错开
        自身.介绍时长=介绍文字延迟毫秒+(len(字列表)-1)*错开+介绍字符淡入毫秒#总时长
        自身.介绍完结=介绍完#回调

    def 渲染(自身):
        '产出芯片+菜单；无名册则 None'
        属性=自身.属性#props
        态=自身.状态()#态
        翻译=属性['t']#翻译
        选项列表=态['options']#选项
        当前=态['current']#当前
        就绪=len(选项列表)>0 and 当前!=''#就绪；判 length 与空串
        if not 就绪:#无
            return None#不画
        选中=None#项
        for 项 in 选项列表:#找
            if 项['id']==当前:#命中
                选中=项
                break
        展示=预设展示文案(选中,翻译) if 选中 is not None else None#展示
        标签=展示['name'] if 展示 is not None else 当前#标签
        if 态['introduce'] and not 自身.介绍中:#武装介绍
            自身.开始介绍(标签)#武装
        字列表=list(标签)#字符
        错开=介绍错开毫秒(len(字列表))#错开
        条目=[]#菜单项
        for 项 in 选项列表:#逐项
            文=预设展示文案(项,翻译)#文
            述=文['description'] if 'description' in 文 else None#述
            if 述 is None:#无述
                述=翻译('noDescription')#回退
            条目.append({#项
                'id':项['id'],#id
                'name':文['name'],#名
                'description':述,#述
            })
        错文=态['error'] if 'error' in 态 else None#错误
        if isinstance(错文,str) and 错文!='':#原文错误作标题
            标题=页面失败文案(错文)#错误
        else:#提示
            标题=翻译('seatHint')#提示
        def 改开(开):
            '同步菜单开闭后重画'
            自身.打开=开 is True#显式开
            自身.渲染()#重画
        旧=getattr(自身,'画面',None)#已有容器
        if 旧 is not None:
            try:
                旧.clear()
            except Exception as 错误:#父级清掉容器后，把失败留在页面上
                自身.画面=None
                自身.画面失败=页面失败文案(错误)
        if 自身.画面 is None:#新建
            自身.画面=界面.row().classes('预设芯片根 seat')#根
        自身.画面.clear()#再清一次
        with 自身.画面:#根
            if isinstance(自身.画面失败,str) and 自身.画面失败!='':
                界面.label(自身.画面失败)
            界面.label(标题)#提示
            图标智能体预设16()#预设图标
            if 自身.介绍中:#逐字揭开
                for 字 in 字列表:#逐字
                    界面.label(字)#一字
            图标下chevron14()#下拉箭头
            预设菜单({
                't':翻译,
                'options':态['options'],
                'open':自身.打开,
                'onOpenChange':改开,
                'onSelect':自身.选定,
                'selectedId':当前,
                'label':标签,
                'disabled':态['busy'] is True,
            }).渲染()#菜单由父组件调用渲染
            错=态['error'] if 'error' in 态 else None#拒绝
            if isinstance(错,dict) and 'reason' in 错:#结构化拒绝
                预设名=错['preset']['name'] if 'preset' in 错 and isinstance(错['preset'],dict) and 'name' in 错['preset'] else ''#名
                界面.notify(翻译('switchRefused',{'name':预设名,'reason':页面失败文案(错['reason'])}))#拒绝吐司
                图标警告16()#警告图标
            elif isinstance(错,str) and 错!='':#原文
                界面.notify(页面失败文案(错))#吐司

    def __call__(自身,属性=None):
        '只接收一个属性字典'
        if 属性 is not None:
            自身.更新(属性)#刷
        return 自身.渲染()
