"""Real Git HTTPS authentication, SSH URL translation and recursive submodules."""
import base64
import io
import importlib.util
import json
import os
from pathlib import Path
import shutil
import shlex
import ssl
import subprocess
import sys
import tempfile
import threading
import unittest
from contextlib import redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch
from urllib.parse import urlsplit

from obt import dep, git_auth
from obt.command import Command, runasync2


class GitAuthFixture:
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='obt auth ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.token = self.root/'read token';self.token.write_text('test-only-read-token');self.token.chmod(0o600)
        self.config = self.root/'auth.json'
        self.write_config({'https://github.com/example/private.git': {'token_file':str(self.token)}})
        self.env = dict(os.environ, OBT_GIT_AUTH_FILE=str(self.config))

    def write_config(self, value):
        self.config.write_text(json.dumps(value));self.config.chmod(0o600)


class GitAuthTests(GitAuthFixture, unittest.TestCase):

    def test_generic_commands_ignore_git_auth_configuration(self):
        environment=dict(self.env,OBT_GIT_AUTH_FILE=str(self.root/'missing-config'))
        with patch.dict(os.environ,environment,clear=True):
            self.assertEqual(Command([sys.executable,'-c','print("generic")'],do_log=False).capture().strip(),'generic')
            self.assertEqual(runasync2([sys.executable,'-c','pass']).future.result(timeout=10),0)

    def test_opt_in_and_no_mutation_of_callers_environment(self):
        plain={'PATH':'/usr/bin'}
        self.assertIs(git_auth.environment(plain),plain)
        before=dict(self.env);configured=git_auth.environment(self.env)
        self.assertEqual(self.env,before)
        self.assertNotIn(self.token.read_text(),json.dumps(configured))
        self.assertEqual(git_auth.environment(configured),configured)
        self.assertEqual(configured['GIT_TERMINAL_PROMPT'],'0')

    def test_real_git_url_translation_without_network(self):
        environment=git_auth.environment(dict(self.env,GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='core.abbrev',GIT_CONFIG_VALUE_0='12'))
        for url in ('git@github.com:example/private.git','ssh://git@github.com/example/private.git','ssh://git@github.com:22/example/private.git'):
            result=subprocess.run(['git','ls-remote','--get-url',url],env=environment,text=True,capture_output=True,check=True)
            self.assertEqual(result.stdout.strip(),'https://github.com/example/private.git')
        self.assertEqual(environment['GIT_CONFIG_VALUE_0'],'12')

    def test_helper_is_exact_repository_and_does_not_store_tokens(self):
        environment=git_auth.environment(self.env)
        query='protocol=https\nhost=github.com\npath=example/private.git\n\n'
        result=subprocess.run(['git','credential','fill'],input=query,env=environment,text=True,capture_output=True,check=True)
        self.assertIn('password=test-only-read-token',result.stdout)
        for path in ('example/other.git','example/private-extra.git','example/private.git/info/lfs-evil'):
            self.assertEqual(git_auth.credential(dict(protocol='https',host='github.com',path=path),self.env),{})
        self.assertEqual(git_auth.credential(dict(protocol='http',host='github.com',path='example/private.git'),self.env),{})
        self.assertEqual(git_auth.credential(dict(protocol='https',host='github.com',path='example/private.git/info/lfs'),self.env)['password'],'test-only-read-token')
        self.token.write_text('test-only-rotated-token')
        self.assertEqual(git_auth.credential(dict(protocol='https',host='github.com',path='example/private'),self.env)['password'],'test-only-rotated-token')
        self.assertFalse((self.root/'.git-credentials').exists())

    def test_private_files_and_invalid_configuration_fail_closed(self):
        for filename in (self.config,self.token):
            filename.chmod(0o644)
            with self.assertRaises(ValueError):git_auth.credential(dict(protocol='https',host='github.com',path='example/private'),self.env)
            filename.chmod(0o600)
        link=self.root/'linked-token';link.symlink_to(self.token)
        self.write_config({'https://github.com/example/private.git':{'token_file':str(link)}})
        with self.assertRaises(ValueError):git_auth.credential(dict(protocol='https',host='github.com',path='example/private'),self.env)
        for url in ('http://github.com/a/b','https://secret@github.com/a/b','https://github.com/a/../b','https://github.com/a/b?token=bad'):
            self.write_config({url:{'token_file':str(self.token)}})
            with self.assertRaises(ValueError):git_auth.environment(self.env)

    def test_github_tarball_shortcut_uses_git_for_configured_private_repository(self):
        from obt._dep_fetch import GithubFetcher
        fetcher=GithubFetcher(name='private',repospec='example/private.git')
        with patch.dict(os.environ,self.env),patch('obt.git.Clone',return_value=True) as clone,patch('obt.git.fetch_tarball_from_github') as tarball:
            self.assertTrue(fetcher.fetch(self.root/'checkout'))
            clone.assert_called_once();tarball.assert_not_called()
        public=GithubFetcher(name='public',repospec='example/public.git')
        with patch.dict(os.environ,self.env),patch('obt.git.fetch_tarball_from_github',return_value=0) as tarball:
            self.assertTrue(public.fetch(self.root/'public'))
            tarball.assert_called_once()

    def provider(self,name):
        import obt.path
        filename=obt.path.obt_modules_base()/'dep'/(name+'.py')
        spec=importlib.util.spec_from_file_location('git_auth_'+name,filename)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        return module

    def test_slang_applies_auth_at_its_direct_git_fetch_and_submodule_calls(self):
        module=self.provider('slang');dest=self.root/'slang';(dest/'.git').mkdir(parents=True)
        with patch.dict(os.environ,self.env,clear=True),patch.object(module.subprocess,'check_output',return_value=module.REVISION),patch.object(module.subprocess,'run') as execute:
            self.assertTrue(module._Fetcher().fetch(dest))
            self.assertEqual(len(execute.call_args_list),2)
            for call in execute.call_args_list:
                self.assertEqual(call.kwargs['env']['GIT_TERMINAL_PROMPT'],'0')
                self.assertIn('_OBT_GIT_AUTH_CONFIG',call.kwargs['env'])

    def test_oidn_applies_auth_at_its_submodule_and_lfs_fetch_calls(self):
        module=self.provider('oidn');dest=self.root/'oidn';(dest/'.git').mkdir(parents=True)
        with patch.dict(os.environ,self.env,clear=True),patch.object(module.subprocess,'run') as execute:
            self.assertTrue(module._Fetcher(False,False).fetch(dest))
            network=[call for call in execute.call_args_list if call.args[0][1:3] in (['submodule','update'],['lfs','pull'])]
            self.assertEqual(len(network),2)
            for call in network:self.assertIn('_OBT_GIT_AUTH_CONFIG',call.kwargs['env'])


