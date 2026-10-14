'路径手势的控件级失败横幅'
from ...ui_基础界面组件.吐司 import 吐司

__all__=['使用打开失败提示']#仅中文公开名

def 使用打开失败提示():
    """瞬态失败横幅；toast 画出吐司，show 宣告失败。
    同文案再宣告会换 seq 重放，避免静默停在原位
    """
    箱={'seq':0,'banner':None}#序号与横幅
    def 收起():
        '卸横幅'
        箱['banner']=None#清
    def 显示(文本):
        '宣告一条失败文案'
        箱['seq']+=1#递序号
        箱['banner']={'seq':箱['seq'],'text':文本}#记下
    def 取提示():
        '有横幅时画出吐司'
        横幅=箱['banner']#当前
        if 横幅 is None:#无
            return None#空
        吐司({#公告
            'text':横幅['text'],#文案
            'icon':'IconWarningOutlineRegular',#警告图标
            'onDone':收起,#收起
        }).渲染()#画出
        return None#已画
    return {'toast':取提示,'show':显示,'dismiss':收起,'state':箱}#面
