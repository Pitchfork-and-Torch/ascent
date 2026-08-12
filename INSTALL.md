# Install ASCENT

**SPEC:** 1.0.0-rc1 · **Nexus / packages:** 2.1.0 · MIT

## Python (`ascent-wire`)

### Recommended: PyPI

```bash
pip install ascent-wire
ascent self-test
ascent encode --header --role guide "Hello, Universe."
```

Project: https://pypi.org/project/ascent-wire/

Optional deep-space RS support:

```bash
pip install "ascent-wire[deep-space]"
# or: pip install reedsolo
```

### GitHub Release wheel / git

```bash
# Release asset
pip install ascent_wire-2.1.0-py3-none-any.whl

# From git tag
pip install "git+https://github.com/Pitchfork-and-Torch/ascent.git@v2.1.0"
```

### Editable clone

```bash
git clone https://github.com/Pitchfork-and-Torch/ascent.git
cd ascent
pip install -e ".[deep-space]"
python -m ascent self-test
```

### Import

```python
from ascent import encode_text, decode_stream, hello_universe_bytes
print(hello_universe_bytes().hex()[:32])
```

## JavaScript (`ascent-wire` on npm)

```bash
npm install ascent-wire
```

```js
const { AscentCodec, AscentRS, AscentDLab } = require("ascent-wire");
const wire = AscentCodec.encodeText("Hello, Universe.\n", {
  header: true,
  roleName: "guide",
  nonAscii: "v",
});
console.log(AscentCodec.hexOf(wire));
```

https://www.npmjs.com/package/ascent-wire

Monorepo path (same sources): `packages/ascent-js`  
Live lab: https://ascent.jonbailey.xyz/

## Golden lock

```bash
set PYTHONPATH=ref
python tests/test_ascent_codec.py
node tests/run_js_lock.js
```

## Registries

| Registry | Status |
|----------|--------|
| **PyPI** `ascent-wire` | **In-repo 2.1.0** (publish on Jon release) |
| **npm** `ascent-wire` | **In-repo 2.1.0** (publish on Jon release) |
| GitHub Releases | Wheel + sdist also attached |
| Trusted Publishing | `.github/workflows/publish-pypi.yml` (OIDC on release) |

Re-publish helper: `scripts/publish-packages.ps1`

### Future releases (no Desktop tokens)

If PyPI Trusted Publisher is linked to this repo:

1. Bump `version` in `pyproject.toml`
2. `git tag` + `gh release create`
3. Workflow `publish-pypi` uploads to PyPI via OIDC

Configure on pypi.org: Project → Settings → Trusted publishers  
Owner `Pitchfork-and-Torch`, repo `ascent`, workflow `publish-pypi.yml`, environment `pypi`.
