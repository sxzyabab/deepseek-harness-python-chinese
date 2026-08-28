"""智能体预设设置分区：名册卡片、复制对话框、只读查看与删除确认。

对齐上游 `ui-agent-preset/src/client/AgentPresetSection.tsx`。公开面仅中文名。
浏览器不编辑组合正文；复制是创建唯一途径。
"""
from .文案 import 预设展示文案#展示文案
from .分区仓库 import 草稿阻挡#客户端阻挡

__all__=['预设分区']#仅中文公开名

def 读(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 预设分区:#设置分区组件
    """部署无名册时返回 None。"""
    def __init__(自身,属性=None,**关键字参数):#构造
        """合并 props 并拉名册。"""
        自身.属性=dict(属性 or {})#基础
        自身.属性.update(关键字参数)#覆盖
        加载=读(自身.属性,'load')#加载
        if 加载 is not None:#有
            加载()#拉

    def 更新(自身,属性):#刷新
        """刷新 props。"""
        自身.属性=dict(属性)#最新

    def 状态(自身):#分区快照
        """经 useAgentPresetSection。"""
        用=读(自身.属性,'useAgentPresetSection')#钩
        if 用 is None:#无
            return {'status':'idle','rows':[],'error':None}#空
        return 用(lambda 快照:快照) or {}#快照

    def 渲染(自身):#结构化视图
        """产出分区；unavailable 则 None。"""
        属性=自身.属性#props
        态=自身.状态()#态
        翻译=读(属性,'t')#翻译
        状态码=读(态,'status')#生命周期
        if 状态码=='unavailable':#部署无预设
            return None#不画
        if 状态码=='error':#错误
            return {#错误面
                'type':'agent-preset-section',#类型
                'status':'error',#态
                'error':读(态,'error') or '',#文案
                'retry':读(属性,'load'),#重试
                'labels':{'error':翻译('error') if 翻译 else '','retry':翻译('retry') if 翻译 else ''},#文案
                'cssModule':'预设分区.module.css',#样式
            }#结束
        行们=读(态,'rows') or []#名册
        组们=[]#分组视图
        for 信任,标题键 in (('system','builtInGroup'),('user','customGroup')):#两组
            组行=[]#本组
            for 行 in 行们:#过滤
                if 读(行,'trust')!=信任:#不属
                    continue#跳
                文=预设展示文案(行,翻译) if 翻译 is not None else None#展示
                组行.append({#卡片
                    'row':行,#原行
                    'name':文['name'] if 文 is not None else 读(行,'id'),#名
                    'description':(文['description'] if 文 is not None else None) or (翻译('noDescription') if 翻译 else ''),#述
                })#结束
            尾=None#自定义组尾
            if 信任=='user' and 读(属性,'startCreatorDraft') is not None:#有编写入口
                if any(读(r,'id')=='cordis' for r in 行们):#名册有 cordis
                    def 点编写(启=读(属性,'startCreatorDraft'),关=读(属性,'close')):#闭包
                        """暂存并关设置。"""
                        启()#启动
                        if 关 is not None:#有关
                            关()#关设置
                    尾={#编写按钮
                        'disabled':not 读(态,'authorable'),#不可写则禁
                        'title':None if 读(态,'authorable') else (翻译('duplicateUnavailable') if 翻译 else ''),#提示
                        'label':翻译('creatorDraft') if 翻译 else '',#文案
                        'onClick':点编写,#开
                    }#结束
            if not 组行 and 尾 is None:#空组无尾
                continue#跳
            组们.append({'trust':信任,'heading':翻译(标题键) if 翻译 else 标题键,'cards':组行,'tail':尾})#组
        草稿=读(态,'copy')#复制草稿
        阻挡=草稿阻挡(草稿,行们) if 草稿 is not None else None#阻挡
        草稿消息=None#消息
        if 草稿 is not None:#开着
            草稿消息=读(草稿,'error') or (翻译(阻挡) if 阻挡 is not None and 翻译 else 阻挡)#优先错误
        查看=读(态,'view')#查看器
        查看标题=''#标题
        if 查看 is not None:#开着
            命中=next((r for r in 行们 if 读(r,'id')==读(查看,'id')),None)#行
            查看标题=预设展示文案(命中,翻译)['name'] if 命中 is not None and 翻译 else 读(查看,'title')#名
        return {#视图
            'type':'agent-preset-section',#类型
            'status':状态码,#态
            'error':读(态,'error'),#整页错误
            'title':翻译('nav') if 翻译 else '',#标题
            'intro':翻译('sectionIntro') if 翻译 else '',#引言
            'groups':组们,#分组
            'hasDocument':bool(读(态,'hasDocument')),#有打开器
            'authorable':bool(读(态,'authorable')),#可写
            'revealedPaths':读(态,'revealedPaths') or {},#揭示路径
            'actions':{#动词
                'makeDefault':读(属性,'makeDefault'),#设默认
                'view':读(属性,'view'),#查看
                'openLocation':读(属性,'openLocation'),#位置
                'beginCopy':读(属性,'beginCopy'),#复制
                'confirmDelete':读(属性,'confirmDelete'),#删除确认
                'load':读(属性,'load'),#重载
            },#结束
            'copy':{#复制对话框
                'open':草稿 is not None,#开
                'draft':草稿,#草稿
                'blocker':阻挡,#阻挡
                'message':草稿消息,#消息
                'cancel':读(属性,'cancelCopy'),#取消
                'confirm':读(属性,'confirmCopy'),#确认
                'setId':读(属性,'setCopyId'),#改 id
                'setName':读(属性,'setCopyName'),#改名
            },#结束
            'viewer':{#只读查看
                'open':查看 is not None,#开
                'title':查看标题,#标题
                'content':读(查看,'content') if 查看 else None,#正文
                'close':读(属性,'closeView'),#关
            },#结束
            'delete':{#删除确认
                'open':读(态,'pendingDelete') is not None,#开
                'deleting':bool(读(态,'deleting')),#删中
                'cancel':lambda:读(属性,'confirmDelete')(None) if 读(属性,'confirmDelete') else None,#取消
                'confirm':读(属性,'remove'),#确认
            },#结束
            'cssModule':'预设分区.module.css',#样式
        }#视图结束

    def __call__(自身,属性=None,**关键字参数):#调用形
        """对齐 React。"""
        if 属性 is not None or 关键字参数:#有
            合并=dict(属性 or {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()#渲
