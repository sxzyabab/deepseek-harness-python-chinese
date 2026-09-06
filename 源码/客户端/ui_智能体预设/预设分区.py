"""智能体预设设置分区：名册卡片、复制对话框、只读查看与删除确认。

对齐上游 `ui-agent-preset/src/client/AgentPresetSection.tsx`。公开面仅中文名。
浏览器不编辑组合正文；复制是创建唯一途径。
"""
from .文案 import 预设展示文案#展示文案
from .分区存储 import 草稿阻挡#客户端阻挡

__all__=['预设分区']#仅中文公开名

class 预设分区:
    """部署无名册时返回 None。属性与快照都是 dict。"""
    def __init__(自身,属性=None,**关键字参数):
        """合并 props 并拉名册。"""
        自身.属性=dict(属性) if 属性 is not None else {}#基础
        自身.属性.update(关键字参数)#覆盖
        自身.属性['load']()#拉

    def 更新(自身,属性):
        """刷新 props。"""
        自身.属性=dict(属性)#最新

    def 状态(自身):
        """经 useAgentPresetSection。"""
        def 恒等(快照):
            """整表。"""
            return 快照#快照
        return 自身.属性['useAgentPresetSection'](恒等)#快照

    def 取消删除(自身):
        """关掉删除确认。"""
        自身.属性['confirmDelete'](None)#取消

    def 渲染(自身):
        """产出分区；unavailable 则 None。"""
        属性=自身.属性#props
        态=自身.状态()#态
        翻译=属性['t']#翻译
        状态码=态['status']#生命周期
        if 状态码=='unavailable':#部署无预设
            return None#不画
        if 状态码=='error':#错误
            错=态['error']#文案
            return {#错误面
                'type':'agent-preset-section',#类型
                'status':'error',#态
                'error':错 if 错 is not None else '',#文案
                'retry':属性['load'],#重试
                'labels':{'error':翻译('error'),'retry':翻译('retry')},#文案
                'cssModule':'预设分区.module.css',#样式
            }#结束
        行列表=态['rows']#名册
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
                        有创造=True#有
                        break#停
                if 有创造:#名册有 cordis
                    启=属性['startCreatorDraft']#启动
                    关=属性['close'] if 'close' in 属性 else None#关设置
                    def 点编写(启动=启,关闭=关):
                        """暂存并关设置。"""
                        启动()#启动
                        if 关闭 is not None:#有关
                            关闭()#关设置
                    可写=态['authorable']#可写
                    尾={#编写按钮
                        'disabled':not 可写,#不可写则禁
                        'title':None if 可写 else 翻译('duplicateUnavailable'),#提示
                        'label':翻译('creatorDraft'),#文案
                        'onClick':点编写,#开
                    }#结束
            if len(组行)==0 and 尾 is None:#空组无尾；判 length
                continue#跳
            组列表.append({'trust':信任,'heading':翻译(标题键),'cards':组行,'tail':尾})#组
        草稿=态['copy']#复制草稿
        阻挡=草稿阻挡(草稿,行列表) if 草稿 is not None else None#阻挡
        草稿消息=None#消息
        if 草稿 is not None:#开着
            草稿错=草稿['error'] if 'error' in 草稿 else None#错误
            if 草稿错 is not None:#优先错误
                草稿消息=草稿错#错误
            elif 阻挡 is not None:#客户端阻挡
                草稿消息=翻译(阻挡)#文案
            else:#无
                草稿消息=阻挡#空
        查看=态['view']#查看器
        查看标题=''#标题
        if 查看 is not None:#开着
            命中=None#行
            for r in 行列表:#找
                if r['id']==查看['id']:#命中
                    命中=r#记下
                    break#停
            if 命中 is not None:#有行
                查看标题=预设展示文案(命中,翻译)['name']#名
            else:#无
                查看标题=查看['title']#标题
        揭示=态['revealedPaths']#揭示路径
        if 揭示 is None:#无
            揭示={}#空
        return {#视图
            'type':'agent-preset-section',#类型
            'status':状态码,#态
            'error':态['error'],#整页错误
            'title':翻译('nav'),#标题
            'intro':翻译('sectionIntro'),#引言
            'groups':组列表,#分组
            'hasDocument':态['hasDocument'],#有打开器
            'authorable':态['authorable'],#可写
            'revealedPaths':揭示,#揭示路径
            'actions':{#动词
                'makeDefault':属性['makeDefault'],#设默认
                'view':属性['view'],#查看
                'openLocation':属性['openLocation'],#位置
                'beginCopy':属性['beginCopy'],#复制
                'confirmDelete':属性['confirmDelete'],#删除确认
                'load':属性['load'],#重载
            },#结束
            'copy':{#复制对话框
                'open':草稿 is not None,#开
                'draft':草稿,#草稿
                'blocker':阻挡,#阻挡
                'message':草稿消息,#消息
                'cancel':属性['cancelCopy'],#取消
                'confirm':属性['confirmCopy'],#确认
                'setId':属性['setCopyId'],#改 id
                'setName':属性['setCopyName'],#改名
            },#结束
            'viewer':{#只读查看
                'open':查看 is not None,#开
                'title':查看标题,#标题
                'content':查看['content'] if 查看 is not None else None,#正文
                'close':属性['closeView'],#关
            },#结束
            'delete':{#删除确认
                'open':态['pendingDelete'] is not None,#开
                'deleting':态['deleting'],#删中
                'cancel':自身.取消删除,#取消
                'confirm':属性['remove'],#确认
            },#结束
            'cssModule':'预设分区.module.css',#样式
        }#视图结束

    def __call__(自身,属性=None,**关键字参数):
        """对齐 React。"""
        if 属性 is not None or len(关键字参数)>0:#有
            合并=dict(属性) if 属性 is not None else {}#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()#渲
