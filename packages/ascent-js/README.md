# ascent-wire (JavaScript)

Browser / Node codec for the ASCENT wire standard (2.1.0), including SkyPulse PATHHINT.

## Install

```bash
npm install ascent-wire
```

https://www.npmjs.com/package/ascent-wire

From monorepo: `cd packages/ascent-js && npm test`

## API

```js
const { AscentCodec, AscentRS, AscentDLab } = require("ascent-wire");

const wire = AscentCodec.encodeText("Hello, Universe.\n", {
  header: true,
  roleName: "guide",
  nonAscii: "v",
});
const events = AscentCodec.decodeStream(wire);
const hint = AscentCodec.canonicalPathhintBytes(false);
const frame = AscentDLab.encodeP9(wire);
```

PATHHINT is a LEO goodput/CCA hint, not an RF Mbps upgrade. Prefer
`AscentCodec.recommendIntegrity("ASCENT-E-LEO")` on Starlink IP (no P9 RS).

Sources stay in lockstep with `site/public/` via `npm run sync-from-site`.

## Golden lock

```bash
node ../../tests/run_js_lock.js
```

Must stay bit-identical with Python `ref/` packing.
