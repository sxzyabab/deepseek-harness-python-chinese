from nicegui import ui as 界面
from ..ui_基础界面组件.icons import 图标关闭16,图标列表笔16

__all__=['预设指南','系统指南']#仅中文公开名

指南目录={#出厂 id → 词条键
    'standard':{'name':'presetStandardName','intro':'guideStandardIntro','explanation':'guideStandardExplanation','usage':'guideStandardUsage'},#标准
    'ptc':{'name':'presetCodeName','intro':'guidePtcIntro','explanation':'guidePtcExplanation','usage':'guidePtcUsage'},#PTC
    'code':{'name':'presetCodeName','intro':'guidePtcIntro','explanation':'guidePtcExplanation','usage':'guidePtcUsage'},#代码
    'minimal':{'name':'presetMinimalName','intro':'guideMinimalIntro','explanation':'guideMinimalExplanation','usage':'guideMinimalUsage'},#极简
    'cordis':{'name':'presetCordisName','intro':'guideCordisIntro','explanation':'guideCordisExplanation','usage':'guideCordisUsage'},#创造
}#目录结束

def 系统指南(标识,信任):
    '只给出厂系统预设的帮助；自定义预设返回 None'
    if 信任!='system':#非系统
        return None#无
    if 标识 not in 指南目录:#未知
        return None#无
    return 指南目录[标识]#键表

class 预设指南:
    '只读帮助。父分区构造后调用渲染，构造时不画'
    def __init__(自身,属性=None):
        '只记下合并后的属性字典'
        自身.属性=属性 if isinstance(属性,dict) else {}#属性

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性 if isinstance(属性,dict) else {}#最新

    def 渲染(自身):
        '画出标题、两页切换和正文'
        属性=自身.属性#props
        if 't' not in 属性 or 'guide' not in 属性:#未填齐
            return None#不画
        翻译=属性['t']#翻译
        指南=属性['guide']#键表
        页=属性['page'] if 'page' in 属性 else 'explanation'#当前页
        关闭=属性['onClose'] if 'onClose' in 属性 else None#关闭
        换页=属性['onPage'] if 'onPage' in 属性 else None#换页
        def 关():
            '关闭帮助'
            if 关闭 is not None:
                关闭()#关
        def 去说明():
            '切到模式说明'
            if 换页 is not None:
                换页('explanation')#说明
        def 去用法():
            '切到如何使用'
            if 换页 is not None:
                换页('usage')#用法
        with 界面.dialog() as 框:#帮助框
            with 界面.card():#卡
                with 界面.row():#标题行
                    界面.label(翻译(指南['name']))#预设名
                    界面.button(翻译('close'), on_click=关)#关闭
                    图标关闭16()#关闭图标
                界面.button(翻译('modeExplanation'), on_click=去说明)#模式说明
                界面.button(翻译('howToUse'), on_click=去用法)#如何使用
                界面.label(翻译(指南['intro']))#导语
                if 页=='usage':#用法页
                    界面.label(翻译('guideExampleTask'))#示例任务
                    图标列表笔16()#示例图标
                    界面.markdown(翻译(指南['usage']))#用法正文
                else:#说明页
                    界面.markdown(翻译(指南['explanation']))#说明正文
        框.open()#打开

    def __call__(自身,属性=None):
        '只接收一个属性字典'
        if 属性 is not None:
            自身.更新(属性)#刷
        return 自身.渲染()