class GitHTTPTests(GitAuthFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.repos=self.root/'repos';(self.repos/'team').mkdir(parents=True)
        cert=self.root/'certificate.pem';key=self.root/'key.pem'
        subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-days','1',
                        '-subj','/CN=localhost','-addext','subjectAltName=DNS:localhost,IP:127.0.0.1',
                        '-keyout',str(key),'-out',str(cert)],check=True,capture_output=True)
        base={k:v for k,v in os.environ.items() if not k.startswith(('GIT_','OBT_GIT_','_OBT_GIT_'))}
        self.env=dict(base,HOME=str(self.root),GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull,
                      GIT_SSL_CAINFO=str(cert),OBT_GIT_AUTH_FILE=str(self.config),
                      GIT_AUTHOR_NAME='Fixture',GIT_COMMITTER_NAME='Fixture',
                      GIT_AUTHOR_EMAIL='fixture@example.invalid',GIT_COMMITTER_EMAIL='fixture@example.invalid')
        self.requests=[];fixture=self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_GET(self):self.serve()
            def do_POST(self):self.serve()
            def serve(self):
                parsed=urlsplit(self.path)
                auth='Basic '+base64.b64encode(b'x-access-token:test-only-read-token').decode()
                if self.headers.get('Authorization')!=auth:
                    self.send_response(401);self.send_header('WWW-Authenticate','Basic realm="fixture"');self.end_headers();return
                fixture.requests.append(parsed.path)
                environment=dict(fixture.env,GIT_PROJECT_ROOT=str(fixture.repos),GIT_HTTP_EXPORT_ALL='1',
                    PATH_INFO=parsed.path,QUERY_STRING=parsed.query,REQUEST_METHOD=self.command,
                    CONTENT_TYPE=self.headers.get('Content-Type',''),REMOTE_USER='fixture',
                    HTTP_GIT_PROTOCOL=self.headers.get('Git-Protocol',''))
                length=int(self.headers.get('Content-Length','0'))
                environment['CONTENT_LENGTH']=str(length)
                result=subprocess.run(['git','http-backend'],input=self.rfile.read(length),env=environment,capture_output=True,timeout=20)
                headers,_,body=result.stdout.partition(b'\r\n\r\n')
                lines=[line.decode().split(':',1) for line in headers.split(b'\r\n') if b':' in line]
                code=next((int(v.strip().split()[0]) for k,v in lines if k.lower()=='status'),200)
                self.send_response(code)
                for k,v in lines:
                    if k.lower()!='status':self.send_header(k,v.strip())
                self.end_headers();self.wfile.write(body)
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);context.load_cert_chain(cert,key)
        self.server.socket=context.wrap_socket(self.server.socket,server_side=True)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.addCleanup(self.stop_server)
        authority='127.0.0.1:'+str(self.server.server_port)
        self.write_config({f'https://{authority}/team/{name}.git':{'token_file':str(self.token)} for name in ('main','sub')})
        sub=self.root/'source-sub';self.git('init','-b','main',str(sub));(sub/'hello').write_text('submodule data')
        self.git('-C',str(sub),'add','.');self.git('-C',str(sub),'commit','-m','fixture')
        self.git('clone','--bare',str(sub),str(self.repos/'team/sub.git'))
        main=self.root/'source-main';self.git('init','-b','main',str(main))
        self.git('-C',str(main),'-c','protocol.file.allow=always','submodule','add',str(sub),'nested')
        self.git('-C',str(main),'config','-f','.gitmodules','submodule.nested.url','git@127.0.0.1:team/sub.git')
        self.git('-C',str(main),'add','.');self.git('-C',str(main),'commit','-m','fixture')
        self.git('clone','--bare',str(main),str(self.repos/'team/main.git'))

    def stop_server(self):
        self.server.shutdown();self.server.server_close();self.thread.join()

    def git(self,*args):
        return subprocess.run(['git',*args],env=self.env,text=True,capture_output=True,check=True)

    def test_private_recursive_clone_uses_token_with_ssh_urls_and_no_persisted_secret(self):
        from obt.git import Clone
        output=io.StringIO();dest=self.root/'clone'
        with patch.dict(os.environ,self.env,clear=True),redirect_stdout(output):
            self.assertTrue(Clone('git@127.0.0.1:team/main.git',dest,rev='main',recursive=True,cache=False))
        self.assertEqual((dest/'nested/hello').read_text(),'submodule data')
        self.assertTrue(any('/sub.git/' in p for p in self.requests))
        self.assertNotIn(self.token.read_text(),output.getvalue())
        for path in (dest/'.git').rglob('config'):
            self.assertNotIn(self.token.read_text(),path.read_text())
            self.assertNotIn(str(self.config),path.read_text())
        self.assertEqual(self.git('-C',str(dest),'config','--get','remote.origin.url').stdout.strip(),'git@127.0.0.1:team/main.git')

    def test_runtime_child_and_async_fetches_inherit_authentication(self):
        destination=self.root/'dynamic'
        script='from pathlib import Path;import sys;from obt.git import Clone;sys.exit(0 if Clone(sys.argv[1],Path(sys.argv[2]),rev="main",cache=False,shallow=True) else 1)'
        command=[sys.executable,'-c',script,'git@127.0.0.1:team/main.git',str(destination)]
        self.assertEqual(Command(command,environment=self.env,do_log=False).exec(),0)
        self.assertTrue((destination/'.git').is_dir())
        async_command=[sys.executable,'-c',script,'git@127.0.0.1:team/main.git',str(self.root/'async')]
        handle=runasync2(async_command,environment=self.env)
        self.assertEqual(handle.future.result(timeout=30),0)

    def test_unconfigured_private_repository_does_not_receive_token(self):
        marker=self.root/'unexpected-prompt'
        askpass=self.root/'ambient-askpass'
        askpass.write_text('#!/bin/sh\ntouch '+shlex.quote(str(marker))+'\nexit 1\n');askpass.chmod(0o700)
        environment=dict(self.env,GIT_ASKPASS=str(askpass),SSH_ASKPASS=str(askpass))
        result=subprocess.run(['git','ls-remote','git@127.0.0.1:team/other.git'],env=git_auth.environment(environment),text=True,capture_output=True,timeout=20)
        self.assertNotEqual(result.returncode,0)
        self.assertFalse(marker.exists())
        self.assertFalse(any('/other.git/' in p for p in self.requests))
        self.assertNotIn(self.token.read_text(),result.stderr)

    def test_checkout_update_authenticates_its_pull_without_generic_runner_hooks(self):
        from obt.git import Clone,checkout_update
        dest=self.root/'updated'
        with patch.dict(os.environ,self.env,clear=True):
            self.assertTrue(Clone('git@127.0.0.1:team/main.git',dest,rev='main',cache=False))
        source=self.root/'source-main';(source/'update').write_text('new commit')
        self.git('-C',str(source),'add','.');self.git('-C',str(source),'commit','-m','update')
        self.git('-C',str(source),'push',str(self.repos/'team/main.git'),'main')
        with patch.dict(os.environ,self.env,clear=True):self.assertTrue(checkout_update(dest,'main'))
        self.assertEqual((dest/'update').read_text(),'new commit')


if __name__=='__main__':
    unittest.main()
