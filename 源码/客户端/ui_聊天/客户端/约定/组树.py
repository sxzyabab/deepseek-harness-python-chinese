__all__=['组树深度','在该层或更外']

组树深度={'exchange':0,'input':1,'turn':2,'process':3}


def 在该层或更外(节点,位置):
    '节点的组树位置是这一层，或比这一层更靠外'
    组树=节点.get('groupTree')
    if 组树 is None:
        return False
    return 组树深度[组树]<=组树深度[位置]
