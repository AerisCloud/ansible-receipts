import json
import os
import multiprocessing


def receipt_queue(queue, out_queue):
    """
    due to ansible forking, use this thread to aggregate data from the tasks, then send back all that data to the
    parent process when done
    """
    receipts = []
    while True:
        item = queue.get()
        if item == 'finished':
            break
        receipts.append(item)
    # send back everything
    for receipt in receipts:
        out_queue.put(receipt)
    out_queue.put('finished')


class CallbackModule(object):
    """
    logs ansible-playbook and ansible runs to a json file
    """

    def __init__(self):
        self._current_task = None
        if not os.getenv('ANSIBLE_RECEIPTS_FILE'):
            return

        self._queue = multiprocessing.Queue()
        self._out_queue = multiprocessing.Queue()
        self._proc = multiprocessing.Process(target=receipt_queue, args=(self._queue, self._out_queue, ))
        self._proc.start()

    def _put(self, item):
        if not self._queue:
            return
        self._queue.put(item)

    def _register_task(self, host, state, res=None):
        self._put({
            'task': self._current_task,
            'host': host,
            'state': state,
            'res': res
        })

    def on_any(self, *args, **kwargs):
        pass

    def runner_on_failed(self, host, res, ignore_errors=False):
        if ignore_errors:
            # failed tasks that have ignore_errors set are consided ok by ansible
            self._register_task(host, 'ok', res)
        else:
            self._register_task(host, 'failed', res)

    def runner_on_ok(self, host, res):
        #if 'ansible_facts' in res:
        #    self._register_facts(host, res['ansible_facts'])
        #    return

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

    def playbook_on_vars_prompt(self, varname, private=True, prompt=None, encrypt=None, confirm=False, salt_size=None,
                                salt=None, default=None):
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
        if not self._queue:
            return

        receipts = {}
        # playbook is finished, tell that to our helper thread, then read from the output queue
        self._queue.put('finished')
        while True:
            receipt = self._out_queue.get()
            if receipt == 'finished':
                break

            host = receipt['host']
            if not host in receipts:
                receipts[host] = {
                    'facts': {},
                    'tasks': [],
                    'stats': {
                        'ok': 0,
                        'changed': 0,
                        'failed': 0,
                        'skipped': 0,
                        'unreachable': 0
                    }
                }

            if receipt['task']:
                receipts[host]['tasks'].append({
                    'name': receipt['task'],
                    'state': receipt['state'],
                    'res': receipt['res']
                })

                receipts[host]['stats'][receipt['state']] += 1
                if 'changed' in receipt['res'] and receipt['res']['changed']:
                    receipts[host]['stats']['changed'] += 1

            if 'ansible_facts' in receipt['res']:
                receipts[host]['facts'].update(receipt['res']['ansible_facts'])

        # terminate thread
        self._proc.join()

        receipt_file = os.getenv('ANSIBLE_RECEIPTS_FILE')
        if not os.path.exists(os.path.basename(receipt_file)):
            os.makedirs(os.path.basename(receipt_file))

        with open(receipt_file, 'w') as fd:
            json.dump(receipts, fd)
