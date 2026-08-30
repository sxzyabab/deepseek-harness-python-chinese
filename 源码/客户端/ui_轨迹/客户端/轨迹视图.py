"""轨迹视图：会话视图槽上的轨迹标签页面。

对齐上游 `ui-trajectory/src/client/TrajectoryView.tsx` 的注入与布局消费面。公开面仅中文名。
"""
from .轨迹记录 import 取字段#字段读取
from .布局 import 派生轨迹布局,追加轨迹流式布局 as 追加轨迹部分布局#布局折叠
from .轨迹表实现 import 轨迹表#权威实现（上游 TrajectoryTable）

__all__=['轨迹视图']#仅中文公开名

class 轨迹视图:#轨迹标签页
    """消费会话 trajectory 快照，折叠成轮次表并支持加载更早历史。"""
    def __init__(自身,会话标识,注入,快照=None,翻译=None):#会话与注入面
        """记下会话 id、注入钩子与可选快照。"""
        自身.会话标识=会话标识#会话 id
        自身.注入=注入 or {}#注入面
        自身.快照=快照 or {'eventNodes':[],'requests':[],'partial':None,'runningCalls':[]}#快照
        自身.翻译=翻译 or (lambda 键,*_位置,**_关键字:键)#文案
        自身.查询=''#搜索
        自身.等宽=False#等宽操作偏好（与时长偏好对偶）
        自身.表=轨迹表()#账本表实例

    def 轮次(自身):#折叠后的轮次
        """从快照派生轮次布局。"""
        定稿=派生轨迹布局({#定稿布局（空 partial 锚点）
            'nodes':取字段(自身.快照,'eventNodes'),#节点
            'eventLocations':取字段(自身.快照,'eventLocations'),#位置
            'partial':None,#定稿不含流式
            'runningCalls':取字段(自身.快照,'runningCalls'),#进行中调用
            'requests':取字段(自身.快照,'requests'),#请求
            'callSchemas':取字段(自身.快照,'callSchemas'),#schema
        })#派生结束
        最后=0#最高下标
        for 轮 in 定稿:#各轮
            for 组 in 取字段(轮,'groups') or []:#各组
                for 格 in 取字段(组,'cells') or []:#各格
                    最后=max(最后,取字段(格,'index',0))#刷新
        return 追加轨迹部分布局(定稿,取字段(自身.快照,'partial'),最后)#接上流式

    def 表属性(自身,属性=None):#表 props
        """组装轨迹表 props；可选覆盖。"""
        合成={#基线（上游挂 Table 的 turns / loadOlder）
            'turns':自身.轮次(),#轮次布局
            'onLoadOlder':取字段(自身.注入,'loadOlder'),#更早分页
        }#基线结束
        if 属性:#有覆盖
            合成.update(属性)#合并
        return 合成#props

    def 表视图(自身,属性=None):#可调用表出口
        """与时间线对称：可调用的表视图结构树。"""
        return 自身.表(自身.表属性(属性))#更新并渲染

    def 渲染(自身):#视图结构树
        """返回轨迹视图结构树。"""
        return {#根
            'type':'div','class':'trajectoryView','sessionId':自身.会话标识,#根
            'toolbar':{#工具栏
                'aria':自身.翻译('toolbar.aria'),#无障碍
                'searchPlaceholder':自身.翻译('toolbar.searchPlaceholder'),#搜索占位
                'query':自身.查询,#当前查询
            },#工具栏结束
            'table':自身.表视图(),#挂 TrajectoryTable
            'turns':自身.轮次(),#轮次布局（时间线等仍可用）
        }#根结束

    def 处理动作(自身,动作,载荷=None):#分发
        """搜索、加载更早、写入实测时长；其余委托表。"""
        if 动作=='set-query':#写查询
            自身.查询=载荷 or ''#查询
            return#已处理
        if 动作=='load-older':#加载更早
            加载=取字段(自身.注入,'loadOlder')#注入
            if callable(加载):#有
                return 加载()#加载
            return False#无
        if 动作=='set-actual-duration':#实测时长
            写入=取字段(自身.注入,'setActualDuration')#注入
            if callable(写入):#有
                写入(载荷)#写入
            return#已处理
        return 自身.表.处理动作(动作,载荷)#表交互
