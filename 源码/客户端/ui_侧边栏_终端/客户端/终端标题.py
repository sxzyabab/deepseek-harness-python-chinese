from .终端图标 import 终端图标#线条图标
__all__=['终端标题']#仅中文公开名

class 终端标题:#页签标题
    """双击就地改名。"""
    def __init__(自身,属性):#记下合成 props
        """记下 props。"""
        自身.属性=属性#合成
        自身.编辑中=False#是否编辑
        自身.已取消=False#Escape 取消

    def 更新(自身,属性):#props 变更
        """刷新合成 props。"""
        自身.属性=属性#最新

    def 当前标题(自身):#读名
        """优先模型标题，否则页签标题。"""
        标签=自身.属性['useTabInfo']()['tab']#页签
        def 取标题(状态):#keyed 状态
            """info.title 或 title。"""
            if 状态 is None:#无
                return None#空
            信息=状态['info'] if 'info' in 状态 else None#信息
            if 信息 is not None and 'title' in 信息 and 信息['title'] is not None:#info 标题
                return 信息['title']#标题
            return 状态['title'] if 'title' in 状态 else None#状态标题
        名=自身.属性['useTerminal'](标签['id'],取标题)#模型名
        if 名 is None:#无模型名
            return 标签['title']#页签名
        return 名#模型名

    def 开始改名(自身):#进入编辑
        """停冒泡后进入编辑。"""
        自身.已取消=False#未取消
        自身.编辑中=True#编辑

    def 提交改名(自身,下一):#失焦提交
        """非空且不同则 rename。"""
        自身.编辑中=False#退出
        修剪=下一.strip()#修剪
        标题=自身.当前标题()#当前
        if 自身.已取消:#Escape
            return#丢弃
        if 修剪=='' or 修剪==标题:#无变化
            return#停
        标签=自身.属性['useTabInfo']()['tab']#页签
        自身.属性['view'](标签['id']).rename(修剪)#改名

    def 视图(自身):#投影标题
        """图标加名称或输入框。"""
        翻译=自身.属性['t']#文案
        标题=自身.当前标题()#名
        if 自身.编辑中:#输入
            名节点={#输入
                'tag':'input',#输入
                'className':'name',#类
                'cssModule':'终端体.module.css',#样式
                'defaultValue':标题,#初值
                'maxLength':120,#上限
                'aria-label':翻译('rename'),#无障碍
                'onBlur':自身.提交改名,#提交
            }#输入结束
        else:#展示
            名节点={#跨度
                'tag':'span',#跨度
                'className':'title',#类
                'cssModule':'终端体.module.css',#样式
                'text':标题,#文本
                'onDoubleClick':自身.开始改名,#双击
            }#跨度结束
        return {#片段
            'tag':'fragment',#片段
            'children':[终端图标()(),名节点],#图标与名
        }#结束

    def __call__(自身,属性=None):#组件调用
        """对齐 React 组件调用。"""
        if 属性 is not None:#有新 props
            自身.更新(属性)#刷新
        return 自身.视图()#视图
