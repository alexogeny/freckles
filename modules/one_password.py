#!/usr/bin/python

__metaclass__ = type

import re
import errno
import pexpect
from ansible.module_utils.common.text.converters import to_native
from ansible.module_utils.basic import AnsibleModule


class AnsibleModuleError(Exception):
    def __init__(self, results):
        self.results = results

    def __repr__(self):
        return self.results


class OnePassword(object):
    def __init__(self):
        self.cli = "op"
        self.logged_in = False
        self.token = None

        self.command = module.params.get("command")
        self.login_details = module.params.get("login_details")
        self.password = self.login_details.get("password")
        self.key = self.login_details.get("key")
        self.email = self.login_details.get("email")
        self.sub = self.login_details.get("subdomain")
        if self.sub == None:
            self.sub = "my"
        self.path = module.params.get("path")

    def runner(
        self,
        command: str,
        internal: str = None,
        expected: int = 0,
        ignore: bool = False,
    ):
        result = None
        prompt = pexpect.spawnu(command)
        if internal == "initial":
            prompt.expect(re.compile(r"^Enter the Secret Key.*"))
            prompt.sendline(self.key)
            prompt.expect(re.compile(r"Enter the password for .*$"))
            prompt.sendline(self.password)
            prompt.readlines()
            prompt.expect(pexpect.EOF)
        elif internal == "get":
            result = prompt.readline()
            prompt.readlines()
            prompt.expect(pexpect.EOF)
        elif internal == "signin":
            prompt.expect(re.compile(r"^Enter the password for .*"))
            prompt.sendline(self.password)
            result = prompt.readlines()
            prompt.expect(pexpect.EOF)
        else:
            prompt.readlines()
        prompt.close()
        rc, out, err = prompt.exitstatus, prompt.stdout, prompt.stderr
        if ignore == False and rc != expected:
            raise AnsibleModuleError(to_native(err))
        return rc, out, err, result

    def run_return(self, cmd, itl, failmsg):
        _, _, _, res = self.runner(cmd, internal=itl)
        if res:
            return res
        module.fail_json(msg=failmsg)

    def login_token(self):
        _, _, _, result = self.runner("op account list", internal="list")
        if result == []:
            self.login()
        else:
            self.token = "".join(
                self.run_return(
                    f"op signin --account {self.sub}.1password.com --raw",
                    "signin",
                    "There was an error getting the token from 1password.",
                )
            ).strip()

    def check_login(self):
        try:
            rc, _, _, _ = self.runner(
                "op account get", ignore=True, internal="is_logged_in"
            )
            self.logged_in = rc == 0
            if not self.logged_in:
                self.login_token()
        except OSError as e:
            if e.errno == errno.ENOENT:
                module.fail_json(msg="1password-cli was not found on the path")
            raise e

    def login(self):
        if self.login_details != None and all([self.password, self.key, self.email]):
            c = f'op account add --address "{self.sub}.1password.com" --email {self.email}'
            try:
                self.runner(c, internal="initial")
                return {"status": True}
            except AnsibleModuleError as e:
                module.fail_json(msg="Failed to login to 1Password. %s" % to_native(e))
        else:
            module.fail_json(msg="Unable to sign in. Missing a param perhaps?")

    def get(self):
        if not self.token:
            self.internal = "token"
            self.check_login()

        try:
            assert re.compile(r"(\w+\.){3}(\w+)").match(self.path)
        except AssertionError:
            module.fail_json(
                msg="Path should be in the format: vault.item.section.name"
            )

        vault, item, section, name = self.path.split(".")

        try:
            _, _, _, result = self.runner(
                f'op read op://{vault}/{item}/{section}/{name} --account {self.sub}.1password.com --session "{self.token}"',
                internal="get",
            )
            return {"secret": result.strip()}
        except AnsibleModuleError as e:
            module.fail_json(msg="Failed to read secret. %s" % to_native(e))

    def run(self):
        assert self.command in ["login", "get"]
        return getattr(self, self.command)()


def main():
    global module
    module = AnsibleModule(
        argument_spec=dict(
            login_details=dict(
                type="dict",
                options=dict(
                    email=dict(type="str"),
                    password=dict(type="str", no_log=True),
                    key=dict(type="str", no_log=True),
                    subdomain=dict(type="str"),
                ),
            ),
            command=dict(type="str"),
            path=dict(type="str"),
        ),
        supports_check_mode=True,
    )

    results = {"onepassword": OnePassword().run()}

    module.exit_json(changed=False, **results)


if __name__ == "__main__":
    main()
