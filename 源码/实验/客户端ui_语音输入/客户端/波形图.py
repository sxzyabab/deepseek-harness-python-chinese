__all__=['波形图']

条数=80

class 波形图:
    """近期麦克风振幅；静音保持点状基线。"""
    def __init__(自身,属性=None):
        """记下录音句柄。"""
        自身.属性={} if 属性 is None else 属性
        自身.电平=[0.0]*条数

    def 更新(自身,属性):
        """刷新。"""
        自身.属性=属性

    def 刷新(自身):
        """把当前 RMS 推进条带。"""
        录音=自身.属性.get('recording')
        下一=0 if 录音 is None else 录音.振幅()
        新=[]
        for 旧 in 自身.电平:
            新.append(下一)
            下一=旧
        自身.电平=新

    def 渲染(自身):
        """SVG 条带。"""
        自身.刷新()
        线=[]
        for 下标 in range(条数):
            高=1+min(1,自身.电平[下标]*5)*17
            线.append({
                'x':下标*8+4,
                'y1':20-高,
                'y2':20+高,
                'opacity':0.25+下标/120,
            })
        return {
            'type':'waveform',
            'cssModule':'语音输入.module.css',
            'label':自身.属性.get('label'),
            'lines':线,
        }

    def __call__(自身,属性=None):
        """对齐 React 调用。"""
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
