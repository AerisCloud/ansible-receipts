# Receipts

![I wanna see the receipts](receipts.gif)

Always wanted to retrieved detailed information about an ansible-playbook run
but don't want to deal with calling the Runner yourself? Fret not, for ye
quick and dirty solution has cometh.

## Installation

Just retrieve `receipts.py` or the repository in a folder on the same computer
where ansible is running.

## Usage

1.  Make sure that the folder where `receipts.py` is loaded by setting the
    `callback_plugins` variable in `ansible.cfg` or using the
    `ANSIBLE_CALLBACK_PLUGINS` environment variable.
2.  Call `ansible-playbook` with the `ANSIBLE_RECEIPTS_FILE` environment variable
    set to the file where you want to store the result.
3.  Once `ansible-playbook` is done running, the file shoud have been created
    with information about the run stored in it.

## Output Format

```javascript
{
  "hostname1": {
    "facts": { /* facts retrieved for this host */ },
    // list of tasks in the order they were run
    "tasks": [{
      "name": "task name",
      "state": "ok", /* one of "ok", "failed", "skipped", "unreachable" */
      "res": { /* custom data, different based on the task */ }
    }],
    "stats": {
      "ok": 5,
      "changed": 3,
      "failed": 0,
      "skipped": 2,
      "unreachable": 0
    }
  }
}
```

