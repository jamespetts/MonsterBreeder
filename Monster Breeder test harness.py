# SPDX-License-Identifier: GPL-3.0-only
from pathlib import Path
import json
import re
import subprocess
import sys
import tempfile


def FindHtmlPath():
    if len(sys.argv) > 1:
        return Path(sys.argv[1])
    candidates = [
        Path('monster_breeder_round_end_stats_20260704.html'),
        Path('monster_breeder_fixes_20260703_2315.html'),
        Path('monster_breeder_round_season_pathfinding_20260703.html'),
        Path('index.html'),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[-1]


def ExtractScripts(html):
    workerMatch = re.search(r'<script\s+id="simulationWorkerSource"[^>]*>(.*?)</script>', html, flags=re.S | re.I)
    if not workerMatch:
        raise SystemExit('Could not find simulationWorkerSource script block')
    scripts = re.findall(r'<script([^>]*)>(.*?)</script>', html, flags=re.S | re.I)
    normalScripts = [content for attrs, content in scripts if 'simulationWorkerSource' not in attrs]
    if not normalScripts:
        raise SystemExit('Could not find main browser script block')
    return workerMatch.group(1), normalScripts[-1]


def RunNodeCheck(path):
    result = subprocess.run(['node', '--check', str(path)], capture_output=True, text=True, timeout=15)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def RunWorkerRegression(workerPath):
    # Keep this harness deliberately short. It is a fast smoke/regression gate
    # intended to finish comfortably in constrained Copilot/container runs.
    # Large-map and long-raid soak tests should be separate opt-in diagnostics.
    nodeSource = r'''
const fs = require('fs');
const vm = require('vm');
const code = fs.readFileSync(process.argv[2], 'utf8');
const messages = [];
const context = { console, setInterval, clearInterval, Date, Math, Object, Array, Number, String, Boolean, JSON };
context.self = { postMessage: (message) => messages.push(message) };
context.globalThis = context;
vm.createContext(context);
vm.runInContext(code, context, { filename: 'simulationWorkerSource.js' });
messages.length = 0;
context.self.onmessage({ data: { protocolVersion: 1, messageId: 'regression', type: 'RUN_HEADLESS_TESTS', payload: { count: 1, seed: 100000, maxTicks: 180 } } });
const result = messages.find((message) => message.type === 'HEADLESS_TEST_RESULTS');
if (!result) {
    console.error(JSON.stringify(messages, null, 2));
    process.exit(2);
}
console.log(JSON.stringify({ regressionTests: result.payload.regressionTests, endedCount: result.payload.endedCount, timedOutCount: result.payload.timedOutCount }, null, 2));
if (!result.payload.regressionTests || !result.payload.regressionTests.passed) {
    process.exit(3);
}
'''
    runner = Path('monster_breeder_node_regression_runner_20260703_2327.js')
    runner.write_text(nodeSource, encoding='utf-8')
    result = subprocess.run(['node', str(runner), str(workerPath)], capture_output=True, text=True, timeout=60)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    if result.returncode != 0:
        raise SystemExit(result.returncode)



def RunMainRendererSmokeTest(workerPath, mainPath):
    # Renderer smoke test should stay below roughly 30 seconds. It uses one
    # legacy-size world and one animation frame only; do not expand this into a
    # large-map renderer benchmark in the default harness.
    nodeSource = r'''
const fs = require('fs');
const vm = require('vm');
const workerSource = fs.readFileSync(process.argv[2], 'utf8');
const mainSource = fs.readFileSync(process.argv[3], 'utf8');
function makeElement(id) {
    return {
        id,
        style: {},
        classList: {
            values: new Set(),
            add(value) { this.values.add(value); },
            remove(value) { this.values.delete(value); },
            contains(value) { return this.values.has(value); },
            toggle(value, force) {
                if (force === undefined) {
                    if (this.values.has(value)) { this.values.delete(value); return false; }
                    this.values.add(value); return true;
                }
                if (force) { this.values.add(value); } else { this.values.delete(value); }
                return !!force;
            }
        },
        children: [],
        appendChild(child) { this.children.push(child); },
        prepend(child) { this.children.unshift(child); },
        removeChild(child) {},
        querySelector() { return makeElement('query'); },
        getBoundingClientRect() { return { width: 960, height: 540, left: 0, top: 0 }; },
        addEventListener() {},
        setAttribute(key, value) { this[key] = value; },
        removeAttribute(key) { delete this[key]; },
        focus() {},
        set textContent(value) { this._textContent = value; },
        get textContent() { return this._textContent || ''; },
        set innerHTML(value) { this._innerHTML = value; },
        get innerHTML() { return this._innerHTML || ''; },
        disabled: false,
        value: 'standard'
    };
}
const canvas = makeElement('raidCanvas');
canvas.width = 960;
canvas.height = 540;
const operations = [];
const ctx = new Proxy({}, {
    get(target, prop) {
        if (prop === 'canvas') { return canvas; }
        if (!(prop in target)) {
            target[prop] = (...args) => { operations.push([prop, ...args]); };
        }
        return target[prop];
    },
    set(target, prop, value) { target[prop] = value; return true; }
});
canvas.getContext = () => ctx;
const elements = { raidCanvas: canvas, simulationWorkerSource: { textContent: workerSource } };
const document = {
    getElementById(id) { if (!elements[id]) { elements[id] = makeElement(id); } return elements[id]; },
    createElement(tag) { return makeElement(tag); },
    querySelector() { return makeElement('query'); }
};
const mainWorkers = [];
class WorkerStub {
    constructor() { mainWorkers.push(this); }
    postMessage(message) { this.lastPost = message; }
}
let frameCallback = null;
const mainContext = {
    console,
    document,
    window: { innerWidth: 1280, innerHeight: 800, addEventListener() {} },
    Blob: function () {},
    URL: { createObjectURL() { return 'blob:renderer-test'; } },
    Worker: WorkerStub,
    requestAnimationFrame(callback) { frameCallback = callback; },
    Set, Math, Date, JSON, Number, String, Boolean, Object, Array,
    performance: { now: () => 1000 }
};
vm.createContext(mainContext);
vm.runInContext(mainSource, mainContext, { filename: 'mainBrowserScript.js' });
const workerMessages = [];
const workerContext = { console, setInterval() {}, clearInterval() {}, Date, Math, Object, Array, Number, String, Boolean, JSON };
workerContext.self = { postMessage: (message) => workerMessages.push(message) };
workerContext.globalThis = workerContext;
vm.createContext(workerContext);
vm.runInContext(workerSource, workerContext, { filename: 'simulationWorkerSource.js' });
workerMessages.length = 0;
workerContext.self.onmessage({ data: { protocolVersion: 1, messageId: 'renderer-smoke', type: 'NEW_WORLD', payload: { seed: 834930943, mode: 'quick', worldOptions: { mapSizeKey: 'legacy', customTreasureAmounts: { bronze: 55 } } } } });
if (!mainWorkers[0] || typeof mainWorkers[0].onmessage !== 'function') {
    throw new Error('Main renderer did not register a worker onmessage handler');
}
for (const message of workerMessages) {
    mainWorkers[0].onmessage({ data: message });
}
operations.length = 0;
if (typeof frameCallback !== 'function') {
    throw new Error('Main renderer did not register an animation frame callback');
}
frameCallback(1100);
const pathCount = operations.filter((operation) => operation[0] === 'beginPath').length;
const fillCount = operations.filter((operation) => operation[0] === 'fill' || operation[0] === 'fillRect').length;
const result = { operations: operations.length, pathCount, fillCount, workerMessages: workerMessages.map((message) => message.type) };
console.log(JSON.stringify(result, null, 2));
if (operations.length < 50 || pathCount < 10 || fillCount < 10) {
    throw new Error('Renderer smoke test did not draw enough terrain operations: ' + JSON.stringify(result));
}
'''
    runner = Path('monster_breeder_main_renderer_smoke_20260705_1140.js')
    runner.write_text(nodeSource, encoding='utf-8')
    result = subprocess.run(['node', str(runner), str(workerPath), str(mainPath)], capture_output=True, text=True, timeout=30)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    if result.returncode != 0:
        raise SystemExit(result.returncode)

def StaticDomChecks(html):
    required = [
        'id="resumeGameMenuButton"',
        'function DrawTreasurePile',
        "kind:'droppedTreasure'",
        'function RunRegressionTests()',
        'class MicrofaunaEmitter',
        'getTreasureBreakdown(extraLooseTreasure)',
        'function FormatEndOfRoundStats',
        'function SeasonNameForSnapshot',
        'Food expenditure does not remove physical treasure units',
        'Knights are not deterred by lower-class adventurers failing to return alive',
    ]
    missing = [text for text in required if text not in html]
    if missing:
        raise SystemExit('Static checks failed; missing: ' + ', '.join(missing))


def main():
    htmlPath = FindHtmlPath()
    html = htmlPath.read_text(encoding='utf-8')
    StaticDomChecks(html)
    workerSource, mainSource = ExtractScripts(html)
    workerPath = Path('monster_breeder_extracted_worker_regression_20260703_2327.js')
    mainPath = Path('monster_breeder_extracted_main_regression_20260703_2327.js')
    workerPath.write_text(workerSource, encoding='utf-8')
    mainPath.write_text(mainSource, encoding='utf-8')
    RunNodeCheck(workerPath)
    RunNodeCheck(mainPath)
    RunMainRendererSmokeTest(workerPath, mainPath)
    RunWorkerRegression(workerPath)
    print('All syntax and regression checks passed:', htmlPath)


if __name__ == '__main__':
    main()
