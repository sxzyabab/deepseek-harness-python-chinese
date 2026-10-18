'选取和定位用的高亮框。框在对话外面，不改对话节点'

from ......客户端.模块.客户端.通告 import 取握手窗口

def 可见聊天矩形(元素):
    '和滚动口、输入席以上的对话区域求交。完全在外面就没有矩形'
    矩形=元素.getBoundingClientRect()#元素盒
    窗口=取握手窗口()#视口
    左=max(0,矩形.left)#不超出视口左
    右=min(窗口.innerWidth,矩形.right)#不超出视口右
    上=max(0,矩形.top)#不超出视口上
    下=min(窗口.innerHeight,矩形.bottom)#不超出视口下
    父=元素.parentElement#从父开始找滚动口
    while 父 is not None:#还有祖先
        if 父.matches('[data-conversation-scroll], [data-step-process-body]'):#滚动口或过程体
            界=父.getBoundingClientRect()#祖先盒
            左=max(左,界.left)#再收左
            右=min(右,界.right)#再收右
            上=max(上,界.top)#再收上
            下=min(下,界.bottom)#再收下
            if 父.hasAttribute('data-conversation-scroll'):#对话滚动口
                席=父.querySelector(':scope > [data-composer-seat]')#输入席
                if 席 is not None:#有输入席
                    席盒=席.getBoundingClientRect()#输入席盒
                    if 席盒.height>0:#占了高度
                        下=min(下,席盒.top)#不超过输入席顶
        父=父.parentElement#再上一层
    if 下<=上 or 右<=左:#没有剩余面积
        return None#看不见
    return {'left':左,'top':上,'width':右-左,'height':下-上}#可见矩形

def 放置聊天高亮(覆盖,元素):
    '把检查器自己的固定层放到可见矩形上，不改对话盒子'
    矩形=可见聊天矩形(元素)#裁剪后的盒子
    if 矩形 is None:#完全在外面
        return False#放不上
    覆盖.style.left=str(矩形['left'])+'px'#左
    覆盖.style.top=str(矩形['top'])+'px'#上
    覆盖.style.width=str(矩形['width'])+'px'#宽
    覆盖.style.height=str(矩形['height'])+'px'#高
    return True#还有可见部分
