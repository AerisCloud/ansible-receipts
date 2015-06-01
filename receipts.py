import json
import os

class CallbackModule(object):
    """
    logs ansible-playbook and ansible runs to a json file
    """

    def __init__(self):
        self._receipts = {}
        self._current_task = None

    def _register_facts(self, host, facts):
        self._receipts[host] = {
            'facts': facts,
            'tasks': [],
            'stats': {
                'ok': 0,
                'failed': 0,
                'unreachable': 0,
                'changed': 0,
                'skipped': 0
            }
        }

    def _register_task(self, host, state, res=None):
        self._receipts[host]['tasks'].append({
            'name': self._current_task,
            'state': state,
            'res': res
        })

        self._receipts[host]['stats'][state] += 1
        if 'changed' in res and res['changed']:
            self._receipts[host]['stats']['changed'] += 1

    def on_any(self, *args, **kwargs):
        pass

    def runner_on_failed(self, host, res, ignore_errors=False):
        if ignore_errors:
            # failed tasks that have ignore_errors set are consided ok by ansible
            self._register_task(host, 'ok', res)
        else:
            self._register_task(host, 'failed', res)

    def runner_on_ok(self, host, res):
        if 'ansible_facts' in res:
            self._register_facts(host, res['ansible_facts'])
            return

        self._register_task(host, 'ok', res)

    def runner_on_skipped(self, host, item=None):
        self._register_task(host, 'skipped', {'item': item})

    def runner_on_unreachable(self, host, res):
        self._register_task(host, 'unreachable', res)

    def runner_on_no_hosts(self):
        pass

    def runner_on_async_poll(self, host, res):
        pass

    def runner_on_async_ok(self, host, res):
        pass

    def runner_on_async_failed(self, host, res):
        pass

    def playbook_on_start(self):
        pass

    def playbook_on_notify(self, host, handler):
        pass

    def playbook_on_no_hosts_matched(self):
        pass

    def playbook_on_no_hosts_remaining(self):
        pass

    def playbook_on_task_start(self, name, is_conditional):
        self._current_task = name

    def playbook_on_vars_prompt(self, varname, private=True, prompt=None, encrypt=None, confirm=False, salt_size=None, salt=None, default=None):
        pass

    def playbook_on_setup(self):
        pass

    def playbook_on_import_for_host(self, host, imported_file):
        pass

    def playbook_on_not_import_for_host(self, host, missing_file):
        pass

    def playbook_on_play_start(self, name):
        pass

    def playbook_on_stats(self, stats):
        receipt_file = os.getenv('ANSIBLE_RECEIPTS_FILE')
        if not receipt_file:
            return

        if not os.path.exists(os.path.basename(receipt_file)):
            os.makedirs(os.path.basename(receipt_file))

        with open(receipt_file, 'w') as fd:
            json.dump(self._receipts, fd)
