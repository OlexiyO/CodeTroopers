from utilities.BaseRunner import Runner


from subprocess import call
P = 'C:/Coding/CodeTroopers/Repeater/repeater.bat'
token = '6a94d9237857485bd2026557363152557fc2d31c'
call([P, token], shell=True)
Runner().run()