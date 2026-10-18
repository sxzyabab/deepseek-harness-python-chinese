'撰写器和 /model 共用的提供方显示顺序'

__all__=['排列模型提供方']

def 排列模型提供方(分组):
    '账号和官方提供方排在前面，其余保持原来的相对顺序'
    def 序(组):
        '账号 0，官方 1，其余 2'
        标识=组['id']
        if 标识=='deepseek-account':
            return 0
        if 标识=='deepseek-official':
            return 1
        return 2
    return sorted(分组,key=序)
