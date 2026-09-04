"""已完成回合 transcript 呈现方式的通用设置行。

对齐上游 `ui-chat/src/client/settings/TranscriptViewRow.tsx`。公开面仅中文名。
无真 React：结构树描述。
"""

__all__=['转录视图行','转录视图选项']#仅中文公开名

转录视图选项=(#可选模式
    {'id':'normal','label':'settings.transcript.normal'},#普通
    {'id':'compact','label':'settings.transcript.compact'},#紧凑
)#OPTIONS 结束

def 取字段(对象,键,缺省=None):#读字段
    """映射或属性。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 转录视图行:#transcript 偏好行
    """模式选择器结构树。"""

    def __init__(自身,属性=None):#构造
        """记下 props。"""
        自身.属性=属性 or {}#合成
        自身.打开=False#菜单开合

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=属性 or {}#新

    def 渲染(自身):#结构树
        """标题 + 下拉。"""
        属性=自身.属性#props
        翻译=取字段(属性,'t',lambda 键,_=None:键)#文案
        用模式=取字段(属性,'useTranscriptView')#钩子
        模式='compact'#默认
        if callable(用模式):#有
            模式=用模式(lambda 值:值) or 模式#当前
        标签键='settings.transcript.normal' if 模式=='normal' else 'settings.transcript.compact'#标签
        项们=[{'id':取字段(项,'id'),'label':翻译(取字段(项,'label'))} for 项 in 转录视图选项]#菜单项
        return {#行
            'type':'transcript-view-row',#类型
            'title':翻译('settings.transcript.title'),#标题
            'description':翻译('settings.transcript.description'),#说明
            'mode':模式,#当前
            'selectedLabel':翻译(标签键),#选中标签
            'open':自身.打开,#开合
            'items':项们,#项
            'setTranscriptView':取字段(属性,'setTranscriptView'),#写入
            'cssModule':'TranscriptViewRow.module.css',#样式
        }#结束

    def __call__(自身,属性=None):#调用形
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
