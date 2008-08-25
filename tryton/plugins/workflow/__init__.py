#This file is part of Tryton.  The COPYRIGHT file at the top level of this repository contains the full copyright notices and license terms.
from tryton.action import Action

def workflow_print(datas, parent):
    datas = datas.copy()
    datas['nested'] = False
    Action.exec_report('workflow.instance.graph', datas, parent)
    return True

def workflow_print_complex(datas, parent):
    datas = datas.copy()
    datas['nested'] = True
    Action.exec_report('workflow.instance.graph', datas, parent)
    return True

def get_plugins(model):
    return [
            (_('Print Workflow'), workflow_print),
            (_('Print Workflow (Complex)'), workflow_print_complex),
        ]
