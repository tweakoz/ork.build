# File-backed Git fetch tokens

OBT can use read-only GitHub/Gitea HTTPS tokens while dependency definitions keep
their existing SSH-style Git URLs. This is opt-in: without `OBT_GIT_AUTH_FILE`,
existing SSH/key and public tarball behavior is unchanged. No additional package,
gateway or background service is required.

Create a private JSON file mapping exact HTTPS repository URLs to token files:

```json
{
  "https://github.com/example/private-library.git": {
    "token_file": "/private/credentials/github-read.token"
  },
  "https://git.example.org/team/engine.git": {
    "username": "build-reader",
    "token_file": "/private/credentials/gitea-read.token"
  }
}
```

Use absolute filenames, owned by the build user, mode `0600`, without symlinks.
Each token file contains just the token (a final newline is fine). GitHub's
default username is `x-access-token`; set the provider account name for Gitea.
One token file may serve several mapped repositories; different repositories can
use different tokens, including on the same host. Optional `.git` suffixes match
the same repository. URLs must not contain credentials, queries or fragments.

```bash
chmod 600 /private/credentials/git-auth.json /private/credentials/*.token
export OBT_GIT_AUTH_FILE=/private/credentials/git-auth.json
obt.env.create.py --stagedir /build/stage --pipeline
# Or use an already initialized stage:
obt.env.launch.py --stagedir /build/stage --project /src/engine \
  --command 'ork.build.py'
```

OBT's Git fetch/update code passes ordinary Git configuration explicitly when
constructing Git commands. The generic command runner is unchanged. Git rewrites
`git@HOST:path` and `ssh://git@HOST/path` (also explicit SSH port 22) to HTTPS for
configured hosts. Git's child processes, including recursive submodules, inherit that
configuration. Git's credential helper reads a token only for an exact mapped
repository, including its own LFS endpoint. Public repositories on those hosts
can still fetch anonymously; private repositories not in the map fail without
receiving a token or prompting. Use canonical URLs; authenticated redirects are
disabled. Custom certificate authorities can use Git's normal `GIT_SSL_CAINFO`;
TLS verification remains enabled. SSH host aliases/custom SSH ports are not
inferred; use a canonical provider URL for those cases.

OBT dependency fetches continue to authenticate when invoked during a build.
Custom fetchers that invoke Git directly can opt in at that Git call site:

```python
import os, subprocess
from obt import git_auth
subprocess.run(["git", "fetch", "origin"],
               env=git_auth.environment(os.environ), check=True)
```

Non-Git commands and unrelated build processes do not receive automatic Git
configuration. Custom build systems that fetch internally must explicitly opt
in at their own source-fetch boundary.

GitHub's tarball shortcut uses the existing Git clone path when the requested
repository has a token mapping, so private dependencies authenticate through the
same helper. Public tarball downloads are unchanged. Normal, shallow, cached and
recursive Git fetches keep their existing OBT behavior.

Tokens are never embedded in URLs, command arguments, environment values, Git
configuration or keychain storage. The environment contains the configuration
filename and helper settings only; helper output goes to Git's credential pipe.
Token rotation is picked up on the next credential request. OBT does not copy
these files into the stage or generated launch scripts; CI/callers supply them
per job and remove them afterward. Build code running as that user can read the
files while they exist, so use trusted builds and narrowly scoped read-only
tokens. This feature does not provide credential isolation from build code.
