from .文案 import 命名空间,中文,英文#词典
from .菜单视图 import 菜单视图#菜单组件
from .服务 import 触发服务#根服务
from .控制器 import 触发控制器#每会话控制器
from .异常 import 触发错误
from .探测 import 检测触发#纯核心探测
from .菜单归约 import 菜单关闭,铺分组,菜单归约,精确匹配#纯核心归约

__all__=['依赖','应用','菜单视图','触发服务','触发控制器','检测触发','菜单关闭','铺分组','菜单归约','精确匹配','命名空间','中文','英文']#仅中文公开名

依赖=['sessions','locale']#会话与文案

def 应用(上下文):#安装斜杠触发浏览器半边
    '登记词典与触发服务，并把菜单视图挂进 input.overlay'
    def 登记词表():#登记本包词典
        '把中英文词表交给 locale'
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})#登记
    上下文.副作用(登记词表,'ui-input-trigger: menu dictionaries')#词典
    上下文.启动插件(触发服务)#挂 ctx.inputTriggers
    def 挂菜单(作用域):#等槽位、inputTriggers、会话
        '登记 slash-menu 叠层条目'
        触发=作用域.inputTriggers#触发服务
        会话面=作用域.sessions#会话
        def 登记():#登记菜单
            '候选菜单视图'
            def 注入面(会话标识):#按会话解析
                '菜单状态与点选/关闭'
                作用域会话=会话面.scope(会话标识)#作用域
                if 作用域会话 is None:#无
                    说明=str(会话标识)
                    句子='ui-input-trigger: session resolved no scope'#固定句
                    if 说明!='':#还能留下的身份
                        句子=句子+' '+说明#接在固定句后
                    raise 触发错误(句子)#失败
                控制器=触发.sessionOf(作用域会话)#该会话控制器
                def 点选项(来源,下标,动作='pick'):#点选
                    '转调 pick；下钻带 drill'
                    return 控制器.pick(来源,下标,动作)#点选
                def 点屑(来源,下标):#面包屑
                    '转调 pickCrumb'
                    return 控制器.pickCrumb(来源,下标)#下钻
                def 悬停(来源,下标):#指针
                    '转调 hover'
                    return 控制器.hover(来源,下标)#高亮
                def 关闭菜单():#关闭
                    '转调 dismiss'
                    return 控制器.dismiss()#关闭
                return {#注入面
                    'menu':控制器.menu,#菜单仓
                    'headers':控制器.headers,#页眉仓
                    'onPick':点选项,#点选
                    'onCrumb':点屑,#面包屑
                    'onHover':悬停,#悬停
                    'onDismiss':关闭菜单,#关闭
                    'pageFailure':控制器,#菜单上显示的页面失败
                }
            return 作用域.slots.register({#登记
                'name':'conversation.input.overlay',#叠层槽
                'id':'slash-menu',#条目 id
                'order':0,#顺序
                'locale':命名空间,#词表
                'inject':注入面,#注入
            },菜单视图)#组件
        作用域.slots.inject('conversation.input.overlay',登记)#等槽
    上下文.依赖启动(['slots','inputTriggers','sessions'],挂菜单)#注入

inject=依赖#框架槽
apply=应用#框架槽
