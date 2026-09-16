__all__=['终端体','终端屏幕','适配屏幕']#仅中文公开名

def 适配屏幕(仿真,适配,状态,模型):#测量后 resize
    """按视口与环境上限调整列行。"""
    尺寸=适配.proposeDimensions()#提议
    环境=状态['environment'] if 'environment' in 状态 else None#环境
    if 尺寸 is None or 环境 is None:#缺
        return#停
    列=min(尺寸['cols'],环境['maxCols'])#列
    行=min(尺寸['rows'],环境['maxRows'])#行
    if 列<2 or 行<1:#太小
        return#停
    仿真.resize(列,行)#仿真
    模型.resize(列,行)#模型

class 终端屏幕:#xterm 画面
    """挂载仿真器并跟随主题与画面修订。"""
    def __init__(自身,属性):#记下合成 props
        """记下 state/model/visible/label/theme。"""
        自身.属性=属性#合成
        自身.修订=0#已应用修订

    def 更新(自身,属性):#props 变更
        """刷新合成 props。"""
        自身.属性=属性#最新

    def 视图(自身):#投影屏幕节点
        """屏幕根节点。"""
        return {#屏
            'tag':'div',#根
            'className':'screen',#类
            'cssModule':'终端体.module.css',#样式
        }#结束

    def __call__(自身,属性=None):#组件调用
        """对齐 React 组件调用。"""
        if 属性 is not None:#有新 props
            自身.更新(属性)#刷新
        return 自身.视图()#视图

class 终端体:#侧栏正文
    """保留终端加主题与状态条。"""
    def __init__(自身,属性):#记下合成 props
        """记下 props 并挂载模型。"""
        自身.属性=属性#合成
        标签=属性['useTabInfo']()['tab']#页签
        属性['view'](标签['id']).mount()#挂载

    def 更新(自身,属性):#props 变更
        """刷新合成 props。"""
        自身.属性=属性#最新
        标签=属性['useTabInfo']()['tab']#页签
        属性['view'](标签['id']).mount()#挂载

    def 视图(自身):#投影正文
        """状态条、屏幕与错误。"""
        翻译=自身.属性['t']#文案
        标签=自身.属性['useTabInfo']()['tab']#页签
        def 取主题(值):#主题钩
            """交还原快照。"""
            return 值#快照
        主题=自身.属性['useTheme'](取主题)#主题
        模型=自身.属性['view'](标签['id'])#模型
        状态=自身.属性['useTerminal'](标签['id'])#状态
        if 状态 is None:#尚无
            return None#空
        if 状态.get('issue') is None:#无 issue 键文案
            错误=状态['error'] if 'error' in 状态 and 状态['error'] is not None else None#error
            信息=状态['info'] if 'info' in 状态 else None#info
            if 错误 is None and 信息 is not None:#info.error
                错误=信息['error'] if 'error' in 信息 else None#info 错
        else:#issue 文案键
            错误=翻译(状态['issue'])#翻译
        阶段=状态['phase'] if 'phase' in 状态 else None#阶段
        信息=状态['info'] if 'info' in 状态 else None#info
        状态文案=None#条
        if 阶段=='idle' or 阶段=='loading':#读环境
            状态文案=翻译('loading')#读中
        elif 阶段=='creating' or 阶段=='connecting' or 阶段=='disconnected':#同名键
            状态文案=翻译(阶段)#阶段文案
        elif 信息 is not None and 信息.get('state')=='exited':#退出
            码=信息['exitCode'] if 'exitCode' in 信息 and 信息['exitCode'] is not None else '—'#码
            状态文案=翻译('exited',{'code':str(码)})#退出
        elif 信息 is not None and 信息.get('state')=='failed':#失败
            状态文案=翻译('unavailable')#不可用
        elif 阶段=='closed':#已关
            状态文案=翻译('closed')#已关
        可重试=阶段=='failed' or 阶段=='disconnected'#重试
        只读=阶段=='connected' and 信息 is not None and 信息.get('state')=='running' and not 状态.get('writable')#只读
        子=[]#子节点
        if 状态文案 is not None or 可重试 or 只读:#状态条
            条子=[状态文案]#文
            if 只读:#接管
                条子.append(翻译('readonly'))#只读文
                条子.append({#按钮
                    'tag':'button','type':'button','onClick':模型.connect,'text':翻译('control'),#接管
                })#按钮
            if 可重试:#重试或重连
                if 信息 is None:#尚无 info
                    条子.append({#刷新
                        'tag':'button','type':'button','onClick':模型.refresh,'text':翻译('retry'),#重试
                    })#按钮
                else:#重连
                    条子.append({#重连
                        'tag':'button','type':'button','onClick':模型.connect,'text':翻译('reconnect'),#重连
                    })#按钮
            子.append({#条
                'tag':'div','className':'status','role':'status','children':条子,#条
            })#条结束
        if 信息 is not None:#有画面
            子.append(终端屏幕({#屏幕
                'state':状态,#状态
                'model':模型,#模型
                'visible':标签['visible'],#可见
                'label':翻译('title'),#无障碍
                'theme':主题,#主题
            })())#屏幕
        if 错误 is not None:#错误段
            子.append({#段
                'tag':'p','className':'error','role':'alert','text':翻译('failed',{'message':错误}),#错误
            })#段
        return {#节
            'tag':'section',#节
            'className':'root',#类
            'cssModule':'终端体.module.css',#样式
            'data-sidebar-terminal':True,#标记
            'children':子,#子
        }#结束

    def __call__(自身,属性=None):#组件调用
        """对齐 React 组件调用。"""
        if 属性 is not None:#有新 props
            自身.更新(属性)#刷新
        return 自身.视图()#视图
