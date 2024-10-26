/**
 * Minified by jsDelivr using Terser v5.17.1.
 * Original file: /npm/@popperjs/core@2.11.8/dist/esm/popper.js#
 *
 * Popper (now floating-ui) licensed under MIT
 *
 * MIT License
 *
 * Copyright (c) 2021 Floating UI contributors
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 *
 * Do NOT use SRI with dynamically generated files! More information: https://www.jsdelivr.com/using-sri-with-dynamic-files
 */
import{popperGenerator,detectOverflow}from"./createPopper.js";import eventListeners from"./modifiers/eventListeners.js";import popperOffsets from"./modifiers/popperOffsets.js";import computeStyles from"./modifiers/computeStyles.js";import applyStyles from"./modifiers/applyStyles.js";import offset from"./modifiers/offset.js";import flip from"./modifiers/flip.js";import preventOverflow from"./modifiers/preventOverflow.js";import arrow from"./modifiers/arrow.js";import hide from"./modifiers/hide.js";var defaultModifiers=[eventListeners,popperOffsets,computeStyles,applyStyles,offset,flip,preventOverflow,arrow,hide],createPopper=popperGenerator({defaultModifiers:defaultModifiers});export{createPopper,popperGenerator,defaultModifiers,detectOverflow};export{createPopper as createPopperLite}from"./popper-lite.js";export*from"./modifiers/index.js";
//# sourceMappingURL=/sm/eaecbcde251f0941e657c718d2ce2b9b573d7fb10f7c1e5a253536955e488005.map