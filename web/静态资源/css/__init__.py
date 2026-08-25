from pathlib import Path
根路径=Path(__file__).parent

def 获取css(css名:str)->str:
    return 根路径/css名.read_text(encoding='utf-8')