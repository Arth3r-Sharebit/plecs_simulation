# todo

json_main.py 当中实现对路径的检测(当output.disable == True时)

注意！！！！！
PLECS 当To File 模块的Filename参数异常时 仿真会立刻结束并且不会返回任何错误或抛出异常 ！！！
当仿真参数都在正常范围内但仿真瞬间中止时 务必检查此处


# todo

仿真被用户强制退出后 plecs仿真文件下次被打开时候会有异常退出弹窗 研究如何消除这个弹窗