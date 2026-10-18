拖拽标记='data-window-drag'#一行铬标在自己拥有窗口拖拽的元素上

召回标记='data-window-drag-recall'#壳打一帧，让 Electron 重新收集拖拽矩形

交互选择器=', '.join((#从拖拽行里扣掉的交互元素。选择器文本与样式表同一份
    'button','a','input','select','textarea','summary',"[contenteditable='true']",'[tabindex]',
    "[role='dialog']","[role='alertdialog']","[role='menu']","[role='listbox']","[role='tooltip']",
    "[role='button']","[role='link']","[role='tab']","[role='menuitem']","[role='menuitemcheckbox']",
    "[role='menuitemradio']","[role='option']","[role='checkbox']","[role='radio']","[role='switch']",
    "[role='slider']","[role='combobox']","[role='textbox']",
))#选择器结束


def 包含点(矩形,横坐标,纵坐标):
    '点是否落在盒子里。边属于盒子，右缘和下缘不属于'
    if 横坐标<矩形['x']:#在左缘外
        return False#不包含
    if 横坐标>=矩形['x']+矩形['width']:#在右缘上或右边
        return False#不包含
    if 纵坐标<矩形['y']:#在上缘外
        return False#不包含
    if 纵坐标>=矩形['y']+矩形['height']:#在下缘上或下边
        return False#不包含
    return True#在盒子里


def 该点可拖(区域表,横坐标,纵坐标):
    '按下这一点时窗口会不会拖。最后一个罩住它的盒子说了算'
    可拖=False#没有盒子罩住时不拖
    for 区域 in 区域表:#按文档顺序
        if 包含点(区域,横坐标,纵坐标):#罩住这一点
            可拖=区域['draggable']#后一个盖过前一个
    return 可拖#最后的决定
