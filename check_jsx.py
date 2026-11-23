"""
JSX / JavaScript Syntax Validation for Nexus-Pulse Enterprise GUI
Verifies ui/js/app.js using Babel Standalone via Node.js
"""
import subprocess
import sys
import os

NODE_SCRIPT = """
const https = require('https');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const cacheFile = path.join(__dirname, '.babel-standalone.cache.js');

function loadBabel(cb) {
  if (fs.existsSync(cacheFile)) {
    const data = fs.readFileSync(cacheFile, 'utf8');
    const sandbox = { window: {}, console: console };
    vm.createContext(sandbox);
    vm.runInContext(data, sandbox);
    return cb(null, sandbox.Babel || sandbox.window.Babel);
  }
  
  https.get('https://cdnjs.cloudflare.com/ajax/libs/babel-standalone/7.24.4/babel.min.js', (res) => {
    let data = '';
    res.on('data', chunk => data += chunk);
    res.on('end', () => {
      try {
        fs.writeFileSync(cacheFile, data, 'utf8');
      } catch (e) {}
      const sandbox = { window: {}, console: console };
      vm.createContext(sandbox);
      vm.runInContext(data, sandbox);
      cb(null, sandbox.Babel || sandbox.window.Babel);
    });
  }).on('error', cb);
}

loadBabel((err, Babel) => {
  if (err) {
    console.error('Failed to load Babel:', err.message);
    process.exit(1);
  }
  
  const appPath = path.join(__dirname, 'ui', 'js', 'app.js');
  const code = fs.readFileSync(appPath, 'utf8');
  try {
    const res = Babel.transform(code, { presets: ['react'] });
    console.log(`[PASS] ui/js/app.js syntax & JSX verified clean (${res.code.length} bytes transpiled)`);
    process.exit(0);
  } catch (parseErr) {
    console.error('[FAIL] JSX/Syntax Error in ui/js/app.js:');
    console.error(parseErr.message);
    if (parseErr.loc) {
      console.error(`Line: ${parseErr.loc.line}, Column: ${parseErr.loc.column}`);
    }
    process.exit(1);
  }
});
"""

def main():
    print("Checking Nexus-Pulse React JSX syntax...")
    result = subprocess.run(["node", "-e", NODE_SCRIPT], cwd=os.path.dirname(os.path.abspath(__file__)))
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
