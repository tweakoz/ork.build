import os
import ork.path
import ork.command

def run(args):
    vivado = ork.path.vivado_base()/"bin"/"vivado"
    ork.command.run([vivado]+args)
