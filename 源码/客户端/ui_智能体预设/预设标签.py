from nicegui import ui as 界面
from ..ui_基础界面组件.icons import 图标智能体预设16
from .异常 import 页面失败文案
from .文案 import 预设展示文案#展示文案
from .预设行 import _读样式,挂到根#样式挂到标签根

__all__=['预设标签']#仅中文公开名

界面.add_css(挂到根(_读样式('预设标签.module.css'),'预设标签根'),shared=True)

class 预设标签:
    '无预设记录时返回 None。属性与快照都是 dict'
    def __init__(自身,属性):
        '只接收合并后的属性字典；有预设时拉名册并画出'
        自身.属性=属性 if isinstance(属性,dict) else {}#属性
        自身.画面=None#可反复清空的容器
        自身.画面失败=None
        if 'sessionId' in 自身.属性 and 'useSessions' in 自身.属性 and 't' in 自身.属性 and 'useAgentPresets' in 自身.属性 and 'load' in 自身.属性:
            自身.确保加载()#按需加载
            自身.渲染()#槽位只调用构造

    def 更新(自身,属性):
        '刷新并按需加载'
        自身.属性=属性 if isinstance(属性,dict) else {}#最新
        自身.确保加载()#加载

    def 会话预设(自身):
        '经 useSessions 读 byId[sessionId].agentPreset。会话列表快照是对象'
        属性=自身.属性#props
        会话标识=属性['sessionId']#会话
        def 选摘要(态):
            '当前会话摘要。byId 是 dict'
            表=态.byId#会话表
            if 表 is None or 会话标识 not in 表:#无
                return None#无
            return 表[会话标识]#摘要 dict
        摘要=属性['useSessions'](选摘要)#摘要
        if 摘要 is None:#无
            return None#无
        return 摘要['agentPreset'] if 'agentPreset' in 摘要 else None#预设

    def 取选项列表(自身):
        '经 useAgentPresets 读 options'
        def 选选项(快照):
            '名册选项'
            return 快照['options']#选项
        return 自身.属性['useAgentPresets'](选选项)#选项

    def 确保加载(自身):
        '部署无预设时不请求'
        if 自身.会话预设() is None:#无
            return#跳过
        自身.属性['load']()#拉

    def 渲染(自身):
        '产出页眉标签；无预设则 None'
        预设=自身.会话预设()#预设 id
        if 预设 is None:#无
            return None#不画
        翻译=自身.属性['t']#翻译
        选项=None#命中项
        for 项 in 自身.取选项列表():#找
            if 项['id']==预设:#命中
                选项=项
                break
        展示=预设展示文案(选项,翻译) if 选项 is not None else None#展示
        名=展示['name'] if 展示 is not None else 预设#名
        说明=展示['description'] if 展示 is not None and 'description' in 展示 else None#说明
        if 说明 is None:#回退提示
            说明=翻译('headerHint')#页眉提示
        旧=getattr(自身,'画面',None)#已有容器
        if 旧 is not None:
            try:
                旧.clear()
            except Exception as 错误:#父级清掉容器后，把失败留在页面上
                自身.画面=None
                自身.画面失败=页面失败文案(错误)
        if 自身.画面 is None:#新建
            自身.画面=界面.row().classes('预设标签根 label')#根
        自身.画面.clear()#再清一次
        with 自身.画面:#根
            if isinstance(自身.画面失败,str) and 自身.画面失败!='':
                界面.label(自身.画面失败)
            图标智能体预设16()#预设图标
            界面.label(名).tooltip(说明)#名称

    def __call__(自身,属性=None):
        '只接收一个属性字典'
        if 属性 is not None:
            自身.更新(属性)#刷
        return 自身.渲染()
