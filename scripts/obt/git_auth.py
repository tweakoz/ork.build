"""Opt-in, file-backed Git credentials. No tokens in argv, environment or URLs."""
import hashlib
import json
import os
from pathlib import Path
import shlex
import stat
import sys
from urllib.parse import urlsplit

AUTH_FILE = 'OBT_GIT_AUTH_FILE'
_MARKER = '_OBT_GIT_AUTH_CONFIG'


def _private_file(filename, limit):
    path = Path(filename).expanduser()
    if not path.is_absolute() or any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('Git authentication files must be absolute, without symlinks')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise ValueError('Git authentication files must be owned by this user, mode 0600')
        if not 1 <= info.st_size <= limit:
            raise ValueError('Git authentication file exceeds its size limit')
        data = stream.read(limit + 1)
        if len(data) > limit:
            raise ValueError('Git authentication file exceeds its size limit')
        return data


def _repository(url):
    parsed = urlsplit(url)
    if (parsed.scheme != 'https' or not parsed.hostname or parsed.username is not None
            or parsed.password is not None or parsed.query or parsed.fragment
            or any(c.isspace() for c in url)):
        raise ValueError('Git authentication requires credential-free HTTPS repository URLs')
    # Access is exact-repository, including the host/port. Ignore the optional .git suffix.
    authority = parsed.hostname.lower() + ((':' + str(parsed.port)) if parsed.port and parsed.port != 443 else '')
    path = parsed.path.strip('/')
    if path.endswith('.git'):
        path = path[:-4]
    if not path or any(p in ('', '.', '..') for p in path.split('/')) or any(c in path for c in '\\%\0'):
        raise ValueError('Invalid Git authentication repository path')
    return authority, path


def _configuration(env):
    filename = env.get(AUTH_FILE)
    if not filename:
        return {}, None
    raw = _private_file(filename, 262144)
    entries = json.loads(raw)
    if not isinstance(entries, dict) or not 1 <= len(entries) <= 256:
        raise ValueError('Git authentication configuration must map repository URLs to token files')
    result = {}
    authorities = {}
    for url, credential in entries.items():
        key = _repository(url)
        if key in result:
            raise ValueError('Duplicate Git authentication repository')
        if not isinstance(credential, dict) or set(credential) - {'token_file', 'username'} or 'token_file' not in credential:
            raise ValueError('Git authentication entries require token_file and optional username')
        username = credential.get('username', 'x-access-token')
        if not isinstance(username, str) or not username or any(c in username for c in '\r\n\0'):
            raise ValueError('Invalid Git authentication username')
        if not isinstance(credential['token_file'], str):
            raise ValueError('Git token_file must be a filename')
        authority = key[0]
        host = urlsplit(url).hostname.lower()
        if host in authorities and authorities[host] != authority:
            raise ValueError('Use one HTTPS port per Git authentication host')
        authorities[host] = authority
        result[key] = dict(username=username, token_file=credential['token_file'])
    marker = hashlib.sha256((str(Path(filename).expanduser()) + '\0').encode() + raw).hexdigest()
    return result, marker


def environment(env):
    """Configure Git for this child process and its descendants, without global edits."""
    entries, marker = _configuration(env)
    if not entries or env.get(_MARKER) == marker:
        return env
    result = dict(env)
    count = int(result.get('GIT_CONFIG_COUNT', '0'))
    if not 0 <= count <= 4096:
        raise ValueError('Invalid inherited Git configuration count')
    program = shlex.join([sys.executable, '-I', str(Path(__file__).resolve())])
    helper = '!' + program
    settings = [('credential.helper', ''), ('credential.helper', helper),
                ('credential.useHttpPath', 'true'), ('http.followRedirects', 'false'),
                ('http.sslVerify', 'true')]
    for authority in sorted({key[0] for key in entries}):
        host = urlsplit('https://' + authority).hostname
        for prefix in ('git@' + host + ':', 'ssh://git@' + host + '/', 'ssh://git@' + host + ':22/'):
            settings.append(('url.https://' + authority + '/.insteadOf', prefix))
    for key, value in settings:
        result['GIT_CONFIG_KEY_' + str(count)] = key
        result['GIT_CONFIG_VALUE_' + str(count)] = value
        count += 1
    result.update(GIT_CONFIG_COUNT=str(count), GIT_TERMINAL_PROMPT='0', GIT_ASKPASS=program + ' askpass',
                  GIT_TRACE_REDACT='1', GIT_TRACE_CURL='0')
    result[_MARKER] = marker
    result.pop('GIT_SSL_NO_VERIFY', None)
    result.pop('GIT_CURL_VERBOSE', None)
    return result


def configured_for(url, env=None):
    env = os.environ if env is None else env
    entries, _ = _configuration(env)
    if url.startswith('git@') and ':' in url:
        host, path = url[4:].split(':', 1)
        url = 'https://' + host + '/' + path
    elif url.startswith('ssh://git@'):
        parsed = urlsplit(url)
        url = 'https://' + parsed.hostname + parsed.path
    return bool(entries) and _repository(url) in entries


def credential(fields, env=None):
    entries, _ = _configuration(os.environ if env is None else env)
    if fields.get('protocol') != 'https' or not fields.get('host') or not fields.get('path'):
        return {}
    path = fields['path']
    # Git LFS requests credentials for its repository's own HTTPS endpoint.
    if '/info/lfs' in path:
        repository, endpoint = path.split('/info/lfs', 1)
        if not endpoint or endpoint.startswith('/'):
            path = repository
    entry = entries.get(_repository('https://' + fields['host'] + '/' + path))
    if entry is None:
        return {}
    token = _private_file(entry['token_file'], 8192).decode('utf-8').strip()
    if not token or any(c.isspace() or c == '\0' for c in token):
        raise ValueError('Invalid Git fetch token file')
    return dict(username=entry['username'], password=token)


def main():
    # Git appends get/store/erase to the configured helper command. Never store credentials.
    if sys.argv[1:2] == ['askpass']:
        return 1
    if sys.argv[1:] != ['get']:
        return 0
    try:
        raw = sys.stdin.buffer.read(16385)
        if len(raw) > 16384:
            raise ValueError('Git credential request exceeds its size limit')
        fields = dict(line.split('=', 1) for line in raw.decode().splitlines() if '=' in line)
        for key, value in credential(fields).items():
            print(key + '=' + value)
    except (OSError, ValueError, TypeError, UnicodeError):
        print('OBT: Git authentication configuration or token is unavailable', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
