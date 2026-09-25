"""路径手势的控件级失败横幅。
由发起手势的控件持有，一次失败只从用户按下的控件宣告一次；再宣告则重放横幅。
"""

__all__=['使用打开失败提示']#仅中文公开名

def 使用打开失败提示():
    """瞬态失败横幅；返回 toast 视图与 show 宣告。
    同文案再宣告会换 seq 重放，避免静默停在原位。
    """
    箱={'seq':0,'banner':None}#序号与横幅
    def 收起():
        """卸横幅。"""
        箱['banner']=None#清
    def 显示(文本):
        """宣告一条失败文案。"""
        箱['seq']+=1#递序号
        箱['banner']={'seq':箱['seq'],'text':文本}#记下
    def 取提示():
        """渲染 toast 结构或 None。"""
        横幅=箱['banner']#当前
        if 横幅 is None:#无
            return None#空
        return {#Toast
            'type':'Toast',#种类
            'key':横幅['seq'],#重放键
            'text':横幅['text'],#文案
            'icon':'IconWarningOutlineRegular',#警告图标
            'onDone':收起,#收起
        }#Toast 结束
    return {'toast':取提示,'show':显示,'dismiss':收起,'state':箱}#面
