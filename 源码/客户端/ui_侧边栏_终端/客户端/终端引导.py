from .终端图标 import 终端引导图标#卡片图标
__all__=['终端引导']#仅中文公开名

class 终端引导:#开始页入口
    """卡片启动记住的壳，菜单另选壳。"""
    def __init__(自身,属性):#记下合成 props
        """记下 props。"""
        自身.属性=属性#合成
        自身.打开=False#菜单开
        自身.尝试=0#重试计数
        自身.菜单={'phase':'loading'}#菜单态

    def 更新(自身,属性):#props 变更
        """刷新合成 props。"""
        自身.属性=属性#最新

    def 切菜单(自身):#开关菜单
        """打开时重置为 loading。"""
        自身.菜单={'phase':'loading'}#读中
        自身.打开=not 自身.打开#翻转

    def 关菜单(自身):#关闭
        """关上菜单。"""
        自身.打开=False#关

    def 选壳(自身,路径):#选一项
        """失败则重试；否则记住并打开标签。"""
        if 自身.菜单['phase']=='failed':#失败项
            自身.菜单={'phase':'loading'}#再读
            自身.尝试+=1#计数
            return#停
        自身.属性['selectShell'](路径)#记住
        自身.打开=False#关菜单
        标签=自身.属性['useTabInfo']()['tab']#页签
        标签['actions'].openTab('terminal',{'replaceTab':True,'params':{'shellPath':路径}})#打开

    def 开终端(自身):#主按钮
        """替换当前页签为终端。"""
        标签=自身.属性['useTabInfo']()['tab']#页签
        标签['actions'].openTab('terminal',{'replaceTab':True})#打开

    def 菜单项(自身):#菜单条目
        """按阶段投影项。"""
        翻译=自身.属性['t']#文案
        阶段=自身.菜单['phase']#阶段
        if 阶段=='ready':#已就绪
            项表=[]#项
            for 壳 in 自身.菜单['choices']['shells']:#每个壳
                项表.append({'id':壳['path'],'label':壳['name']})#项
            return 项表#项
        if 阶段=='loading':#读中
            return [{'id':'loading','label':翻译('shellLoading'),'disabled':True}]#占位
        return [#失败
            {'id':'error','label':翻译('failed',{'message':自身.菜单['message']}),'disabled':True},#错误
            {'id':'retry','label':翻译('retry')},#重试
        ]#失败项

    def 视图(自身):#投影卡片
        """主按钮加菜单触发。"""
        翻译=自身.属性['t']#文案
        标题=自身.属性['title']#标题
        说明=自身.属性['description'] if 'description' in 自身.属性 else None#说明
        种类=自身.属性['kind']#种类
        图标尺寸=22 if 说明 is None else 26#尺寸
        项表=自身.菜单项()#项
        if len(项表)==0:#空
            项表=[{'id':'empty','label':翻译('shellEmpty'),'disabled':True}]#空提示
        选中=自身.菜单['choices']['selectedShell'] if 自身.菜单['phase']=='ready' else None#选中
        return {#卡片
            'tag':'div',#根
            'className':'entry',#类
            'cssModule':'终端引导.module.css',#样式
            'data-sidebar-right-guide-entry':种类,#种类
            'children':[{#主按钮
                'tag':'button',#按钮
                'variant':'ghost',#幽灵
                'className':'main',#类
                'onClick':自身.开终端,#打开
                'children':[#图标与文
                    终端引导图标({'size':图标尺寸,'className':'icon'})(),#图标
                    {#文本列
                        'tag':'span',#列
                        'className':'text',#类
                        'children':[#标题说明
                            {'tag':'span','className':'title','text':标题},#标题
                            {'tag':'span','className':'description','text':说明} if 说明 is not None else None,#说明
                        ],#子
                    },#列结束
                ],#主按钮子
            },{#菜单
                'tag':'menu',#菜单
                'open':自身.打开,#开
                'portal':True,#传送
                'autoFocus':True,#焦点
                'align':'end',#对齐
                'className':'menu',#类
                'items':项表,#项
                'selectedId':选中,#选中
                'onClose':自身.关菜单,#关
                'onSelect':自身.选壳,#选
                'anchor':{#触发
                    'tag':'button',#按钮
                    'variant':'ghost',#幽灵
                    'className':'trigger',#类
                    'aria-label':翻译('shell'),#无障碍
                    'aria-haspopup':'menu',#弹出
                    'aria-expanded':自身.打开,#展开
                    'onClick':自身.切菜单,#开关
                    'icon':'chevron-down-outline-14',#箭头
                },#触发结束
            }],#子
        }#卡片结束

    def __call__(自身,属性=None):#组件调用
        """对齐 React 组件调用。"""
        if 属性 is not None:#有新 props
            自身.更新(属性)#刷新
        return 自身.视图()#视图
