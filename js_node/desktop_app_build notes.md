
**1. Install Rust + Cargo**
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env   # or restart your terminal
rustc --version       # verify
```

**2. Install Xcode Command Line Tools** (if you haven't already)
```bash
xcode-select --install
```

**3. Add Tauri CLI**
```bash
npm install -D @tauri-apps/cli
```

**4. Initialize Tauri in your project**
```bash
npx tauri init
```
It'll ask a few questions — the important ones:
- *Where are your web assets?* → `../dist`
- *What is your dev server URL?* → `http://localhost:4566`
- *What is your frontend dev command?* → `npm run dev`
- *What is your frontend build command?* → `npm run build`

**5. Build the final app**
```bash
npx tauri build
# → produces a .app (and .dmg installer) under js_node-tauri/target/release/bundle/
```

---

One thing to be aware of: Tauri's webview on macOS uses **WKWebView** (Safari engine). If you hit any AWS SDK quirks, add this to `src-tauri/tauri.conf.json` under `app.security`:

```json
"csp": null
```

That disables the default Content Security Policy which can block the SDK's requests during development.