// tools/reading-order/node_modules/@preact/signals-core/dist/signals-core.module.js
var i = /* @__PURE__ */ Symbol.for("preact-signals");
function t() {
  if (!(v > 1)) {
    var i2, t2 = false;
    !(function() {
      var i3 = c;
      c = void 0;
      while (void 0 !== i3) {
        var t3 = i3.S;
        if (t3.v === i3.v) {
          for (var n3 = t3.t; void 0 !== n3; n3 = n3.x) if (n3.i === i3.i) n3.i = t3.i;
        }
        i3 = i3.o;
      }
    })();
    while (void 0 !== h) {
      var n2 = h;
      h = void 0;
      s++;
      while (void 0 !== n2) {
        var r2 = n2.u;
        n2.u = void 0;
        n2.f &= -3;
        if (!(8 & n2.f) && w(n2)) try {
          n2.c();
        } catch (n3) {
          if (!t2) {
            i2 = n3;
            t2 = true;
          }
        }
        n2 = r2;
      }
    }
    s = 0;
    v--;
    if (t2) throw i2;
  } else v--;
}
function n(i2) {
  if (v > 0) return i2();
  e = ++u;
  v++;
  try {
    return i2();
  } finally {
    t();
  }
}
var r;
var o = void 0;
function f(i2) {
  var t2 = o, n2 = r;
  o = void 0;
  r = void 0;
  try {
    return i2();
  } finally {
    o = t2;
    r = n2;
  }
}
var h = void 0;
var v = 0;
var s = 0;
var u = 0;
var e = 0;
var c = void 0;
var d = 0;
function a(i2) {
  if (void 0 !== o) {
    var t2 = i2.n;
    if (void 0 === t2 || t2.t !== o) {
      t2 = { i: 0, S: i2, p: o.s, n: void 0, t: o, e: void 0, x: void 0, r: t2 };
      if (void 0 !== o.s) o.s.n = t2;
      o.s = t2;
      i2.n = t2;
      if (32 & o.f) i2.S(t2);
      return t2;
    } else if (-1 === t2.i) {
      t2.i = 0;
      if (void 0 !== t2.n) {
        t2.n.p = t2.p;
        if (void 0 !== t2.p) t2.p.n = t2.n;
        t2.p = o.s;
        t2.n = void 0;
        o.s.n = t2;
        o.s = t2;
      }
      return t2;
    }
  }
}
function l(i2, t2) {
  this.v = i2;
  this.i = 0;
  this.n = void 0;
  this.t = void 0;
  this.l = 0;
  this.W = null == t2 ? void 0 : t2.watched;
  this.Z = null == t2 ? void 0 : t2.unwatched;
  this.name = null == t2 ? void 0 : t2.name;
}
l.prototype.brand = i;
l.prototype.h = function() {
  return true;
};
l.prototype.S = function(i2) {
  var t2 = this, n2 = this.t;
  if (n2 !== i2 && void 0 === i2.e) {
    i2.x = n2;
    this.t = i2;
    if (void 0 !== n2) n2.e = i2;
    else f(function() {
      var i3;
      null == (i3 = t2.W) || i3.call(t2);
    });
  }
};
l.prototype.U = function(i2) {
  var t2 = this;
  if (void 0 !== this.t) {
    var n2 = i2.e, r2 = i2.x;
    if (void 0 !== n2) {
      n2.x = r2;
      i2.e = void 0;
    }
    if (void 0 !== r2) {
      r2.e = n2;
      i2.x = void 0;
    }
    if (i2 === this.t) {
      this.t = r2;
      if (void 0 === r2) f(function() {
        var i3;
        null == (i3 = t2.Z) || i3.call(t2);
      });
    }
  }
};
l.prototype.subscribe = function(i2) {
  var t2 = this;
  return j(function() {
    var n2 = t2.value;
    f(function() {
      return i2(n2);
    });
  }, { name: "sub" });
};
l.prototype.valueOf = function() {
  return this.value;
};
l.prototype.toString = function() {
  return this.value + "";
};
l.prototype.toJSON = function() {
  return this.value;
};
l.prototype.peek = function() {
  var i2 = this;
  return f(function() {
    return i2.value;
  });
};
Object.defineProperty(l.prototype, "value", { get: function() {
  var i2 = a(this);
  if (void 0 !== i2) i2.i = this.i;
  return this.v;
}, set: function(i2) {
  if (i2 !== this.v) {
    if (s > 100) throw new Error("Cycle detected");
    !(function(i3) {
      if (0 !== v && 0 === s) {
        if (i3.l !== e) {
          i3.l = e;
          c = { S: i3, v: i3.v, i: i3.i, o: c };
        }
      }
    })(this);
    this.v = i2;
    this.i++;
    d++;
    v++;
    try {
      for (var n2 = this.t; void 0 !== n2; n2 = n2.x) n2.t.N();
    } finally {
      t();
    }
  }
} });
function y(i2, t2) {
  return new l(i2, t2);
}
function w(i2) {
  for (var t2 = i2.s; void 0 !== t2; t2 = t2.n) if (t2.S.i !== t2.i || !t2.S.h() || t2.S.i !== t2.i) return true;
  return false;
}
function _(i2) {
  for (var t2 = i2.s; void 0 !== t2; t2 = t2.n) {
    var n2 = t2.S.n;
    if (void 0 !== n2) t2.r = n2;
    t2.S.n = t2;
    t2.i = -1;
    if (void 0 === t2.n) {
      i2.s = t2;
      break;
    }
  }
}
function b(i2) {
  var t2 = i2.s, n2 = void 0;
  while (void 0 !== t2) {
    var r2 = t2.p;
    if (-1 === t2.i) {
      t2.S.U(t2);
      if (void 0 !== r2) r2.n = t2.n;
      if (void 0 !== t2.n) t2.n.p = r2;
    } else n2 = t2;
    t2.S.n = t2.r;
    if (void 0 !== t2.r) t2.r = void 0;
    t2 = r2;
  }
  i2.s = n2;
}
function p(i2, t2) {
  l.call(this, void 0, t2);
  this.x = i2;
  this.s = void 0;
  this.g = d - 1;
  this.f = 4;
}
p.prototype = new l();
p.prototype.h = function() {
  this.f &= -3;
  if (1 & this.f) return false;
  if (32 == (36 & this.f)) return true;
  this.f &= -5;
  if (this.g === d) return true;
  this.g = d;
  this.f |= 1;
  if (this.i > 0 && !w(this)) {
    this.f &= -2;
    return true;
  }
  var i2 = o;
  try {
    _(this);
    o = this;
    var t2 = this.x();
    if (16 & this.f || this.v !== t2 || 0 === this.i) {
      this.v = t2;
      this.f &= -17;
      this.i++;
    }
  } catch (i3) {
    this.v = i3;
    this.f |= 16;
    this.i++;
  }
  o = i2;
  b(this);
  this.f &= -2;
  return true;
};
p.prototype.S = function(i2) {
  if (void 0 === this.t) {
    this.f |= 36;
    for (var t2 = this.s; void 0 !== t2; t2 = t2.n) t2.S.S(t2);
  }
  l.prototype.S.call(this, i2);
};
p.prototype.U = function(i2) {
  if (void 0 !== this.t) {
    l.prototype.U.call(this, i2);
    if (void 0 === this.t) {
      this.f &= -33;
      for (var t2 = this.s; void 0 !== t2; t2 = t2.n) t2.S.U(t2);
    }
  }
};
p.prototype.N = function() {
  if (!(2 & this.f)) {
    this.f |= 6;
    for (var i2 = this.t; void 0 !== i2; i2 = i2.x) i2.t.N();
  }
};
Object.defineProperty(p.prototype, "value", { get: function() {
  if (1 & this.f) throw new Error("Cycle detected");
  var i2 = a(this);
  this.h();
  if (void 0 !== i2) i2.i = this.i;
  if (16 & this.f) throw this.v;
  return this.v;
} });
function g(i2, t2) {
  return new p(i2, t2);
}
function S(i2) {
  var n2 = i2.m;
  i2.m = void 0;
  if ("function" == typeof n2) {
    v++;
    var r2 = o;
    o = void 0;
    try {
      n2();
    } catch (t2) {
      i2.f &= -2;
      i2.f |= 8;
      m(i2);
      throw t2;
    } finally {
      o = r2;
      t();
    }
  }
}
function m(i2) {
  for (var t2 = i2.s; void 0 !== t2; t2 = t2.n) t2.S.U(t2);
  i2.x = void 0;
  i2.s = void 0;
  S(i2);
}
function x(i2) {
  if (o !== this) throw new Error("Out-of-order effect");
  b(this);
  o = i2;
  this.f &= -2;
  if (8 & this.f) m(this);
  t();
}
function E(i2, t2) {
  this.x = i2;
  this.m = void 0;
  this.s = void 0;
  this.u = void 0;
  this.f = 32;
  this.name = null == t2 ? void 0 : t2.name;
  if (r) r.push(this);
}
E.prototype.c = function() {
  var i2 = this.S();
  try {
    if (8 & this.f) return;
    if (void 0 === this.x) return;
    var t2 = this.x();
    if ("function" == typeof t2) this.m = t2;
  } finally {
    i2();
  }
};
E.prototype.S = function() {
  if (1 & this.f) throw new Error("Cycle detected");
  this.f |= 1;
  this.f &= -9;
  S(this);
  _(this);
  v++;
  var i2 = o;
  o = this;
  return x.bind(this, i2);
};
E.prototype.N = function() {
  if (!(2 & this.f)) {
    this.f |= 2;
    this.u = h;
    h = this;
  }
};
E.prototype.d = function() {
  this.f |= 8;
  if (!(1 & this.f)) m(this);
};
E.prototype.dispose = function() {
  this.d();
};
function j(i2, t2) {
  var n2 = new E(i2, t2);
  try {
    n2.c();
  } catch (i3) {
    n2.d();
    throw i3;
  }
  var r2 = n2.d.bind(n2);
  r2[Symbol.dispose] = r2;
  return r2;
}

// tools/reading-order/node_modules/@dnd-kit/state/dist/index.mjs
var __create = Object.create;
var __defProp = Object.defineProperty;
var __defProps = Object.defineProperties;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropDescs = Object.getOwnPropertyDescriptors;
var __getOwnPropSymbols = Object.getOwnPropertySymbols;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __propIsEnum = Object.prototype.propertyIsEnumerable;
var __knownSymbol = (name, symbol) => (symbol = Symbol[name]) ? symbol : /* @__PURE__ */ Symbol.for("Symbol." + name);
var __typeError = (msg) => {
  throw TypeError(msg);
};
var __defNormalProp = (obj, key, value) => key in obj ? __defProp(obj, key, { enumerable: true, configurable: true, writable: true, value }) : obj[key] = value;
var __spreadValues = (a2, b2) => {
  for (var prop in b2 || (b2 = {}))
    if (__hasOwnProp.call(b2, prop))
      __defNormalProp(a2, prop, b2[prop]);
  if (__getOwnPropSymbols)
    for (var prop of __getOwnPropSymbols(b2)) {
      if (__propIsEnum.call(b2, prop))
        __defNormalProp(a2, prop, b2[prop]);
    }
  return a2;
};
var __spreadProps = (a2, b2) => __defProps(a2, __getOwnPropDescs(b2));
var __name = (target, value) => __defProp(target, "name", { value, configurable: true });
var __decoratorStart = (base) => {
  var _a23;
  return [, , , __create((_a23 = base == null ? void 0 : base[__knownSymbol("metadata")]) != null ? _a23 : null)];
};
var __decoratorStrings = ["class", "method", "getter", "setter", "accessor", "field", "value", "get", "set"];
var __expectFn = (fn) => fn !== void 0 && typeof fn !== "function" ? __typeError("Function expected") : fn;
var __decoratorContext = (kind, name, done, metadata, fns) => ({ kind: __decoratorStrings[kind], name, metadata, addInitializer: (fn) => done._ ? __typeError("Already initialized") : fns.push(__expectFn(fn || null)) });
var __decoratorMetadata = (array, target) => __defNormalProp(target, __knownSymbol("metadata"), array[3]);
var __runInitializers = (array, flags, self, value) => {
  for (var i2 = 0, fns = array[flags >> 1], n2 = fns && fns.length; i2 < n2; i2++) flags & 1 ? fns[i2].call(self) : value = fns[i2].call(self, value);
  return value;
};
var __decorateElement = (array, flags, name, decorators, target, extra) => {
  var fn, it, done, ctx, access, k = flags & 7, s2 = !!(flags & 8), p2 = !!(flags & 16);
  var j2 = k > 3 ? array.length + 1 : k ? s2 ? 1 : 2 : 0, key = __decoratorStrings[k + 5];
  var initializers = k > 3 && (array[j2 - 1] = []), extraInitializers = array[j2] || (array[j2] = []);
  var desc = k && (!p2 && !s2 && (target = target.prototype), k < 5 && (k > 3 || !p2) && __getOwnPropDesc(k < 4 ? target : { get [name]() {
    return __privateGet(this, extra);
  }, set [name](x2) {
    return __privateSet(this, extra, x2);
  } }, name));
  k ? p2 && k < 4 && __name(extra, (k > 2 ? "set " : k > 1 ? "get " : "") + name) : __name(target, name);
  for (var i2 = decorators.length - 1; i2 >= 0; i2--) {
    ctx = __decoratorContext(k, name, done = {}, array[3], extraInitializers);
    if (k) {
      ctx.static = s2, ctx.private = p2, access = ctx.access = { has: p2 ? (x2) => __privateIn(target, x2) : (x2) => name in x2 };
      if (k ^ 3) access.get = p2 ? (x2) => (k ^ 1 ? __privateGet : __privateMethod)(x2, target, k ^ 4 ? extra : desc.get) : (x2) => x2[name];
      if (k > 2) access.set = p2 ? (x2, y2) => __privateSet(x2, target, y2, k ^ 4 ? extra : desc.set) : (x2, y2) => x2[name] = y2;
    }
    it = (0, decorators[i2])(k ? k < 4 ? p2 ? extra : desc[key] : k > 4 ? void 0 : { get: desc.get, set: desc.set } : target, ctx), done._ = 1;
    if (k ^ 4 || it === void 0) __expectFn(it) && (k > 4 ? initializers.unshift(it) : k ? p2 ? extra = it : desc[key] = it : target = it);
    else if (typeof it !== "object" || it === null) __typeError("Object expected");
    else __expectFn(fn = it.get) && (desc.get = fn), __expectFn(fn = it.set) && (desc.set = fn), __expectFn(fn = it.init) && initializers.unshift(fn);
  }
  return k || __decoratorMetadata(array, target), desc && __defProp(target, name, desc), p2 ? k ^ 4 ? extra : desc : target;
};
var __accessCheck = (obj, member, msg) => member.has(obj) || __typeError("Cannot " + msg);
var __privateIn = (member, obj) => Object(obj) !== obj ? __typeError('Cannot use the "in" operator on this value') : member.has(obj);
var __privateGet = (obj, member, getter) => (__accessCheck(obj, member, "read from private field"), getter ? getter.call(obj) : member.get(obj));
var __privateAdd = (obj, member, value) => member.has(obj) ? __typeError("Cannot add the same private member more than once") : member instanceof WeakSet ? member.add(obj) : member.set(obj, value);
var __privateSet = (obj, member, value, setter) => (__accessCheck(obj, member, "write to private field"), setter ? setter.call(obj, value) : member.set(obj, value), value);
var __privateMethod = (obj, member, method) => (__accessCheck(obj, member, "access private method"), method);
function computed(compute, comparator) {
  if (comparator) {
    let previousValue;
    return g(() => {
      const value = compute();
      if (value && previousValue && comparator(previousValue, value)) {
        return previousValue;
      }
      previousValue = value;
      return value;
    });
  }
  return g(compute);
}
function deepEqual(a2, b2) {
  if (Object.is(a2, b2)) {
    return true;
  }
  if (a2 === null || b2 === null) return false;
  if (typeof a2 === "function" && typeof b2 === "function") {
    return a2 === b2;
  }
  if (a2 instanceof Set && b2 instanceof Set) {
    if (a2.size !== b2.size) {
      return false;
    }
    for (const value of a2) {
      if (!b2.has(value)) {
        return false;
      }
    }
    return true;
  }
  if (Array.isArray(a2)) {
    if (!Array.isArray(b2) || a2.length !== b2.length) {
      return false;
    }
    const hasDifferentValues = a2.some(
      (value, index) => !deepEqual(value, b2[index])
    );
    return !hasDifferentValues;
  }
  if (typeof a2 === "object" && typeof b2 === "object") {
    const aKeys = Object.keys(a2);
    const bKeys = Object.keys(b2);
    if (aKeys.length !== bKeys.length) return false;
    const hasDifferentValues = aKeys.some(
      (key) => !deepEqual(a2[key], b2[key])
    );
    return !hasDifferentValues;
  }
  return false;
}
function reactive({ get }, _2) {
  return {
    init(value) {
      return y(value);
    },
    get() {
      const current = get.call(this);
      return current.value;
    },
    set(newValue) {
      const current = get.call(this);
      if (current.peek() === newValue) {
        return;
      }
      current.value = newValue;
    }
  };
}
function derived(target, _2) {
  const map = /* @__PURE__ */ new WeakMap();
  return function() {
    let result = map.get(this);
    if (!result) {
      result = computed(target.bind(this));
      map.set(this, result);
    }
    return result.value;
  };
}
function enumerable(enumerable2 = true) {
  return function(_value2, context) {
    context.addInitializer(function() {
      const host = context.kind === "field" ? this : context.static ? this : Object.getPrototypeOf(this);
      const descriptor2 = Object.getOwnPropertyDescriptor(host, context.name);
      if (descriptor2) {
        Object.defineProperty(host, context.name, __spreadProps(__spreadValues({}, descriptor2), { enumerable: enumerable2 }));
      }
    });
  };
}
function effects(...entries) {
  const effects2 = entries.map((fn) => j(fn));
  return () => effects2.forEach((cleanup) => cleanup());
}
var _previous_dec;
var _initial_dec;
var _current_dec;
var _current_dec2;
var _previous_dec2;
var _initial_dec2;
var _init;
var _initial;
var _a;
var initial_get;
var initial_set;
var _ValueHistory_instances;
var _previous;
var _b;
var previous_get;
var previous_set;
var _current;
var _c;
var current_get;
var current_set;
_initial_dec2 = [reactive], _previous_dec2 = [reactive], _current_dec2 = [reactive], _current_dec = [enumerable()], _initial_dec = [enumerable()], _previous_dec = [enumerable()];
var ValueHistory = class {
  constructor(defaultValue, equals = Object.is) {
    this.defaultValue = defaultValue;
    this.equals = equals;
    __runInitializers(_init, 5, this);
    __privateAdd(this, _ValueHistory_instances);
    __privateAdd(this, _initial, __runInitializers(_init, 8, this)), __runInitializers(_init, 11, this);
    __privateAdd(this, _previous, __runInitializers(_init, 12, this)), __runInitializers(_init, 15, this);
    __privateAdd(this, _current, __runInitializers(_init, 16, this)), __runInitializers(_init, 19, this);
    this.reset = this.reset.bind(this);
    this.reset();
  }
  get current() {
    return __privateGet(this, _ValueHistory_instances, current_get);
  }
  get initial() {
    return __privateGet(this, _ValueHistory_instances, initial_get);
  }
  get previous() {
    return __privateGet(this, _ValueHistory_instances, previous_get);
  }
  /** Set the current value */
  set current(value) {
    const current = f(() => __privateGet(this, _ValueHistory_instances, current_get));
    if (value && current && this.equals(current, value)) {
      return;
    }
    n(() => {
      if (!__privateGet(this, _ValueHistory_instances, initial_get)) {
        __privateSet(this, _ValueHistory_instances, value, initial_set);
      }
      __privateSet(this, _ValueHistory_instances, current, previous_set);
      __privateSet(this, _ValueHistory_instances, value, current_set);
    });
  }
  /** Reset the state to the initial value */
  reset(value = this.defaultValue) {
    n(() => {
      __privateSet(this, _ValueHistory_instances, void 0, previous_set);
      __privateSet(this, _ValueHistory_instances, value, initial_set);
      __privateSet(this, _ValueHistory_instances, value, current_set);
    });
  }
};
_init = __decoratorStart(null);
_initial = /* @__PURE__ */ new WeakMap();
_ValueHistory_instances = /* @__PURE__ */ new WeakSet();
_previous = /* @__PURE__ */ new WeakMap();
_current = /* @__PURE__ */ new WeakMap();
_a = __decorateElement(_init, 20, "#initial", _initial_dec2, _ValueHistory_instances, _initial), initial_get = _a.get, initial_set = _a.set;
_b = __decorateElement(_init, 20, "#previous", _previous_dec2, _ValueHistory_instances, _previous), previous_get = _b.get, previous_set = _b.set;
_c = __decorateElement(_init, 20, "#current", _current_dec2, _ValueHistory_instances, _current), current_get = _c.get, current_set = _c.set;
__decorateElement(_init, 2, "current", _current_dec, ValueHistory);
__decorateElement(_init, 2, "initial", _initial_dec, ValueHistory);
__decorateElement(_init, 2, "previous", _previous_dec, ValueHistory);
__decoratorMetadata(_init, ValueHistory);
function snapshot(value) {
  return f(() => {
    const output = {};
    for (const key in value) {
      output[key] = value[key];
    }
    return output;
  });
}
var _store;
var WeakStore = class {
  constructor() {
    __privateAdd(this, _store, /* @__PURE__ */ new WeakMap());
  }
  get(key, id) {
    var _a23;
    return key ? (_a23 = __privateGet(this, _store).get(key)) == null ? void 0 : _a23.get(id) : void 0;
  }
  set(key, id, value) {
    var _a23;
    if (!key) return;
    if (!__privateGet(this, _store).has(key)) __privateGet(this, _store).set(key, /* @__PURE__ */ new Map());
    return (_a23 = __privateGet(this, _store).get(key)) == null ? void 0 : _a23.set(id, value);
  }
  clear(key) {
    var _a23;
    return key ? (_a23 = __privateGet(this, _store).get(key)) == null ? void 0 : _a23.clear() : void 0;
  }
};
_store = /* @__PURE__ */ new WeakMap();

// tools/reading-order/node_modules/@dnd-kit/geometry/dist/index.mjs
var __create2 = Object.create;
var __defProp2 = Object.defineProperty;
var __getOwnPropDesc2 = Object.getOwnPropertyDescriptor;
var __getOwnPropSymbols2 = Object.getOwnPropertySymbols;
var __hasOwnProp2 = Object.prototype.hasOwnProperty;
var __propIsEnum2 = Object.prototype.propertyIsEnumerable;
var __knownSymbol2 = (name, symbol) => (symbol = Symbol[name]) ? symbol : /* @__PURE__ */ Symbol.for("Symbol." + name);
var __typeError2 = (msg) => {
  throw TypeError(msg);
};
var __pow = Math.pow;
var __defNormalProp2 = (obj, key, value) => key in obj ? __defProp2(obj, key, { enumerable: true, configurable: true, writable: true, value }) : obj[key] = value;
var __spreadValues2 = (a2, b2) => {
  for (var prop in b2 || (b2 = {}))
    if (__hasOwnProp2.call(b2, prop))
      __defNormalProp2(a2, prop, b2[prop]);
  if (__getOwnPropSymbols2)
    for (var prop of __getOwnPropSymbols2(b2)) {
      if (__propIsEnum2.call(b2, prop))
        __defNormalProp2(a2, prop, b2[prop]);
    }
  return a2;
};
var __name2 = (target, value) => __defProp2(target, "name", { value, configurable: true });
var __decoratorStart2 = (base) => {
  var _a23;
  return [, , , __create2((_a23 = base == null ? void 0 : base[__knownSymbol2("metadata")]) != null ? _a23 : null)];
};
var __decoratorStrings2 = ["class", "method", "getter", "setter", "accessor", "field", "value", "get", "set"];
var __expectFn2 = (fn) => fn !== void 0 && typeof fn !== "function" ? __typeError2("Function expected") : fn;
var __decoratorContext2 = (kind, name, done, metadata, fns) => ({ kind: __decoratorStrings2[kind], name, metadata, addInitializer: (fn) => done._ ? __typeError2("Already initialized") : fns.push(__expectFn2(fn || null)) });
var __decoratorMetadata2 = (array, target) => __defNormalProp2(target, __knownSymbol2("metadata"), array[3]);
var __runInitializers2 = (array, flags, self, value) => {
  for (var i2 = 0, fns = array[flags >> 1], n2 = fns && fns.length; i2 < n2; i2++) flags & 1 ? fns[i2].call(self) : value = fns[i2].call(self, value);
  return value;
};
var __decorateElement2 = (array, flags, name, decorators, target, extra) => {
  var fn, it, done, ctx, access, k = flags & 7, s2 = !!(flags & 8), p2 = !!(flags & 16);
  var j2 = k > 3 ? array.length + 1 : k ? s2 ? 1 : 2 : 0, key = __decoratorStrings2[k + 5];
  var initializers = k > 3 && (array[j2 - 1] = []), extraInitializers = array[j2] || (array[j2] = []);
  var desc = k && (!p2 && !s2 && (target = target.prototype), k < 5 && (k > 3 || !p2) && __getOwnPropDesc2(k < 4 ? target : { get [name]() {
    return __privateGet2(this, extra);
  }, set [name](x2) {
    return __privateSet2(this, extra, x2);
  } }, name));
  k ? p2 && k < 4 && __name2(extra, (k > 2 ? "set " : k > 1 ? "get " : "") + name) : __name2(target, name);
  for (var i2 = decorators.length - 1; i2 >= 0; i2--) {
    ctx = __decoratorContext2(k, name, done = {}, array[3], extraInitializers);
    if (k) {
      ctx.static = s2, ctx.private = p2, access = ctx.access = { has: p2 ? (x2) => __privateIn2(target, x2) : (x2) => name in x2 };
      if (k ^ 3) access.get = p2 ? (x2) => (k ^ 1 ? __privateGet2 : __privateMethod2)(x2, target, k ^ 4 ? extra : desc.get) : (x2) => x2[name];
      if (k > 2) access.set = p2 ? (x2, y2) => __privateSet2(x2, target, y2, k ^ 4 ? extra : desc.set) : (x2, y2) => x2[name] = y2;
    }
    it = (0, decorators[i2])(k ? k < 4 ? p2 ? extra : desc[key] : k > 4 ? void 0 : { get: desc.get, set: desc.set } : target, ctx), done._ = 1;
    if (k ^ 4 || it === void 0) __expectFn2(it) && (k > 4 ? initializers.unshift(it) : k ? p2 ? extra = it : desc[key] = it : target = it);
    else if (typeof it !== "object" || it === null) __typeError2("Object expected");
    else __expectFn2(fn = it.get) && (desc.get = fn), __expectFn2(fn = it.set) && (desc.set = fn), __expectFn2(fn = it.init) && initializers.unshift(fn);
  }
  return k || __decoratorMetadata2(array, target), desc && __defProp2(target, name, desc), p2 ? k ^ 4 ? extra : desc : target;
};
var __accessCheck2 = (obj, member, msg) => member.has(obj) || __typeError2("Cannot " + msg);
var __privateIn2 = (member, obj) => Object(obj) !== obj ? __typeError2('Cannot use the "in" operator on this value') : member.has(obj);
var __privateGet2 = (obj, member, getter) => (__accessCheck2(obj, member, "read from private field"), getter ? getter.call(obj) : member.get(obj));
var __privateAdd2 = (obj, member, value) => member.has(obj) ? __typeError2("Cannot add the same private member more than once") : member instanceof WeakSet ? member.add(obj) : member.set(obj, value);
var __privateSet2 = (obj, member, value, setter) => (__accessCheck2(obj, member, "write to private field"), setter ? setter.call(obj, value) : member.set(obj, value), value);
var __privateMethod2 = (obj, member, method) => (__accessCheck2(obj, member, "access private method"), method);
var Point = class _Point {
  /**
   * @param {number} Coordinate of the point on the horizontal axis
   * @param {number} Coordinate of the point on the vertical axis
   */
  constructor(x2, y2) {
    this.x = x2;
    this.y = y2;
  }
  /**
   * Returns the delta between this point and another point.
   *
   * @param {Point} a - A point
   * @param {Point} b - Another point
   */
  static delta(a2, b2) {
    return new _Point(a2.x - b2.x, a2.y - b2.y);
  }
  /**
   * Returns the distance (hypotenuse) between this point and another point.
   *
   * @param {Point} a - A point
   * @param {Point} b - Another point
   */
  static distance(a2, b2) {
    return Math.hypot(a2.x - b2.x, a2.y - b2.y);
  }
  /**
   * Returns true if both points are equal.
   *
   * @param {Point} a - A point
   * @param {Point} b - Another point
   */
  static equals(a2, b2) {
    return a2.x === b2.x && a2.y === b2.y;
  }
  static from({ x: x2, y: y2 }) {
    return new _Point(x2, y2);
  }
};
var Rectangle = class _Rectangle {
  constructor(left, top, width, height) {
    this.left = left;
    this.top = top;
    this.width = width;
    this.height = height;
    this.scale = {
      x: 1,
      y: 1
    };
  }
  get inverseScale() {
    return {
      x: 1 / this.scale.x,
      y: 1 / this.scale.y
    };
  }
  translate(x2, y2) {
    const { top, left, width, height, scale } = this;
    const newShape = new _Rectangle(left + x2, top + y2, width, height);
    newShape.scale = __spreadValues2({}, scale);
    return newShape;
  }
  get boundingRectangle() {
    const { width, height, left, top, right, bottom } = this;
    return { width, height, left, top, right, bottom };
  }
  get center() {
    const { left, top, right, bottom } = this;
    return new Point((left + right) / 2, (top + bottom) / 2);
  }
  get area() {
    const { width, height } = this;
    return width * height;
  }
  equals(shape) {
    if (!(shape instanceof _Rectangle)) {
      return false;
    }
    const { left, top, width, height } = this;
    return left === shape.left && top === shape.top && width === shape.width && height === shape.height;
  }
  containsPoint(point) {
    const { top, left, bottom, right } = this;
    return top <= point.y && point.y <= bottom && left <= point.x && point.x <= right;
  }
  intersectionArea(shape) {
    if (shape instanceof _Rectangle) {
      return rectangleRectangleIntersection(this, shape);
    }
    return 0;
  }
  intersectionRatio(shape) {
    const { area } = this;
    const intersectionArea = this.intersectionArea(shape);
    const intersectionRatio = intersectionArea / (shape.area + area - intersectionArea);
    return intersectionRatio;
  }
  get bottom() {
    const { top, height } = this;
    return top + height;
  }
  get right() {
    const { left, width } = this;
    return left + width;
  }
  get aspectRatio() {
    const { width, height } = this;
    return width / height;
  }
  get corners() {
    return [
      { x: this.left, y: this.top },
      { x: this.right, y: this.top },
      { x: this.left, y: this.bottom },
      { x: this.right, y: this.bottom }
    ];
  }
  static from({ top, left, width, height }) {
    return new _Rectangle(left, top, width, height);
  }
  static delta(a2, b2, alignment = { x: "center", y: "center" }) {
    const getCoordinate = (rect, axis) => {
      const align = alignment[axis];
      const start = axis === "x" ? rect.left : rect.top;
      const size = axis === "x" ? rect.width : rect.height;
      if (align == "start") return start;
      if (align == "end") return start + size;
      return start + size / 2;
    };
    return Point.delta(
      { x: getCoordinate(a2, "x"), y: getCoordinate(a2, "y") },
      { x: getCoordinate(b2, "x"), y: getCoordinate(b2, "y") }
    );
  }
  static intersectionRatio(a2, b2) {
    return _Rectangle.from(a2).intersectionRatio(_Rectangle.from(b2));
  }
};
function rectangleRectangleIntersection(a2, b2) {
  const top = Math.max(b2.top, a2.top);
  const left = Math.max(b2.left, a2.left);
  const right = Math.min(b2.left + b2.width, a2.left + a2.width);
  const bottom = Math.min(b2.top + b2.height, a2.top + a2.height);
  const width = right - left;
  const height = bottom - top;
  if (left < right && top < bottom) {
    const intersectionArea = width * height;
    return intersectionArea;
  }
  return 0;
}
var _direction_dec;
var _delta_dec;
var _a2;
var _timestamp;
var _init2;
var Position = class extends (_a2 = ValueHistory, _delta_dec = [derived], _direction_dec = [derived], _a2) {
  constructor(initialValue) {
    const point = Point.from(initialValue);
    super(point, (a2, b2) => Point.equals(a2, b2));
    __runInitializers2(_init2, 5, this);
    __privateAdd2(this, _timestamp, 0);
    this.velocity = { x: 0, y: 0 };
  }
  get delta() {
    return Point.delta(this.current, this.initial);
  }
  get direction() {
    const { current, previous } = this;
    if (!previous) return null;
    const delta = {
      x: current.x - previous.x,
      y: current.y - previous.y
    };
    if (!delta.x && !delta.y) {
      return null;
    }
    if (Math.abs(delta.x) > Math.abs(delta.y)) {
      return delta.x > 0 ? "right" : "left";
    }
    return delta.y > 0 ? "down" : "up";
  }
  get current() {
    return super.current;
  }
  set current(coordinates) {
    const { current } = this;
    const point = Point.from(coordinates);
    const delta = {
      x: point.x - current.x,
      y: point.y - current.y
    };
    const timestamp = Date.now();
    const timeDelta = timestamp - __privateGet2(this, _timestamp);
    const velocity = (delta2) => Math.round(delta2 / timeDelta * 100);
    n(() => {
      __privateSet2(this, _timestamp, timestamp);
      this.velocity = {
        x: velocity(delta.x),
        y: velocity(delta.y)
      };
      super.current = point;
    });
  }
  reset(coordinates = this.defaultValue) {
    super.reset(Point.from(coordinates));
    this.velocity = { x: 0, y: 0 };
  }
};
_init2 = __decoratorStart2(_a2);
_timestamp = /* @__PURE__ */ new WeakMap();
__decorateElement2(_init2, 2, "delta", _delta_dec, Position);
__decorateElement2(_init2, 2, "direction", _direction_dec, Position);
__decoratorMetadata2(_init2, Position);
function exceedsDistance({ x: x2, y: y2 }, distance) {
  const dx = Math.abs(x2);
  const dy = Math.abs(y2);
  if (typeof distance === "number") {
    return Math.sqrt(__pow(dx, 2) + __pow(dy, 2)) > distance;
  }
  if ("x" in distance && "y" in distance) {
    return dx > distance.x && dy > distance.y;
  }
  if ("x" in distance) {
    return dx > distance.x;
  }
  if ("y" in distance) {
    return dy > distance.y;
  }
  return false;
}
var Axis = /* @__PURE__ */ ((Axis2) => {
  Axis2["Horizontal"] = "x";
  Axis2["Vertical"] = "y";
  return Axis2;
})(Axis || {});
var Axes = Object.values(Axis);

// tools/reading-order/node_modules/@dnd-kit/abstract/index.js
var __create3 = Object.create;
var __defProp3 = Object.defineProperty;
var __defProps2 = Object.defineProperties;
var __getOwnPropDesc3 = Object.getOwnPropertyDescriptor;
var __getOwnPropDescs2 = Object.getOwnPropertyDescriptors;
var __getOwnPropSymbols3 = Object.getOwnPropertySymbols;
var __hasOwnProp3 = Object.prototype.hasOwnProperty;
var __propIsEnum3 = Object.prototype.propertyIsEnumerable;
var __knownSymbol3 = (name, symbol) => (symbol = Symbol[name]) ? symbol : /* @__PURE__ */ Symbol.for("Symbol." + name);
var __typeError3 = (msg) => {
  throw TypeError(msg);
};
var __defNormalProp3 = (obj, key, value) => key in obj ? __defProp3(obj, key, { enumerable: true, configurable: true, writable: true, value }) : obj[key] = value;
var __spreadValues3 = (a2, b2) => {
  for (var prop in b2 || (b2 = {}))
    if (__hasOwnProp3.call(b2, prop))
      __defNormalProp3(a2, prop, b2[prop]);
  if (__getOwnPropSymbols3)
    for (var prop of __getOwnPropSymbols3(b2)) {
      if (__propIsEnum3.call(b2, prop))
        __defNormalProp3(a2, prop, b2[prop]);
    }
  return a2;
};
var __spreadProps2 = (a2, b2) => __defProps2(a2, __getOwnPropDescs2(b2));
var __name3 = (target, value) => __defProp3(target, "name", { value, configurable: true });
var __objRest = (source, exclude) => {
  var target = {};
  for (var prop in source)
    if (__hasOwnProp3.call(source, prop) && exclude.indexOf(prop) < 0)
      target[prop] = source[prop];
  if (source != null && __getOwnPropSymbols3)
    for (var prop of __getOwnPropSymbols3(source)) {
      if (exclude.indexOf(prop) < 0 && __propIsEnum3.call(source, prop))
        target[prop] = source[prop];
    }
  return target;
};
var __decoratorStart3 = (base) => {
  var _a5;
  return [, , , __create3((_a5 = base == null ? void 0 : base[__knownSymbol3("metadata")]) != null ? _a5 : null)];
};
var __decoratorStrings3 = ["class", "method", "getter", "setter", "accessor", "field", "value", "get", "set"];
var __expectFn3 = (fn) => fn !== void 0 && typeof fn !== "function" ? __typeError3("Function expected") : fn;
var __decoratorContext3 = (kind, name, done, metadata, fns) => ({ kind: __decoratorStrings3[kind], name, metadata, addInitializer: (fn) => done._ ? __typeError3("Already initialized") : fns.push(__expectFn3(fn || null)) });
var __decoratorMetadata3 = (array, target) => __defNormalProp3(target, __knownSymbol3("metadata"), array[3]);
var __runInitializers3 = (array, flags, self, value) => {
  for (var i2 = 0, fns = array[flags >> 1], n2 = fns && fns.length; i2 < n2; i2++) flags & 1 ? fns[i2].call(self) : value = fns[i2].call(self, value);
  return value;
};
var __decorateElement3 = (array, flags, name, decorators, target, extra) => {
  var fn, it, done, ctx, access, k = flags & 7, s2 = !!(flags & 8), p2 = !!(flags & 16);
  var j2 = k > 3 ? array.length + 1 : k ? s2 ? 1 : 2 : 0, key = __decoratorStrings3[k + 5];
  var initializers = k > 3 && (array[j2 - 1] = []), extraInitializers = array[j2] || (array[j2] = []);
  var desc = k && (!p2 && !s2 && (target = target.prototype), k < 5 && (k > 3 || !p2) && __getOwnPropDesc3(k < 4 ? target : { get [name]() {
    return __privateGet3(this, extra);
  }, set [name](x2) {
    return __privateSet3(this, extra, x2);
  } }, name));
  k ? p2 && k < 4 && __name3(extra, (k > 2 ? "set " : k > 1 ? "get " : "") + name) : __name3(target, name);
  for (var i2 = decorators.length - 1; i2 >= 0; i2--) {
    ctx = __decoratorContext3(k, name, done = {}, array[3], extraInitializers);
    if (k) {
      ctx.static = s2, ctx.private = p2, access = ctx.access = { has: p2 ? (x2) => __privateIn3(target, x2) : (x2) => name in x2 };
      if (k ^ 3) access.get = p2 ? (x2) => (k ^ 1 ? __privateGet3 : __privateMethod3)(x2, target, k ^ 4 ? extra : desc.get) : (x2) => x2[name];
      if (k > 2) access.set = p2 ? (x2, y2) => __privateSet3(x2, target, y2, k ^ 4 ? extra : desc.set) : (x2, y2) => x2[name] = y2;
    }
    it = (0, decorators[i2])(k ? k < 4 ? p2 ? extra : desc[key] : k > 4 ? void 0 : { get: desc.get, set: desc.set } : target, ctx), done._ = 1;
    if (k ^ 4 || it === void 0) __expectFn3(it) && (k > 4 ? initializers.unshift(it) : k ? p2 ? extra = it : desc[key] = it : target = it);
    else if (typeof it !== "object" || it === null) __typeError3("Object expected");
    else __expectFn3(fn = it.get) && (desc.get = fn), __expectFn3(fn = it.set) && (desc.set = fn), __expectFn3(fn = it.init) && initializers.unshift(fn);
  }
  return k || __decoratorMetadata3(array, target), desc && __defProp3(target, name, desc), p2 ? k ^ 4 ? extra : desc : target;
};
var __accessCheck3 = (obj, member, msg) => member.has(obj) || __typeError3("Cannot " + msg);
var __privateIn3 = (member, obj) => Object(obj) !== obj ? __typeError3('Cannot use the "in" operator on this value') : member.has(obj);
var __privateGet3 = (obj, member, getter) => (__accessCheck3(obj, member, "read from private field"), getter ? getter.call(obj) : member.get(obj));
var __privateAdd3 = (obj, member, value) => member.has(obj) ? __typeError3("Cannot add the same private member more than once") : member instanceof WeakSet ? member.add(obj) : member.set(obj, value);
var __privateSet3 = (obj, member, value, setter) => (__accessCheck3(obj, member, "write to private field"), setter ? setter.call(obj, value) : member.set(obj, value), value);
var __privateMethod3 = (obj, member, method) => (__accessCheck3(obj, member, "access private method"), method);
function configure(plugin, options) {
  return {
    plugin,
    options
  };
}
function configurator(plugin) {
  return (options) => {
    return configure(plugin, options);
  };
}
function descriptor(plugin) {
  if (typeof plugin === "function") {
    return {
      plugin,
      options: void 0
    };
  }
  return plugin;
}
var _disabled_dec;
var _init3;
var _disabled;
var _cleanupFunctions;
_disabled_dec = [reactive];
var Plugin = class {
  /**
   * Creates a new plugin instance.
   *
   * @param manager - The drag and drop manager that owns this plugin
   * @param options - Optional configuration for the plugin
   */
  constructor(manager, options) {
    this.manager = manager;
    this.options = options;
    __privateAdd3(this, _disabled, __runInitializers3(_init3, 8, this, false)), __runInitializers3(_init3, 11, this);
    __privateAdd3(this, _cleanupFunctions, /* @__PURE__ */ new Set());
  }
  /**
   * Enables a disabled plugin instance.
   *
   * @remarks
   * This method triggers effects when called.
   */
  enable() {
    this.disabled = false;
  }
  /**
   * Disables an enabled plugin instance.
   *
   * @remarks
   * This method triggers effects when called.
   */
  disable() {
    this.disabled = true;
  }
  /**
   * Checks if the plugin instance is disabled.
   *
   * @returns true if the plugin is disabled
   * @remarks
   * This method does not trigger effects when accessed.
   */
  isDisabled() {
    return f(() => {
      return this.disabled;
    });
  }
  /**
   * Configures a plugin instance with new options.
   *
   * @param options - The new options to apply
   */
  configure(options) {
    this.options = options;
  }
  /**
   * Registers an effect that will be cleaned up when the plugin is destroyed.
   *
   * @param callback - The effect callback to register
   * @returns A function to dispose of the effect
   */
  registerEffect(callback) {
    const dispose = j(callback.bind(this));
    __privateGet3(this, _cleanupFunctions).add(dispose);
    return dispose;
  }
  /**
   * Destroys a plugin instance and cleans up its resources.
   *
   * @remarks
   * This method:
   * - Calls all registered cleanup functions
   * - Should be overridden by subclasses to clean up additional resources
   */
  destroy() {
    __privateGet3(this, _cleanupFunctions).forEach((cleanup) => cleanup());
  }
  /**
   * Configures a plugin constructor with options.
   *
   * @param options - The options to configure the constructor with
   * @returns The configured plugin constructor
   *
   * @remarks
   * This method is used to configure the options that the
   * plugin constructor will use to create plugin instances.
   */
  static configure(options) {
    return configure(this, options);
  }
};
_init3 = __decoratorStart3(null);
_disabled = /* @__PURE__ */ new WeakMap();
_cleanupFunctions = /* @__PURE__ */ new WeakMap();
__decorateElement3(_init3, 4, "disabled", _disabled_dec, Plugin, _disabled);
__decoratorMetadata3(_init3, Plugin);
var CorePlugin = class extends Plugin {
};
var _previousValues;
var PluginRegistry = class {
  /**
   * Creates a new plugin registry.
   *
   * @param manager - The drag and drop manager that owns this registry
   */
  constructor(manager) {
    this.manager = manager;
    this.instances = /* @__PURE__ */ new Map();
    __privateAdd3(this, _previousValues, []);
  }
  /**
   * Gets all registered plugin instances.
   *
   * @returns An array of all active plugin instances
   */
  get values() {
    return Array.from(this.instances.values());
  }
  /**
   * Sets the list of plugins to be used by the registry.
   *
   * @param entries - Array of plugin constructors or descriptors
   * @remarks
   * This method:
   * - Filters out duplicate plugins
   * - Unregisters plugins that are no longer in use
   * - Registers new plugins with their options
   */
  set values(entries) {
    const descriptors = entries.map(descriptor).reduce((acc, descriptor2) => {
      const existing = acc.find(({ plugin }) => plugin === descriptor2.plugin);
      if (existing) {
        existing.options = descriptor2.options;
        return acc;
      }
      return [...acc, descriptor2];
    }, []);
    const constructors = descriptors.map(({ plugin }) => plugin);
    for (const plugin of __privateGet3(this, _previousValues)) {
      if (!constructors.includes(plugin)) {
        if (plugin.prototype instanceof CorePlugin) {
          continue;
        }
        this.unregister(plugin);
      }
    }
    for (const { plugin, options } of descriptors) {
      this.register(plugin, options);
    }
    __privateSet3(this, _previousValues, constructors);
  }
  /**
   * Gets a plugin instance by its constructor.
   *
   * @param plugin - The plugin constructor to look up
   * @returns The plugin instance or undefined if not found
   */
  get(plugin) {
    const instance = this.instances.get(plugin);
    return instance;
  }
  /**
   * Registers a new plugin instance.
   *
   * @param plugin - The plugin constructor to register
   * @param options - Optional configuration for the plugin
   * @returns The registered plugin instance
   * @remarks
   * If the plugin is already registered, its options will be updated
   * and the existing instance will be returned.
   */
  register(plugin, options) {
    const existingInstance = this.instances.get(plugin);
    if (existingInstance) {
      if (existingInstance.options !== options) {
        existingInstance.options = options;
      }
      return existingInstance;
    }
    const instance = new plugin(this.manager, options);
    this.instances.set(plugin, instance);
    return instance;
  }
  /**
   * Unregisters a plugin instance.
   *
   * @param plugin - The plugin constructor to unregister
   * @remarks
   * This method:
   * - Destroys the plugin instance
   * - Removes it from the registry
   */
  unregister(plugin) {
    const instance = this.instances.get(plugin);
    if (instance) {
      instance.destroy();
      this.instances.delete(plugin);
    }
  }
  /**
   * Destroys all registered plugin instances.
   *
   * @remarks
   * This method:
   * - Calls destroy() on all plugin instances
   * - Clears the registry
   */
  destroy() {
    for (const plugin of this.instances.values()) {
      plugin.destroy();
    }
    this.instances.clear();
  }
};
_previousValues = /* @__PURE__ */ new WeakMap();
function sortCollisions(a2, b2) {
  if (a2.priority === b2.priority) {
    if (a2.type === b2.type) {
      return b2.value - a2.value;
    }
    return b2.type - a2.type;
  }
  return b2.priority - a2.priority;
}
var DEFAULT_VALUE = [];
var _previousCoordinates;
var _collisions;
var CollisionObserver = class extends Plugin {
  /**
   * Creates a new CollisionObserver instance.
   *
   * @param manager - The drag drop manager instance
   */
  constructor(manager) {
    super(manager);
    __privateAdd3(this, _previousCoordinates);
    __privateAdd3(this, _collisions);
    this.computeCollisions = this.computeCollisions.bind(this);
    __privateSet3(this, _collisions, y(DEFAULT_VALUE));
    this.destroy = effects(
      () => {
        const collisions = this.computeCollisions();
        const coordinates = f(
          () => this.manager.dragOperation.position.current
        );
        if (collisions !== DEFAULT_VALUE) {
          const previousCoordinates = __privateGet3(this, _previousCoordinates);
          __privateSet3(this, _previousCoordinates, coordinates);
          if (previousCoordinates && coordinates.x == previousCoordinates.x && coordinates.y == previousCoordinates.y) {
            return;
          }
        } else {
          __privateSet3(this, _previousCoordinates, void 0);
        }
        __privateGet3(this, _collisions).value = collisions;
      },
      () => {
        const { dragOperation } = this.manager;
        if (dragOperation.status.initialized) {
          this.forceUpdate();
        }
      }
    );
  }
  /**
   * Forces an immediate update of collision detection.
   *
   * @param immediate - If true, updates collisions immediately. If false, resets previous coordinates.
   */
  forceUpdate(immediate = true) {
    f(() => {
      if (immediate) {
        __privateGet3(this, _collisions).value = this.computeCollisions();
      } else {
        __privateSet3(this, _previousCoordinates, void 0);
      }
    });
  }
  /**
   * Computes collisions between draggable and droppable elements.
   *
   * @param entries - Optional array of droppable elements to check. If not provided, uses all registered droppables.
   * @param collisionDetector - Optional custom collision detector function
   * @returns Array of detected collisions, sorted by priority
   */
  computeCollisions(entries, collisionDetector) {
    const { registry, dragOperation } = this.manager;
    const { source, shape, status } = dragOperation;
    if (!status.initialized || !shape) {
      return DEFAULT_VALUE;
    }
    const collisions = [];
    const potentialTargets = [];
    for (const entry of entries != null ? entries : registry.droppables) {
      if (entry.disabled) {
        continue;
      }
      if (source && !entry.accepts(source)) {
        continue;
      }
      const detectCollision = collisionDetector != null ? collisionDetector : entry.collisionDetector;
      if (!detectCollision) {
        continue;
      }
      potentialTargets.push(entry);
      void entry.shape;
      const collision = f(
        () => detectCollision({
          droppable: entry,
          dragOperation
        })
      );
      if (collision) {
        if (entry.collisionPriority != null) {
          collision.priority = entry.collisionPriority;
        }
        collisions.push(collision);
      }
    }
    if (potentialTargets.length === 0) {
      return DEFAULT_VALUE;
    }
    collisions.sort(sortCollisions);
    return collisions;
  }
  /**
   * Gets the current collisions signal value.
   */
  get collisions() {
    return __privateGet3(this, _collisions).value;
  }
};
_previousCoordinates = /* @__PURE__ */ new WeakMap();
_collisions = /* @__PURE__ */ new WeakMap();
var _disabled_dec2;
var _data_dec;
var _manager_dec;
var _Entity_static;
var flushIdChanges_fn;
var _init22;
var _manager;
var _idSignal;
var _data;
var _disabled2;
_manager_dec = [reactive], _data_dec = [reactive], _disabled_dec2 = [reactive];
var _Entity = class _Entity2 {
  /**
   * Creates a new instance of the `Entity` class.
   *
   * @param input - An object containing the initial properties of the entity.
   * @param manager - The manager that controls the drag and drop operations.
   */
  constructor(input, manager) {
    __privateAdd3(this, _manager, __runInitializers3(_init22, 8, this)), __runInitializers3(_init22, 11, this);
    __privateAdd3(this, _idSignal);
    __privateAdd3(this, _data, __runInitializers3(_init22, 12, this)), __runInitializers3(_init22, 15, this);
    __privateAdd3(this, _disabled2, __runInitializers3(_init22, 16, this)), __runInitializers3(_init22, 19, this);
    const { effects: effects6, id, data = {}, disabled = false, register = true } = input;
    let previousId = id;
    __privateSet3(this, _idSignal, y(id));
    this.manager = manager;
    this.data = data;
    this.disabled = disabled;
    this.effects = () => {
      var _a5;
      return [
        () => {
          const { id: id2, manager: manager2 } = this;
          if (id2 === previousId) {
            return;
          }
          previousId = id2;
          manager2 == null ? void 0 : manager2.registry.register(this);
          return () => manager2 == null ? void 0 : manager2.registry.unregister(this);
        },
        ...(_a5 = effects6 == null ? void 0 : effects6()) != null ? _a5 : []
      ];
    };
    this.register = this.register.bind(this);
    this.unregister = this.unregister.bind(this);
    this.destroy = this.destroy.bind(this);
    if (manager && register) {
      queueMicrotask(this.register);
    }
  }
  get id() {
    var _a5, _b3;
    const signalValue = __privateGet3(this, _idSignal).value;
    return (_b3 = (_a5 = _Entity2.pendingIdChanges) == null ? void 0 : _a5.get(this)) != null ? _b3 : signalValue;
  }
  set id(value) {
    var _a5, _b3;
    const current = (_b3 = (_a5 = _Entity2.pendingIdChanges) == null ? void 0 : _a5.get(this)) != null ? _b3 : __privateGet3(this, _idSignal).peek();
    if (value === current) return;
    if (!_Entity2.pendingIdChanges) {
      _Entity2.pendingIdChanges = /* @__PURE__ */ new Map();
      queueMicrotask(() => {
        var _a23;
        return __privateMethod3(_a23 = _Entity2, _Entity_static, flushIdChanges_fn).call(_a23);
      });
    }
    _Entity2.pendingIdChanges.set(this, value);
  }
  /**
   * A method that registers the entity with the manager.
   * @returns CleanupFunction | void
   */
  register() {
    var _a5;
    return (_a5 = this.manager) == null ? void 0 : _a5.registry.register(this);
  }
  /**
   * A method that unregisters the entity from the manager.
   * @returns void
   */
  unregister() {
    var _a5;
    (_a5 = this.manager) == null ? void 0 : _a5.registry.unregister(this);
  }
  /**
   * A method that cleans up the entity when it is no longer needed.
   * @returns void
   */
  destroy() {
    var _a5;
    (_a5 = this.manager) == null ? void 0 : _a5.registry.unregister(this);
  }
};
_init22 = __decoratorStart3(null);
_Entity_static = /* @__PURE__ */ new WeakSet();
flushIdChanges_fn = function() {
  const changes = _Entity.pendingIdChanges;
  _Entity.pendingIdChanges = null;
  if (changes) {
    n(() => {
      for (const [entity, id] of changes) {
        __privateGet3(entity, _idSignal).value = id;
      }
    });
  }
};
_manager = /* @__PURE__ */ new WeakMap();
_idSignal = /* @__PURE__ */ new WeakMap();
_data = /* @__PURE__ */ new WeakMap();
_disabled2 = /* @__PURE__ */ new WeakMap();
__decorateElement3(_init22, 4, "manager", _manager_dec, _Entity, _manager);
__decorateElement3(_init22, 4, "data", _data_dec, _Entity, _data);
__decorateElement3(_init22, 4, "disabled", _disabled_dec2, _Entity, _disabled2);
__privateAdd3(_Entity, _Entity_static);
__decoratorMetadata3(_init22, _Entity);
_Entity.pendingIdChanges = null;
var Entity = _Entity;
var EntityRegistry = class {
  constructor() {
    this.map = y(/* @__PURE__ */ new Map());
    this.cleanupFunctions = /* @__PURE__ */ new WeakMap();
    this.register = (key, value) => {
      const current = this.map.peek();
      const currentValue = current.get(key);
      const unregister = () => this.unregister(key, value);
      if (currentValue === value) return unregister;
      if (currentValue) {
        if (currentValue.id === key) {
          const cleanup2 = this.cleanupFunctions.get(currentValue);
          cleanup2 == null ? void 0 : cleanup2();
          this.cleanupFunctions.delete(currentValue);
        }
      }
      const updatedMap = new Map(current);
      for (const [existingKey, existingValue] of current) {
        if (existingValue === value && existingKey !== key) {
          updatedMap.delete(existingKey);
          break;
        }
      }
      updatedMap.set(key, value);
      this.map.value = updatedMap;
      const cleanup = effects(...value.effects());
      this.cleanupFunctions.set(value, cleanup);
      return unregister;
    };
    this.unregister = (key, value) => {
      const current = this.map.peek();
      if (current.get(key) !== value) {
        return;
      }
      const cleanup = this.cleanupFunctions.get(value);
      cleanup == null ? void 0 : cleanup();
      this.cleanupFunctions.delete(value);
      const updatedMap = new Map(current);
      updatedMap.delete(key);
      this.map.value = updatedMap;
    };
  }
  /**
   * Iterator for the EntityRegistry class.
   * @returns An iterator for the values in the map.
   */
  [Symbol.iterator]() {
    return this.map.peek().values();
  }
  get value() {
    return this.map.value.values();
  }
  /**
   * Checks if a entity with the given identifier exists in the registry.
   * @param identifier - The unique identifier of the entity.
   * @returns True if the entity exists, false otherwise.
   */
  has(identifier) {
    return this.map.value.has(identifier);
  }
  /**
   * Retrieves a entity from the registry using its identifier.
   * @param identifier - The unique identifier of the entity.
   * @returns The entity if it exists, undefined otherwise.
   */
  get(identifier) {
    return this.map.value.get(identifier);
  }
  /**
   * Destroys all entries in the registry and clears the registry.
   */
  destroy() {
    for (const entry of this) {
      const cleanup = this.cleanupFunctions.get(entry);
      cleanup == null ? void 0 : cleanup();
      entry.destroy();
    }
    this.map.value = /* @__PURE__ */ new Map();
  }
};
var _isDragSource_dec;
var _isDragging_dec;
var _isDropping_dec;
var _status_dec;
var _modifiers_dec;
var _type_dec;
var _c2;
var _init32;
var _type;
var _modifiers;
var _status;
var Draggable = class extends (_c2 = Entity, _type_dec = [reactive], _modifiers_dec = [reactive], _status_dec = [reactive], _isDropping_dec = [derived], _isDragging_dec = [derived], _isDragSource_dec = [derived], _c2) {
  constructor(_a5, manager) {
    var _b3 = _a5, { modifiers, type, sensors, plugins, effects: effects6 } = _b3, input = __objRest(_b3, ["modifiers", "type", "sensors", "plugins", "effects"]);
    super(
      __spreadProps2(__spreadValues3({}, input), {
        effects: () => {
          var _a23;
          return [
            ...(_a23 = effects6 == null ? void 0 : effects6()) != null ? _a23 : [],
            () => {
              const { manager: manager2, plugins: plugins2 } = this;
              if (!manager2 || !plugins2) return;
              for (const entry of plugins2) {
                const { plugin } = descriptor(entry);
                manager2.registry.plugins.register(plugin);
              }
            }
          ];
        }
      }),
      manager
    );
    __runInitializers3(_init32, 5, this);
    __privateAdd3(this, _type, __runInitializers3(_init32, 8, this)), __runInitializers3(_init32, 11, this);
    __privateAdd3(this, _modifiers, __runInitializers3(_init32, 12, this)), __runInitializers3(_init32, 15, this);
    __privateAdd3(this, _status, __runInitializers3(_init32, 16, this, this.isDragSource ? "dragging" : "idle")), __runInitializers3(_init32, 19, this);
    this.type = type;
    this.sensors = sensors;
    this.modifiers = modifiers;
    this.alignment = input.alignment;
    this.plugins = plugins;
  }
  /**
   * Look up per-entity options for a given plugin constructor.
   */
  pluginConfig(plugin) {
    if (!this.plugins) return void 0;
    for (const entry of this.plugins) {
      const desc = descriptor(entry);
      if (desc.plugin === plugin) return desc.options;
    }
    return void 0;
  }
  get isDropping() {
    return this.status === "dropping" && this.isDragSource;
  }
  get isDragging() {
    return this.status === "dragging" && this.isDragSource;
  }
  get isDragSource() {
    var _a5, _b3;
    return ((_b3 = (_a5 = this.manager) == null ? void 0 : _a5.dragOperation.source) == null ? void 0 : _b3.id) === this.id;
  }
};
_init32 = __decoratorStart3(_c2);
_type = /* @__PURE__ */ new WeakMap();
_modifiers = /* @__PURE__ */ new WeakMap();
_status = /* @__PURE__ */ new WeakMap();
__decorateElement3(_init32, 4, "type", _type_dec, Draggable, _type);
__decorateElement3(_init32, 4, "modifiers", _modifiers_dec, Draggable, _modifiers);
__decorateElement3(_init32, 4, "status", _status_dec, Draggable, _status);
__decorateElement3(_init32, 2, "isDropping", _isDropping_dec, Draggable);
__decorateElement3(_init32, 2, "isDragging", _isDragging_dec, Draggable);
__decorateElement3(_init32, 2, "isDragSource", _isDragSource_dec, Draggable);
__decoratorMetadata3(_init32, Draggable);
var _isDropTarget_dec;
var _shape_dec;
var _collisionPriority_dec;
var _collisionDetector_dec;
var _type_dec2;
var _accept_dec;
var _c22;
var _init4;
var _accept;
var _type2;
var _collisionDetector;
var _collisionPriority;
var _shape;
var Droppable = class extends (_c22 = Entity, _accept_dec = [reactive], _type_dec2 = [reactive], _collisionDetector_dec = [reactive], _collisionPriority_dec = [reactive], _shape_dec = [reactive], _isDropTarget_dec = [derived], _c22) {
  constructor(_a5, manager) {
    var _b3 = _a5, { accept, collisionDetector, collisionPriority, type } = _b3, input = __objRest(_b3, ["accept", "collisionDetector", "collisionPriority", "type"]);
    super(input, manager);
    __runInitializers3(_init4, 5, this);
    __privateAdd3(this, _accept, __runInitializers3(_init4, 8, this)), __runInitializers3(_init4, 11, this);
    __privateAdd3(this, _type2, __runInitializers3(_init4, 12, this)), __runInitializers3(_init4, 15, this);
    __privateAdd3(this, _collisionDetector, __runInitializers3(_init4, 16, this)), __runInitializers3(_init4, 19, this);
    __privateAdd3(this, _collisionPriority, __runInitializers3(_init4, 20, this)), __runInitializers3(_init4, 23, this);
    __privateAdd3(this, _shape, __runInitializers3(_init4, 24, this)), __runInitializers3(_init4, 27, this);
    this.accept = accept;
    this.collisionDetector = collisionDetector;
    this.collisionPriority = collisionPriority;
    this.type = type;
  }
  /**
   * Checks whether or not the droppable accepts a given draggable.
   *
   * @param draggable - The draggable to check
   * @returns true if the draggable can be dropped here
   */
  accepts(draggable) {
    const { accept } = this;
    if (!accept) {
      return true;
    }
    if (typeof accept === "function") {
      return accept(draggable);
    }
    if (!draggable.type) {
      return false;
    }
    if (Array.isArray(accept)) {
      return accept.includes(draggable.type);
    }
    return draggable.type === accept;
  }
  get isDropTarget() {
    var _a5, _b3;
    return ((_b3 = (_a5 = this.manager) == null ? void 0 : _a5.dragOperation.target) == null ? void 0 : _b3.id) === this.id;
  }
};
_init4 = __decoratorStart3(_c22);
_accept = /* @__PURE__ */ new WeakMap();
_type2 = /* @__PURE__ */ new WeakMap();
_collisionDetector = /* @__PURE__ */ new WeakMap();
_collisionPriority = /* @__PURE__ */ new WeakMap();
_shape = /* @__PURE__ */ new WeakMap();
__decorateElement3(_init4, 4, "accept", _accept_dec, Droppable, _accept);
__decorateElement3(_init4, 4, "type", _type_dec2, Droppable, _type2);
__decorateElement3(_init4, 4, "collisionDetector", _collisionDetector_dec, Droppable, _collisionDetector);
__decorateElement3(_init4, 4, "collisionPriority", _collisionPriority_dec, Droppable, _collisionPriority);
__decorateElement3(_init4, 4, "shape", _shape_dec, Droppable, _shape);
__decorateElement3(_init4, 2, "isDropTarget", _isDropTarget_dec, Droppable);
__decoratorMetadata3(_init4, Droppable);
var Monitor = class {
  constructor() {
    this.registry = /* @__PURE__ */ new Map();
  }
  /**
   * Adds an event listener for the specified event type.
   *
   * @param name - The name of the event to listen for
   * @param handler - The function to call when the event occurs
   * @returns A function to remove the event listener
   */
  addEventListener(name, handler) {
    const { registry } = this;
    const listeners = new Set(registry.get(name));
    listeners.add(handler);
    registry.set(name, listeners);
    return () => this.removeEventListener(name, handler);
  }
  /**
   * Removes an event listener for the specified event type.
   *
   * @param name - The name of the event
   * @param handler - The function to remove
   */
  removeEventListener(name, handler) {
    const { registry } = this;
    const listeners = new Set(registry.get(name));
    listeners.delete(handler);
    registry.set(name, listeners);
  }
  /**
   * Dispatches an event to all registered listeners.
   *
   * @param name - The name of the event to dispatch
   * @param args - Arguments to pass to the event handlers
   */
  dispatch(name, ...args) {
    const { registry } = this;
    const listeners = registry.get(name);
    if (!listeners) {
      return;
    }
    for (const listener of listeners) {
      listener(...args);
    }
  }
};
var DragDropMonitor = class extends Monitor {
  /**
   * Creates a new drag and drop monitor.
   *
   * @param manager - The drag and drop manager to monitor
   */
  constructor(manager) {
    super();
    this.manager = manager;
  }
  /**
   * Dispatches a drag and drop event.
   *
   * @param type - The type of event to dispatch
   * @param event - The event data to dispatch
   */
  dispatch(type, event) {
    const args = [event, this.manager];
    super.dispatch(type, ...args);
  }
};
function defaultPreventable(event, cancelable = true) {
  let defaultPrevented = false;
  return __spreadProps2(__spreadValues3({}, event), {
    cancelable,
    get defaultPrevented() {
      return defaultPrevented;
    },
    preventDefault() {
      if (!cancelable) {
        return;
      }
      defaultPrevented = true;
    }
  });
}
var CollisionNotifier = class extends CorePlugin {
  constructor(manager) {
    super(manager);
    const isEqual = (a2, b2) => a2.map(({ id }) => id).join("") === b2.map(({ id }) => id).join("");
    let previousCollisions = [];
    this.destroy = effects(
      () => {
        const { dragOperation, collisionObserver } = manager;
        if (dragOperation.status.initializing) {
          previousCollisions = [];
          collisionObserver.enable();
        }
      },
      () => {
        const { collisionObserver, monitor } = manager;
        const { collisions } = collisionObserver;
        if (collisionObserver.isDisabled()) {
          return;
        }
        if (Entity.pendingIdChanges) {
          return;
        }
        const event = defaultPreventable({
          collisions
        });
        monitor.dispatch("collision", event);
        if (event.defaultPrevented) {
          return;
        }
        if (isEqual(collisions, previousCollisions)) {
          return;
        } else {
          previousCollisions = collisions;
        }
        const [firstCollision] = collisions;
        f(() => {
          var _a5;
          if ((firstCollision == null ? void 0 : firstCollision.id) !== ((_a5 = manager.dragOperation.target) == null ? void 0 : _a5.id)) {
            collisionObserver.disable();
            manager.actions.setDropTarget(firstCollision == null ? void 0 : firstCollision.id).then(() => {
              collisionObserver.enable();
            });
          }
        });
      }
    );
  }
};
var CollisionPriority = /* @__PURE__ */ ((CollisionPriority2) => {
  CollisionPriority2[CollisionPriority2["Lowest"] = 0] = "Lowest";
  CollisionPriority2[CollisionPriority2["Low"] = 1] = "Low";
  CollisionPriority2[CollisionPriority2["Normal"] = 2] = "Normal";
  CollisionPriority2[CollisionPriority2["High"] = 3] = "High";
  CollisionPriority2[CollisionPriority2["Highest"] = 4] = "Highest";
  return CollisionPriority2;
})(CollisionPriority || {});
var CollisionType = /* @__PURE__ */ ((CollisionType2) => {
  CollisionType2[CollisionType2["Collision"] = 0] = "Collision";
  CollisionType2[CollisionType2["ShapeIntersection"] = 1] = "ShapeIntersection";
  CollisionType2[CollisionType2["PointerIntersection"] = 2] = "PointerIntersection";
  return CollisionType2;
})(CollisionType || {});
var _dropped_dec;
var _dragging_dec;
var _initialized_dec;
var _initializing_dec;
var _idle_dec;
var _current_dec3;
var _value_dec;
var _init5;
var _value;
_value_dec = [reactive], _current_dec3 = [derived], _idle_dec = [derived], _initializing_dec = [derived], _initialized_dec = [derived], _dragging_dec = [derived], _dropped_dec = [derived];
var Status = class {
  constructor() {
    __runInitializers3(_init5, 5, this);
    __privateAdd3(this, _value, __runInitializers3(
      _init5,
      8,
      this,
      "idle"
      /* Idle */
    )), __runInitializers3(_init5, 11, this);
  }
  get current() {
    return this.value;
  }
  get idle() {
    return this.value === "idle";
  }
  get initializing() {
    return this.value === "initializing";
  }
  get initialized() {
    const { value } = this;
    return value !== "idle" && value !== "initialization-pending";
  }
  get dragging() {
    return this.value === "dragging";
  }
  get dropped() {
    return this.value === "dropped";
  }
  /**
   * Sets the current status value.
   *
   * @param value - The new status value
   */
  set(value) {
    this.value = value;
  }
};
_init5 = __decoratorStart3(null);
_value = /* @__PURE__ */ new WeakMap();
__decorateElement3(_init5, 4, "value", _value_dec, Status, _value);
__decorateElement3(_init5, 2, "current", _current_dec3, Status);
__decorateElement3(_init5, 2, "idle", _idle_dec, Status);
__decorateElement3(_init5, 2, "initializing", _initializing_dec, Status);
__decorateElement3(_init5, 2, "initialized", _initialized_dec, Status);
__decorateElement3(_init5, 2, "dragging", _dragging_dec, Status);
__decorateElement3(_init5, 2, "dropped", _dropped_dec, Status);
__decoratorMetadata3(_init5, Status);
var DragActions = class {
  /**
   * Creates a new instance of drag actions.
   *
   * @param manager - The drag and drop manager instance
   */
  constructor(manager) {
    this.manager = manager;
  }
  /**
   * Sets the source of the drag operation.
   *
   * @param source - The draggable entity or its unique identifier
   */
  setDragSource(source) {
    const { dragOperation } = this.manager;
    dragOperation.sourceIdentifier = typeof source === "string" || typeof source === "number" ? source : source.id;
  }
  /**
   * Sets the target of the drop operation.
   *
   * @param identifier - The unique identifier of the droppable entity or null/undefined
   * @returns A promise that resolves to true if the drop was prevented
   */
  setDropTarget(identifier) {
    return f(() => {
      const { dragOperation } = this.manager;
      const id = identifier != null ? identifier : null;
      if (dragOperation.targetIdentifier === id) {
        return Promise.resolve(false);
      }
      dragOperation.targetIdentifier = id;
      const event = defaultPreventable({
        operation: dragOperation.snapshot()
      });
      if (dragOperation.status.dragging) {
        this.manager.monitor.dispatch("dragover", event);
      }
      return this.manager.renderer.rendering.then(() => event.defaultPrevented);
    });
  }
  /**
   * Starts a new drag operation.
   *
   * @param args - Configuration for the drag operation
   * @param args.event - The event that initiated the drag
   * @param args.source - The source draggable entity or its identifier
   * @param args.coordinates - The initial coordinates of the drag
   * @returns true if the drag operation started successfully
   * @throws {Error} If there is no drag source or another operation is active
   */
  start(args) {
    return f(() => {
      const { dragOperation } = this.manager;
      if (args.source != null) {
        this.setDragSource(args.source);
      }
      const sourceInstance = dragOperation.source;
      if (!sourceInstance) {
        throw new Error("Cannot start a drag operation without a drag source");
      }
      if (!dragOperation.status.idle) {
        throw new Error(
          "Cannot start a drag operation while another is active"
        );
      }
      const controller = new AbortController();
      const { event: nativeEvent, coordinates } = args;
      n(() => {
        dragOperation.status.set(
          "initialization-pending"
          /* InitializationPending */
        );
        dragOperation.shape = null;
        dragOperation.canceled = false;
        dragOperation.activatorEvent = nativeEvent != null ? nativeEvent : null;
        dragOperation.position.reset(coordinates);
      });
      const beforeStartEvent = defaultPreventable({
        operation: dragOperation.snapshot()
      });
      this.manager.monitor.dispatch("beforedragstart", beforeStartEvent);
      if (beforeStartEvent.defaultPrevented) {
        dragOperation.reset();
        controller.abort();
        return controller;
      }
      dragOperation.status.set(
        "initializing"
        /* Initializing */
      );
      dragOperation.controller = controller;
      this.manager.renderer.rendering.then(() => {
        if (controller.signal.aborted) return;
        const { status } = dragOperation;
        if (status.current !== "initializing") return;
        n(() => {
          dragOperation.status.set(
            "dragging"
            /* Dragging */
          );
          this.manager.monitor.dispatch("dragstart", {
            nativeEvent,
            operation: dragOperation.snapshot(),
            cancelable: false
          });
        });
      });
      return controller;
    });
  }
  /**
   * Moves the dragged entity to a new position.
   *
   * @param args - Configuration for the move operation
   * @param args.by - Relative coordinates to move by
   * @param args.to - Absolute coordinates to move to
   * @param args.event - The event that triggered the move
   * @param args.cancelable - Whether the move can be canceled
   * @param args.propagate - Whether to dispatch dragmove events
   */
  move(args) {
    return f(() => {
      var _a5, _b3;
      const { dragOperation } = this.manager;
      const { status, controller } = dragOperation;
      if (!status.dragging || !controller || controller.signal.aborted) {
        return;
      }
      const event = defaultPreventable(
        {
          nativeEvent: args.event,
          operation: dragOperation.snapshot(),
          by: args.by,
          to: args.to
        },
        (_a5 = args.cancelable) != null ? _a5 : true
      );
      if ((_b3 = args.propagate) != null ? _b3 : true) {
        this.manager.monitor.dispatch("dragmove", event);
      }
      queueMicrotask(() => {
        var _a23, _b22, _c32, _d2, _e;
        if (event.defaultPrevented) {
          return;
        }
        const coordinates = (_e = args.to) != null ? _e : {
          x: dragOperation.position.current.x + ((_b22 = (_a23 = args.by) == null ? void 0 : _a23.x) != null ? _b22 : 0),
          y: dragOperation.position.current.y + ((_d2 = (_c32 = args.by) == null ? void 0 : _c32.y) != null ? _d2 : 0)
        };
        dragOperation.position.current = coordinates;
      });
    });
  }
  /**
   * Stops the current drag operation.
   *
   * @param args - Configuration for stopping the operation
   * @param args.event - The event that triggered the stop
   * @param args.canceled - Whether the operation was canceled
   * @remarks
   * This method:
   * - Dispatches a dragend event
   * - Allows suspension of the operation
   * - Handles cleanup of the operation state
   */
  stop(args = {}) {
    return f(() => {
      var _a5, _b3;
      const { dragOperation } = this.manager;
      const { controller } = dragOperation;
      if (!controller || controller.signal.aborted) return;
      let promise;
      const suspend = () => {
        const output = {
          resume: () => {
          },
          abort: () => {
          }
        };
        promise = new Promise((resolve, reject) => {
          output.resume = resolve;
          output.abort = reject;
        });
        return output;
      };
      controller.abort();
      const end = () => {
        this.manager.renderer.rendering.then(() => {
          dragOperation.status.set(
            "dropped"
            /* Dropped */
          );
          const dropping = f(
            () => {
              var _a23;
              return ((_a23 = dragOperation.source) == null ? void 0 : _a23.status) === "dropping";
            }
          );
          const cleanup = () => {
            if (dragOperation.controller === controller) {
              dragOperation.controller = void 0;
            }
            dragOperation.reset();
          };
          if (dropping) {
            const { source } = dragOperation;
            const dispose = j(() => {
              if ((source == null ? void 0 : source.status) === "idle") {
                dispose();
                cleanup();
              }
            });
          } else {
            this.manager.renderer.rendering.then(cleanup);
          }
        });
      };
      dragOperation.canceled = (_a5 = args.canceled) != null ? _a5 : false;
      this.manager.monitor.dispatch("dragend", {
        nativeEvent: args.event,
        operation: dragOperation.snapshot(),
        canceled: (_b3 = args.canceled) != null ? _b3 : false,
        suspend
      });
      if (promise) {
        promise.then(end).catch(() => dragOperation.reset());
      } else {
        end();
      }
    });
  }
};
var Sensor = class extends Plugin {
  /**
   * Creates a new sensor instance.
   *
   * @param manager - The drag drop manager instance
   * @param options - Optional sensor configuration
   */
  constructor(manager, options) {
    super(manager, options);
    this.manager = manager;
    this.options = options;
  }
};
var ActivationController = class extends AbortController {
  constructor(constraints, onActivate) {
    super();
    this.constraints = constraints;
    this.onActivate = onActivate;
    this.activated = false;
    for (const constraint of constraints != null ? constraints : []) {
      constraint.controller = this;
    }
  }
  onEvent(event) {
    var _a5;
    if (this.activated) return;
    if ((_a5 = this.constraints) == null ? void 0 : _a5.length) {
      for (const constraint of this.constraints) {
        constraint.onEvent(event);
      }
    } else {
      this.activate(event);
    }
  }
  activate(event) {
    if (this.activated) return;
    this.activated = true;
    this.onActivate(event);
  }
  abort(event) {
    this.activated = false;
    super.abort(event);
  }
};
var _controller;
var ActivationConstraint = class {
  constructor(options) {
    this.options = options;
    __privateAdd3(this, _controller);
  }
  set controller(controller) {
    __privateSet3(this, _controller, controller);
    controller.signal.addEventListener("abort", () => this.abort());
  }
  /**
   * Called when the activation is triggered.
   */
  activate(event) {
    var _a5;
    (_a5 = __privateGet3(this, _controller)) == null ? void 0 : _a5.activate(event);
  }
};
_controller = /* @__PURE__ */ new WeakMap();
var Modifier = class extends Plugin {
  /**
   * Creates a new modifier instance.
   *
   * @param manager - The drag and drop manager that owns this modifier
   * @param options - Optional configuration for the modifier
   */
  constructor(manager, options) {
    super(manager, options);
    this.manager = manager;
    this.options = options;
  }
  /**
   * Applies the modifier to the current drag operation.
   *
   * @param operation - The current state of the drag operation
   * @returns The transformed coordinates
   *
   * @remarks
   * Override this method to implement custom transformation logic.
   * The default implementation returns the original transform unchanged.
   */
  apply(operation) {
    return operation.transform;
  }
};
var DragDropRegistry = class {
  /**
   * Creates a new registry instance.
   *
   * @param manager - The drag and drop manager that owns this registry
   */
  constructor(manager) {
    this.draggables = new EntityRegistry();
    this.droppables = new EntityRegistry();
    this.plugins = new PluginRegistry(manager);
    this.sensors = new PluginRegistry(manager);
    this.modifiers = new PluginRegistry(manager);
  }
  register(input, options) {
    if (input instanceof Draggable) {
      return this.draggables.register(input.id, input);
    }
    if (input instanceof Droppable) {
      return this.droppables.register(input.id, input);
    }
    if (input.prototype instanceof Modifier) {
      return this.modifiers.register(input, options);
    }
    if (input.prototype instanceof Sensor) {
      return this.sensors.register(input, options);
    }
    if (input.prototype instanceof Plugin) {
      return this.plugins.register(input, options);
    }
    throw new Error("Invalid instance type");
  }
  unregister(input) {
    if (input instanceof Entity) {
      if (input instanceof Draggable) {
        return this.draggables.unregister(input.id, input);
      }
      if (input instanceof Droppable) {
        return this.droppables.unregister(input.id, input);
      }
      return () => {
      };
    }
    if (input.prototype instanceof Modifier) {
      return this.modifiers.unregister(input);
    }
    if (input.prototype instanceof Sensor) {
      return this.sensors.unregister(input);
    }
    if (input.prototype instanceof Plugin) {
      return this.plugins.unregister(input);
    }
    throw new Error("Invalid instance type");
  }
  /**
   * Destroys all registered entities and cleans up resources.
   *
   * @remarks
   * This method:
   * - Destroys all draggable and droppable entities
   * - Destroys all plugins, sensors, and modifiers
   * - Cleans up any associated resources
   */
  destroy() {
    this.draggables.destroy();
    this.droppables.destroy();
    this.plugins.destroy();
    this.sensors.destroy();
    this.modifiers.destroy();
  }
};
var _transform_dec;
var _target_dec;
var _source_dec;
var _modifiers_dec2;
var _targetIdentifier_dec;
var _sourceIdentifier_dec;
var _activatorEvent_dec;
var _canceled_dec;
var _shape_dec2;
var _manager2;
var _previousSource;
var _shape2;
var _init6;
var _canceled;
var _activatorEvent;
var _sourceIdentifier;
var _targetIdentifier;
var _modifiers2;
var _transform;
_shape_dec2 = [derived], _canceled_dec = [reactive], _activatorEvent_dec = [reactive], _sourceIdentifier_dec = [reactive], _targetIdentifier_dec = [reactive], _modifiers_dec2 = [reactive], _source_dec = [derived], _target_dec = [derived], _transform_dec = [derived];
var DragOperation = class {
  /**
   * Creates a new drag operation instance.
   *
   * @param manager - The drag and drop manager that owns this operation
   */
  constructor(manager) {
    __runInitializers3(_init6, 5, this);
    __privateAdd3(this, _manager2);
    __privateAdd3(this, _previousSource);
    __privateAdd3(this, _shape2, new ValueHistory(
      void 0,
      (a2, b2) => a2 && b2 ? a2.equals(b2) : a2 === b2
    ));
    this.status = new Status();
    __privateAdd3(this, _canceled, __runInitializers3(_init6, 8, this, false)), __runInitializers3(_init6, 11, this);
    __privateAdd3(this, _activatorEvent, __runInitializers3(_init6, 12, this, null)), __runInitializers3(_init6, 15, this);
    __privateAdd3(this, _sourceIdentifier, __runInitializers3(_init6, 16, this, null)), __runInitializers3(_init6, 19, this);
    __privateAdd3(this, _targetIdentifier, __runInitializers3(_init6, 20, this, null)), __runInitializers3(_init6, 23, this);
    __privateAdd3(this, _modifiers2, __runInitializers3(_init6, 24, this, [])), __runInitializers3(_init6, 27, this);
    this.position = new Position({ x: 0, y: 0 });
    __privateAdd3(this, _transform, { x: 0, y: 0 });
    __privateSet3(this, _manager2, manager);
  }
  get shape() {
    const { current, initial, previous } = __privateGet3(this, _shape2);
    if (!current || !initial) {
      return null;
    }
    return { current, initial, previous };
  }
  /**
   * Sets the shape of the dragged entity.
   *
   * @param value - The new shape or null to reset
   */
  set shape(value) {
    if (!value) {
      __privateGet3(this, _shape2).reset();
    } else {
      __privateGet3(this, _shape2).current = value;
    }
  }
  get source() {
    var _a5;
    const identifier = this.sourceIdentifier;
    if (identifier == null) return null;
    const value = __privateGet3(this, _manager2).registry.draggables.get(identifier);
    if (value) {
      __privateSet3(this, _previousSource, value);
    }
    return (_a5 = value != null ? value : __privateGet3(this, _previousSource)) != null ? _a5 : null;
  }
  get target() {
    var _a5;
    const identifier = this.targetIdentifier;
    return identifier != null ? (_a5 = __privateGet3(this, _manager2).registry.droppables.get(identifier)) != null ? _a5 : null : null;
  }
  get transform() {
    const { x: x2, y: y2 } = this.position.delta;
    let transform = { x: x2, y: y2 };
    for (const modifier of this.modifiers) {
      transform = modifier.apply(__spreadProps2(__spreadValues3({}, this.snapshot()), {
        transform
      }));
    }
    __privateSet3(this, _transform, transform);
    return transform;
  }
  /**
   * Creates a snapshot of the current drag operation state.
   *
   * @returns An immutable snapshot of the current operation state
   */
  snapshot() {
    return f(() => ({
      source: this.source,
      target: this.target,
      activatorEvent: this.activatorEvent,
      transform: __privateGet3(this, _transform),
      shape: this.shape ? snapshot(this.shape) : null,
      position: snapshot(this.position),
      status: snapshot(this.status),
      canceled: this.canceled
    }));
  }
  /**
   * Resets the drag operation to its initial state.
   *
   * @remarks
   * This method:
   * - Sets status to idle
   * - Clears source and target identifiers
   * - Resets shape history
   * - Resets position and transform
   * - Clears modifiers
   */
  reset() {
    n(() => {
      this.status.set(
        "idle"
        /* Idle */
      );
      this.sourceIdentifier = null;
      this.targetIdentifier = null;
      __privateGet3(this, _shape2).reset();
      this.position.reset({ x: 0, y: 0 });
      __privateSet3(this, _transform, { x: 0, y: 0 });
      this.modifiers = [];
    });
  }
};
_init6 = __decoratorStart3(null);
_manager2 = /* @__PURE__ */ new WeakMap();
_previousSource = /* @__PURE__ */ new WeakMap();
_shape2 = /* @__PURE__ */ new WeakMap();
_canceled = /* @__PURE__ */ new WeakMap();
_activatorEvent = /* @__PURE__ */ new WeakMap();
_sourceIdentifier = /* @__PURE__ */ new WeakMap();
_targetIdentifier = /* @__PURE__ */ new WeakMap();
_modifiers2 = /* @__PURE__ */ new WeakMap();
_transform = /* @__PURE__ */ new WeakMap();
__decorateElement3(_init6, 2, "shape", _shape_dec2, DragOperation);
__decorateElement3(_init6, 4, "canceled", _canceled_dec, DragOperation, _canceled);
__decorateElement3(_init6, 4, "activatorEvent", _activatorEvent_dec, DragOperation, _activatorEvent);
__decorateElement3(_init6, 4, "sourceIdentifier", _sourceIdentifier_dec, DragOperation, _sourceIdentifier);
__decorateElement3(_init6, 4, "targetIdentifier", _targetIdentifier_dec, DragOperation, _targetIdentifier);
__decorateElement3(_init6, 4, "modifiers", _modifiers_dec2, DragOperation, _modifiers2);
__decorateElement3(_init6, 2, "source", _source_dec, DragOperation);
__decorateElement3(_init6, 2, "target", _target_dec, DragOperation);
__decorateElement3(_init6, 2, "transform", _transform_dec, DragOperation);
__decoratorMetadata3(_init6, DragOperation);
var defaultRenderer = {
  get rendering() {
    return Promise.resolve();
  }
};
function resolveCustomizable(value, defaults3) {
  if (typeof value === "function") {
    return value(defaults3);
  }
  return value != null ? value : defaults3;
}
var DragDropManager = class {
  /**
   * Creates a new drag and drop manager instance.
   *
   * @param config - Optional configuration for plugins, sensors, modifiers, and renderer
   */
  constructor(config) {
    this.destroy = () => {
      if (!this.dragOperation.status.idle) {
        this.actions.stop({ canceled: true });
      }
      this.dragOperation.modifiers.forEach((modifier) => modifier.destroy());
      this.registry.destroy();
      this.collisionObserver.destroy();
    };
    var _a5;
    const raw = config != null ? config : {};
    const plugins = resolveCustomizable(raw.plugins, []);
    const sensors = resolveCustomizable(raw.sensors, []);
    const modifiers = resolveCustomizable(raw.modifiers, []);
    const renderer = (_a5 = raw.renderer) != null ? _a5 : defaultRenderer;
    const monitor = new DragDropMonitor(this);
    const registry = new DragDropRegistry(this);
    this.registry = registry;
    this.monitor = monitor;
    this.renderer = renderer;
    this.actions = new DragActions(this);
    this.dragOperation = new DragOperation(this);
    this.collisionObserver = new CollisionObserver(this);
    this.plugins = [CollisionNotifier, ...plugins];
    this.modifiers = modifiers;
    this.sensors = sensors;
    const { destroy } = this;
    const cleanup = effects(() => {
      var _a23, _b3, _c32;
      const currentModifiers = f(() => this.dragOperation.modifiers);
      const managerModifiers = this.modifiers;
      for (const modifier of currentModifiers) {
        if (!managerModifiers.includes(modifier)) {
          modifier.destroy();
        }
      }
      this.dragOperation.modifiers = (_c32 = (_b3 = (_a23 = this.dragOperation.source) == null ? void 0 : _a23.modifiers) == null ? void 0 : _b3.map((modifier) => {
        const { plugin, options } = descriptor(modifier);
        return new plugin(this, options);
      })) != null ? _c32 : managerModifiers;
    });
    this.destroy = () => {
      cleanup();
      destroy();
    };
  }
  /**
   * Gets the list of active plugins.
   *
   * @returns Array of active plugin instances
   */
  get plugins() {
    return this.registry.plugins.values;
  }
  /**
   * Sets the list of plugins to be used by the manager.
   *
   * @param plugins - Array of plugin constructors or instances
   */
  set plugins(plugins) {
    this.registry.plugins.values = plugins;
  }
  /**
   * Gets the list of active modifiers.
   *
   * @returns Array of active modifier instances
   */
  get modifiers() {
    return this.registry.modifiers.values;
  }
  /**
   * Sets the list of modifiers to be used by the manager.
   *
   * @param modifiers - Array of modifier constructors or instances
   */
  set modifiers(modifiers) {
    this.registry.modifiers.values = modifiers;
  }
  /**
   * Gets the list of active sensors.
   *
   * @returns Array of active sensor instances
   */
  get sensors() {
    return this.registry.sensors.values;
  }
  /**
   * Sets the list of sensors to be used by the manager.
   *
   * @param sensors - Array of sensor constructors or instances
   */
  set sensors(sensors) {
    this.registry.sensors.values = sensors;
  }
};

// tools/reading-order/node_modules/@dnd-kit/dom/utilities.js
var __typeError4 = (msg) => {
  throw TypeError(msg);
};
var __accessCheck4 = (obj, member, msg) => member.has(obj) || __typeError4("Cannot " + msg);
var __privateGet4 = (obj, member, getter) => (__accessCheck4(obj, member, "read from private field"), member.get(obj));
var __privateAdd4 = (obj, member, value) => member.has(obj) ? __typeError4("Cannot add the same private member more than once") : member instanceof WeakSet ? member.add(obj) : member.set(obj, value);
var __privateSet4 = (obj, member, value, setter) => (__accessCheck4(obj, member, "write to private field"), member.set(obj, value), value);
var __privateMethod4 = (obj, member, method) => (__accessCheck4(obj, member, "access private method"), method);
function isKeyframeEffect(effect) {
  if (!effect) return false;
  if (effect instanceof KeyframeEffect) return true;
  return "getKeyframes" in effect && typeof effect.getKeyframes === "function";
}
function getFinalKeyframe(element, match) {
  const animations2 = element.getAnimations();
  let result = null;
  for (const animation of animations2) {
    if (animation.playState !== "running") continue;
    const { effect } = animation;
    const keyframes = isKeyframeEffect(effect) ? effect.getKeyframes() : [];
    const matchedKeyframes = keyframes.filter(match);
    if (matchedKeyframes.length > 0) {
      result = [matchedKeyframes[matchedKeyframes.length - 1], animation];
    }
  }
  return result;
}
function getBoundingRectangle(element) {
  const { width, height, top, left, bottom, right } = element.getBoundingClientRect();
  return { width, height, top, left, bottom, right };
}
function isWindow(element) {
  const elementString = Object.prototype.toString.call(element);
  return elementString === "[object Window]" || // In Electron context the Window object serializes to [object global]
  elementString === "[object global]";
}
function isNode(node) {
  return "nodeType" in node;
}
function getWindow(target) {
  var _a5, _b3, _c4;
  if (!target) {
    return window;
  }
  if (isWindow(target)) {
    return target;
  }
  if (!isNode(target)) {
    return window;
  }
  if ("defaultView" in target) {
    return (_a5 = target.defaultView) != null ? _a5 : window;
  }
  return (_c4 = (_b3 = target.ownerDocument) == null ? void 0 : _b3.defaultView) != null ? _c4 : window;
}
function isDocument(node) {
  const { Document: Document2 } = getWindow(node);
  return node instanceof Document2 || "nodeType" in node && node.nodeType === Node.DOCUMENT_NODE;
}
function isHTMLElement(node) {
  if (!node || isWindow(node)) return false;
  return node instanceof getWindow(node).HTMLElement || "namespaceURI" in node && typeof node.namespaceURI === "string" && node.namespaceURI.endsWith("html");
}
function isSVGElement(node) {
  return node instanceof getWindow(node).SVGElement || "namespaceURI" in node && typeof node.namespaceURI === "string" && node.namespaceURI.endsWith("svg");
}
function getDocument(target) {
  if (!target) {
    return document;
  }
  if (isWindow(target)) {
    return target.document;
  }
  if (!isNode(target)) {
    return document;
  }
  if (isDocument(target)) {
    return target;
  }
  if (isHTMLElement(target) || isSVGElement(target)) {
    return target.ownerDocument;
  }
  return document;
}
function getViewportBoundingRectangle(element) {
  var _a5, _b3, _c4, _d2;
  const { documentElement } = getDocument(element);
  const vv = getWindow(element).visualViewport;
  const width = (_a5 = vv == null ? void 0 : vv.width) != null ? _a5 : documentElement.clientWidth;
  const height = (_b3 = vv == null ? void 0 : vv.height) != null ? _b3 : documentElement.clientHeight;
  const top = (_c4 = vv == null ? void 0 : vv.offsetTop) != null ? _c4 : 0;
  const left = (_d2 = vv == null ? void 0 : vv.offsetLeft) != null ? _d2 : 0;
  return {
    top,
    left,
    right: left + width,
    bottom: top + height,
    width,
    height
  };
}
function isOverflowVisible(element, style) {
  if (isDetailsElement(element) && element.open === false) {
    return false;
  }
  const { overflow, overflowX, overflowY } = getComputedStyle(element);
  return overflow === "visible" && overflowX === "visible" && overflowY === "visible";
}
function isDetailsElement(element) {
  return element.tagName === "DETAILS";
}
function getVisibleBoundingRectangle(element, boundingClientRect = element.getBoundingClientRect(), margin = 0) {
  var _a5, _b3, _c4, _d2, _e;
  let rect = boundingClientRect;
  const { ownerDocument } = element;
  const ownerWindow = (_a5 = ownerDocument.defaultView) != null ? _a5 : window;
  let ancestor = element.parentElement;
  while (ancestor && ancestor !== ownerDocument.documentElement) {
    if (!isOverflowVisible(ancestor)) {
      const ancestorRect = ancestor.getBoundingClientRect();
      const marginTop = margin * (ancestorRect.bottom - ancestorRect.top);
      const marginRight = margin * (ancestorRect.right - ancestorRect.left);
      const marginBottom = margin * (ancestorRect.bottom - ancestorRect.top);
      const marginLeft = margin * (ancestorRect.right - ancestorRect.left);
      rect = {
        top: Math.max(rect.top, ancestorRect.top - marginTop),
        right: Math.min(rect.right, ancestorRect.right + marginRight),
        bottom: Math.min(rect.bottom, ancestorRect.bottom + marginBottom),
        left: Math.max(rect.left, ancestorRect.left - marginLeft),
        width: 0,
        // Will be calculated next
        height: 0
        // Will be calculated next
      };
      rect.width = rect.right - rect.left;
      rect.height = rect.bottom - rect.top;
    }
    ancestor = ancestor.parentElement;
  }
  const vv = ownerWindow.visualViewport;
  const viewportTop = (_b3 = vv == null ? void 0 : vv.offsetTop) != null ? _b3 : 0;
  const viewportLeft = (_c4 = vv == null ? void 0 : vv.offsetLeft) != null ? _c4 : 0;
  const viewportWidth = (_d2 = vv == null ? void 0 : vv.width) != null ? _d2 : ownerWindow.innerWidth;
  const viewportHeight = (_e = vv == null ? void 0 : vv.height) != null ? _e : ownerWindow.innerHeight;
  const viewportMarginY = margin * viewportHeight;
  const viewportMarginX = margin * viewportWidth;
  rect = {
    top: Math.max(rect.top, viewportTop - viewportMarginY),
    right: Math.min(
      rect.right,
      viewportLeft + viewportWidth + viewportMarginX
    ),
    bottom: Math.min(
      rect.bottom,
      viewportTop + viewportHeight + viewportMarginY
    ),
    left: Math.max(rect.left, viewportLeft - viewportMarginX),
    width: 0,
    // Will be calculated next
    height: 0
    // Will be calculated next
  };
  rect.width = rect.right - rect.left;
  rect.height = rect.bottom - rect.top;
  if (rect.width < 0) {
    rect.width = 0;
  }
  if (rect.height < 0) {
    rect.height = 0;
  }
  return rect;
}
function getEventCoordinates(event) {
  return {
    x: event.clientX,
    y: event.clientY
  };
}
var canUseDOM = typeof window !== "undefined" && typeof window.document !== "undefined" && typeof window.document.createElement !== "undefined";
function getDocuments(rootDoc = document, seen = /* @__PURE__ */ new Set()) {
  if (seen.has(rootDoc)) return [];
  seen.add(rootDoc);
  const docs = [rootDoc];
  for (const frame of Array.from(
    rootDoc.querySelectorAll("iframe, frame")
  )) {
    try {
      const childDoc = frame.contentDocument;
      if (childDoc && !seen.has(childDoc)) {
        docs.push(...getDocuments(childDoc, seen));
      }
    } catch (e2) {
    }
  }
  try {
    const win = rootDoc.defaultView;
    if (win && win !== window.top) {
      const parentWin = win.parent;
      if (parentWin && parentWin.document && parentWin.document !== rootDoc) {
        docs.push(...getDocuments(parentWin.document, seen));
      }
    }
  } catch (e2) {
  }
  return docs;
}
function isSafari() {
  return /^((?!chrome|android).)*safari/i.test(navigator.userAgent);
}
function getFixedPositionOffset() {
  var _a5, _b3;
  const vv = isSafari() ? window.visualViewport : null;
  return {
    x: (_a5 = vv == null ? void 0 : vv.offsetLeft) != null ? _a5 : 0,
    y: (_b3 = vv == null ? void 0 : vv.offsetTop) != null ? _b3 : 0
  };
}
function isShadowRoot(target) {
  if (!target || !isNode(target)) return false;
  return target instanceof getWindow(target).ShadowRoot;
}
function getRoot(target) {
  if (target && isNode(target)) {
    let root = target.getRootNode();
    if (isShadowRoot(root)) {
      return root;
    } else if (root instanceof Document) {
      return root;
    }
  }
  return getDocument(target);
}
function prefersReducedMotion(window2) {
  return window2.matchMedia("(prefers-reduced-motion: reduce)").matches;
}
function cloneElement(element) {
  const selector = "input, textarea, select, canvas, [contenteditable]";
  const clonedElement = element.cloneNode(true);
  const fields = Array.from(element.querySelectorAll(selector));
  const clonedFields = Array.from(clonedElement.querySelectorAll(selector));
  clonedFields.forEach((field, index) => {
    const originalField = fields[index];
    if (isField(field) && isField(originalField)) {
      if (field.type !== "file") {
        field.value = originalField.value;
      }
      if (field.type === "radio" && field.name) {
        field.name = `Cloned__${field.name}`;
      }
    }
    if (isCanvasElement(field) && isCanvasElement(originalField) && originalField.width > 0 && originalField.height > 0) {
      const destCtx = field.getContext("2d");
      destCtx == null ? void 0 : destCtx.drawImage(originalField, 0, 0);
    }
  });
  return clonedElement;
}
function isField(element) {
  return "value" in element;
}
function isCanvasElement(element) {
  return element.tagName === "CANVAS";
}
function getElementFromPoint(root, { x: x2, y: y2 }) {
  const element = root.elementFromPoint(x2, y2);
  if (isIFrameElement(element)) {
    const { contentDocument } = element;
    if (contentDocument) {
      const { left, top } = element.getBoundingClientRect();
      return getElementFromPoint(contentDocument, {
        x: x2 - left,
        y: y2 - top
      });
    }
  }
  return element;
}
function isIFrameElement(element) {
  return (element == null ? void 0 : element.tagName) === "IFRAME";
}
var ProxiedElements = /* @__PURE__ */ new WeakMap();
function getInteractiveElement(element) {
  return element.closest(`
    input:not([disabled]),
    select:not([disabled]),
    textarea:not([disabled]),
    button:not([disabled]),
    a[href],
    [contenteditable]:not([contenteditable="false"])
  `);
}
var Listeners = class {
  constructor() {
    this.entries = /* @__PURE__ */ new Set();
    this.clear = () => {
      for (const entry of this.entries) {
        const [target, { type, listener, options }] = entry;
        target.removeEventListener(type, listener, options);
      }
      this.entries.clear();
    };
  }
  bind(target, input) {
    const eventTargets = Array.isArray(target) ? target : [target];
    const listeners = Array.isArray(input) ? input : [input];
    const entries = [];
    for (const target2 of eventTargets) {
      for (const descriptor2 of listeners) {
        const { type, listener, options } = descriptor2;
        const entry = [target2, descriptor2];
        target2.addEventListener(type, listener, options);
        this.entries.add(entry);
        entries.push(entry);
      }
    }
    const allEntries = this.entries;
    return function cleanup() {
      for (const entry of entries) {
        const [target2, { type, listener, options }] = entry;
        target2.removeEventListener(type, listener, options);
        allEntries.delete(entry);
      }
    };
  }
};
function getFrameElement(el) {
  const refWindow = el == null ? void 0 : el.ownerDocument.defaultView;
  if (refWindow && refWindow.self !== refWindow.parent) {
    return refWindow.frameElement;
  }
}
function getFrameElements(el) {
  const frames = /* @__PURE__ */ new Set();
  let frame = getFrameElement(el);
  while (frame) {
    frames.add(frame);
    frame = getFrameElement(frame);
  }
  return frames;
}
function timeout(callback, duration) {
  const id = setTimeout(callback, duration);
  return () => clearTimeout(id);
}
function throttle(func, limit) {
  const time = () => performance.now();
  let cancel;
  let lastRan;
  return function(...args) {
    const context = this;
    if (!lastRan) {
      func.apply(context, args);
      lastRan = time();
    } else {
      cancel == null ? void 0 : cancel();
      cancel = timeout(
        () => {
          func.apply(context, args);
          lastRan = time();
        },
        limit - (time() - lastRan)
      );
    }
  };
}
function isRectEqual(a2, b2) {
  if (a2 === b2) return true;
  if (!a2 || !b2) return false;
  return a2.top == b2.top && a2.left == b2.left && a2.right == b2.right && a2.bottom == b2.bottom;
}
function isVisible(element, boundingClientRect = element.getBoundingClientRect()) {
  const { width, height } = getVisibleBoundingRectangle(
    element,
    boundingClientRect
  );
  return width > 0 && height > 0;
}
var Observer = canUseDOM ? ResizeObserver : class MockResizeObserver {
  observe() {
  }
  unobserve() {
  }
  disconnect() {
  }
};
var _initialized;
var ResizeNotifier = class extends Observer {
  constructor(callback) {
    super((entries) => {
      if (!__privateGet4(this, _initialized)) {
        __privateSet4(this, _initialized, true);
        return;
      }
      callback(entries, this);
    });
    __privateAdd4(this, _initialized, false);
  }
};
_initialized = /* @__PURE__ */ new WeakMap();
var threshold = Array.from({ length: 100 }, (_2, index) => index / 100);
var THROTTLE_INTERVAL = 75;
var _visible;
var _previousBoundingClientRect;
var _resizeObserver;
var _positionObserver;
var _visibilityObserver;
var _debug;
var _disconnected;
var _observePosition;
var _PositionObserver_instances;
var notify_fn;
var updateDebug_fn;
var PositionObserver = class {
  constructor(element, callback, options = {
    debug: false,
    skipInitial: false
  }) {
    this.element = element;
    this.callback = callback;
    __privateAdd4(this, _PositionObserver_instances);
    this.disconnect = () => {
      var _a5, _b3, _c4;
      __privateSet4(this, _disconnected, true);
      (_a5 = __privateGet4(this, _resizeObserver)) == null ? void 0 : _a5.disconnect();
      (_b3 = __privateGet4(this, _positionObserver)) == null ? void 0 : _b3.disconnect();
      __privateGet4(this, _visibilityObserver).disconnect();
      (_c4 = __privateGet4(this, _debug)) == null ? void 0 : _c4.remove();
    };
    __privateAdd4(this, _visible, true);
    __privateAdd4(this, _previousBoundingClientRect);
    __privateAdd4(this, _resizeObserver);
    __privateAdd4(this, _positionObserver);
    __privateAdd4(this, _visibilityObserver);
    __privateAdd4(this, _debug);
    __privateAdd4(this, _disconnected, false);
    __privateAdd4(this, _observePosition, throttle(() => {
      var _a5, _b3, _c4;
      const { element: element2 } = this;
      (_a5 = __privateGet4(this, _positionObserver)) == null ? void 0 : _a5.disconnect();
      if (__privateGet4(this, _disconnected) || !__privateGet4(this, _visible) || !element2.isConnected) {
        return;
      }
      const root2 = (_b3 = element2.ownerDocument) != null ? _b3 : document;
      const { innerHeight: innerHeight2, innerWidth: innerWidth2 } = (_c4 = root2.defaultView) != null ? _c4 : window;
      const clientRect = element2.getBoundingClientRect();
      const visibleRect = getVisibleBoundingRectangle(element2, clientRect);
      const { top, left, bottom, right } = visibleRect;
      const insetTop = -Math.floor(top);
      const insetLeft = -Math.floor(left);
      const insetRight = -Math.floor(innerWidth2 - right);
      const insetBottom = -Math.floor(innerHeight2 - bottom);
      const rootMargin = `${insetTop}px ${insetRight}px ${insetBottom}px ${insetLeft}px`;
      this.boundingClientRect = clientRect;
      __privateSet4(this, _positionObserver, new IntersectionObserver(
        (entries) => {
          const [entry] = entries;
          const { intersectionRect } = entry;
          const intersectionRatio = entry.intersectionRatio !== 1 ? entry.intersectionRatio : Rectangle.intersectionRatio(
            intersectionRect,
            getVisibleBoundingRectangle(element2)
          );
          if (intersectionRatio !== 1) {
            __privateGet4(this, _observePosition).call(this);
          }
        },
        {
          threshold,
          rootMargin,
          root: root2
        }
      ));
      __privateGet4(this, _positionObserver).observe(element2);
      __privateMethod4(this, _PositionObserver_instances, notify_fn).call(this);
    }, THROTTLE_INTERVAL));
    this.boundingClientRect = element.getBoundingClientRect();
    __privateSet4(this, _visible, isVisible(element, this.boundingClientRect));
    let initial = true;
    this.callback = (boundingClientRect) => {
      if (initial) {
        initial = false;
        if (options.skipInitial) return;
      }
      callback(boundingClientRect);
    };
    const root = element.ownerDocument;
    if (options == null ? void 0 : options.debug) {
      __privateSet4(this, _debug, document.createElement("div"));
      __privateGet4(this, _debug).style.background = "rgba(0,0,0,0.15)";
      __privateGet4(this, _debug).style.position = "fixed";
      __privateGet4(this, _debug).style.pointerEvents = "none";
      root.body.appendChild(__privateGet4(this, _debug));
    }
    __privateSet4(this, _visibilityObserver, new IntersectionObserver(
      (entries) => {
        var _a5, _b3;
        const entry = entries[entries.length - 1];
        const { boundingClientRect, isIntersecting: visible } = entry;
        const { width, height } = boundingClientRect;
        const previousVisible = __privateGet4(this, _visible);
        __privateSet4(this, _visible, visible);
        if (!width && !height) return;
        if (previousVisible && !visible) {
          (_a5 = __privateGet4(this, _positionObserver)) == null ? void 0 : _a5.disconnect();
          this.callback(null);
          (_b3 = __privateGet4(this, _resizeObserver)) == null ? void 0 : _b3.disconnect();
          __privateSet4(this, _resizeObserver, void 0);
          if (__privateGet4(this, _debug)) __privateGet4(this, _debug).style.visibility = "hidden";
        } else {
          __privateGet4(this, _observePosition).call(this);
        }
        if (visible && !__privateGet4(this, _resizeObserver)) {
          __privateSet4(this, _resizeObserver, new ResizeNotifier(__privateGet4(this, _observePosition)));
          __privateGet4(this, _resizeObserver).observe(element);
        }
      },
      {
        threshold,
        root
      }
    ));
    if (__privateGet4(this, _visible) && !options.skipInitial) {
      this.callback(this.boundingClientRect);
    }
    __privateGet4(this, _visibilityObserver).observe(element);
  }
};
_visible = /* @__PURE__ */ new WeakMap();
_previousBoundingClientRect = /* @__PURE__ */ new WeakMap();
_resizeObserver = /* @__PURE__ */ new WeakMap();
_positionObserver = /* @__PURE__ */ new WeakMap();
_visibilityObserver = /* @__PURE__ */ new WeakMap();
_debug = /* @__PURE__ */ new WeakMap();
_disconnected = /* @__PURE__ */ new WeakMap();
_observePosition = /* @__PURE__ */ new WeakMap();
_PositionObserver_instances = /* @__PURE__ */ new WeakSet();
notify_fn = function() {
  if (__privateGet4(this, _disconnected)) return;
  __privateMethod4(this, _PositionObserver_instances, updateDebug_fn).call(this);
  if (isRectEqual(this.boundingClientRect, __privateGet4(this, _previousBoundingClientRect)))
    return;
  this.callback(this.boundingClientRect);
  __privateSet4(this, _previousBoundingClientRect, this.boundingClientRect);
};
updateDebug_fn = function() {
  if (__privateGet4(this, _debug)) {
    const { top, left, width, height } = getVisibleBoundingRectangle(
      this.element
    );
    __privateGet4(this, _debug).style.overflow = "hidden";
    __privateGet4(this, _debug).style.visibility = "visible";
    __privateGet4(this, _debug).style.top = `${Math.floor(top)}px`;
    __privateGet4(this, _debug).style.left = `${Math.floor(left)}px`;
    __privateGet4(this, _debug).style.width = `${Math.floor(width)}px`;
    __privateGet4(this, _debug).style.height = `${Math.floor(height)}px`;
  }
};
var framePositionObservers = /* @__PURE__ */ new WeakMap();
var scrollListeners = /* @__PURE__ */ new WeakMap();
function addFrameListener(frame, callback) {
  let cached = framePositionObservers.get(frame);
  if (!cached) {
    const observer = new PositionObserver(
      frame,
      (boundingClientRect) => {
        const cached2 = framePositionObservers.get(frame);
        if (!cached2) return;
        cached2.callbacks.forEach((callback2) => callback2(boundingClientRect));
      },
      { skipInitial: true }
    );
    cached = { disconnect: observer.disconnect, callbacks: /* @__PURE__ */ new Set() };
  }
  cached.callbacks.add(callback);
  framePositionObservers.set(frame, cached);
  return () => {
    cached.callbacks.delete(callback);
    if (cached.callbacks.size === 0) {
      framePositionObservers.delete(frame);
      cached.disconnect();
    }
  };
}
function observeParentFrames(frames, callback) {
  const cleanup = /* @__PURE__ */ new Set();
  for (const frame of frames) {
    const remove = addFrameListener(frame, callback);
    cleanup.add(remove);
  }
  return () => cleanup.forEach((remove) => remove());
}
function addScrollListener(element, callback) {
  var _a5;
  const doc = element.ownerDocument;
  if (!scrollListeners.has(doc)) {
    const controller = new AbortController();
    const listeners2 = /* @__PURE__ */ new Set();
    document.addEventListener(
      "scroll",
      (event) => listeners2.forEach((listener) => listener(event)),
      {
        capture: true,
        passive: true,
        signal: controller.signal
      }
    );
    scrollListeners.set(doc, { disconnect: () => controller.abort(), listeners: listeners2 });
  }
  const { listeners, disconnect } = (_a5 = scrollListeners.get(doc)) != null ? _a5 : {};
  if (!listeners || !disconnect) return () => {
  };
  listeners.add(callback);
  return () => {
    listeners.delete(callback);
    if (listeners.size === 0) {
      disconnect();
      scrollListeners.delete(doc);
    }
  };
}
var _elementObserver;
var _disconnected2;
var _frames;
var _handleScroll;
var FrameObserver = class {
  constructor(element, callback, options) {
    this.callback = callback;
    __privateAdd4(this, _elementObserver);
    __privateAdd4(this, _disconnected2, false);
    __privateAdd4(this, _frames);
    __privateAdd4(this, _handleScroll, throttle((event) => {
      if (__privateGet4(this, _disconnected2)) return;
      if (!event.target) return;
      if ("contains" in event.target && typeof event.target.contains === "function") {
        for (const frame of __privateGet4(this, _frames)) {
          if (event.target.contains(frame)) {
            this.callback(__privateGet4(this, _elementObserver).boundingClientRect);
            break;
          }
        }
      }
    }, THROTTLE_INTERVAL));
    const frames = getFrameElements(element);
    const unobserveParentFrames = observeParentFrames(frames, callback);
    const removeScrollListener = addScrollListener(element, __privateGet4(this, _handleScroll));
    __privateSet4(this, _frames, frames);
    __privateSet4(this, _elementObserver, new PositionObserver(element, callback, options));
    this.disconnect = () => {
      if (__privateGet4(this, _disconnected2)) return;
      __privateSet4(this, _disconnected2, true);
      unobserveParentFrames();
      removeScrollListener();
      __privateGet4(this, _elementObserver).disconnect();
    };
  }
};
_elementObserver = /* @__PURE__ */ new WeakMap();
_disconnected2 = /* @__PURE__ */ new WeakMap();
_frames = /* @__PURE__ */ new WeakMap();
_handleScroll = /* @__PURE__ */ new WeakMap();
function supportsPopover(element) {
  return "showPopover" in element && "hidePopover" in element && typeof element.showPopover === "function" && typeof element.hidePopover === "function";
}
function showPopover(element) {
  try {
    if (supportsPopover(element) && element.isConnected && element.hasAttribute("popover") && // This selector can throw an error in browsers that don't support it
    !element.matches(":popover-open")) {
      element.showPopover();
    }
  } catch (error) {
  }
}
function isDocumentScrollingElement(element) {
  if (!canUseDOM || !element) {
    return false;
  }
  return element === getDocument(element).scrollingElement;
}
function getScrollPosition(scrollableElement) {
  var _a5, _b3;
  const window2 = getWindow(scrollableElement);
  const rect = isDocumentScrollingElement(scrollableElement) ? getViewportBoundingRectangle(scrollableElement) : getBoundingRectangle(scrollableElement);
  const vv = window2.visualViewport;
  const dimensions = isDocumentScrollingElement(scrollableElement) ? {
    height: (_a5 = vv == null ? void 0 : vv.height) != null ? _a5 : window2.innerHeight,
    width: (_b3 = vv == null ? void 0 : vv.width) != null ? _b3 : window2.innerWidth
  } : {
    height: scrollableElement.clientHeight,
    width: scrollableElement.clientWidth
  };
  const position = {
    current: {
      x: scrollableElement.scrollLeft,
      y: scrollableElement.scrollTop
    },
    max: {
      x: scrollableElement.scrollWidth - dimensions.width,
      y: scrollableElement.scrollHeight - dimensions.height
    }
  };
  const isTop = position.current.y <= 0;
  const isLeft = position.current.x <= 0;
  const isBottom = position.current.y >= position.max.y;
  const isRight = position.current.x >= position.max.x;
  return {
    rect,
    position,
    isTop,
    isLeft,
    isBottom,
    isRight
  };
}
function canScroll(scrollableElement, by) {
  const { isTop, isBottom, isLeft, isRight, position } = getScrollPosition(scrollableElement);
  const { x: x2, y: y2 } = by != null ? by : { x: 0, y: 0 };
  const top = !isTop && position.current.y + y2 > 0;
  const bottom = !isBottom && position.current.y + y2 < position.max.y;
  const left = !isLeft && position.current.x + x2 > 0;
  const right = !isRight && position.current.x + x2 < position.max.x;
  return {
    top,
    bottom,
    left,
    right,
    x: left || right,
    y: top || bottom
  };
}
var Scheduler = class {
  constructor(scheduler4) {
    this.scheduler = scheduler4;
    this.pending = false;
    this.tasks = /* @__PURE__ */ new Set();
    this.resolvers = /* @__PURE__ */ new Set();
    this.flush = () => {
      const { tasks, resolvers } = this;
      this.pending = false;
      this.tasks = /* @__PURE__ */ new Set();
      this.resolvers = /* @__PURE__ */ new Set();
      for (const task of tasks) {
        task();
      }
      for (const resolve of resolvers) {
        resolve();
      }
    };
  }
  schedule(task) {
    this.tasks.add(task);
    if (!this.pending) {
      this.pending = true;
      this.scheduler(this.flush);
    }
    return new Promise((resolve) => this.resolvers.add(resolve));
  }
};
var scheduler = new Scheduler((callback) => {
  if (typeof requestAnimationFrame === "function") {
    requestAnimationFrame(callback);
  } else {
    callback();
  }
});
var scheduler2 = new Scheduler((callback) => setTimeout(callback, 50));
var cachedStyles = /* @__PURE__ */ new Map();
var clear = cachedStyles.clear.bind(cachedStyles);
function getComputedStyles(element, cached = false) {
  if (!cached) return computeStyles(element);
  let styles = cachedStyles.get(element);
  if (styles) return styles;
  styles = computeStyles(element);
  cachedStyles.set(element, styles);
  scheduler2.schedule(clear);
  return styles;
}
function computeStyles(element) {
  return getWindow(element).getComputedStyle(element);
}
function isFixed(node, computedStyle = getComputedStyles(node, true)) {
  return computedStyle.position === "fixed" || computedStyle.position === "sticky";
}
function isScrollable(element, computedStyle = getComputedStyles(element, true)) {
  const overflowRegex = /(auto|scroll|overlay)/;
  const properties = ["overflow", "overflowX", "overflowY"];
  return properties.some((property) => {
    const value = computedStyle[property];
    return typeof value === "string" ? overflowRegex.test(value) : false;
  });
}
var defaultOptions = {
  excludeElement: true,
  escapeShadowDOM: true
};
function getScrollableAncestors(element, options = defaultOptions) {
  const { limit, excludeElement, escapeShadowDOM } = options;
  const scrollParents = /* @__PURE__ */ new Set();
  function findScrollableAncestors(node) {
    if (limit != null && scrollParents.size >= limit) {
      return scrollParents;
    }
    if (!node) {
      return scrollParents;
    }
    if (isDocument(node) && node.scrollingElement != null && !scrollParents.has(node.scrollingElement)) {
      scrollParents.add(node.scrollingElement);
      return scrollParents;
    }
    if (escapeShadowDOM && isShadowRoot(node)) {
      return findScrollableAncestors(node.host);
    }
    if (!isHTMLElement(node)) {
      if (isSVGElement(node)) {
        return findScrollableAncestors(node.parentElement);
      }
      return scrollParents;
    }
    if (scrollParents.has(node)) {
      return scrollParents;
    }
    const computedStyle = getComputedStyles(node, true);
    if (excludeElement && node === element) ;
    else if (isScrollable(node, computedStyle)) {
      scrollParents.add(node);
    }
    if (isFixed(node, computedStyle)) {
      const { scrollingElement } = node.ownerDocument;
      if (scrollingElement) scrollParents.add(scrollingElement);
      return scrollParents;
    }
    return findScrollableAncestors(node.parentNode);
  }
  if (!element) {
    return scrollParents;
  }
  return findScrollableAncestors(element);
}
function getFrameTransform(el, boundary = window.frameElement) {
  const transform = {
    x: 0,
    y: 0,
    scaleX: 1,
    scaleY: 1
  };
  if (!el) return transform;
  let frame = getFrameElement(el);
  while (frame) {
    if (frame === boundary) {
      return transform;
    }
    const rect = getBoundingRectangle(frame);
    const { x: scaleX, y: scaleY } = getScale(frame, rect);
    transform.x = transform.x + rect.left;
    transform.y = transform.y + rect.top;
    transform.scaleX = transform.scaleX * scaleX;
    transform.scaleY = transform.scaleY * scaleY;
    frame = getFrameElement(frame);
  }
  return transform;
}
function getScale(element, boundingRectangle = getBoundingRectangle(element)) {
  const width = Math.round(boundingRectangle.width);
  const height = Math.round(boundingRectangle.height);
  if (isHTMLElement(element)) {
    return {
      x: width / element.offsetWidth,
      y: height / element.offsetHeight
    };
  }
  const styles = getComputedStyles(element, true);
  return {
    x: (parseFloat(styles.width) || width) / width,
    y: (parseFloat(styles.height) || height) / height
  };
}
function parseScale(scale) {
  if (!scale || scale === "none") {
    return null;
  }
  const values = scale.split(" ");
  const x2 = parseFloat(values[0]);
  const y2 = parseFloat(values[1]);
  if (isNaN(x2) && isNaN(y2)) {
    return null;
  }
  return {
    x: isNaN(x2) ? y2 : x2,
    y: isNaN(y2) ? x2 : y2
  };
}
function parseTranslate(translate) {
  if (!translate || translate === "none") {
    return null;
  }
  const [x2, y2, z = "0"] = translate.split(" ");
  const output = { x: parseFloat(x2), y: parseFloat(y2), z: parseInt(z, 10) };
  if (isNaN(output.x) && isNaN(output.y)) {
    return null;
  }
  return {
    x: isNaN(output.x) ? 0 : output.x,
    y: isNaN(output.y) ? 0 : output.y,
    z: isNaN(output.z) ? 0 : output.z
  };
}
function parseTransform(computedStyles) {
  var _a5, _b3, _c4, _d2, _e, _f, _g, _h, _i;
  const { scale, transform, translate } = computedStyles;
  const parsedScale = parseScale(scale);
  const parsedTranslate = parseTranslate(translate);
  const parsedMatrix = parseTransformMatrix(transform);
  if (!parsedMatrix && !parsedScale && !parsedTranslate) {
    return null;
  }
  const normalizedScale = {
    x: (_a5 = parsedScale == null ? void 0 : parsedScale.x) != null ? _a5 : 1,
    y: (_b3 = parsedScale == null ? void 0 : parsedScale.y) != null ? _b3 : 1
  };
  const normalizedTranslate = {
    x: (_c4 = parsedTranslate == null ? void 0 : parsedTranslate.x) != null ? _c4 : 0,
    y: (_d2 = parsedTranslate == null ? void 0 : parsedTranslate.y) != null ? _d2 : 0
  };
  const normalizedMatrix = {
    x: (_e = parsedMatrix == null ? void 0 : parsedMatrix.x) != null ? _e : 0,
    y: (_f = parsedMatrix == null ? void 0 : parsedMatrix.y) != null ? _f : 0,
    scaleX: (_g = parsedMatrix == null ? void 0 : parsedMatrix.scaleX) != null ? _g : 1,
    scaleY: (_h = parsedMatrix == null ? void 0 : parsedMatrix.scaleY) != null ? _h : 1
  };
  return {
    x: normalizedTranslate.x + normalizedMatrix.x,
    y: normalizedTranslate.y + normalizedMatrix.y,
    z: (_i = parsedTranslate == null ? void 0 : parsedTranslate.z) != null ? _i : 0,
    scaleX: normalizedScale.x * normalizedMatrix.scaleX,
    scaleY: normalizedScale.y * normalizedMatrix.scaleY
  };
}
function parseTransformMatrix(transform) {
  if (transform.startsWith("matrix3d(")) {
    const transformArray = transform.slice(9, -1).split(/, /);
    return {
      x: +transformArray[12],
      y: +transformArray[13],
      scaleX: +transformArray[0],
      scaleY: +transformArray[5]
    };
  } else if (transform.startsWith("matrix(")) {
    const transformArray = transform.slice(7, -1).split(/, /);
    return {
      x: +transformArray[4],
      y: +transformArray[5],
      scaleX: +transformArray[0],
      scaleY: +transformArray[3]
    };
  }
  return null;
}
var ScrollDirection = /* @__PURE__ */ ((ScrollDirection2) => {
  ScrollDirection2[ScrollDirection2["Idle"] = 0] = "Idle";
  ScrollDirection2[ScrollDirection2["Forward"] = 1] = "Forward";
  ScrollDirection2[ScrollDirection2["Reverse"] = -1] = "Reverse";
  return ScrollDirection2;
})(ScrollDirection || {});
var defaultThreshold = {
  x: 0.2,
  y: 0.2
};
var defaultTolerance = {
  x: 10,
  y: 10
};
function detectScrollIntent(scrollableElement, coordinates, intent, acceleration = 25, thresholdPercentage = defaultThreshold, tolerance = defaultTolerance) {
  const { x: x2, y: y2 } = coordinates;
  const { rect, isTop, isBottom, isLeft, isRight } = getScrollPosition(scrollableElement);
  const frameTransform = getFrameTransform(scrollableElement);
  const computedStyles = getComputedStyles(scrollableElement, true);
  const parsedTransform = parseTransform(computedStyles);
  const isXAxisInverted = parsedTransform !== null ? (parsedTransform == null ? void 0 : parsedTransform.scaleX) < 0 : false;
  const isYAxisInverted = parsedTransform !== null ? (parsedTransform == null ? void 0 : parsedTransform.scaleY) < 0 : false;
  const scrollContainerRect = new Rectangle(
    rect.left * frameTransform.scaleX + frameTransform.x,
    rect.top * frameTransform.scaleY + frameTransform.y,
    rect.width * frameTransform.scaleX,
    rect.height * frameTransform.scaleY
  );
  const direction = {
    x: 0,
    y: 0
    /* Idle */
  };
  const speed = {
    x: 0,
    y: 0
  };
  const threshold2 = {
    height: scrollContainerRect.height * thresholdPercentage.y,
    width: scrollContainerRect.width * thresholdPercentage.x
  };
  if (threshold2.height > 0 && (!isTop || isYAxisInverted && !isBottom) && y2 <= scrollContainerRect.top + threshold2.height && (intent == null ? void 0 : intent.y) !== 1 && x2 >= scrollContainerRect.left - tolerance.x && x2 <= scrollContainerRect.right + tolerance.x) {
    direction.y = isYAxisInverted ? 1 : -1;
    speed.y = acceleration * Math.abs(
      (scrollContainerRect.top + threshold2.height - y2) / threshold2.height
    );
  } else if (threshold2.height > 0 && (!isBottom || isYAxisInverted && !isTop) && y2 >= scrollContainerRect.bottom - threshold2.height && (intent == null ? void 0 : intent.y) !== -1 && x2 >= scrollContainerRect.left - tolerance.x && x2 <= scrollContainerRect.right + tolerance.x) {
    direction.y = isYAxisInverted ? -1 : 1;
    speed.y = acceleration * Math.abs(
      (scrollContainerRect.bottom - threshold2.height - y2) / threshold2.height
    );
  }
  if (threshold2.width > 0 && (!isRight || isXAxisInverted && !isLeft) && x2 >= scrollContainerRect.right - threshold2.width && (intent == null ? void 0 : intent.x) !== -1 && y2 >= scrollContainerRect.top - tolerance.y && y2 <= scrollContainerRect.bottom + tolerance.y) {
    direction.x = isXAxisInverted ? -1 : 1;
    speed.x = acceleration * Math.abs(
      (scrollContainerRect.right - threshold2.width - x2) / threshold2.width
    );
  } else if (threshold2.width > 0 && (!isLeft || isXAxisInverted && !isRight) && x2 <= scrollContainerRect.left + threshold2.width && (intent == null ? void 0 : intent.x) !== 1 && y2 >= scrollContainerRect.top - tolerance.y && y2 <= scrollContainerRect.bottom + tolerance.y) {
    direction.x = isXAxisInverted ? 1 : -1;
    speed.x = acceleration * Math.abs(
      (scrollContainerRect.left + threshold2.width - x2) / threshold2.width
    );
  }
  return {
    direction,
    speed
  };
}
function scrollIntoViewIfNeeded(el, { block = "nearest", inline = "nearest" } = {}) {
  if (!isHTMLElement(el)) {
    return;
  }
  const scrollableAncestors = getScrollableAncestors(el);
  const processedAncestors = [];
  for (const ancestor of scrollableAncestors) {
    if (!isHTMLElement(ancestor)) {
      continue;
    }
    const { top, left } = getOffsetRelativeTo(el, ancestor);
    let adjustedTop = top;
    let adjustedLeft = left;
    for (const inner of processedAncestors) {
      adjustedTop -= inner.scrollTop;
      adjustedLeft -= inner.scrollLeft;
    }
    if (block !== "none") {
      const overTop = adjustedTop < ancestor.scrollTop;
      const overBottom = adjustedTop + el.offsetHeight > ancestor.scrollTop + ancestor.clientHeight;
      if (overTop !== overBottom) {
        if (block === "center") {
          ancestor.scrollTop = adjustedTop - ancestor.clientHeight / 2 + el.offsetHeight / 2;
        } else if (overTop) {
          ancestor.scrollTop = adjustedTop;
        } else {
          ancestor.scrollTop = adjustedTop + el.offsetHeight - ancestor.clientHeight;
        }
      }
    }
    if (inline !== "none") {
      const overLeft = adjustedLeft < ancestor.scrollLeft;
      const overRight = adjustedLeft + el.offsetWidth > ancestor.scrollLeft + ancestor.clientWidth;
      if (overLeft !== overRight) {
        if (inline === "center") {
          ancestor.scrollLeft = adjustedLeft - ancestor.clientWidth / 2 + el.offsetWidth / 2;
        } else if (overLeft) {
          ancestor.scrollLeft = adjustedLeft;
        } else {
          ancestor.scrollLeft = adjustedLeft + el.offsetWidth - ancestor.clientWidth;
        }
      }
    }
    processedAncestors.push(ancestor);
  }
}
function getDocumentOffset(element) {
  let top = 0;
  let left = 0;
  let current = element;
  while (current) {
    top += current.offsetTop;
    left += current.offsetLeft;
    const offsetParent = current.offsetParent;
    if (!isHTMLElement(offsetParent)) {
      break;
    }
    top += offsetParent.clientTop;
    left += offsetParent.clientLeft;
    current = offsetParent;
  }
  return { top, left };
}
function getOffsetRelativeTo(element, ancestor) {
  const elOffset = getDocumentOffset(element);
  const ancestorOffset = getDocumentOffset(ancestor);
  return {
    top: elOffset.top - ancestorOffset.top - ancestor.clientTop,
    left: elOffset.left - ancestorOffset.left - ancestor.clientLeft
  };
}
function applyTransform(rect, parsedTransform, transformOrigin) {
  const { scaleX, scaleY, x: translateX, y: translateY } = parsedTransform;
  const x2 = rect.left + translateX + (1 - scaleX) * parseFloat(transformOrigin);
  const y2 = rect.top + translateY + (1 - scaleY) * parseFloat(transformOrigin.slice(transformOrigin.indexOf(" ") + 1));
  const w2 = scaleX ? rect.width * scaleX : rect.width;
  const h2 = scaleY ? rect.height * scaleY : rect.height;
  return {
    width: w2,
    height: h2,
    top: y2,
    right: x2 + w2,
    bottom: y2 + h2,
    left: x2
  };
}
function inverseTransform(rect, parsedTransform, transformOrigin) {
  const { scaleX, scaleY, x: translateX, y: translateY } = parsedTransform;
  const x2 = rect.left - translateX - (1 - scaleX) * parseFloat(transformOrigin);
  const y2 = rect.top - translateY - (1 - scaleY) * parseFloat(transformOrigin.slice(transformOrigin.indexOf(" ") + 1));
  const w2 = scaleX ? rect.width / scaleX : rect.width;
  const h2 = scaleY ? rect.height / scaleY : rect.height;
  return {
    width: w2,
    height: h2,
    top: y2,
    right: x2 + w2,
    bottom: y2 + h2,
    left: x2
  };
}
function animateTransform({ element, keyframes, options }) {
  return element.animate(keyframes, options).finished;
}
function computeTranslate(element, translate = getComputedStyles(element).translate, projected = true) {
  if (projected) {
    const keyframe = getFinalKeyframe(
      element,
      (keyframe2) => "translate" in keyframe2
    );
    if (keyframe) {
      const { translate: translate2 = "" } = keyframe[0];
      if (typeof translate2 === "string") {
        const finalTranslate = parseTranslate(translate2);
        if (finalTranslate) {
          return finalTranslate;
        }
      }
    }
  }
  if (translate) {
    const finalTranslate = parseTranslate(translate);
    if (finalTranslate) {
      return finalTranslate;
    }
  }
  return { x: 0, y: 0, z: 0 };
}
var scheduler3 = new Scheduler((callback) => setTimeout(callback, 0));
var animations = /* @__PURE__ */ new Map();
var clear2 = animations.clear.bind(animations);
function getDocumentAnimations(element) {
  const document2 = element.ownerDocument;
  let documentAnimations = animations.get(document2);
  if (documentAnimations) return documentAnimations;
  documentAnimations = document2.getAnimations();
  animations.set(document2, documentAnimations);
  scheduler3.schedule(clear2);
  const elementAnimations = documentAnimations.filter(
    (animation) => isKeyframeEffect(animation.effect) && animation.effect.target === element
  );
  animations.set(element, elementAnimations);
  return documentAnimations;
}
function forceFinishAnimations(element, options) {
  const animations2 = getDocumentAnimations(element).filter((animation) => {
    var _a5, _b3;
    if (isKeyframeEffect(animation.effect)) {
      const { target } = animation.effect;
      const isValidTarget = (_b3 = target && ((_a5 = options.isValidTarget) == null ? void 0 : _a5.call(options, target))) != null ? _b3 : true;
      if (isValidTarget) {
        return animation.effect.getKeyframes().some((keyframe) => {
          for (const property of options.properties) {
            if (keyframe[property]) return true;
          }
        });
      }
    }
  }).map((animation) => {
    const { effect, currentTime } = animation;
    const duration = effect == null ? void 0 : effect.getComputedTiming().duration;
    if (animation.pending || animation.playState === "finished") return;
    if (typeof duration == "number" && typeof currentTime == "number" && currentTime < duration) {
      animation.currentTime = duration;
      return () => {
        animation.currentTime = currentTime;
      };
    }
  });
  if (animations2.length > 0) {
    return () => animations2.forEach((reset) => reset == null ? void 0 : reset());
  }
}
var DOMRectangle = class extends Rectangle {
  constructor(element, options = {}) {
    var _a5, _b3, _c4, _d2;
    const {
      frameTransform = getFrameTransform(element),
      ignoreTransforms,
      getBoundingClientRect = getBoundingRectangle
    } = options;
    const resetAnimations = forceFinishAnimations(element, {
      properties: ["transform", "translate", "scale", "width", "height"],
      isValidTarget: (target) => (target !== element || isSafari()) && target.contains(element)
    });
    const boundingRectangle = getBoundingClientRect(element);
    let { top, left, width, height } = boundingRectangle;
    let updated;
    const computedStyles = getComputedStyles(element);
    const parsedTransform = parseTransform(computedStyles);
    const scale = {
      x: (_a5 = parsedTransform == null ? void 0 : parsedTransform.scaleX) != null ? _a5 : 1,
      y: (_b3 = parsedTransform == null ? void 0 : parsedTransform.scaleY) != null ? _b3 : 1
    };
    const projectedTransform = getProjectedTransform(element, computedStyles);
    resetAnimations == null ? void 0 : resetAnimations();
    if (parsedTransform) {
      updated = inverseTransform(
        boundingRectangle,
        parsedTransform,
        computedStyles.transformOrigin
      );
      if (ignoreTransforms || projectedTransform) {
        top = updated.top;
        left = updated.left;
        width = updated.width;
        height = updated.height;
      }
    }
    const intrinsic = {
      width: (_c4 = updated == null ? void 0 : updated.width) != null ? _c4 : width,
      height: (_d2 = updated == null ? void 0 : updated.height) != null ? _d2 : height
    };
    if (projectedTransform && !ignoreTransforms && updated) {
      const projected = applyTransform(
        updated,
        projectedTransform,
        computedStyles.transformOrigin
      );
      top = projected.top;
      left = projected.left;
      width = projected.width;
      height = projected.height;
      scale.x = projectedTransform.scaleX;
      scale.y = projectedTransform.scaleY;
    }
    if (frameTransform) {
      if (!ignoreTransforms) {
        left *= frameTransform.scaleX;
        width *= frameTransform.scaleX;
        top *= frameTransform.scaleY;
        height *= frameTransform.scaleY;
      }
      left += frameTransform.x;
      top += frameTransform.y;
    }
    super(left, top, width, height);
    this.scale = scale;
    this.intrinsicWidth = intrinsic.width;
    this.intrinsicHeight = intrinsic.height;
  }
};
function getProjectedTransform(element, computedStyles) {
  const animations2 = element.getAnimations();
  if (!animations2.length) return null;
  let latestTransform;
  let latestTranslate;
  let latestScale;
  let hasAnimatedProperty = false;
  for (const animation of animations2) {
    if (animation.playState !== "running") continue;
    const keyframes = isKeyframeEffect(animation.effect) ? animation.effect.getKeyframes() : [];
    const keyframe = keyframes[keyframes.length - 1];
    if (!keyframe) continue;
    const { transform, translate, scale } = keyframe;
    if (typeof transform === "string" && transform) {
      latestTransform = transform;
      hasAnimatedProperty = true;
    }
    if (typeof translate === "string" && translate) {
      latestTranslate = translate;
      hasAnimatedProperty = true;
    }
    if (typeof scale === "string" && scale) {
      latestScale = scale;
      hasAnimatedProperty = true;
    }
  }
  if (!hasAnimatedProperty) return null;
  return parseTransform({
    transform: latestTransform != null ? latestTransform : computedStyles.transform,
    translate: latestTranslate != null ? latestTranslate : computedStyles.translate,
    scale: latestScale != null ? latestScale : computedStyles.scale
  });
}
function supportsStyle(element) {
  return "style" in element && typeof element.style === "object" && element.style !== null && "setProperty" in element.style && "removeProperty" in element.style && typeof element.style.setProperty === "function" && typeof element.style.removeProperty === "function";
}
var Styles = class {
  constructor(element) {
    this.element = element;
    this.initial = /* @__PURE__ */ new Map();
  }
  set(properties, prefix = "") {
    const { element } = this;
    if (!supportsStyle(element)) {
      return;
    }
    for (const [key, value] of Object.entries(properties)) {
      const property = `${prefix}${key}`;
      if (!this.initial.has(property)) {
        this.initial.set(property, element.style.getPropertyValue(property));
      }
      element.style.setProperty(
        property,
        typeof value === "string" ? value : `${value}px`
      );
    }
  }
  remove(properties, prefix = "") {
    const { element } = this;
    if (!supportsStyle(element)) {
      return;
    }
    for (const key of properties) {
      const property = `${prefix}${key}`;
      element.style.removeProperty(property);
    }
  }
  reset() {
    const { element } = this;
    if (!supportsStyle(element)) {
      return;
    }
    for (const [key, value] of this.initial) {
      element.style.setProperty(key, value);
    }
    if (element.getAttribute("style") === "") {
      element.removeAttribute("style");
    }
  }
};
function isElement(target) {
  if (!target) return false;
  return target instanceof getWindow(target).Element || isNode(target) && target.nodeType === Node.ELEMENT_NODE;
}
function isKeyboardEvent(event) {
  if (!event) return false;
  const { KeyboardEvent } = getWindow(event.target);
  return event instanceof KeyboardEvent;
}
function isPointerEvent(event) {
  if (!event) return false;
  const { PointerEvent } = getWindow(event.target);
  return event instanceof PointerEvent;
}
function isTextInput(target) {
  if (!isElement(target)) return false;
  const { tagName } = target;
  return tagName === "INPUT" || tagName === "TEXTAREA" || isContentEditable(target);
}
function isContentEditable(element) {
  return element.hasAttribute("contenteditable") && element.getAttribute("contenteditable") !== "false";
}
var ids = {};
function generateUniqueId(prefix) {
  const id = ids[prefix] == null ? 0 : ids[prefix] + 1;
  ids[prefix] = id;
  return `${prefix}-${id}`;
}

// tools/reading-order/node_modules/@dnd-kit/collision/dist/index.js
var pointerIntersection = ({
  dragOperation,
  droppable
}) => {
  const pointerCoordinates = dragOperation.position.current;
  if (!pointerCoordinates) {
    return null;
  }
  const { id } = droppable;
  if (!droppable.shape) {
    return null;
  }
  if (droppable.shape.containsPoint(pointerCoordinates)) {
    const distance = Point.distance(droppable.shape.center, pointerCoordinates);
    return {
      id,
      value: 1 / distance,
      type: CollisionType.PointerIntersection,
      priority: CollisionPriority.High
    };
  }
  return null;
};
var shapeIntersection = ({
  dragOperation,
  droppable
}) => {
  const { shape } = dragOperation;
  if (!droppable.shape || !(shape == null ? void 0 : shape.current)) {
    return null;
  }
  const intersectionArea = shape.current.intersectionArea(droppable.shape);
  if (intersectionArea) {
    const { position } = dragOperation;
    const distance = Point.distance(droppable.shape.center, position.current);
    const intersectionRatio = intersectionArea / (shape.current.area + droppable.shape.area - intersectionArea);
    const value = intersectionRatio / distance;
    return {
      id: droppable.id,
      value,
      type: CollisionType.ShapeIntersection,
      priority: CollisionPriority.Normal
    };
  }
  return null;
};
var defaultCollisionDetection = (args) => {
  var _a5;
  return (_a5 = pointerIntersection(args)) != null ? _a5 : shapeIntersection(args);
};
var closestCorners = (input) => {
  const { dragOperation, droppable } = input;
  const { shape, position } = dragOperation;
  if (!droppable.shape) {
    return null;
  }
  const shapeCorners = shape ? Rectangle.from(shape.current.boundingRectangle).corners : void 0;
  const distance = Rectangle.from(
    droppable.shape.boundingRectangle
  ).corners.reduce(
    (acc, corner, index) => {
      var _a5;
      return acc + Point.distance(
        Point.from(corner),
        (_a5 = shapeCorners == null ? void 0 : shapeCorners[index]) != null ? _a5 : position.current
      );
    },
    0
  );
  const value = distance / 4;
  return {
    id: droppable.id,
    value: 1 / value,
    type: CollisionType.Collision,
    priority: CollisionPriority.Normal
  };
};

// tools/reading-order/node_modules/@dnd-kit/dom/index.js
var __create4 = Object.create;
var __defProp4 = Object.defineProperty;
var __defProps3 = Object.defineProperties;
var __getOwnPropDesc4 = Object.getOwnPropertyDescriptor;
var __getOwnPropDescs3 = Object.getOwnPropertyDescriptors;
var __getOwnPropSymbols4 = Object.getOwnPropertySymbols;
var __hasOwnProp4 = Object.prototype.hasOwnProperty;
var __propIsEnum4 = Object.prototype.propertyIsEnumerable;
var __knownSymbol4 = (name, symbol) => (symbol = Symbol[name]) ? symbol : /* @__PURE__ */ Symbol.for("Symbol." + name);
var __typeError5 = (msg) => {
  throw TypeError(msg);
};
var __defNormalProp4 = (obj, key, value) => key in obj ? __defProp4(obj, key, { enumerable: true, configurable: true, writable: true, value }) : obj[key] = value;
var __spreadValues4 = (a2, b2) => {
  for (var prop in b2 || (b2 = {}))
    if (__hasOwnProp4.call(b2, prop))
      __defNormalProp4(a2, prop, b2[prop]);
  if (__getOwnPropSymbols4)
    for (var prop of __getOwnPropSymbols4(b2)) {
      if (__propIsEnum4.call(b2, prop))
        __defNormalProp4(a2, prop, b2[prop]);
    }
  return a2;
};
var __spreadProps3 = (a2, b2) => __defProps3(a2, __getOwnPropDescs3(b2));
var __name4 = (target, value) => __defProp4(target, "name", { value, configurable: true });
var __objRest2 = (source, exclude) => {
  var target = {};
  for (var prop in source)
    if (__hasOwnProp4.call(source, prop) && exclude.indexOf(prop) < 0)
      target[prop] = source[prop];
  if (source != null && __getOwnPropSymbols4)
    for (var prop of __getOwnPropSymbols4(source)) {
      if (exclude.indexOf(prop) < 0 && __propIsEnum4.call(source, prop))
        target[prop] = source[prop];
    }
  return target;
};
var __decoratorStart4 = (base) => {
  var _a5;
  return [, , , __create4((_a5 = base == null ? void 0 : base[__knownSymbol4("metadata")]) != null ? _a5 : null)];
};
var __decoratorStrings4 = ["class", "method", "getter", "setter", "accessor", "field", "value", "get", "set"];
var __expectFn4 = (fn) => fn !== void 0 && typeof fn !== "function" ? __typeError5("Function expected") : fn;
var __decoratorContext4 = (kind, name, done, metadata, fns) => ({ kind: __decoratorStrings4[kind], name, metadata, addInitializer: (fn) => done._ ? __typeError5("Already initialized") : fns.push(__expectFn4(fn || null)) });
var __decoratorMetadata4 = (array, target) => __defNormalProp4(target, __knownSymbol4("metadata"), array[3]);
var __runInitializers4 = (array, flags, self, value) => {
  for (var i2 = 0, fns = array[flags >> 1], n2 = fns && fns.length; i2 < n2; i2++) flags & 1 ? fns[i2].call(self) : value = fns[i2].call(self, value);
  return value;
};
var __decorateElement4 = (array, flags, name, decorators, target, extra) => {
  var fn, it, done, ctx, access, k = flags & 7, s2 = !!(flags & 8), p2 = !!(flags & 16);
  var j2 = k > 3 ? array.length + 1 : k ? s2 ? 1 : 2 : 0, key = __decoratorStrings4[k + 5];
  var initializers = k > 3 && (array[j2 - 1] = []), extraInitializers = array[j2] || (array[j2] = []);
  var desc = k && (!p2 && !s2 && (target = target.prototype), k < 5 && (k > 3 || !p2) && __getOwnPropDesc4(k < 4 ? target : { get [name]() {
    return __privateGet5(this, extra);
  }, set [name](x2) {
    return __privateSet5(this, extra, x2);
  } }, name));
  k ? p2 && k < 4 && __name4(extra, (k > 2 ? "set " : k > 1 ? "get " : "") + name) : __name4(target, name);
  for (var i2 = decorators.length - 1; i2 >= 0; i2--) {
    ctx = __decoratorContext4(k, name, done = {}, array[3], extraInitializers);
    if (k) {
      ctx.static = s2, ctx.private = p2, access = ctx.access = { has: p2 ? (x2) => __privateIn4(target, x2) : (x2) => name in x2 };
      if (k ^ 3) access.get = p2 ? (x2) => (k ^ 1 ? __privateGet5 : __privateMethod5)(x2, target, k ^ 4 ? extra : desc.get) : (x2) => x2[name];
      if (k > 2) access.set = p2 ? (x2, y2) => __privateSet5(x2, target, y2, k ^ 4 ? extra : desc.set) : (x2, y2) => x2[name] = y2;
    }
    it = (0, decorators[i2])(k ? k < 4 ? p2 ? extra : desc[key] : k > 4 ? void 0 : { get: desc.get, set: desc.set } : target, ctx), done._ = 1;
    if (k ^ 4 || it === void 0) __expectFn4(it) && (k > 4 ? initializers.unshift(it) : k ? p2 ? extra = it : desc[key] = it : target = it);
    else if (typeof it !== "object" || it === null) __typeError5("Object expected");
    else __expectFn4(fn = it.get) && (desc.get = fn), __expectFn4(fn = it.set) && (desc.set = fn), __expectFn4(fn = it.init) && initializers.unshift(fn);
  }
  return k || __decoratorMetadata4(array, target), desc && __defProp4(target, name, desc), p2 ? k ^ 4 ? extra : desc : target;
};
var __accessCheck5 = (obj, member, msg) => member.has(obj) || __typeError5("Cannot " + msg);
var __privateIn4 = (member, obj) => Object(obj) !== obj ? __typeError5('Cannot use the "in" operator on this value') : member.has(obj);
var __privateGet5 = (obj, member, getter) => (__accessCheck5(obj, member, "read from private field"), getter ? getter.call(obj) : member.get(obj));
var __privateAdd5 = (obj, member, value) => member.has(obj) ? __typeError5("Cannot add the same private member more than once") : member instanceof WeakSet ? member.add(obj) : member.set(obj, value);
var __privateSet5 = (obj, member, value, setter) => (__accessCheck5(obj, member, "write to private field"), setter ? setter.call(obj, value) : member.set(obj, value), value);
var __privateMethod5 = (obj, member, method) => (__accessCheck5(obj, member, "access private method"), method);
var defaultAttributes = {
  role: "button",
  roleDescription: "draggable"
};
var defaultDescriptionIdPrefix = `dnd-kit-description`;
var defaultAnnouncementIdPrefix = `dnd-kit-announcement`;
var defaultScreenReaderInstructions = {
  draggable: `To pick up a draggable item, press the space bar. While dragging, use the arrow keys to move the item in a given direction. Press space again to drop the item in its new position, or press escape to cancel.`
};
var defaultAnnouncements = {
  dragstart({ operation: { source } }) {
    if (!source) return;
    return `Picked up draggable item ${source.id}.`;
  },
  dragover({ operation: { source, target } }) {
    if (!source || source.id === (target == null ? void 0 : target.id)) return;
    if (target) {
      return `Draggable item ${source.id} was moved over droppable target ${target.id}.`;
    }
    return `Draggable item ${source.id} is no longer over a droppable target.`;
  },
  dragend({ operation: { source, target }, canceled }) {
    if (!source) return;
    if (canceled) {
      return `Dragging was cancelled. Draggable item ${source.id} was dropped.`;
    }
    if (target) {
      return `Draggable item ${source.id} was dropped over droppable target ${target.id}`;
    }
    return `Draggable item ${source.id} was dropped.`;
  }
};
function isFocusable(element) {
  const tagName = element.tagName.toLowerCase();
  return ["input", "select", "textarea", "a", "button"].includes(tagName);
}
function createHiddenText(id, value) {
  const element = document.createElement("div");
  element.id = id;
  element.style.setProperty("display", "none");
  element.textContent = value;
  return element;
}
function createLiveRegion(id) {
  const element = document.createElement("div");
  element.id = id;
  element.setAttribute("role", "status");
  element.setAttribute("aria-live", "polite");
  element.setAttribute("aria-atomic", "true");
  element.style.setProperty("position", "fixed");
  element.style.setProperty("width", "1px");
  element.style.setProperty("height", "1px");
  element.style.setProperty("margin", "-1px");
  element.style.setProperty("border", "0");
  element.style.setProperty("padding", "0");
  element.style.setProperty("overflow", "hidden");
  element.style.setProperty("clip", "rect(0 0 0 0)");
  element.style.setProperty("clip-path", "inset(100%)");
  element.style.setProperty("white-space", "nowrap");
  return element;
}
var debouncedEvents = ["dragover", "dragmove"];
var Accessibility = class extends Plugin {
  constructor(manager, options) {
    super(manager);
    const {
      id,
      idPrefix: {
        description: descriptionPrefix = defaultDescriptionIdPrefix,
        announcement: announcementPrefix = defaultAnnouncementIdPrefix
      } = {},
      announcements = defaultAnnouncements,
      screenReaderInstructions = defaultScreenReaderInstructions,
      debounce: debounceMs = 500
    } = options != null ? options : {};
    const descriptionId = id ? `${descriptionPrefix}-${id}` : generateUniqueId(descriptionPrefix);
    const announcementId = id ? `${announcementPrefix}-${id}` : generateUniqueId(announcementPrefix);
    let hiddenTextElement;
    let liveRegionElement;
    let liveRegionTextNode;
    let latestAnnouncement;
    const updateAnnouncement = (value = latestAnnouncement) => {
      if (!liveRegionTextNode || !value) return;
      if ((liveRegionTextNode == null ? void 0 : liveRegionTextNode.nodeValue) !== value) {
        liveRegionTextNode.nodeValue = value;
      }
    };
    const scheduleUpdateAnnouncement = () => scheduler.schedule(updateAnnouncement);
    const debouncedUpdateAnnouncement = debounce(
      scheduleUpdateAnnouncement,
      debounceMs
    );
    const eventListeners = Object.entries(announcements).map(
      ([eventName, getAnnouncement]) => {
        return this.manager.monitor.addEventListener(
          eventName,
          (event, manager2) => {
            const element = liveRegionTextNode;
            if (!element) return;
            const announcement = getAnnouncement == null ? void 0 : getAnnouncement(event, manager2);
            if (announcement && element.nodeValue !== announcement) {
              latestAnnouncement = announcement;
              if (debouncedEvents.includes(eventName)) {
                debouncedUpdateAnnouncement();
              } else {
                scheduleUpdateAnnouncement();
                debouncedUpdateAnnouncement.cancel();
              }
            }
          }
        );
      }
    );
    const initialize = () => {
      let elements = [];
      if (!(hiddenTextElement == null ? void 0 : hiddenTextElement.isConnected)) {
        hiddenTextElement = createHiddenText(
          descriptionId,
          screenReaderInstructions.draggable
        );
        elements.push(hiddenTextElement);
      }
      if (!(liveRegionElement == null ? void 0 : liveRegionElement.isConnected)) {
        liveRegionElement = createLiveRegion(announcementId);
        liveRegionTextNode = document.createTextNode("");
        liveRegionElement.appendChild(liveRegionTextNode);
        elements.push(liveRegionElement);
      }
      if (elements.length > 0) {
        document.body.append(...elements);
      }
    };
    const mutations = /* @__PURE__ */ new Set();
    function executeMutations() {
      for (const operation of mutations) {
        operation();
      }
    }
    this.registerEffect(() => {
      var _a5;
      mutations.clear();
      for (const draggable of this.manager.registry.draggables.value) {
        const activator = (_a5 = draggable.handle) != null ? _a5 : draggable.element;
        if (activator) {
          if (!hiddenTextElement || !liveRegionElement) {
            mutations.add(initialize);
          }
          if ((!isFocusable(activator) || isSafari()) && !activator.hasAttribute("tabindex")) {
            mutations.add(() => activator.setAttribute("tabindex", "0"));
          }
          if (!activator.hasAttribute("role") && !(activator.tagName.toLowerCase() === "button")) {
            mutations.add(
              () => activator.setAttribute("role", defaultAttributes.role)
            );
          }
          if (!activator.hasAttribute("aria-roledescription")) {
            mutations.add(
              () => activator.setAttribute(
                "aria-roledescription",
                defaultAttributes.roleDescription
              )
            );
          }
          if (!activator.hasAttribute("aria-describedby")) {
            mutations.add(
              () => activator.setAttribute("aria-describedby", descriptionId)
            );
          }
          for (const key of ["aria-pressed", "aria-grabbed"]) {
            const value = String(draggable.isDragging);
            if (activator.getAttribute(key) !== value) {
              mutations.add(() => activator.setAttribute(key, value));
            }
          }
          const disabled = String(draggable.disabled);
          if (activator.getAttribute("aria-disabled") !== disabled) {
            mutations.add(
              () => activator.setAttribute("aria-disabled", disabled)
            );
          }
        }
      }
      if (mutations.size > 0) {
        scheduler.schedule(executeMutations);
      }
    });
    this.destroy = () => {
      super.destroy();
      hiddenTextElement == null ? void 0 : hiddenTextElement.remove();
      liveRegionElement == null ? void 0 : liveRegionElement.remove();
      eventListeners.forEach((unsubscribe) => unsubscribe());
    };
  }
};
function debounce(fn, wait) {
  let timeout2;
  const debounced = () => {
    clearTimeout(timeout2);
    timeout2 = setTimeout(fn, wait);
  };
  debounced.cancel = () => clearTimeout(timeout2);
  return debounced;
}
var styleRegistry = /* @__PURE__ */ new Map();
var _roots_dec;
var _targetRoot_dec;
var _sourceRoot_dec;
var _additionalRoots_dec;
var _a3;
var _registeredRules;
var _init7;
var _additionalRoots;
var _StyleInjector_instances;
var syncStyles_fn;
var inject_fn;
var injectStyleElement_fn;
var injectAdoptedSheet_fn;
var _StyleInjector = class _StyleInjector2 extends (_a3 = CorePlugin, _additionalRoots_dec = [reactive], _sourceRoot_dec = [derived], _targetRoot_dec = [derived], _roots_dec = [derived], _a3) {
  constructor(manager, options) {
    super(manager, options);
    __runInitializers4(_init7, 5, this);
    __privateAdd5(this, _StyleInjector_instances);
    __privateAdd5(this, _registeredRules, /* @__PURE__ */ new Set());
    __privateAdd5(this, _additionalRoots, __runInitializers4(_init7, 8, this, /* @__PURE__ */ new Set())), __runInitializers4(_init7, 11, this);
    this.registerEffect(__privateMethod5(this, _StyleInjector_instances, syncStyles_fn));
  }
  /**
   * Registers CSS rules to be injected into the active drag operation's
   * document and shadow roots. The StyleInjector handles tracking
   * which roots need the styles and cleaning up when they're no longer needed.
   *
   * Returns a cleanup function that unregisters the rules.
   */
  register(cssRules) {
    __privateGet5(this, _registeredRules).add(cssRules);
    return () => {
      __privateGet5(this, _registeredRules).delete(cssRules);
    };
  }
  /**
   * Adds an additional root to track for style injection.
   * Returns a cleanup function that removes the root.
   */
  addRoot(root) {
    f(() => {
      const roots = new Set(this.additionalRoots);
      roots.add(root);
      this.additionalRoots = roots;
    });
    return () => {
      f(() => {
        const roots = new Set(this.additionalRoots);
        roots.delete(root);
        this.additionalRoots = roots;
      });
    };
  }
  get sourceRoot() {
    var _a5;
    const { source } = this.manager.dragOperation;
    return getRoot((_a5 = source == null ? void 0 : source.element) != null ? _a5 : null);
  }
  get targetRoot() {
    var _a5;
    const { target } = this.manager.dragOperation;
    return getRoot((_a5 = target == null ? void 0 : target.element) != null ? _a5 : null);
  }
  get roots() {
    const { status } = this.manager.dragOperation;
    if (status.initializing || status.initialized) {
      const roots = [this.sourceRoot, this.targetRoot].filter(
        (root) => root != null
      );
      return /* @__PURE__ */ new Set([...roots, ...this.additionalRoots]);
    }
    return /* @__PURE__ */ new Set();
  }
};
_init7 = __decoratorStart4(_a3);
_registeredRules = /* @__PURE__ */ new WeakMap();
_additionalRoots = /* @__PURE__ */ new WeakMap();
_StyleInjector_instances = /* @__PURE__ */ new WeakSet();
syncStyles_fn = function() {
  const { roots } = this;
  const cleanups = [];
  for (const root of roots) {
    for (const cssRules of __privateGet5(this, _registeredRules)) {
      cleanups.push(__privateMethod5(this, _StyleInjector_instances, inject_fn).call(this, root, cssRules));
    }
  }
  return () => {
    for (const cleanup of cleanups) {
      cleanup();
    }
  };
};
inject_fn = function(root, cssRules) {
  let rootStyles = styleRegistry.get(root);
  if (!rootStyles) {
    rootStyles = /* @__PURE__ */ new Map();
    styleRegistry.set(root, rootStyles);
  }
  let registration = rootStyles.get(cssRules);
  if (!registration) {
    const created = isDocument(root) ? __privateMethod5(this, _StyleInjector_instances, injectStyleElement_fn).call(this, root, rootStyles, cssRules) : __privateMethod5(this, _StyleInjector_instances, injectAdoptedSheet_fn).call(this, root, rootStyles, cssRules);
    if (!created) {
      return () => {
      };
    }
    registration = created;
    rootStyles.set(cssRules, registration);
  }
  registration.refCount++;
  let disposed = false;
  return () => {
    if (disposed) return;
    disposed = true;
    registration.refCount--;
    if (registration.refCount === 0) {
      registration.cleanup();
    }
  };
};
injectStyleElement_fn = function(root, rootStyles, cssRules) {
  var _a5;
  const style = root.createElement("style");
  const { nonce } = (_a5 = this.options) != null ? _a5 : {};
  if (nonce) {
    style.setAttribute("nonce", nonce);
  }
  style.textContent = cssRules;
  root.head.prepend(style);
  const observer = new MutationObserver((entries) => {
    for (const entry of entries) {
      for (const node of Array.from(entry.removedNodes)) {
        if (node === style) {
          root.head.prepend(style);
          return;
        }
      }
    }
  });
  observer.observe(root.head, { childList: true });
  return {
    refCount: 0,
    cleanup: () => {
      observer.disconnect();
      style.remove();
      rootStyles.delete(cssRules);
      if (rootStyles.size === 0) {
        styleRegistry.delete(root);
      }
    }
  };
};
injectAdoptedSheet_fn = function(root, rootStyles, cssRules) {
  if (!("adoptedStyleSheets" in root && Array.isArray(root.adoptedStyleSheets)) && true) {
    console.error(
      "Cannot inject styles: This browser doesn't support adoptedStyleSheets"
    );
  }
  const targetWindow = root.ownerDocument.defaultView;
  const { CSSStyleSheet } = targetWindow != null ? targetWindow : {};
  if (!CSSStyleSheet) {
    if (true) {
      console.error(
        "Cannot inject styles: CSSStyleSheet constructor not available"
      );
    }
    return null;
  }
  const sheet = new CSSStyleSheet();
  sheet.replaceSync(cssRules);
  root.adoptedStyleSheets.push(sheet);
  return {
    refCount: 0,
    cleanup: () => {
      var _a5;
      if (isShadowRoot(root) && ((_a5 = root.host) == null ? void 0 : _a5.isConnected)) {
        const index = root.adoptedStyleSheets.indexOf(sheet);
        if (index !== -1) {
          root.adoptedStyleSheets.splice(index, 1);
        }
      }
      rootStyles.delete(cssRules);
      if (rootStyles.size === 0) {
        styleRegistry.delete(root);
      }
    }
  };
};
__decorateElement4(_init7, 4, "additionalRoots", _additionalRoots_dec, _StyleInjector, _additionalRoots);
__decorateElement4(_init7, 2, "sourceRoot", _sourceRoot_dec, _StyleInjector);
__decorateElement4(_init7, 2, "targetRoot", _targetRoot_dec, _StyleInjector);
__decorateElement4(_init7, 2, "roots", _roots_dec, _StyleInjector);
__decoratorMetadata4(_init7, _StyleInjector);
_StyleInjector.configure = configurator(_StyleInjector);
var StyleInjector = _StyleInjector;
var Cursor = class extends Plugin {
  constructor(manager, options) {
    super(manager, options);
    this.manager = manager;
    const { cursor = "grabbing" } = options != null ? options : {};
    const styleInjector = manager.registry.plugins.get(
      StyleInjector
    );
    const unregisterStyles = styleInjector == null ? void 0 : styleInjector.register(
      `* { cursor: ${cursor} !important; }`
    );
    if (unregisterStyles) {
      const originalDestroy = this.destroy.bind(this);
      this.destroy = () => {
        unregisterStyles();
        originalDestroy();
      };
    }
  }
};
var ATTR_PREFIX = "data-dnd-";
var DROPPING_ATTRIBUTE = `${ATTR_PREFIX}dropping`;
var CSS_PREFIX = "--dnd-";
var ATTRIBUTE = `${ATTR_PREFIX}dragging`;
var PLACEHOLDER_ATTRIBUTE = `${ATTR_PREFIX}placeholder`;
var IGNORED_ATTRIBUTES = [
  ATTRIBUTE,
  PLACEHOLDER_ATTRIBUTE,
  "popover",
  "aria-pressed",
  "aria-grabbing"
];
var IGNORED_STYLES = ["view-transition-name"];
var CSS_RULES = `
  :is(:root,:host) [${ATTRIBUTE}] {
    position: fixed !important;
    pointer-events: none !important;
    touch-action: none;
    z-index: calc(infinity);
    will-change: translate;
    top: var(${CSS_PREFIX}top, 0px) !important;
    left: var(${CSS_PREFIX}left, 0px) !important;
    right: unset !important;
    bottom: unset !important;
    width: var(${CSS_PREFIX}width, auto);
    max-width: var(${CSS_PREFIX}width, auto);
    height: var(${CSS_PREFIX}height, auto);
    max-height: var(${CSS_PREFIX}height, auto);
    transform: var(${CSS_PREFIX}transform, none) !important;
    transition: var(${CSS_PREFIX}transition) !important;
  }

  :is(:root,:host) [${PLACEHOLDER_ATTRIBUTE}] {
    transition: none;
  }

  :is(:root,:host) [${PLACEHOLDER_ATTRIBUTE}='hidden'] {
    visibility: hidden;
  }

  [${ATTRIBUTE}] * {
    pointer-events: none !important;
  }

  [${ATTRIBUTE}]:not([${DROPPING_ATTRIBUTE}]) {
    translate: var(${CSS_PREFIX}translate) !important;
  }

  [${ATTRIBUTE}][style*='${CSS_PREFIX}scale'] {
    scale: var(${CSS_PREFIX}scale) !important;
    transform-origin: var(${CSS_PREFIX}transform-origin) !important;
  }

  @layer dnd-kit {
    :where([${ATTRIBUTE}][popover]) {
      overflow: visible;
      background: unset;
      border: unset;
      margin: unset;
      padding: unset;
      color: inherit;

      &:is(input, button) {
        border: revert;
        background: revert;
      }
    }
  }
  [${ATTRIBUTE}]::backdrop, [${ATTR_PREFIX}overlay]:not([${ATTRIBUTE}]) {
    display: none;
    visibility: hidden;
  }
`.replace(/\n+/g, " ").replace(/\s+/g, " ").trim();
function createPlaceholder(source, type = "hidden") {
  return f(() => {
    const { element, manager } = source;
    if (!element || !manager) return;
    const containedDroppables = findContainedDroppables(
      element,
      manager.registry.droppables
    );
    const cleanup = [];
    const placeholder = cloneElement(element);
    const { remove } = placeholder;
    proxyDroppableElements(containedDroppables, placeholder, cleanup);
    configurePlaceholder(placeholder, type);
    placeholder.remove = () => {
      cleanup.forEach((fn) => fn());
      remove.call(placeholder);
    };
    return placeholder;
  });
}
function findContainedDroppables(element, droppables) {
  const containedDroppables = /* @__PURE__ */ new Map();
  for (const droppable of droppables) {
    if (!droppable.element) continue;
    if (element === droppable.element || element.contains(droppable.element)) {
      const identifierAttribute = `${ATTR_PREFIX}${generateUniqueId("dom-id")}`;
      droppable.element.setAttribute(identifierAttribute, "");
      containedDroppables.set(droppable, identifierAttribute);
    }
  }
  return containedDroppables;
}
function proxyDroppableElements(containedDroppables, placeholder, cleanup) {
  for (const [droppable, identifierAttribute] of containedDroppables) {
    if (!droppable.element) continue;
    const selector = `[${identifierAttribute}]`;
    const clonedElement = placeholder.matches(selector) ? placeholder : placeholder.querySelector(selector);
    droppable.element.removeAttribute(identifierAttribute);
    if (!clonedElement) continue;
    const originalElement = droppable.element;
    droppable.proxy = clonedElement;
    clonedElement.removeAttribute(identifierAttribute);
    ProxiedElements.set(originalElement, clonedElement);
    cleanup.push(() => {
      ProxiedElements.delete(originalElement);
      droppable.proxy = void 0;
    });
  }
}
function configurePlaceholder(placeholder, type = "hidden") {
  placeholder.setAttribute("inert", "true");
  placeholder.setAttribute("tab-index", "-1");
  placeholder.setAttribute("aria-hidden", "true");
  placeholder.setAttribute(PLACEHOLDER_ATTRIBUTE, type);
}
function isSameFrame(element, target) {
  if (element === target) return true;
  return getFrameElement(element) === getFrameElement(target);
}
function preventPopoverClose(event) {
  const { target } = event;
  if ("newState" in event && event.newState === "closed" && isElement(target) && target.hasAttribute("popover")) {
    requestAnimationFrame(() => showPopover(target));
  }
}
function isTableRow(element) {
  return element.tagName === "TR";
}
function createElementMutationObserver(element, placeholder, clone) {
  const observer = new MutationObserver((mutations) => {
    let hasChildrenMutations = false;
    for (const mutation of mutations) {
      if (mutation.target !== element) {
        hasChildrenMutations = true;
        continue;
      }
      if (mutation.type !== "attributes") {
        continue;
      }
      const attributeName = mutation.attributeName;
      if (attributeName.startsWith("aria-") || IGNORED_ATTRIBUTES.includes(attributeName)) {
        continue;
      }
      const attributeValue = element.getAttribute(attributeName);
      if (attributeName === "style") {
        if (supportsStyle(element) && supportsStyle(placeholder)) {
          const styles = element.style;
          for (const key of Array.from(placeholder.style)) {
            if (styles.getPropertyValue(key) === "") {
              placeholder.style.removeProperty(key);
            }
          }
          for (const key of Array.from(styles)) {
            if (IGNORED_STYLES.includes(key) || key.startsWith(CSS_PREFIX)) {
              continue;
            }
            const value = styles.getPropertyValue(key);
            placeholder.style.setProperty(key, value);
          }
        }
      } else if (attributeValue !== null) {
        placeholder.setAttribute(attributeName, attributeValue);
      } else {
        placeholder.removeAttribute(attributeName);
      }
    }
    if (hasChildrenMutations && clone) {
      placeholder.replaceChildren(...element.cloneNode(true).childNodes);
    }
  });
  observer.observe(element, {
    attributes: true,
    subtree: true,
    childList: true
  });
  return observer;
}
function createDocumentMutationObserver(element, placeholder, feedbackElement) {
  const observer = new MutationObserver((entries) => {
    for (const entry of entries) {
      if (entry.addedNodes.length === 0) continue;
      for (const node of Array.from(entry.addedNodes)) {
        if (node.contains(element) && element.nextElementSibling !== placeholder) {
          element.insertAdjacentElement("afterend", placeholder);
          showPopover(feedbackElement);
          return;
        }
        if (node.contains(placeholder) && placeholder.previousElementSibling !== element) {
          placeholder.insertAdjacentElement("beforebegin", element);
          showPopover(feedbackElement);
          return;
        }
      }
    }
    if (element.isConnected && placeholder.isConnected && element.nextElementSibling !== placeholder) {
      element.insertAdjacentElement("afterend", placeholder);
      showPopover(feedbackElement);
    }
  });
  observer.observe(element.ownerDocument.body, {
    childList: true,
    subtree: true
  });
  return observer;
}
function createResizeObserver(ctx) {
  return new ResizeObserver(() => {
    var _a5, _b22, _c32;
    const placeholderShape = new DOMRectangle(ctx.placeholder, {
      frameTransform: ctx.frameTransform,
      ignoreTransforms: true
    });
    const origin = (_a5 = ctx.transformOrigin) != null ? _a5 : { x: 1, y: 1 };
    const dX = (ctx.width - placeholderShape.width) * origin.x + ctx.delta.x;
    const dY = (ctx.height - placeholderShape.height) * origin.y + ctx.delta.y;
    const fixedOffset = getFixedPositionOffset();
    ctx.styles.set(
      {
        width: placeholderShape.width - ctx.widthOffset,
        height: placeholderShape.height - ctx.heightOffset,
        top: ctx.top + dY + fixedOffset.y,
        left: ctx.left + dX + fixedOffset.x
      },
      CSS_PREFIX
    );
    (_b22 = ctx.getElementMutationObserver()) == null ? void 0 : _b22.takeRecords();
    if (isTableRow(ctx.element) && isTableRow(ctx.placeholder)) {
      const cells = Array.from(ctx.element.cells);
      const placeholderCells = Array.from(ctx.placeholder.cells);
      if (!ctx.getSavedCellWidths()) {
        ctx.setSavedCellWidths(cells.map((cell) => cell.style.width));
      }
      for (const [index, cell] of cells.entries()) {
        const placeholderCell = placeholderCells[index];
        cell.style.width = `${placeholderCell.getBoundingClientRect().width}px`;
      }
    }
    const translate = (_c32 = ctx.getTranslate()) != null ? _c32 : { x: 0, y: 0 };
    const shapeLeft = ctx.left + dX + fixedOffset.x + translate.x;
    const shapeTop = ctx.top + dY + fixedOffset.y + translate.y;
    const shapeWidth = placeholderShape.width - ctx.widthOffset;
    const shapeHeight = placeholderShape.height - ctx.heightOffset;
    const ft = ctx.frameTransform;
    ctx.dragOperation.shape = new Rectangle(
      shapeLeft * ft.scaleX + ft.x,
      shapeTop * ft.scaleY + ft.y,
      shapeWidth * ft.scaleX,
      shapeHeight * ft.scaleY
    );
  });
}
var DEFAULT_DURATION = 250;
var DEFAULT_EASING = "ease";
function runDropAnimation(ctx) {
  var _a5, _b22, _c32, _d2;
  const { animation } = ctx;
  if (typeof animation === "function") {
    const result = animation({
      source: ctx.source,
      element: ctx.element,
      feedbackElement: ctx.feedbackElement,
      placeholder: ctx.placeholder,
      translate: ctx.translate,
      moved: ctx.moved
    });
    Promise.resolve(result).then(() => {
      ctx.cleanup();
      requestAnimationFrame(ctx.restoreFocus);
    });
    return;
  }
  const {
    duration = DEFAULT_DURATION,
    easing = DEFAULT_EASING
  } = animation != null ? animation : {};
  showPopover(ctx.feedbackElement);
  const [, runningAnimation] = (_a5 = getFinalKeyframe(
    ctx.feedbackElement,
    (keyframe) => "translate" in keyframe
  )) != null ? _a5 : [];
  runningAnimation == null ? void 0 : runningAnimation.pause();
  const target = (_b22 = ctx.placeholder) != null ? _b22 : ctx.element;
  const options = {
    frameTransform: isSameFrame(ctx.feedbackElement, target) ? null : void 0
  };
  const current = new DOMRectangle(ctx.feedbackElement, options);
  const currentTranslate = (_c32 = parseTranslate(getComputedStyles(ctx.feedbackElement).translate)) != null ? _c32 : ctx.translate;
  const final = new DOMRectangle(target, options);
  const delta = Rectangle.delta(current, final, ctx.alignment);
  const finalTranslate = {
    x: currentTranslate.x - delta.x,
    y: currentTranslate.y - delta.y
  };
  const heightKeyframes = Math.round(current.intrinsicHeight) !== Math.round(final.intrinsicHeight) ? {
    minHeight: [
      `${current.intrinsicHeight}px`,
      `${final.intrinsicHeight}px`
    ],
    maxHeight: [
      `${current.intrinsicHeight}px`,
      `${final.intrinsicHeight}px`
    ]
  } : {};
  const widthKeyframes = Math.round(current.intrinsicWidth) !== Math.round(final.intrinsicWidth) ? {
    minWidth: [
      `${current.intrinsicWidth}px`,
      `${final.intrinsicWidth}px`
    ],
    maxWidth: [
      `${current.intrinsicWidth}px`,
      `${final.intrinsicWidth}px`
    ]
  } : {};
  ctx.styles.set({ transition: ctx.transition }, CSS_PREFIX);
  ctx.feedbackElement.setAttribute(DROPPING_ATTRIBUTE, "");
  (_d2 = ctx.getElementMutationObserver()) == null ? void 0 : _d2.takeRecords();
  animateTransform({
    element: ctx.feedbackElement,
    keyframes: __spreadProps3(__spreadValues4(__spreadValues4({}, heightKeyframes), widthKeyframes), {
      translate: [
        `${currentTranslate.x}px ${currentTranslate.y}px 0`,
        `${finalTranslate.x}px ${finalTranslate.y}px 0`
      ]
    }),
    options: {
      duration: prefersReducedMotion(getWindow(ctx.feedbackElement)) ? 0 : ctx.moved || ctx.feedbackElement !== ctx.element ? duration : 0,
      easing
    }
  }).then(() => {
    ctx.feedbackElement.removeAttribute(DROPPING_ATTRIBUTE);
    runningAnimation == null ? void 0 : runningAnimation.finish();
    ctx.cleanup();
    requestAnimationFrame(ctx.restoreFocus);
  });
}
var _overlay_dec;
var _a22;
var _init23;
var _overlay;
var _Feedback_instances;
var trackOverlayRoot_fn;
var render_fn;
var _Feedback = class _Feedback2 extends (_a22 = Plugin, _overlay_dec = [reactive], _a22) {
  constructor(manager, options) {
    super(manager, options);
    __privateAdd5(this, _Feedback_instances);
    __privateAdd5(this, _overlay, __runInitializers4(_init23, 8, this)), __runInitializers4(_init23, 11, this);
    this.state = {
      initial: {},
      current: {}
    };
    const styleInjector = manager.registry.plugins.get(StyleInjector);
    const unregisterStyles = styleInjector == null ? void 0 : styleInjector.register(CSS_RULES);
    if (unregisterStyles) {
      const originalDestroy = this.destroy.bind(this);
      this.destroy = () => {
        unregisterStyles();
        originalDestroy();
      };
    }
    this.registerEffect(__privateMethod5(this, _Feedback_instances, trackOverlayRoot_fn).bind(this, styleInjector));
    this.registerEffect(__privateMethod5(this, _Feedback_instances, render_fn));
  }
};
_init23 = __decoratorStart4(_a22);
_overlay = /* @__PURE__ */ new WeakMap();
_Feedback_instances = /* @__PURE__ */ new WeakSet();
trackOverlayRoot_fn = function(styleInjector) {
  const { overlay } = this;
  if (!overlay || !styleInjector) return;
  const root = getRoot(overlay);
  if (!root) return;
  return styleInjector.addRoot(root);
};
render_fn = function() {
  var _a5, _b22, _c32, _d2, _e, _f, _g;
  const { state, manager, options } = this;
  const { dragOperation } = manager;
  const { position, source, status } = dragOperation;
  if (status.idle) {
    state.current = {};
    state.initial = {};
    return;
  }
  if (!source) return;
  const { element } = source;
  const entityOptions = source.pluginConfig(_Feedback);
  const feedbackOption = (_b22 = (_a5 = entityOptions == null ? void 0 : entityOptions.feedback) != null ? _a5 : options == null ? void 0 : options.feedback) != null ? _b22 : "default";
  const feedback = typeof feedbackOption === "function" ? feedbackOption(source, manager) : feedbackOption;
  if (!element || feedback === "none" || !status.initialized || status.initializing) {
    return;
  }
  const { initial } = state;
  const feedbackElement = (_c32 = this.overlay) != null ? _c32 : element;
  const frameTransform = getFrameTransform(feedbackElement);
  const elementFrameTransform = getFrameTransform(element);
  const crossFrame = !isSameFrame(element, feedbackElement);
  const shape = new DOMRectangle(element, {
    frameTransform: crossFrame ? elementFrameTransform : null,
    ignoreTransforms: !crossFrame
  });
  const scaleDelta = {
    x: elementFrameTransform.scaleX / frameTransform.scaleX,
    y: elementFrameTransform.scaleY / frameTransform.scaleY
  };
  let { width, height, top, left } = shape;
  if (crossFrame) {
    width = width / scaleDelta.x;
    height = height / scaleDelta.y;
  }
  const styles = new Styles(feedbackElement);
  const elementStyles = getComputedStyles(element);
  const {
    transition,
    translate,
    boxSizing,
    paddingBlockStart,
    paddingBlockEnd,
    paddingInlineStart,
    paddingInlineEnd,
    borderInlineStartWidth,
    borderInlineEndWidth,
    borderBlockStartWidth,
    borderBlockEndWidth
  } = elementStyles;
  const feedbackTransition = transition.split(",").filter((t2) => !/^\s*(transform|translate|scale)\b/.test(t2)).join(",");
  const parsedTransform = parseTransform(elementStyles);
  const initialTransformStyle = elementStyles.transform;
  const clone = feedback === "clone";
  const contentBox = boxSizing === "content-box";
  const widthOffset = contentBox ? parseInt(paddingInlineStart) + parseInt(paddingInlineEnd) + parseInt(borderInlineStartWidth) + parseInt(borderInlineEndWidth) : 0;
  const heightOffset = contentBox ? parseInt(paddingBlockStart) + parseInt(paddingBlockEnd) + parseInt(borderBlockStartWidth) + parseInt(borderBlockEndWidth) : 0;
  const placeholder = feedback !== "move" && !this.overlay ? createPlaceholder(source, clone ? "clone" : "hidden") : null;
  const isKeyboardOperation = f(
    () => isKeyboardEvent(manager.dragOperation.activatorEvent)
  );
  if (!initial.translate) {
    if (this.overlay && parsedTransform) {
      initial.translate = { x: parsedTransform.x, y: parsedTransform.y };
    } else if (translate !== "none") {
      const parsedTranslate = parseTranslate(translate);
      if (parsedTranslate) {
        initial.translate = parsedTranslate;
      }
    }
  }
  if (!initial.transformOrigin) {
    const current = f(() => position.current);
    const visualLeft = left + ((_d2 = parsedTransform == null ? void 0 : parsedTransform.x) != null ? _d2 : 0);
    const visualTop = top + ((_e = parsedTransform == null ? void 0 : parsedTransform.y) != null ? _e : 0);
    initial.transformOrigin = {
      x: (current.x - visualLeft * frameTransform.scaleX - frameTransform.x) / (width * frameTransform.scaleX),
      y: (current.y - visualTop * frameTransform.scaleY - frameTransform.y) / (height * frameTransform.scaleY)
    };
  }
  const { transformOrigin } = initial;
  const relativeTop = top * frameTransform.scaleY + frameTransform.y;
  const relativeLeft = left * frameTransform.scaleX + frameTransform.x;
  if (!initial.coordinates) {
    initial.coordinates = {
      x: relativeLeft,
      y: relativeTop
    };
    if (scaleDelta.x !== 1 || scaleDelta.y !== 1) {
      const { scaleX, scaleY } = elementFrameTransform;
      const { x: tX2, y: tY2 } = transformOrigin;
      initial.coordinates.x += (width * scaleX - width) * tX2;
      initial.coordinates.y += (height * scaleY - height) * tY2;
    }
  }
  if (!initial.dimensions) {
    initial.dimensions = { width, height };
  }
  if (!initial.frameTransform) {
    initial.frameTransform = frameTransform;
  }
  const coordinatesDelta = {
    x: initial.coordinates.x - relativeLeft,
    y: initial.coordinates.y - relativeTop
  };
  const sizeDelta = {
    width: (initial.dimensions.width * initial.frameTransform.scaleX - width * frameTransform.scaleX) * transformOrigin.x,
    height: (initial.dimensions.height * initial.frameTransform.scaleY - height * frameTransform.scaleY) * transformOrigin.y
  };
  const delta = {
    x: coordinatesDelta.x / frameTransform.scaleX + sizeDelta.width,
    y: coordinatesDelta.y / frameTransform.scaleY + sizeDelta.height
  };
  const projected = {
    left: left + delta.x,
    top: top + delta.y
  };
  feedbackElement.setAttribute(ATTRIBUTE, "true");
  const transform = f(() => dragOperation.transform);
  const initialTranslate = (_f = initial.translate) != null ? _f : { x: 0, y: 0 };
  const tX = transform.x * frameTransform.scaleX + initialTranslate.x;
  const tY = transform.y * frameTransform.scaleY + initialTranslate.y;
  const fixedOffset = getFixedPositionOffset();
  styles.set(
    {
      width: width - widthOffset,
      height: height - heightOffset,
      top: projected.top + fixedOffset.y,
      left: projected.left + fixedOffset.x,
      translate: `${tX}px ${tY}px 0`,
      transform: this.overlay ? "none" : initialTransformStyle,
      transition: feedbackTransition ? `${feedbackTransition}, translate 0ms linear` : "translate 0ms linear",
      scale: crossFrame ? `${scaleDelta.x} ${scaleDelta.y}` : "",
      "transform-origin": `${transformOrigin.x * 100}% ${transformOrigin.y * 100}%`
    },
    CSS_PREFIX
  );
  if (placeholder) {
    element.insertAdjacentElement("afterend", placeholder);
    if (options == null ? void 0 : options.rootElement) {
      const root = typeof options.rootElement === "function" ? options.rootElement(source) : options.rootElement;
      root.appendChild(element);
    }
  }
  if (supportsPopover(feedbackElement)) {
    if (!feedbackElement.hasAttribute("popover")) {
      feedbackElement.setAttribute("popover", "manual");
    }
    showPopover(feedbackElement);
    feedbackElement.addEventListener("beforetoggle", preventPopoverClose);
  }
  let elementMutationObserver;
  let documentMutationObserver;
  let savedCellWidths;
  const resizeObserver = createResizeObserver({
    placeholder,
    element,
    feedbackElement,
    frameTransform,
    transformOrigin,
    width,
    height,
    top,
    left,
    widthOffset,
    heightOffset,
    delta,
    styles,
    dragOperation,
    getTranslate: () => state.current.translate,
    getElementMutationObserver: () => elementMutationObserver,
    getSavedCellWidths: () => savedCellWidths,
    setSavedCellWidths: (widths) => {
      savedCellWidths = widths;
    }
  });
  const initialShape = new DOMRectangle(feedbackElement);
  f(() => dragOperation.shape = initialShape);
  const feedbackWindow = getWindow(feedbackElement);
  const handleWindowResize = (event) => {
    this.manager.actions.stop({ event });
  };
  const reducedMotion = prefersReducedMotion(feedbackWindow);
  if (isKeyboardOperation) {
    feedbackWindow.addEventListener("resize", handleWindowResize);
  }
  if (f(() => source.status) === "idle") {
    requestAnimationFrame(() => source.status = "dragging");
  }
  if (placeholder) {
    resizeObserver.observe(placeholder);
    elementMutationObserver = createElementMutationObserver(
      element,
      placeholder,
      clone
    );
    documentMutationObserver = createDocumentMutationObserver(
      element,
      placeholder,
      feedbackElement
    );
  }
  const id = (_g = manager.dragOperation.source) == null ? void 0 : _g.id;
  const restoreFocus = () => {
    var _a6;
    if (!isKeyboardOperation || id == null) return;
    const draggable = manager.registry.draggables.get(id);
    const focusTarget = (_a6 = draggable == null ? void 0 : draggable.handle) != null ? _a6 : draggable == null ? void 0 : draggable.element;
    if (isHTMLElement(focusTarget)) {
      focusTarget.focus();
    }
  };
  const cleanup = () => {
    elementMutationObserver == null ? void 0 : elementMutationObserver.disconnect();
    documentMutationObserver == null ? void 0 : documentMutationObserver.disconnect();
    resizeObserver.disconnect();
    feedbackWindow.removeEventListener("resize", handleWindowResize);
    if (supportsPopover(feedbackElement)) {
      feedbackElement.removeEventListener(
        "beforetoggle",
        preventPopoverClose
      );
      feedbackElement.removeAttribute("popover");
    }
    feedbackElement.removeAttribute(ATTRIBUTE);
    styles.reset();
    const finalize = () => {
      var _a6;
      if (savedCellWidths && isTableRow(element)) {
        const cells = Array.from(element.cells);
        for (const [index, cell] of cells.entries()) {
          cell.style.width = (_a6 = savedCellWidths[index]) != null ? _a6 : "";
        }
      }
      source.status = "idle";
      const moved = state.current.translate != null;
      const isDragging = dragOperation.status.dragging;
      if (placeholder && (!isDragging && moved || placeholder.parentElement !== feedbackElement.parentElement) && feedbackElement.isConnected) {
        placeholder.replaceWith(feedbackElement);
      }
      placeholder == null ? void 0 : placeholder.remove();
    };
    if (feedbackElement === this.overlay) {
      setTimeout(finalize, 0);
    } else {
      finalize();
    }
  };
  const optionsDropAnimation = options == null ? void 0 : options.dropAnimation;
  const feedbackPlugin = this;
  const cleanupEffects = effects(
    // Update transform on move
    () => {
      var _a6, _b3, _c4;
      const { transform: transform2, status: status2 } = dragOperation;
      if (!transform2.x && !transform2.y && !state.current.translate) {
        return;
      }
      if (status2.dragging) {
        const initialTranslate2 = (_a6 = initial.translate) != null ? _a6 : { x: 0, y: 0 };
        const translate2 = {
          x: transform2.x / frameTransform.scaleX + initialTranslate2.x,
          y: transform2.y / frameTransform.scaleY + initialTranslate2.y
        };
        const previousTranslate = state.current.translate;
        const modifiers = f(() => dragOperation.modifiers);
        const currentShape = f(() => {
          var _a7;
          return (_a7 = dragOperation.shape) == null ? void 0 : _a7.current;
        });
        const keyboardTransition = options == null ? void 0 : options.keyboardTransition;
        const translateTransition = isKeyboardOperation && !reducedMotion && keyboardTransition !== null ? `${(_b3 = keyboardTransition == null ? void 0 : keyboardTransition.duration) != null ? _b3 : 250}ms ${(_c4 = keyboardTransition == null ? void 0 : keyboardTransition.easing) != null ? _c4 : "cubic-bezier(0.25, 1, 0.5, 1)"}` : "0ms linear";
        styles.set(
          {
            transition: feedbackTransition ? `${feedbackTransition}, translate ${translateTransition}` : `translate ${translateTransition}`,
            translate: `${translate2.x}px ${translate2.y}px 0`
          },
          CSS_PREFIX
        );
        elementMutationObserver == null ? void 0 : elementMutationObserver.takeRecords();
        if (currentShape && currentShape !== initialShape && previousTranslate && !modifiers.length) {
          const delta2 = Point.delta(translate2, previousTranslate);
          dragOperation.shape = Rectangle.from(
            currentShape.boundingRectangle
          ).translate(
            delta2.x * frameTransform.scaleX,
            delta2.y * frameTransform.scaleY
          );
        } else {
          dragOperation.shape = new DOMRectangle(feedbackElement);
        }
        state.current.translate = translate2;
      }
    },
    // Drop animation
    function() {
      if (dragOperation.status.dropped) {
        this.dispose();
        source.status = "dropping";
        const dropAnimationConfig = (entityOptions == null ? void 0 : entityOptions.dropAnimation) !== void 0 ? entityOptions.dropAnimation : feedbackPlugin.dropAnimation !== void 0 ? feedbackPlugin.dropAnimation : optionsDropAnimation;
        let translate2 = state.current.translate;
        const moved = translate2 != null;
        if (!translate2 && element !== feedbackElement) {
          translate2 = { x: 0, y: 0 };
        }
        if (!translate2 || dropAnimationConfig === null) {
          cleanup();
          return;
        }
        manager.renderer.rendering.then(() => {
          runDropAnimation({
            source,
            element,
            feedbackElement,
            placeholder,
            translate: translate2,
            moved,
            transition,
            alignment: source.alignment,
            styles,
            animation: dropAnimationConfig != null ? dropAnimationConfig : void 0,
            getElementMutationObserver: () => elementMutationObserver,
            cleanup,
            restoreFocus
          });
        });
      }
    }
  );
  return () => {
    cleanup();
    cleanupEffects();
  };
};
__decorateElement4(_init23, 4, "overlay", _overlay_dec, _Feedback, _overlay);
__decoratorMetadata4(_init23, _Feedback);
_Feedback.configure = configurator(_Feedback);
var Feedback = _Feedback;
var LOCKED = true;
var UNLOCKED = false;
var _dec;
var _a32;
var _dec2;
var _b2;
var _init33;
var __b;
var __a;
_b2 = (_dec2 = [reactive], ScrollDirection.Forward), _a32 = (_dec = [reactive], ScrollDirection.Reverse);
var ScrollLock = class {
  constructor() {
    __privateAdd5(this, __b, __runInitializers4(_init33, 8, this, LOCKED)), __runInitializers4(_init33, 11, this);
    __privateAdd5(this, __a, __runInitializers4(_init33, 12, this, LOCKED)), __runInitializers4(_init33, 15, this);
  }
  isLocked(direction) {
    if (direction === ScrollDirection.Idle) {
      return false;
    }
    if (direction == null) {
      return this[ScrollDirection.Forward] === LOCKED && this[ScrollDirection.Reverse] === LOCKED;
    }
    return this[direction] === LOCKED;
  }
  unlock(direction) {
    if (direction === ScrollDirection.Idle) {
      return;
    }
    this[direction] = UNLOCKED;
  }
};
_init33 = __decoratorStart4(null);
__b = /* @__PURE__ */ new WeakMap();
__a = /* @__PURE__ */ new WeakMap();
__decorateElement4(_init33, 4, _b2, _dec2, ScrollLock, __b);
__decorateElement4(_init33, 4, _a32, _dec, ScrollLock, __a);
__decoratorMetadata4(_init33, ScrollLock);
var DIRECTIONS = [ScrollDirection.Forward, ScrollDirection.Reverse];
var ScrollIntent = class {
  constructor() {
    this.x = new ScrollLock();
    this.y = new ScrollLock();
  }
  isLocked() {
    return this.x.isLocked() && this.y.isLocked();
  }
};
var ScrollIntentTracker = class extends Plugin {
  constructor(manager) {
    super(manager);
    const scrollIntent = y(new ScrollIntent());
    let previousDelta = null;
    this.signal = scrollIntent;
    j(() => {
      const { status } = manager.dragOperation;
      if (!status.initialized) {
        previousDelta = null;
        scrollIntent.value = new ScrollIntent();
        return;
      }
      const { delta } = manager.dragOperation.position;
      if (previousDelta) {
        const directions = {
          x: getDirection(delta.x, previousDelta.x),
          y: getDirection(delta.y, previousDelta.y)
        };
        const intent = scrollIntent.peek();
        n(() => {
          for (const axis of Axes) {
            for (const direction of DIRECTIONS) {
              if (directions[axis] === direction) {
                intent[axis].unlock(direction);
              }
            }
          }
          scrollIntent.value = intent;
        });
      }
      previousDelta = delta;
    });
  }
  get current() {
    return this.signal.peek();
  }
};
function getDirection(a2, b2) {
  return Math.sign(a2 - b2);
}
var _autoScrolling_dec;
var _a4;
var _init42;
var _autoScrolling;
var _meta;
var _scroll;
var Scroller = class extends (_a4 = CorePlugin, _autoScrolling_dec = [reactive], _a4) {
  constructor(manager) {
    super(manager);
    __privateAdd5(this, _autoScrolling, __runInitializers4(_init42, 8, this, false)), __runInitializers4(_init42, 11, this);
    __privateAdd5(this, _meta);
    __privateAdd5(this, _scroll, () => {
      if (!__privateGet5(this, _meta)) {
        return;
      }
      const { element, by } = __privateGet5(this, _meta);
      if (by.y) element.scrollTop += by.y;
      if (by.x) element.scrollLeft += by.x;
    });
    this.scroll = (options, scrollOptions) => {
      var _a5;
      if (this.disabled) {
        return false;
      }
      const elements = this.getScrollableElements();
      if (!elements) {
        __privateSet5(this, _meta, void 0);
        return false;
      }
      const { position } = this.manager.dragOperation;
      const currentPosition = position == null ? void 0 : position.current;
      if (currentPosition) {
        const { by } = options != null ? options : {};
        const intent = by ? {
          x: getScrollIntent(by.x),
          y: getScrollIntent(by.y)
        } : void 0;
        const scrollIntent = intent ? void 0 : this.scrollIntentTracker.current;
        if (scrollIntent == null ? void 0 : scrollIntent.isLocked()) {
          return false;
        }
        for (const scrollableElement of elements) {
          const elementCanScroll = canScroll(scrollableElement, by);
          if (elementCanScroll.x || elementCanScroll.y) {
            const { speed, direction } = detectScrollIntent(
              scrollableElement,
              currentPosition,
              intent,
              scrollOptions == null ? void 0 : scrollOptions.acceleration,
              scrollOptions == null ? void 0 : scrollOptions.threshold
            );
            if (scrollIntent) {
              for (const axis of Axes) {
                if (scrollIntent[axis].isLocked(direction[axis])) {
                  speed[axis] = 0;
                  direction[axis] = 0;
                }
              }
            }
            if (direction.x || direction.y) {
              const { x: x2, y: y2 } = by != null ? by : direction;
              const scrollLeftBy = x2 * speed.x;
              const scrollTopBy = y2 * speed.y;
              if (scrollLeftBy || scrollTopBy) {
                const previousScrollBy = (_a5 = __privateGet5(this, _meta)) == null ? void 0 : _a5.by;
                if (this.autoScrolling && previousScrollBy) {
                  const scrollIntentMismatch = previousScrollBy.x && !scrollLeftBy || previousScrollBy.y && !scrollTopBy;
                  if (scrollIntentMismatch) continue;
                }
                __privateSet5(this, _meta, {
                  element: scrollableElement,
                  by: {
                    x: scrollLeftBy,
                    y: scrollTopBy
                  }
                });
                scheduler.schedule(__privateGet5(this, _scroll));
                return true;
              }
            }
          }
        }
      }
      __privateSet5(this, _meta, void 0);
      return false;
    };
    let previousElementFromPoint = null;
    let previousScrollableElements = null;
    const elementFromPoint = computed(() => {
      const { position, source } = manager.dragOperation;
      if (!position) {
        return null;
      }
      const element = getElementFromPoint(
        getRoot(source == null ? void 0 : source.element),
        position.current
      );
      if (element) {
        previousElementFromPoint = element;
      }
      return element != null ? element : previousElementFromPoint;
    });
    const scrollableElements = computed(() => {
      const element = elementFromPoint.value;
      const { documentElement } = getDocument(element);
      if (!element || element === documentElement) {
        const { target } = manager.dragOperation;
        const targetElement = target == null ? void 0 : target.element;
        if (targetElement) {
          const elements = getScrollableAncestors(targetElement, {
            excludeElement: false
          });
          previousScrollableElements = elements;
          return elements;
        }
      }
      if (element) {
        const elements = getScrollableAncestors(element, {
          excludeElement: false
        });
        if (this.autoScrolling && previousScrollableElements && elements.size < (previousScrollableElements == null ? void 0 : previousScrollableElements.size)) {
          return previousScrollableElements;
        }
        previousScrollableElements = elements;
        return elements;
      }
      previousScrollableElements = null;
      return null;
    }, deepEqual);
    this.getScrollableElements = () => {
      return scrollableElements.value;
    };
    this.scrollIntentTracker = new ScrollIntentTracker(manager);
    this.destroy = manager.monitor.addEventListener("dragmove", (event) => {
      if (this.disabled || event.defaultPrevented || !isKeyboardEvent(manager.dragOperation.activatorEvent) || !event.by) {
        return;
      }
      if (this.scroll({ by: event.by })) {
        event.preventDefault();
      }
    });
  }
};
_init42 = __decoratorStart4(_a4);
_autoScrolling = /* @__PURE__ */ new WeakMap();
_meta = /* @__PURE__ */ new WeakMap();
_scroll = /* @__PURE__ */ new WeakMap();
__decorateElement4(_init42, 4, "autoScrolling", _autoScrolling_dec, Scroller, _autoScrolling);
__decoratorMetadata4(_init42, Scroller);
function getScrollIntent(value) {
  if (value > 0) {
    return ScrollDirection.Forward;
  }
  if (value < 0) {
    return ScrollDirection.Reverse;
  }
  return ScrollDirection.Idle;
}
var Scheduler2 = class {
  constructor(scheduler5) {
    this.scheduler = scheduler5;
    this.pending = false;
    this.tasks = /* @__PURE__ */ new Set();
    this.resolvers = /* @__PURE__ */ new Set();
    this.flush = () => {
      const { tasks, resolvers } = this;
      this.pending = false;
      this.tasks = /* @__PURE__ */ new Set();
      this.resolvers = /* @__PURE__ */ new Set();
      for (const task of tasks) {
        task();
      }
      for (const resolve of resolvers) {
        resolve();
      }
    };
  }
  schedule(task) {
    this.tasks.add(task);
    if (!this.pending) {
      this.pending = true;
      this.scheduler(this.flush);
    }
    return new Promise((resolve) => this.resolvers.add(resolve));
  }
};
var scheduler32 = new Scheduler2((callback) => {
  if (typeof requestAnimationFrame === "function") {
    requestAnimationFrame(callback);
  } else {
    callback();
  }
});
var AUTOSCROLL_INTERVAL = 10;
var _AutoScroller = class _AutoScroller2 extends Plugin {
  constructor(manager, options) {
    super(manager, options);
    const scroller = manager.registry.plugins.get(Scroller);
    if (!scroller) {
      throw new Error("AutoScroller plugin depends on Scroller plugin");
    }
    this.destroy = j(() => {
      var _a5, _b22, _c32;
      if (this.disabled) {
        return;
      }
      const { position: _2, status } = manager.dragOperation;
      if (status.dragging) {
        const scrollOptions = {
          acceleration: (_a5 = this.options) == null ? void 0 : _a5.acceleration,
          threshold: typeof ((_b22 = this.options) == null ? void 0 : _b22.threshold) === "number" ? { x: this.options.threshold, y: this.options.threshold } : (_c32 = this.options) == null ? void 0 : _c32.threshold
        };
        const canScroll2 = scroller.scroll(void 0, scrollOptions);
        if (canScroll2) {
          scroller.autoScrolling = true;
          const interval = setInterval(
            () => scheduler32.schedule(
              () => scroller.scroll(void 0, scrollOptions)
            ),
            AUTOSCROLL_INTERVAL
          );
          return () => {
            clearInterval(interval);
          };
        } else {
          scroller.autoScrolling = false;
        }
      }
    });
  }
};
_AutoScroller.configure = configurator(_AutoScroller);
var AutoScroller = _AutoScroller;
var listenerOptions = {
  capture: true,
  passive: true
};
var _timeout;
var ScrollListener = class extends CorePlugin {
  constructor(manager) {
    super(manager);
    __privateAdd5(this, _timeout);
    this.handleScroll = () => {
      if (__privateGet5(this, _timeout) == null) {
        __privateSet5(this, _timeout, setTimeout(() => {
          this.manager.collisionObserver.forceUpdate(false);
          __privateSet5(this, _timeout, void 0);
        }, 50));
      }
    };
    const { dragOperation } = this.manager;
    this.destroy = j(() => {
      var _a5, _b22, _c32;
      const enabled = dragOperation.status.dragging;
      if (enabled) {
        const root = (_c32 = (_b22 = (_a5 = dragOperation.source) == null ? void 0 : _a5.element) == null ? void 0 : _b22.ownerDocument) != null ? _c32 : document;
        root.addEventListener("scroll", this.handleScroll, listenerOptions);
        return () => {
          root.removeEventListener(
            "scroll",
            this.handleScroll,
            listenerOptions
          );
        };
      }
    });
  }
};
_timeout = /* @__PURE__ */ new WeakMap();
var CSS_RULES2 = "* { user-select: none !important; -webkit-user-select: none !important; }";
var PreventSelection = class extends Plugin {
  constructor(manager) {
    super(manager);
    this.manager = manager;
    const styleInjector = manager.registry.plugins.get(
      StyleInjector
    );
    const unregisterStyles = styleInjector == null ? void 0 : styleInjector.register(CSS_RULES2);
    this.destroy = j(() => {
      const { dragOperation } = this.manager;
      if (dragOperation.status.initialized) {
        removeSelection();
        document.addEventListener("selectionchange", removeSelection, {
          capture: true
        });
        return () => {
          document.removeEventListener("selectionchange", removeSelection, {
            capture: true
          });
        };
      }
    });
    if (unregisterStyles) {
      const originalDestroy = this.destroy.bind(this);
      this.destroy = () => {
        unregisterStyles();
        originalDestroy();
      };
    }
  }
};
function removeSelection() {
  var _a5;
  (_a5 = document.getSelection()) == null ? void 0 : _a5.removeAllRanges();
}
var defaults = Object.freeze({
  offset: 10,
  keyboardCodes: {
    start: ["Space", "Enter"],
    cancel: ["Escape"],
    end: ["Space", "Enter", "Tab"],
    up: ["ArrowUp"],
    down: ["ArrowDown"],
    left: ["ArrowLeft"],
    right: ["ArrowRight"]
  },
  preventActivation(event, source) {
    var _a5;
    const target = (_a5 = source.handle) != null ? _a5 : source.element;
    return event.target !== target;
  }
});
var _cleanupFunctions2;
var _KeyboardSensor = class _KeyboardSensor2 extends Sensor {
  constructor(manager, options) {
    super(manager);
    this.manager = manager;
    this.options = options;
    __privateAdd5(this, _cleanupFunctions2, []);
    this.listeners = new Listeners();
    this.handleSourceKeyDown = (event, source, options2) => {
      if (this.disabled || event.defaultPrevented) {
        return;
      }
      if (!isElement(event.target)) {
        return;
      }
      if (source.disabled) {
        return;
      }
      const {
        keyboardCodes = defaults.keyboardCodes,
        preventActivation = defaults.preventActivation
      } = options2 != null ? options2 : {};
      if (!keyboardCodes.start.includes(event.code)) {
        return;
      }
      if (!this.manager.dragOperation.status.idle) {
        return;
      }
      if (preventActivation == null ? void 0 : preventActivation(event, source)) return;
      this.handleStart(event, source, options2);
    };
  }
  bind(source, options = this.options) {
    const unbind = j(() => {
      var _a5;
      const target = (_a5 = source.handle) != null ? _a5 : source.element;
      const listener = (event) => {
        if (isKeyboardEvent(event)) {
          this.handleSourceKeyDown(event, source, options);
        }
      };
      if (target) {
        target.addEventListener("keydown", listener);
        return () => {
          target.removeEventListener("keydown", listener);
        };
      }
    });
    return unbind;
  }
  handleStart(event, source, options) {
    const { element } = source;
    if (!element) {
      throw new Error("Source draggable does not have an associated element");
    }
    event.preventDefault();
    event.stopImmediatePropagation();
    scrollIntoViewIfNeeded(element);
    const { center } = new DOMRectangle(element);
    const controller = this.manager.actions.start({
      event,
      coordinates: {
        x: center.x,
        y: center.y
      },
      source
    });
    if (controller.signal.aborted) return this.cleanup();
    this.sideEffects();
    const sourceDocument = getDocument(element);
    const listeners = [
      this.listeners.bind(sourceDocument, [
        {
          type: "keydown",
          listener: (event2) => this.handleKeyDown(event2, source, options),
          options: { capture: true }
        }
      ])
    ];
    __privateGet5(this, _cleanupFunctions2).push(...listeners);
  }
  handleKeyDown(event, _source, options) {
    const { keyboardCodes = defaults.keyboardCodes } = options != null ? options : {};
    if (isKeycode(event, [...keyboardCodes.end, ...keyboardCodes.cancel])) {
      event.preventDefault();
      const canceled = isKeycode(event, keyboardCodes.cancel);
      this.handleEnd(event, canceled);
      return;
    }
    if (isKeycode(event, keyboardCodes.up)) {
      this.handleMove("up", event);
    } else if (isKeycode(event, keyboardCodes.down)) {
      this.handleMove("down", event);
    }
    if (isKeycode(event, keyboardCodes.left)) {
      this.handleMove("left", event);
    } else if (isKeycode(event, keyboardCodes.right)) {
      this.handleMove("right", event);
    }
  }
  handleEnd(event, canceled) {
    this.manager.actions.stop({
      event,
      canceled
    });
    this.cleanup();
  }
  handleMove(direction, event) {
    var _a5, _b22;
    const { shape } = this.manager.dragOperation;
    const factor = event.shiftKey ? 5 : 1;
    let by = {
      x: 0,
      y: 0
    };
    let offset = (_b22 = (_a5 = this.options) == null ? void 0 : _a5.offset) != null ? _b22 : defaults.offset;
    if (typeof offset === "number") {
      offset = { x: offset, y: offset };
    }
    if (!shape) {
      return;
    }
    switch (direction) {
      case "up":
        by = { x: 0, y: -offset.y * factor };
        break;
      case "down":
        by = { x: 0, y: offset.y * factor };
        break;
      case "left":
        by = { x: -offset.x * factor, y: 0 };
        break;
      case "right":
        by = { x: offset.x * factor, y: 0 };
        break;
    }
    if (by.x || by.y) {
      event.preventDefault();
      this.manager.actions.move({
        event,
        by
      });
    }
  }
  sideEffects() {
    const autoScroller = this.manager.registry.plugins.get(AutoScroller);
    if ((autoScroller == null ? void 0 : autoScroller.disabled) === false) {
      autoScroller.disable();
      __privateGet5(this, _cleanupFunctions2).push(() => {
        autoScroller.enable();
      });
    }
  }
  cleanup() {
    __privateGet5(this, _cleanupFunctions2).forEach((cleanup) => cleanup());
    __privateSet5(this, _cleanupFunctions2, []);
  }
  destroy() {
    this.cleanup();
    this.listeners.clear();
  }
};
_cleanupFunctions2 = /* @__PURE__ */ new WeakMap();
_KeyboardSensor.configure = configurator(_KeyboardSensor);
_KeyboardSensor.defaults = defaults;
var KeyboardSensor = _KeyboardSensor;
function isKeycode(event, codes) {
  return codes.includes(event.code);
}
var _coordinates;
var DistanceConstraint = class extends ActivationConstraint {
  constructor() {
    super(...arguments);
    __privateAdd5(this, _coordinates);
  }
  onEvent(event) {
    switch (event.type) {
      case "pointerdown":
        __privateSet5(this, _coordinates, getEventCoordinates(event));
        break;
      case "pointermove":
        if (!__privateGet5(this, _coordinates)) return;
        const { x: x2, y: y2 } = getEventCoordinates(event);
        const delta = {
          x: x2 - __privateGet5(this, _coordinates).x,
          y: y2 - __privateGet5(this, _coordinates).y
        };
        const { tolerance } = this.options;
        if (tolerance && exceedsDistance(delta, tolerance)) {
          this.abort();
          return;
        }
        if (exceedsDistance(delta, this.options.value)) {
          this.activate(event);
        }
        break;
      case "pointerup":
        this.abort();
        break;
    }
  }
  abort() {
    __privateSet5(this, _coordinates, void 0);
  }
};
_coordinates = /* @__PURE__ */ new WeakMap();
var _timeout2;
var _coordinates2;
var DelayConstraint = class extends ActivationConstraint {
  constructor() {
    super(...arguments);
    __privateAdd5(this, _timeout2);
    __privateAdd5(this, _coordinates2);
  }
  onEvent(event) {
    switch (event.type) {
      case "pointerdown":
        __privateSet5(this, _coordinates2, getEventCoordinates(event));
        __privateSet5(this, _timeout2, setTimeout(
          () => this.activate(event),
          this.options.value
        ));
        break;
      case "pointermove":
        if (!__privateGet5(this, _coordinates2)) return;
        const { x: x2, y: y2 } = getEventCoordinates(event);
        const delta = {
          x: x2 - __privateGet5(this, _coordinates2).x,
          y: y2 - __privateGet5(this, _coordinates2).y
        };
        if (exceedsDistance(delta, this.options.tolerance)) {
          this.abort();
        }
        break;
      case "pointerup":
        this.abort();
        break;
    }
  }
  abort() {
    if (__privateGet5(this, _timeout2)) {
      clearTimeout(__privateGet5(this, _timeout2));
      __privateSet5(this, _coordinates2, void 0);
      __privateSet5(this, _timeout2, void 0);
    }
  }
};
_timeout2 = /* @__PURE__ */ new WeakMap();
_coordinates2 = /* @__PURE__ */ new WeakMap();
var PointerActivationConstraints = class {
};
PointerActivationConstraints.Delay = DelayConstraint;
PointerActivationConstraints.Distance = DistanceConstraint;
var defaults2 = Object.freeze({
  activationConstraints(event, source) {
    var _a5;
    const { pointerType, target } = event;
    if (pointerType === "mouse" && isElement(target) && (source.handle === target || ((_a5 = source.handle) == null ? void 0 : _a5.contains(target)))) {
      return void 0;
    }
    if (pointerType === "touch") {
      return [
        new PointerActivationConstraints.Delay({ value: 250, tolerance: 5 })
      ];
    }
    if (isTextInput(target) && !event.defaultPrevented) {
      return [
        new PointerActivationConstraints.Delay({ value: 200, tolerance: 0 })
      ];
    }
    return [
      new PointerActivationConstraints.Delay({ value: 200, tolerance: 10 }),
      new PointerActivationConstraints.Distance({ value: 5 })
    ];
  },
  preventActivation(event, source) {
    var _a5;
    const { target } = event;
    if (target === source.element) return false;
    if (target === source.handle) return false;
    if (!isElement(target)) return false;
    if ((_a5 = source.handle) == null ? void 0 : _a5.contains(target)) return false;
    const interactiveElement = getInteractiveElement(target);
    if (interactiveElement === source.element) return false;
    return Boolean(interactiveElement);
  }
});
var _cleanup;
var _PointerSensor = class _PointerSensor2 extends Sensor {
  constructor(manager, options) {
    super(manager);
    this.manager = manager;
    this.options = options;
    __privateAdd5(this, _cleanup, /* @__PURE__ */ new Set());
    this.listeners = new Listeners();
    this.latest = {
      event: void 0,
      coordinates: void 0
    };
    this.handleMove = () => {
      const { event, coordinates: to } = this.latest;
      if (!event || !to) {
        return;
      }
      this.manager.actions.move({ event, to });
    };
    this.handleCancel = this.handleCancel.bind(this);
    this.handlePointerUp = this.handlePointerUp.bind(this);
    this.handleKeyDown = this.handleKeyDown.bind(this);
  }
  activationConstraints(event, source, options = this.options) {
    const { activationConstraints = defaults2.activationConstraints } = options != null ? options : {};
    const constraints = typeof activationConstraints === "function" ? activationConstraints(event, source) : activationConstraints;
    return constraints;
  }
  bind(source, options = this.options) {
    const unbind = j(() => {
      var _a5;
      const controller = new AbortController();
      const { signal: signal3 } = controller;
      const listener = (event) => {
        if (isPointerEvent(event)) {
          this.handlePointerDown(event, source, options);
        }
      };
      let targets = [(_a5 = source.handle) != null ? _a5 : source.element];
      if (options == null ? void 0 : options.activatorElements) {
        if (Array.isArray(options.activatorElements)) {
          targets = options.activatorElements;
        } else {
          targets = options.activatorElements(source);
        }
      }
      for (const target of targets) {
        if (!target) continue;
        patchWindow(target.ownerDocument.defaultView);
        target.addEventListener("pointerdown", listener, { signal: signal3 });
      }
      return () => controller.abort();
    });
    return unbind;
  }
  handlePointerDown(event, source, options) {
    if (this.disabled || !event.isPrimary || event.button !== 0 || !isElement(event.target) || source.disabled || isCapturedBySensor(event) || !this.manager.dragOperation.status.idle) {
      return;
    }
    const { preventActivation = defaults2.preventActivation } = options != null ? options : {};
    if (preventActivation == null ? void 0 : preventActivation(event, source)) {
      return;
    }
    const { target } = event;
    const isNativeDraggable = isHTMLElement(target) && target.draggable && target.getAttribute("draggable") === "true";
    const offset = getFrameTransform(source.element);
    const { x: x2, y: y2 } = getEventCoordinates(event);
    this.initialCoordinates = {
      x: x2 * offset.scaleX + offset.x,
      y: y2 * offset.scaleY + offset.y
    };
    const constraints = this.activationConstraints(event, source, options);
    event.sensor = this;
    const controller = new ActivationController(
      constraints,
      (event2) => this.handleStart(source, event2)
    );
    controller.signal.onabort = () => this.handleCancel(event);
    controller.onEvent(event);
    this.controller = controller;
    const documents = getDocuments();
    const unbindListeners = this.listeners.bind(documents, [
      {
        type: "pointermove",
        listener: (event2) => this.handlePointerMove(event2, source)
      },
      {
        type: "pointerup",
        listener: this.handlePointerUp,
        options: {
          capture: true
        }
      },
      {
        type: "pointercancel",
        listener: this.handleCancel
      },
      {
        // Cancel activation if there is a competing Drag and Drop interaction
        type: "dragstart",
        listener: isNativeDraggable ? this.handleCancel : preventDefault,
        options: {
          capture: true
        }
      }
    ]);
    const cleanup = () => {
      unbindListeners();
      this.initialCoordinates = void 0;
    };
    __privateGet5(this, _cleanup).add(cleanup);
  }
  handlePointerMove(event, source) {
    var _a5, _b22;
    if (((_a5 = this.controller) == null ? void 0 : _a5.activated) === false) {
      (_b22 = this.controller) == null ? void 0 : _b22.onEvent(event);
      return;
    }
    if (this.manager.dragOperation.status.dragging) {
      const coordinates = getEventCoordinates(event);
      const offset = getFrameTransform(source.element);
      coordinates.x = coordinates.x * offset.scaleX + offset.x;
      coordinates.y = coordinates.y * offset.scaleY + offset.y;
      event.preventDefault();
      event.stopPropagation();
      this.latest.event = event;
      this.latest.coordinates = coordinates;
      scheduler.schedule(this.handleMove);
    }
  }
  handlePointerUp(event) {
    const { status } = this.manager.dragOperation;
    if (!status.idle) {
      event.preventDefault();
      event.stopPropagation();
      const canceled = !status.initialized;
      this.manager.actions.stop({ event, canceled });
    }
    this.cleanup();
  }
  handleKeyDown(event) {
    if (event.key === "Escape") {
      event.preventDefault();
      this.handleCancel(event);
    }
  }
  handleStart(source, event) {
    const { manager, initialCoordinates } = this;
    if (!initialCoordinates || !manager.dragOperation.status.idle) {
      return;
    }
    if (event.defaultPrevented) {
      return;
    }
    const controller = manager.actions.start({
      coordinates: initialCoordinates,
      event,
      source
    });
    if (controller.signal.aborted) return this.cleanup();
    event.preventDefault();
    const ownerDocument = getDocument(event.target);
    const pointerCaptureTarget = ownerDocument.body;
    try {
      pointerCaptureTarget.setPointerCapture(event.pointerId);
    } catch (e2) {
      this.handleCancel(event);
      return;
    }
    const listenerTargets = isElement(event.target) ? [event.target, pointerCaptureTarget] : pointerCaptureTarget;
    const unbind = this.listeners.bind(listenerTargets, [
      {
        // Prevent scrolling on touch devices
        type: "touchmove",
        listener: preventDefault,
        options: {
          passive: false
        }
      },
      {
        // Prevent click events
        type: "click",
        listener: preventDefault
      },
      {
        type: "contextmenu",
        listener: preventDefault
      },
      {
        type: "keydown",
        listener: this.handleKeyDown
      }
    ]);
    __privateGet5(this, _cleanup).add(unbind);
  }
  handleCancel(event) {
    const { dragOperation } = this.manager;
    if (dragOperation.status.initialized) {
      this.manager.actions.stop({ event, canceled: true });
    }
    this.cleanup();
  }
  cleanup() {
    const { controller } = this;
    this.controller = void 0;
    if (controller && !controller.signal.aborted) {
      controller.abort();
    }
    this.latest = {
      event: void 0,
      coordinates: void 0
    };
    __privateGet5(this, _cleanup).forEach((cleanup) => cleanup());
    __privateGet5(this, _cleanup).clear();
  }
  destroy() {
    this.cleanup();
    this.listeners.clear();
  }
};
_cleanup = /* @__PURE__ */ new WeakMap();
_PointerSensor.configure = configurator(_PointerSensor);
_PointerSensor.defaults = defaults2;
var PointerSensor = _PointerSensor;
function isCapturedBySensor(event) {
  return "sensor" in event;
}
function preventDefault(event) {
  event.preventDefault();
}
function noop() {
}
var windows = /* @__PURE__ */ new WeakSet();
function patchWindow(window2) {
  if (!window2 || windows.has(window2)) {
    return;
  }
  window2.addEventListener("touchmove", noop, {
    capture: false,
    passive: false
  });
  windows.add(window2);
}
var defaultPreset = {
  modifiers: [],
  plugins: [Accessibility, AutoScroller, Cursor, Feedback, PreventSelection],
  sensors: [PointerSensor, KeyboardSensor]
};
var DragDropManager2 = class extends DragDropManager {
  constructor(input = {}) {
    const plugins = resolveCustomizable(input.plugins, defaultPreset.plugins);
    const sensors = resolveCustomizable(input.sensors, defaultPreset.sensors);
    const modifiers = resolveCustomizable(
      input.modifiers,
      defaultPreset.modifiers
    );
    super(__spreadProps3(__spreadValues4({}, input), {
      plugins: [ScrollListener, Scroller, StyleInjector, ...plugins],
      sensors,
      modifiers
    }));
  }
};
var _element_dec;
var _handle_dec;
var _c3;
var _init52;
var _handle;
var _element;
var Draggable2 = class extends (_c3 = Draggable, _handle_dec = [reactive], _element_dec = [reactive], _c3) {
  constructor(_a5, manager) {
    var _b22 = _a5, {
      element,
      effects: effects2 = () => [],
      handle
    } = _b22, input = __objRest2(_b22, [
      "element",
      "effects",
      "handle"
    ]);
    super(
      __spreadValues4({
        effects: () => [
          ...effects2(),
          () => {
            var _a6, _b3;
            const { manager: manager2 } = this;
            if (!manager2) return;
            const sensors = (_b3 = (_a6 = this.sensors) == null ? void 0 : _a6.map(descriptor)) != null ? _b3 : [
              ...manager2.sensors
            ];
            const unbindFunctions = sensors.map((entry) => {
              const sensorInstance = entry instanceof Sensor ? entry : manager2.registry.register(entry.plugin);
              const options = entry instanceof Sensor ? void 0 : entry.options;
              const unbind = sensorInstance.bind(this, options);
              return unbind;
            });
            return function cleanup() {
              unbindFunctions.forEach((unbind) => unbind());
            };
          }
        ]
      }, input),
      manager
    );
    __privateAdd5(this, _handle, __runInitializers4(_init52, 8, this)), __runInitializers4(_init52, 11, this);
    __privateAdd5(this, _element, __runInitializers4(_init52, 12, this)), __runInitializers4(_init52, 15, this);
    this.element = element;
    this.handle = handle;
  }
};
_init52 = __decoratorStart4(_c3);
_handle = /* @__PURE__ */ new WeakMap();
_element = /* @__PURE__ */ new WeakMap();
__decorateElement4(_init52, 4, "handle", _handle_dec, Draggable2, _handle);
__decorateElement4(_init52, 4, "element", _element_dec, Draggable2, _element);
__decoratorMetadata4(_init52, Draggable2);
var _proxy_dec;
var _element_dec2;
var _c23;
var _init62;
var _element2;
var _d;
var element_get;
var element_set;
var _Droppable_instances;
var _proxy;
var Droppable2 = class extends (_c23 = Droppable, _element_dec2 = [reactive], _proxy_dec = [reactive], _c23) {
  constructor(_a5, manager) {
    var _b22 = _a5, { element, effects: effects2 = () => [] } = _b22, input = __objRest2(_b22, ["element", "effects"]);
    const { collisionDetector = defaultCollisionDetection } = input;
    const updateShape = (boundingClientRect) => {
      const { manager: manager2, element: element2 } = this;
      if (!element2 || boundingClientRect === null) {
        this.shape = void 0;
        return void 0;
      }
      if (!manager2) return;
      const updatedShape = new DOMRectangle(element2);
      const shape = f(() => this.shape);
      if (updatedShape && (shape == null ? void 0 : shape.equals(updatedShape))) {
        return shape;
      }
      this.shape = updatedShape;
      return updatedShape;
    };
    const observePosition = y(false);
    super(
      __spreadProps3(__spreadValues4({}, input), {
        collisionDetector,
        effects: () => [
          ...effects2(),
          () => {
            const { element: element2, manager: manager2 } = this;
            if (!manager2) return;
            const { dragOperation } = manager2;
            const { source } = dragOperation;
            observePosition.value = Boolean(
              source && dragOperation.status.initialized && element2 && !this.disabled && this.accepts(source)
            );
          },
          () => {
            const { element: element2 } = this;
            if (observePosition.value && element2) {
              const positionObserver = new FrameObserver(
                element2,
                updateShape
              );
              return () => {
                positionObserver.disconnect();
                this.shape = void 0;
              };
            }
          },
          () => {
            var _a6;
            if ((_a6 = this.manager) == null ? void 0 : _a6.dragOperation.status.initialized) {
              return () => {
                this.shape = void 0;
              };
            }
          }
        ]
      }),
      manager
    );
    __privateAdd5(this, _Droppable_instances);
    __privateAdd5(this, _element2, __runInitializers4(_init62, 8, this)), __runInitializers4(_init62, 11, this);
    __privateAdd5(this, _proxy, __runInitializers4(_init62, 12, this)), __runInitializers4(_init62, 15, this);
    this.element = element;
    this.refreshShape = () => updateShape();
  }
  set element(element) {
    __privateSet5(this, _Droppable_instances, element, element_set);
  }
  get element() {
    var _a5;
    return (_a5 = this.proxy) != null ? _a5 : __privateGet5(this, _Droppable_instances, element_get);
  }
};
_init62 = __decoratorStart4(_c23);
_element2 = /* @__PURE__ */ new WeakMap();
_Droppable_instances = /* @__PURE__ */ new WeakSet();
_proxy = /* @__PURE__ */ new WeakMap();
_d = __decorateElement4(_init62, 20, "#element", _element_dec2, _Droppable_instances, _element2), element_get = _d.get, element_set = _d.set;
__decorateElement4(_init62, 4, "proxy", _proxy_dec, Droppable2, _proxy);
__decoratorMetadata4(_init62, Droppable2);

// tools/reading-order/node_modules/@dnd-kit/dom/sortable.js
var __create5 = Object.create;
var __defProp5 = Object.defineProperty;
var __defProps4 = Object.defineProperties;
var __getOwnPropDesc5 = Object.getOwnPropertyDescriptor;
var __getOwnPropDescs4 = Object.getOwnPropertyDescriptors;
var __getOwnPropSymbols5 = Object.getOwnPropertySymbols;
var __hasOwnProp5 = Object.prototype.hasOwnProperty;
var __propIsEnum5 = Object.prototype.propertyIsEnumerable;
var __knownSymbol5 = (name, symbol) => (symbol = Symbol[name]) ? symbol : /* @__PURE__ */ Symbol.for("Symbol." + name);
var __typeError6 = (msg) => {
  throw TypeError(msg);
};
var __defNormalProp5 = (obj, key, value) => key in obj ? __defProp5(obj, key, { enumerable: true, configurable: true, writable: true, value }) : obj[key] = value;
var __spreadValues5 = (a2, b2) => {
  for (var prop in b2 || (b2 = {}))
    if (__hasOwnProp5.call(b2, prop))
      __defNormalProp5(a2, prop, b2[prop]);
  if (__getOwnPropSymbols5)
    for (var prop of __getOwnPropSymbols5(b2)) {
      if (__propIsEnum5.call(b2, prop))
        __defNormalProp5(a2, prop, b2[prop]);
    }
  return a2;
};
var __spreadProps4 = (a2, b2) => __defProps4(a2, __getOwnPropDescs4(b2));
var __objRest3 = (source, exclude) => {
  var target = {};
  for (var prop in source)
    if (__hasOwnProp5.call(source, prop) && exclude.indexOf(prop) < 0)
      target[prop] = source[prop];
  if (source != null && __getOwnPropSymbols5)
    for (var prop of __getOwnPropSymbols5(source)) {
      if (exclude.indexOf(prop) < 0 && __propIsEnum5.call(source, prop))
        target[prop] = source[prop];
    }
  return target;
};
var __decoratorStart5 = (base) => {
  var _a5;
  return [, , , __create5((_a5 = void 0) != null ? _a5 : null)];
};
var __decoratorStrings5 = ["class", "method", "getter", "setter", "accessor", "field", "value", "get", "set"];
var __expectFn5 = (fn) => fn !== void 0 && typeof fn !== "function" ? __typeError6("Function expected") : fn;
var __decoratorContext5 = (kind, name, done, metadata, fns) => ({ kind: __decoratorStrings5[kind], name, metadata, addInitializer: (fn) => done._ ? __typeError6("Already initialized") : fns.push(__expectFn5(fn || null)) });
var __decoratorMetadata5 = (array, target) => __defNormalProp5(target, __knownSymbol5("metadata"), array[3]);
var __runInitializers5 = (array, flags, self, value) => {
  for (var i2 = 0, fns = array[flags >> 1], n2 = fns && fns.length; i2 < n2; i2++) flags & 1 ? fns[i2].call(self) : value = fns[i2].call(self, value);
  return value;
};
var __decorateElement5 = (array, flags, name, decorators, target, extra) => {
  var fn, it, done, ctx, access, k = flags & 7, s2 = false, p2 = false;
  var j2 = array.length + 1, key = __decoratorStrings5[k + 5];
  var initializers = array[j2 - 1] = [], extraInitializers = array[j2] || (array[j2] = []);
  var desc = (target = target.prototype, __getOwnPropDesc5({ get [name]() {
    return __privateGet6(this, extra);
  }, set [name](x2) {
    return __privateSet6(this, extra, x2);
  } }, name));
  for (var i2 = decorators.length - 1; i2 >= 0; i2--) {
    ctx = __decoratorContext5(k, name, done = {}, array[3], extraInitializers);
    {
      ctx.static = s2, ctx.private = p2, access = ctx.access = { has: (x2) => name in x2 };
      access.get = (x2) => x2[name];
      access.set = (x2, y2) => x2[name] = y2;
    }
    it = (0, decorators[i2])({ get: desc.get, set: desc.set }, ctx), done._ = 1;
    if (it === void 0) __expectFn5(it) && (desc[key] = it);
    else if (typeof it !== "object" || it === null) __typeError6("Object expected");
    else __expectFn5(fn = it.get) && (desc.get = fn), __expectFn5(fn = it.set) && (desc.set = fn), __expectFn5(fn = it.init) && initializers.unshift(fn);
  }
  return desc && __defProp5(target, name, desc), target;
};
var __accessCheck6 = (obj, member, msg) => member.has(obj) || __typeError6("Cannot " + msg);
var __privateGet6 = (obj, member, getter) => (__accessCheck6(obj, member, "read from private field"), member.get(obj));
var __privateAdd6 = (obj, member, value) => member.has(obj) ? __typeError6("Cannot add the same private member more than once") : member instanceof WeakSet ? member.add(obj) : member.set(obj, value);
var __privateSet6 = (obj, member, value, setter) => (__accessCheck6(obj, member, "write to private field"), member.set(obj, value), value);
function isSortable(element) {
  return element instanceof SortableDroppable || element instanceof SortableDraggable;
}
var TOLERANCE = 10;
var SortableKeyboardPlugin = class extends Plugin {
  constructor(manager) {
    super(manager);
    const cleanupEffect = j(() => {
      const { dragOperation } = manager;
      if (!isKeyboardEvent(dragOperation.activatorEvent)) {
        return;
      }
      if (!isSortable(dragOperation.source)) {
        return;
      }
      if (dragOperation.status.initialized) {
        const scroller = manager.registry.plugins.get(Scroller);
        if (scroller) {
          scroller.disable();
          return () => scroller.enable();
        }
      }
    });
    const unsubscribe = manager.monitor.addEventListener(
      "dragmove",
      (event, manager2) => {
        queueMicrotask(() => {
          if (this.disabled || event.defaultPrevented || !event.nativeEvent) {
            return;
          }
          const { dragOperation } = manager2;
          if (!isKeyboardEvent(event.nativeEvent)) {
            return;
          }
          if (!isSortable(dragOperation.source)) {
            return;
          }
          if (!dragOperation.shape) {
            return;
          }
          const { actions, collisionObserver, registry } = manager2;
          const { by } = event;
          if (!by) {
            return;
          }
          const direction = getDirection2(by);
          const { source, target } = dragOperation;
          const { center } = dragOperation.shape.current;
          const potentialTargets = [];
          const cleanup = [];
          n(() => {
            for (const droppable of registry.droppables) {
              const { id: id2 } = droppable;
              if (!droppable.accepts(source) || id2 === (target == null ? void 0 : target.id) && isSortable(droppable) || !droppable.element) {
                continue;
              }
              let previousShape = droppable.shape;
              const shape = new DOMRectangle(droppable.element, {
                getBoundingClientRect: (element) => getVisibleBoundingRectangle(element, void 0, 0.2)
              });
              if (!shape.height || !shape.width) continue;
              if (direction == "down" && center.y + TOLERANCE < shape.center.y || direction == "up" && center.y - TOLERANCE > shape.center.y || direction == "left" && center.x - TOLERANCE > shape.center.x || direction == "right" && center.x + TOLERANCE < shape.center.x) {
                potentialTargets.push(droppable);
                droppable.shape = shape;
                cleanup.push(() => droppable.shape = previousShape);
              }
            }
          });
          event.preventDefault();
          collisionObserver.disable();
          const collisions = collisionObserver.computeCollisions(
            potentialTargets,
            closestCorners
          );
          n(() => cleanup.forEach((clean) => clean()));
          const [firstCollision] = collisions;
          if (!firstCollision) {
            return;
          }
          const { id } = firstCollision;
          const { index, group } = source.sortable;
          actions.setDropTarget(id).then(() => {
            const { source: source2, target: target2, shape } = dragOperation;
            if (!source2 || !isSortable(source2) || !shape) {
              return;
            }
            const {
              index: newIndex,
              group: newGroup,
              target: targetElement
            } = source2.sortable;
            const updated = index !== newIndex || group !== newGroup;
            const element = updated ? targetElement : target2 == null ? void 0 : target2.element;
            if (!element) return;
            scrollIntoViewIfNeeded(element);
            const updatedShape = new DOMRectangle(element);
            if (!updatedShape) {
              return;
            }
            const delta = Rectangle.delta(
              updatedShape,
              Rectangle.from(shape.current.boundingRectangle),
              source2.alignment
            );
            actions.move({
              by: delta
            });
            if (updated) {
              actions.setDropTarget(source2.id).then(() => collisionObserver.enable());
            } else {
              collisionObserver.enable();
            }
          });
        });
      }
    );
    this.destroy = () => {
      unsubscribe();
      cleanupEffect();
    };
  }
};
function getDirection2(delta) {
  const { x: x2, y: y2 } = delta;
  if (x2 > 0) {
    return "right";
  } else if (x2 < 0) {
    return "left";
  } else if (y2 > 0) {
    return "down";
  } else if (y2 < 0) {
    return "up";
  }
}
var __defProp22 = Object.defineProperty;
var __defProps22 = Object.defineProperties;
var __getOwnPropDescs22 = Object.getOwnPropertyDescriptors;
var __getOwnPropSymbols22 = Object.getOwnPropertySymbols;
var __hasOwnProp22 = Object.prototype.hasOwnProperty;
var __propIsEnum22 = Object.prototype.propertyIsEnumerable;
var __defNormalProp22 = (obj, key, value) => key in obj ? __defProp22(obj, key, { enumerable: true, configurable: true, writable: true, value }) : obj[key] = value;
var __spreadValues22 = (a2, b2) => {
  for (var prop in b2 || (b2 = {}))
    if (__hasOwnProp22.call(b2, prop))
      __defNormalProp22(a2, prop, b2[prop]);
  if (__getOwnPropSymbols22)
    for (var prop of __getOwnPropSymbols22(b2)) {
      if (__propIsEnum22.call(b2, prop))
        __defNormalProp22(a2, prop, b2[prop]);
    }
  return a2;
};
var __spreadProps22 = (a2, b2) => __defProps22(a2, __getOwnPropDescs22(b2));
function arrayMove(array, from, to) {
  if (from === to) {
    return array;
  }
  const newArray = array.slice();
  newArray.splice(to, 0, newArray.splice(from, 1)[0]);
  return newArray;
}
function getRecordKey(items, id) {
  const key = String(id);
  return Object.prototype.hasOwnProperty.call(items, key) ? key : void 0;
}
function hasSortableIndices(source) {
  return "initialIndex" in source && typeof source.initialIndex === "number" && "index" in source && typeof source.index === "number";
}
function mutate(items, event, mutation) {
  var _a5, _b3;
  const { source, target, canceled } = event.operation;
  if (!source || !target || canceled) {
    if ("preventDefault" in event) event.preventDefault();
    return items;
  }
  const findIndex = (item, id) => item === id || item !== null && typeof item === "object" && "id" in item && item.id === id;
  if (Array.isArray(items)) {
    const sourceIndex2 = items.findIndex((item) => findIndex(item, source.id));
    const targetIndex2 = items.findIndex((item) => findIndex(item, target.id));
    if (sourceIndex2 === -1 || targetIndex2 === -1) {
      if (hasSortableIndices(source)) {
        const from = source.initialIndex;
        const to = source.index;
        if (from === to || from < 0 || from >= items.length) {
          if ("preventDefault" in event) event.preventDefault();
          return items;
        }
        return mutation(items, from, to);
      }
      return items;
    }
    if (!canceled && "index" in source && typeof source.index === "number") {
      const projectedSourceIndex = source.index;
      if (projectedSourceIndex !== sourceIndex2) {
        return mutation(items, sourceIndex2, projectedSourceIndex);
      }
    }
    return mutation(items, sourceIndex2, targetIndex2);
  }
  const entries = Object.entries(items);
  let sourceIndex = -1;
  let sourceParent;
  let targetIndex = -1;
  let targetParent;
  for (const [id, children] of entries) {
    if (sourceIndex === -1) {
      sourceIndex = children.findIndex((item) => findIndex(item, source.id));
      if (sourceIndex !== -1) {
        sourceParent = id;
      }
    }
    if (targetIndex === -1) {
      targetIndex = children.findIndex((item) => findIndex(item, target.id));
      if (targetIndex !== -1) {
        targetParent = id;
      }
    }
    if (sourceIndex !== -1 && targetIndex !== -1) {
      break;
    }
  }
  if (sourceIndex === -1 && hasSortableIndices(source)) {
    const srcParent = source.initialGroup == null ? void 0 : getRecordKey(items, source.initialGroup);
    const srcIndex = source.initialIndex;
    const tgtParent = source.group == null ? void 0 : getRecordKey(items, source.group);
    const tgtIndex = source.index;
    if (srcParent == null || tgtParent == null) {
      if ("preventDefault" in event) event.preventDefault();
      return items;
    }
    if (srcParent === tgtParent && srcIndex === tgtIndex) {
      if ("preventDefault" in event) event.preventDefault();
      return items;
    }
    if (srcParent === tgtParent) {
      return __spreadProps22(__spreadValues22({}, items), {
        [srcParent]: mutation(items[srcParent], srcIndex, tgtIndex)
      });
    }
    const sourceItem2 = items[srcParent][srcIndex];
    return __spreadProps22(__spreadValues22({}, items), {
      [srcParent]: [
        ...items[srcParent].slice(0, srcIndex),
        ...items[srcParent].slice(srcIndex + 1)
      ],
      [tgtParent]: [
        ...items[tgtParent].slice(0, tgtIndex),
        sourceItem2,
        ...items[tgtParent].slice(tgtIndex)
      ]
    });
  }
  if (!source.manager) return items;
  const { dragOperation } = source.manager;
  const position = (_b3 = (_a5 = dragOperation.shape) == null ? void 0 : _a5.current.center) != null ? _b3 : dragOperation.position.current;
  if (targetParent == null) {
    const targetKey = getRecordKey(items, target.id);
    if (targetKey != null) {
      const insertionIndex = target.shape && position.y > target.shape.center.y ? items[targetKey].length : 0;
      targetParent = targetKey;
      targetIndex = insertionIndex;
    }
  }
  if (sourceParent == null || targetParent == null || sourceParent === targetParent && sourceIndex === targetIndex) {
    if (sourceParent != null && sourceParent === targetParent && sourceIndex === targetIndex && hasSortableIndices(source)) {
      const sourceGroupParent = source.group == null ? void 0 : getRecordKey(items, source.group);
      const hasGroupChanged = source.group != null && sourceGroupParent !== sourceParent;
      const hasIndexChanged = source.index !== sourceIndex;
      if (hasGroupChanged || hasIndexChanged) {
        const reconciledTargetParent = source.group == null ? sourceParent : sourceGroupParent;
        if (reconciledTargetParent != null) {
          if (sourceParent === reconciledTargetParent) {
            return __spreadProps22(__spreadValues22({}, items), {
              [sourceParent]: mutation(
                items[sourceParent],
                sourceIndex,
                source.index
              )
            });
          }
          const sourceItem2 = items[sourceParent][sourceIndex];
          return __spreadProps22(__spreadValues22({}, items), {
            [sourceParent]: [
              ...items[sourceParent].slice(0, sourceIndex),
              ...items[sourceParent].slice(sourceIndex + 1)
            ],
            [reconciledTargetParent]: [
              ...items[reconciledTargetParent].slice(0, source.index),
              sourceItem2,
              ...items[reconciledTargetParent].slice(source.index)
            ]
          });
        }
      }
    }
    if ("preventDefault" in event) event.preventDefault();
    return items;
  }
  if (sourceParent === targetParent) {
    return __spreadProps22(__spreadValues22({}, items), {
      [sourceParent]: mutation(items[sourceParent], sourceIndex, targetIndex)
    });
  }
  const isBelowTarget = target.shape && Math.round(position.y) > Math.round(target.shape.center.y);
  const modifier = isBelowTarget ? 1 : 0;
  const sourceItem = items[sourceParent][sourceIndex];
  return __spreadProps22(__spreadValues22({}, items), {
    [sourceParent]: [
      ...items[sourceParent].slice(0, sourceIndex),
      ...items[sourceParent].slice(sourceIndex + 1)
    ],
    [targetParent]: [
      ...items[targetParent].slice(0, targetIndex + modifier),
      sourceItem,
      ...items[targetParent].slice(targetIndex + modifier)
    ]
  });
}
function move(items, event) {
  return mutate(items, event, arrayMove);
}
function getSortableIndices(instances) {
  const sortableIndices = /* @__PURE__ */ new Map();
  for (const [, group] of instances) {
    for (const sortable of group) {
      sortableIndices.set(sortable.id, sortable.index);
    }
  }
  return sortableIndices;
}
function hasChanged(snapshotIndices, instances, newInstances) {
  var _a5;
  for (const [group, sortables] of instances) {
    for (const sortable of sortables) {
      const index = snapshotIndices.get(sortable.id);
      if (sortable.index !== index || sortable.group !== group || !((_a5 = newInstances.get(group)) == null ? void 0 : _a5.has(sortable))) {
        return true;
      }
    }
  }
  return false;
}
var defaultGroup = "__default__";
var OptimisticSortingPlugin = class extends Plugin {
  constructor(manager) {
    super(manager);
    const getSortableInstances = () => {
      const sortableInstances = /* @__PURE__ */ new Map();
      for (const droppable of manager.registry.droppables) {
        if (droppable instanceof SortableDroppable) {
          const { sortable } = droppable;
          const { group } = sortable;
          let instances = sortableInstances.get(group);
          if (!instances) {
            instances = /* @__PURE__ */ new Set();
            sortableInstances.set(group, instances);
          }
          instances.add(sortable);
        }
      }
      return sortableInstances;
    };
    const unsubscribe = [
      manager.monitor.addEventListener("dragover", (event, manager2) => {
        if (this.disabled) {
          return;
        }
        const { dragOperation } = manager2;
        const { source, target } = dragOperation;
        if (!isSortable(source) || !isSortable(target)) {
          return;
        }
        if (source.sortable === target.sortable) {
          return;
        }
        const instances = getSortableInstances();
        const sortableIndices = getSortableIndices(instances);
        const sameGroup = source.sortable.group === target.sortable.group;
        const sourceInstances = instances.get(source.sortable.group);
        const targetInstances = sameGroup ? sourceInstances : instances.get(target.sortable.group);
        if (!sourceInstances || !targetInstances) return;
        queueMicrotask(() => {
          if (event.defaultPrevented) return;
          manager2.renderer.rendering.then(() => {
            var _a5, _b3;
            const newInstances = getSortableInstances();
            if (hasChanged(sortableIndices, instances, newInstances)) {
              return;
            }
            const sourceElement = source.sortable.element;
            const targetElement = target.sortable.element;
            if (!targetElement || !sourceElement) {
              return;
            }
            if (!sameGroup && target.id === source.sortable.group) {
              return;
            }
            const orderedSourceSortables = sort(sourceInstances);
            const orderedTargetSortables = sameGroup ? orderedSourceSortables : sort(targetInstances);
            const sourceGroup = (_a5 = source.sortable.group) != null ? _a5 : defaultGroup;
            const targetGroup = (_b3 = target.sortable.group) != null ? _b3 : defaultGroup;
            const state = {
              [sourceGroup]: orderedSourceSortables,
              [targetGroup]: orderedTargetSortables
            };
            const newState = move(state, event);
            if (state === newState) return;
            const sourceIndex = newState[targetGroup].indexOf(source.sortable);
            const targetIndex = newState[targetGroup].indexOf(target.sortable);
            manager2.collisionObserver.disable();
            reorder(sourceElement, sourceIndex, targetElement, targetIndex);
            n(() => {
              for (const [index, sortable] of newState[sourceGroup].entries()) {
                sortable.index = index;
              }
              if (!sameGroup) {
                for (const [index, sortable] of newState[targetGroup].entries()) {
                  sortable.group = target.sortable.group;
                  sortable.index = index;
                }
              }
            });
            manager2.actions.setDropTarget(source.id).then(() => manager2.collisionObserver.enable());
          });
        });
      }),
      manager.monitor.addEventListener("dragend", (event, manager2) => {
        if (!event.canceled) {
          return;
        }
        const { dragOperation } = manager2;
        const { source } = dragOperation;
        if (!isSortable(source)) {
          return;
        }
        if (source.sortable.initialIndex === source.sortable.index && source.sortable.initialGroup === source.sortable.group) {
          return;
        }
        queueMicrotask(() => {
          const instances = getSortableInstances();
          const sortableIndices = getSortableIndices(instances);
          const initialGroupInstances = instances.get(
            source.sortable.initialGroup
          );
          if (!initialGroupInstances) return;
          manager2.renderer.rendering.then(() => {
            const newInstances = getSortableInstances();
            if (hasChanged(sortableIndices, instances, newInstances)) {
              return;
            }
            const currentSortables = sort(initialGroupInstances);
            const initialSortables = sort(
              initialGroupInstances,
              sortByInitialIndex
            );
            const sourceElement = source.sortable.element;
            const initialPosition = initialSortables.indexOf(source.sortable);
            const target = currentSortables[initialPosition];
            const targetElement = target == null ? void 0 : target.element;
            if (!target || !targetElement || !sourceElement) {
              return;
            }
            reorder(sourceElement, target.index, targetElement, source.index);
            n(() => {
              for (const sortableInstances of instances.values()) {
                const entries = Array.from(sortableInstances).values();
                for (const sortable of entries) {
                  sortable.index = sortable.initialIndex;
                  sortable.group = sortable.initialGroup;
                }
              }
            });
          });
        });
      })
    ];
    this.destroy = () => {
      for (const unsubscribeListener of unsubscribe) {
        unsubscribeListener();
      }
    };
  }
};
function reorder(sourceElement, sourceIndex, targetElement, targetIndex) {
  const position = targetIndex < sourceIndex ? "afterend" : "beforebegin";
  targetElement.insertAdjacentElement(position, sourceElement);
}
function sortByIndex(a2, b2) {
  return a2.index - b2.index;
}
function sortByInitialIndex(a2, b2) {
  return a2.initialIndex - b2.initialIndex;
}
function sort(instances, sortFn = sortByIndex) {
  return Array.from(instances).sort(sortFn);
}
var defaultPlugins = [
  SortableKeyboardPlugin,
  OptimisticSortingPlugin
];
var defaultSortableTransition = {
  duration: 250,
  easing: "cubic-bezier(0.25, 1, 0.5, 1)",
  idle: false
};
function normalizeDisabled(disabled) {
  var _a5, _b3;
  if (typeof disabled === "boolean") {
    return {
      draggable: disabled,
      droppable: disabled
    };
  }
  return {
    draggable: (_a5 = disabled == null ? void 0 : disabled.draggable) != null ? _a5 : false,
    droppable: (_b3 = disabled == null ? void 0 : disabled.droppable) != null ? _b3 : false
  };
}
var store = new WeakStore();
var _group_dec;
var _index_dec;
var _init8;
var _index;
var _previousGroup;
var _previousIndex;
var _group;
var _element3;
_index_dec = [reactive], _group_dec = [reactive];
var Sortable2 = class {
  constructor(_a5, manager) {
    __privateAdd6(this, _index, __runInitializers5(_init8, 8, this)), __runInitializers5(_init8, 11, this);
    __privateAdd6(this, _previousGroup);
    __privateAdd6(this, _previousIndex);
    __privateAdd6(this, _group, __runInitializers5(_init8, 12, this)), __runInitializers5(_init8, 15, this);
    __privateAdd6(this, _element3);
    this.register = () => {
      n(() => {
        var _a6, _b4;
        (_a6 = this.manager) == null ? void 0 : _a6.registry.register(this.droppable);
        (_b4 = this.manager) == null ? void 0 : _b4.registry.register(this.draggable);
      });
      return () => this.unregister();
    };
    this.unregister = () => {
      n(() => {
        var _a6, _b4;
        (_a6 = this.manager) == null ? void 0 : _a6.registry.unregister(this.droppable);
        (_b4 = this.manager) == null ? void 0 : _b4.registry.unregister(this.draggable);
      });
    };
    this.destroy = () => {
      n(() => {
        this.droppable.destroy();
        this.draggable.destroy();
      });
    };
    var _b3 = _a5, {
      effects: inputEffects = () => [],
      disabled,
      group,
      index,
      sensors,
      type,
      transition = defaultSortableTransition,
      plugins: pluginsInput
    } = _b3, input = __objRest3(_b3, [
      "effects",
      "disabled",
      "group",
      "index",
      "sensors",
      "type",
      "transition",
      "plugins"
    ]);
    const plugins = resolveCustomizable(pluginsInput, defaultPlugins);
    const disabledState = normalizeDisabled(disabled);
    this.droppable = new SortableDroppable(
      __spreadProps4(__spreadValues5({}, input), { disabled: disabledState.droppable }),
      manager,
      this
    );
    this.draggable = new SortableDraggable(
      __spreadProps4(__spreadValues5({}, input), {
        disabled: disabledState.draggable,
        plugins,
        effects: () => [
          () => {
            var _a23, _b22, _c4;
            const status = (_a23 = this.manager) == null ? void 0 : _a23.dragOperation.status;
            if ((status == null ? void 0 : status.initializing) && this.id === ((_c4 = (_b22 = this.manager) == null ? void 0 : _b22.dragOperation.source) == null ? void 0 : _c4.id)) {
              store.clear(this.manager);
            }
            if (status == null ? void 0 : status.dragging) {
              store.set(
                this.manager,
                this.id,
                f(() => ({
                  initialIndex: this.index,
                  initialGroup: this.group
                }))
              );
            }
          },
          () => {
            const { index: index2, group: group2, manager: _2 } = this;
            const previousIndex = __privateGet6(this, _previousIndex);
            const previousGroup = __privateGet6(this, _previousGroup);
            if (index2 !== previousIndex || group2 !== previousGroup) {
              __privateSet6(this, _previousIndex, index2);
              __privateSet6(this, _previousGroup, group2);
              this.animate();
            }
          },
          () => {
            var _a23, _b22;
            const { target } = this;
            const { isDragSource } = this.draggable;
            const feedback = (_b22 = (_a23 = this.draggable.pluginConfig(Feedback)) == null ? void 0 : _a23.feedback) != null ? _b22 : "default";
            if (feedback === "move" && isDragSource) {
              this.droppable.disabled = !target;
            }
          },
          ...inputEffects()
        ],
        type,
        sensors
      }),
      manager,
      this
    );
    __privateSet6(this, _element3, input.element);
    this.manager = manager;
    this.index = index;
    __privateSet6(this, _previousIndex, index);
    this.group = group;
    __privateSet6(this, _previousGroup, group);
    this.type = type;
    this.transition = transition;
  }
  get initialIndex() {
    var _a5, _b3;
    return (_b3 = (_a5 = store.get(this.manager, this.id)) == null ? void 0 : _a5.initialIndex) != null ? _b3 : this.index;
  }
  get initialGroup() {
    var _a5, _b3;
    return (_b3 = (_a5 = store.get(this.manager, this.id)) == null ? void 0 : _a5.initialGroup) != null ? _b3 : this.group;
  }
  animate() {
    f(() => {
      const { manager, transition } = this;
      const { shape } = this.droppable;
      if (!manager) return;
      const { idle } = manager.dragOperation.status;
      if (!shape || !transition || idle && !transition.idle) {
        return;
      }
      manager.renderer.rendering.then(() => {
        const { element } = this;
        if (!element) {
          return;
        }
        for (const animation of element.getAnimations()) {
          if ("transitionProperty" in animation && (animation.transitionProperty === "transform" || animation.transitionProperty === "translate" || animation.transitionProperty === "scale")) {
            animation.cancel();
          }
        }
        const updatedShape = this.refreshShape();
        if (!updatedShape) {
          return;
        }
        const delta = {
          x: shape.boundingRectangle.left - updatedShape.boundingRectangle.left,
          y: shape.boundingRectangle.top - updatedShape.boundingRectangle.top
        };
        const { translate } = getComputedStyles(element);
        const currentTranslate = computeTranslate(element, translate, false);
        const finalTranslate = computeTranslate(element, translate);
        if (delta.x || delta.y) {
          const resolvedTransition = prefersReducedMotion(getWindow(element)) ? __spreadProps4(__spreadValues5({}, transition), { duration: 0 }) : transition;
          animateTransform({
            element,
            keyframes: {
              translate: [
                `${currentTranslate.x + delta.x}px ${currentTranslate.y + delta.y}px ${currentTranslate.z}`,
                `${finalTranslate.x}px ${finalTranslate.y}px ${finalTranslate.z}`
              ]
            },
            options: resolvedTransition
          }).then(() => {
            if (!manager.dragOperation.status.dragging) {
              this.droppable.shape = void 0;
            }
          });
        }
      });
    });
  }
  get manager() {
    return this.draggable.manager;
  }
  set manager(manager) {
    n(() => {
      this.draggable.manager = manager;
      this.droppable.manager = manager;
    });
  }
  set element(element) {
    n(() => {
      const previousElement = __privateGet6(this, _element3);
      const droppableElement = this.droppable.element;
      const draggableElement = this.draggable.element;
      if (!droppableElement || droppableElement === previousElement) {
        this.droppable.element = element;
      }
      if (!draggableElement || draggableElement === previousElement) {
        this.draggable.element = element;
      }
      __privateSet6(this, _element3, element);
    });
  }
  get element() {
    var _a5, _b3;
    const element = __privateGet6(this, _element3);
    if (!element) return;
    return (_b3 = (_a5 = ProxiedElements.get(element)) != null ? _a5 : element) != null ? _b3 : this.droppable.element;
  }
  set target(target) {
    this.droppable.element = target;
  }
  get target() {
    return this.droppable.element;
  }
  set source(source) {
    this.draggable.element = source;
  }
  get source() {
    return this.draggable.element;
  }
  get disabled() {
    const { disabled: draggable } = this.draggable;
    const { disabled: droppable } = this.droppable;
    return draggable === droppable ? draggable : { draggable, droppable };
  }
  set plugins(value) {
    this.draggable.plugins = resolveCustomizable(value, defaultPlugins);
  }
  set disabled(value) {
    const disabled = normalizeDisabled(value);
    n(() => {
      this.droppable.disabled = disabled.droppable;
      this.draggable.disabled = disabled.draggable;
    });
  }
  set data(data) {
    n(() => {
      this.droppable.data = data;
      this.draggable.data = data;
    });
  }
  set handle(handle) {
    this.draggable.handle = handle;
  }
  set id(id) {
    this.droppable.id = id;
    this.draggable.id = id;
  }
  get id() {
    return this.droppable.id;
  }
  set sensors(value) {
    this.draggable.sensors = value;
  }
  set modifiers(value) {
    this.draggable.modifiers = value;
  }
  set collisionPriority(value) {
    this.droppable.collisionPriority = value;
  }
  set collisionDetector(value) {
    this.droppable.collisionDetector = value != null ? value : defaultCollisionDetection;
  }
  set alignment(value) {
    this.draggable.alignment = value;
  }
  get alignment() {
    return this.draggable.alignment;
  }
  set type(type) {
    n(() => {
      this.droppable.type = type;
      this.draggable.type = type;
    });
  }
  get type() {
    return this.draggable.type;
  }
  set accept(value) {
    this.droppable.accept = value;
  }
  get accept() {
    return this.droppable.accept;
  }
  get isDropTarget() {
    return this.droppable.isDropTarget;
  }
  /**
   * A boolean indicating whether the sortable item is the source of a drag operation.
   */
  get isDragSource() {
    return this.draggable.isDragSource;
  }
  /**
   * A boolean indicating whether the sortable item is being dragged.
   */
  get isDragging() {
    return this.draggable.isDragging;
  }
  /**
   * A boolean indicating whether the sortable item is being dropped.
   */
  get isDropping() {
    return this.draggable.isDropping;
  }
  get status() {
    return this.draggable.status;
  }
  refreshShape() {
    return this.droppable.refreshShape();
  }
  accepts(draggable) {
    return this.droppable.accepts(draggable);
  }
};
_init8 = __decoratorStart5();
_index = /* @__PURE__ */ new WeakMap();
_previousGroup = /* @__PURE__ */ new WeakMap();
_previousIndex = /* @__PURE__ */ new WeakMap();
_group = /* @__PURE__ */ new WeakMap();
_element3 = /* @__PURE__ */ new WeakMap();
__decorateElement5(_init8, 4, "index", _index_dec, Sortable2, _index);
__decorateElement5(_init8, 4, "group", _group_dec, Sortable2, _group);
__decoratorMetadata5(_init8, Sortable2);
var SortableDraggable = class extends Draggable2 {
  constructor(input, manager, sortable) {
    super(input, manager);
    this.sortable = sortable;
  }
  get index() {
    return this.sortable.index;
  }
  get initialIndex() {
    return this.sortable.initialIndex;
  }
  get group() {
    return this.sortable.group;
  }
  get initialGroup() {
    return this.sortable.initialGroup;
  }
};
var SortableDroppable = class extends Droppable2 {
  constructor(input, manager, sortable) {
    super(input, manager);
    this.sortable = sortable;
  }
  get index() {
    return this.sortable.index;
  }
  get group() {
    return this.sortable.group;
  }
};

// tools/reading-order/reading-order.js
window.initializeReadingOrder = (bridge) => {
  const launch = document.getElementById("repair-reading-order");
  if (!launch) return;
  const dialog = document.createElement("dialog");
  dialog.id = "reading-order-dialog";
  dialog.setAttribute("aria-labelledby", "ro-heading");
  dialog.setAttribute("aria-describedby", "ro-scope");
  dialog.innerHTML = `<header class="ro-header"><div><h2 id="ro-heading">Repair reading order</h2><p id="ro-scope"></p></div><button type="button" id="ro-close" aria-label="Close reading order">\xD7</button></header>
 <div class="ro-columns" tabindex="0" role="region" aria-label="Source and reading-order panels"><section class="ro-source"><div class="ro-tools"><h3 id="ro-source-title">Source page</h3><label><input type="checkbox" id="ro-labels"> Order labels</label></div><div class="ro-source-scroll" tabindex="0" role="region" aria-label="Source PDF page image"><div class="ro-source-image"><img id="ro-image" alt=""><div id="ro-regions" aria-hidden="true"></div></div></div><p id="ro-region-note" class="helper-text"></p><a id="ro-source-link" target="_blank" rel="noopener">Open source PDF</a></section>
 <section class="ro-sequence"><div class="ro-tools"><h3>Draft reading order</h3><div><button id="ro-undo" type="button">Undo draft</button><button id="ro-reset" type="button">Reset</button></div></div><p class="helper-text" id="ro-instructions">Drag a handle or use Move to. Select adjacent paragraphs or compatible lists to merge.</p><details class="ro-keyboard-help"><summary>Keyboard help</summary><p id="ro-keyboard-instructions" class="helper-text">Focus a drag handle. Space/Enter picks up, \u2191/\u2193 moves, then Space/Enter drops. Escape cancels a move. Tab reaches selection checkboxes, Full text and Move to.</p></details><ol id="ro-cards" tabindex="0" aria-label="Draft reading order"></ol><details id="ro-excluded"><summary>Excluded content <span id="ro-excluded-count"></span></summary><p class="helper-text">Retained outside this sequence; intervening excluded content cannot be skipped by a merge.</p><ul id="ro-excluded-list"></ul></details></section></div>
 <footer class="ro-footer"><div><strong id="ro-moved"></strong><p class="helper-text">Draft only until Apply \xB7 one saved Undo restores the whole change</p><p id="ro-selection" class="helper-text" role="status" aria-live="polite"></p><p id="ro-status" role="status" aria-live="polite"></p></div><div><button id="ro-merge" type="button" aria-describedby="ro-selection">Merge selected</button><button id="ro-cancel" type="button" class="secondary">Cancel</button><button id="ro-apply" type="button">Apply changes</button></div></footer><p id="ro-live" class="ro-sr" role="status" aria-live="polite" aria-atomic="true"></p>`;
  document.body.append(dialog);
  const discard = document.createElement("dialog");
  discard.id = "ro-discard";
  discard.setAttribute("aria-labelledby", "ro-discard-heading");
  discard.innerHTML = '<h2 id="ro-discard-heading">Discard this reading-order draft?</h2><p>Nothing has been saved.</p><button type="button" id="ro-keep">Keep editing</button><button type="button" id="ro-discard-confirm" class="secondary">Discard draft</button>';
  document.body.append(discard);
  const confirm = document.createElement("dialog");
  confirm.id = "ro-confirm";
  confirm.setAttribute("aria-labelledby", "ro-confirm-heading");
  confirm.setAttribute("aria-describedby", "ro-confirm-note");
  confirm.innerHTML = '<div class="ro-confirm-body" tabindex="0" role="region" aria-label="Merge or unmerge preview"><h2 id="ro-confirm-heading"></h2><p id="ro-confirm-note"></p><div id="ro-confirm-content"></div></div><div class="ro-confirm-actions"><button type="button" id="ro-confirm-cancel" class="secondary">Keep editing</button><button type="button" id="ro-confirm-stage">Stage merge</button></div>';
  document.body.append(confirm);
  const $ = (id) => document.getElementById(id);
  let initialView, snapshot2, order = [], baselineKey = "", operations = [], history = [], selected = null, checked = /* @__PURE__ */ new Set(), manager = null, sortables = [], busy = false, uncertain = false, dragging = false, opening = false, pending = null, imageReady = false, imageFailed = false, imageTimer;
  const equal = (a2, b2) => JSON.stringify(a2) === JSON.stringify(b2), row = (id) => snapshot2.rows.find((b2) => b2.id === id);
  const numberFor = (id) => snapshot2.rows[order.indexOf(id)]?.number;
  const key = () => JSON.stringify(order.map((id) => {
    const b2 = row(id);
    return [id, b2.type, b2.text, b2.merge_count, b2.preview];
  }));
  const dirty = () => key() !== baselineKey;
  const capture = () => ({ snapshot: structuredClone(snapshot2), order: [...order], operations: structuredClone(operations) });
  const restore = (state) => {
    snapshot2 = state.snapshot;
    order = state.order;
    operations = state.operations;
    checked.clear();
    if (!order.includes(selected)) selected = null;
  };
  const say = (text) => {
    $("ro-live").textContent = text;
  };
  function typeIcon(b2, index) {
    const label = b2.type === "list" ? `${b2.preview.ordered ? "Ordered" : "Unordered"} list` : b2.type.replaceAll("_", " ").replace(/^./, (c2) => c2.toUpperCase());
    const shapes = { paragraph: '<path d="M10 4h9M15 4v16M19 4v16M10 4a5 5 0 0 0 0 10h5"/>', heading: '<path d="M5 4v16M19 4v16M5 12h14"/>', image: '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="8" cy="9" r="2"/><path d="m3 18 6-5 4 3 3-4 5 5"/>', table: '<rect x="3" y="4" width="18" height="16" rx="1"/><path d="M3 9h18M3 14h18M9 4v16M15 4v16"/>', quote: '<path d="M5 5h5v8H5v-4l3-4M5 13v6M14 5h5v8h-5v-4l3-4M14 13v6"/>', list_item: '<circle cx="4" cy="12" r="1"/><path d="M9 12h12"/>' };
    const list = b2.preview.ordered ? '<text x="2" y="9" stroke="none" fill="currentColor" font-size="8">1</text><text x="2" y="19" stroke="none" fill="currentColor" font-size="8">2</text><path d="M9 6h12M9 16h12"/>' : '<circle cx="4" cy="6" r="1"/><circle cx="4" cy="12" r="1"/><circle cx="4" cy="18" r="1"/><path d="M9 6h12M9 12h12M9 18h12"/>';
    const icon = document.createElement("span");
    icon.className = "ro-kind";
    icon.tabIndex = 0;
    icon.setAttribute("role", "img");
    icon.setAttribute("aria-label", label);
    icon.dataset.blockType = b2.type;
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.setAttribute("aria-hidden", "true");
    svg.setAttribute("focusable", "false");
    svg.innerHTML = b2.type === "list" ? list : shapes[b2.type] || '<circle cx="12" cy="12" r="9"/><path d="M9 8a3 3 0 0 1 6 0c0 3-3 2-3 5M12 17v1"/>';
    icon.append(svg);
    const tip = document.createElement("span");
    tip.id = `ro-type-help-${index}`;
    tip.className = "ro-kind-tooltip";
    tip.setAttribute("role", "tooltip");
    tip.setAttribute("popover", "manual");
    tip.textContent = label;
    tip.hidden = true;
    let hideTimer;
    const hide = () => {
      clearTimeout(hideTimer);
      if (tip.matches(":popover-open")) tip.hidePopover();
      tip.hidden = true;
    };
    const show = () => {
      clearTimeout(hideTimer);
      tip.hidden = false;
      if (tip.showPopover && !tip.matches(":popover-open")) tip.showPopover();
      const r2 = icon.getBoundingClientRect(), t2 = tip.getBoundingClientRect();
      tip.style.left = `${Math.max(8, Math.min(r2.left, innerWidth - t2.width - 8))}px`;
      tip.style.top = `${r2.bottom + t2.height + 12 < innerHeight ? r2.bottom + 4 : Math.max(8, r2.top - t2.height - 4)}px`;
    };
    icon.addEventListener("mouseenter", show);
    icon.addEventListener("mouseleave", () => {
      if (document.activeElement !== icon) hideTimer = setTimeout(hide, 120);
    });
    tip.addEventListener("mouseenter", () => clearTimeout(hideTimer));
    tip.addEventListener("mouseleave", () => {
      if (document.activeElement !== icon) hide();
    });
    icon.addEventListener("focus", show);
    icon.addEventListener("blur", hide);
    icon.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && !tip.hidden) {
        event.preventDefault();
        event.stopPropagation();
        hide();
      }
    });
    return [icon, tip];
  }
  const excerpt = (b2) => {
    const words = String(b2.text || "").trim().split(/\s+/).filter(Boolean);
    return words.length ? words.slice(0, 5).join(" ") + (words.length > 5 ? "\u2026" : "") : `${b2.type || "Block"} (no text)`;
  };
  function previewNode(value) {
    if (value.kind === "list") {
      const list = document.createElement(value.ordered ? "ol" : "ul");
      if (value.ordered) {
        list.start = value.start || 1;
        const type = { "lower-alpha": "a", "upper-alpha": "A", "lower-roman": "i", "upper-roman": "I" }[value.marker_style];
        if (type) list.type = type;
      }
      for (const item of value.items) {
        const li = document.createElement("li");
        const text2 = document.createElement("span");
        text2.textContent = item.text;
        li.append(text2);
        item.children.forEach((child) => li.append(previewNode(child)));
        list.append(li);
      }
      return list;
    }
    const text = document.createElement("p");
    text.className = "ro-full-text";
    text.textContent = value.text || "No text content.";
    return text;
  }
  function destroy() {
    sortables.forEach((item) => item.destroy());
    sortables = [];
    manager?.destroy();
    manager = null;
    dragging = false;
  }
  function reveal(element, container) {
    if (!element) return;
    const r2 = element.getBoundingClientRect(), v2 = container.getBoundingClientRect();
    if (r2.top < v2.top) container.scrollTop += r2.top - v2.top;
    else if (r2.bottom > v2.bottom) container.scrollTop += Math.min(r2.top - v2.top, r2.bottom - v2.bottom);
  }
  function select(id) {
    selected = id;
    [...$("ro-cards").children].forEach((c2) => c2.classList.toggle("ro-selected", c2.dataset.id === id));
    drawRegions();
    reveal($("ro-regions").querySelector(".ro-region-selected"), dialog.querySelector(".ro-source-scroll"));
  }
  function drawRegions() {
    $("ro-regions").replaceChildren();
    if (!imageReady) {
      $("ro-region-note").textContent = imageFailed ? "Source image could not be displayed. Open the source PDF before confirming changes." : "Loading source page\u2026";
      return;
    }
    const size = snapshot2?.size;
    for (const [index, id] of order.entries()) {
      const b2 = row(id);
      if (!size || !b2.regions?.length || !$("ro-labels").checked && id !== selected) continue;
      for (const [x0, y0, x1, y1] of b2.regions) {
        const region = document.createElement("span");
        region.className = "ro-region" + (id === selected ? " ro-region-selected" : " ro-region-label");
        Object.assign(region.style, { left: `${100 * x0 / size[0]}%`, top: `${100 * (size[1] - y1) / size[1]}%`, width: `${100 * (x1 - x0) / size[0]}%`, height: `${100 * (y1 - y0) / size[1]}%` });
        if ($("ro-labels").checked) {
          const label = document.createElement("span");
          label.textContent = snapshot2.rows[index].number;
          region.append(label);
        }
        $("ro-regions").append(region);
      }
    }
    $("ro-region-note").textContent = selected ? row(selected).regions?.length ? "Recorded source regions outlined." : "No reliable source region is available for this block. Use the source PDF." : "Select a block to outline its recorded source regions.";
  }
  function selectionReason() {
    const ids2 = order.filter((id) => checked.has(id));
    if (ids2.length < 2) return "Select at least two consecutive paragraphs or compatible list blocks.";
    const indexes = ids2.map((id) => order.indexOf(id));
    if (indexes.some((index, n2) => index !== indexes[0] + n2 || snapshot2.rows[index].index !== snapshot2.rows[indexes[0]].index + n2)) return "Selections must be consecutive in document order; excluded or intervening content cannot be skipped.";
    const first = row(ids2[0]);
    for (const id of ids2) {
      const b2 = row(id);
      if (b2.merge_reason) return b2.merge_reason;
      if (b2.type !== first.type) return `Block ${numberFor(ids2[0])} is a ${first.type}, but Block ${numberFor(id)} is a ${b2.type}. Mixed types cannot merge. Check their classification against the source; merge paragraphs with paragraphs or compatible lists with lists.`;
      if (!equal(b2.owners, first.owners) || b2.owners.length > 1) return "Assign these blocks to the same Arrange Page before merging.";
    }
    if (first.type === "list") {
      let start = first.preview.start;
      for (const id of ids2) {
        const b2 = row(id).preview;
        if (b2.ordered !== first.preview.ordered || (b2.marker_style || "decimal") !== (first.preview.marker_style || "decimal")) return "List kinds and marker styles must match.";
        if (b2.ordered && b2.start !== start) return "Ordered lists must continue their recorded numbering; restarts stay separate.";
        start += b2.items.length;
      }
    }
    return "";
  }
  function updateSelection() {
    const reason = selectionReason();
    $("ro-selection").textContent = `${checked.size} selected \xB7 ${reason || "Ready to preview merge."}`;
    $("ro-merge").disabled = Boolean(reason) || busy || uncertain;
  }
  function render(focusId) {
    destroy();
    $("ro-cards").replaceChildren();
    $("ro-scope").textContent = `${snapshot2.rows.length} draft rows \xB7 ${snapshot2.excluded.length} excluded. Shared blocks are fixed. Order, merge and unmerge stay drafts until Apply. Other pages stay in place.`;
    for (const [i2, id] of order.entries()) {
      const b2 = row(id), position = snapshot2.rows[i2].number, li = document.createElement("li");
      li.className = "ro-card";
      li.dataset.id = id;
      const main = document.createElement("div");
      main.className = "ro-card-main";
      const checkboxLabel = document.createElement("label");
      checkboxLabel.className = "ro-check";
      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.checked = checked.has(id);
      checkbox.disabled = b2.locked || Boolean(b2.merge_reason) || busy || uncertain;
      checkbox.setAttribute("aria-label", `Select block ${position} for merge`);
      checkbox.title = b2.merge_reason || "Select for merge";
      checkbox.onchange = () => {
        if (checkbox.checked) checked.add(id);
        else checked.delete(id);
        updateSelection();
      };
      checkboxLabel.append(checkbox);
      const handle = document.createElement("button");
      handle.type = "button";
      handle.className = "ro-handle";
      handle.textContent = b2.locked ? "\u{1F512}" : "\u283F";
      handle.disabled = b2.locked || busy || uncertain;
      handle.setAttribute("aria-label", `Move block ${position}`);
      handle.setAttribute("aria-describedby", "ro-instructions ro-keyboard-instructions");
      const number = document.createElement("strong");
      number.className = "ro-number";
      number.textContent = `Block ${position}`;
      const text = document.createElement("p");
      text.className = "ro-excerpt";
      text.id = `ro-text-${i2}`;
      text.textContent = excerpt(b2);
      main.append(checkboxLabel, handle, number, ...typeIcon(b2, i2), text);
      if (b2.merge_reason) {
        const help = document.createElement("span");
        help.id = `ro-merge-help-${i2}`;
        help.className = "ro-sr";
        help.textContent = b2.merge_reason;
        main.append(help);
        checkbox.setAttribute("aria-describedby", help.id);
        handle.setAttribute("aria-describedby", `ro-instructions ro-keyboard-instructions ${help.id}`);
      }
      if (b2.number !== position) {
        const was = document.createElement("span");
        was.className = "ro-was";
        was.textContent = `Was ${b2.number}`;
        main.append(was);
      }
      if (b2.merge_count) {
        const badge = document.createElement("span");
        badge.className = "ro-was";
        badge.textContent = `Merged \xB7 ${b2.merge_count} ${b2.type === "list" ? "lists" : "paragraphs"}`;
        main.append(badge);
      }
      const details = document.createElement("div");
      details.id = `ro-details-${i2}`;
      details.className = "ro-full";
      details.hidden = true;
      const actions = document.createElement("div");
      actions.className = "ro-card-actions";
      const expand = document.createElement("button");
      expand.type = "button";
      expand.textContent = "Full text";
      expand.setAttribute("aria-expanded", "false");
      expand.setAttribute("aria-controls", details.id);
      if (b2.merge_reason) expand.setAttribute("aria-describedby", `ro-merge-help-${i2}`);
      expand.setAttribute("aria-label", `Show full text for block ${position}`);
      expand.onclick = () => {
        const open = details.hidden;
        details.hidden = !open;
        li.classList.toggle("ro-expanded", open);
        expand.textContent = open ? "Less" : "Full text";
        expand.setAttribute("aria-expanded", String(open));
        if (open) {
          details.replaceChildren(previewNode(b2.preview));
          const note = document.createElement("p");
          note.className = "helper-text";
          note.textContent = `${b2.type} \xB7 Block ${position}${b2.merge_reason ? " \xB7 " + b2.merge_reason : ""}`;
          details.append(note);
          if (b2.originals.length) {
            const heading = document.createElement("strong");
            heading.textContent = "Retained originals (before merge)";
            details.append(heading);
            for (const [originalIndex, origin] of b2.originals.entries()) {
              const label2 = document.createElement("p");
              label2.textContent = `Original ${originalIndex + 1} \xB7 ${origin.type}`;
              details.append(label2, previewNode(origin.preview));
            }
          }
        }
      };
      const label = document.createElement("label");
      label.textContent = "Move to ";
      const dropdown = document.createElement("select");
      dropdown.setAttribute("aria-label", `Move block ${position} to position on source page ${snapshot2.page}`);
      dropdown.disabled = b2.locked || busy || uncertain;
      snapshot2.rows.forEach((target, n2) => {
        const option = new Option(`Block ${target.number}`, String(n2), false, n2 === i2);
        option.disabled = target.locked || target.segment !== b2.segment;
        dropdown.add(option);
      });
      dropdown.onchange = () => move2(id, Number(dropdown.value));
      label.append(dropdown);
      actions.append(expand, label);
      if (b2.merge_count) {
        const unmerge = document.createElement("button");
        unmerge.type = "button";
        unmerge.textContent = "Unmerge";
        unmerge.dataset.unmerge = id;
        unmerge.setAttribute("aria-label", `Unmerge block ${position} into ${b2.merge_count} originals`);
        unmerge.disabled = b2.locked || Boolean(b2.unmerge_reason) || busy || uncertain;
        unmerge.onclick = () => stage({ action: "unmerge", block_id: id });
        actions.append(unmerge);
      }
      li.append(main, actions, details);
      if (b2.locked || b2.unmerge_reason) {
        const help = document.createElement("p");
        help.className = "helper-text ro-locked";
        help.textContent = b2.reason || b2.unmerge_reason;
        li.append(help);
      }
      li.addEventListener("focusin", () => select(id));
      li.addEventListener("click", () => select(id));
      $("ro-cards").append(li);
    }
    $("ro-undo").disabled = !history.length || busy || uncertain;
    $("ro-reset").disabled = !dirty() || busy || uncertain;
    $("ro-apply").disabled = !dirty() || busy || uncertain;
    $("ro-moved").textContent = dirty() ? `${operations.length} staged change${operations.length === 1 ? "" : "s"} \xB7 ${order.length} rows` : "Draft matches saved content";
    updateSelection();
    drawRegions();
    if (focusId) {
      const li = [...$("ro-cards").children].find((c2) => c2.dataset.id === focusId);
      li?.querySelector(".ro-handle:not(:disabled)")?.focus({ preventScroll: true });
      reveal(li, $("ro-cards"));
      if (matchMedia("(max-width:760px) and (max-height:760px)").matches) reveal(li, dialog.querySelector(".ro-columns"));
    }
    if (!dialog.open || busy || uncertain) return;
    manager = new DragDropManager2();
    sortables = [...$("ro-cards").children].map((element, index) => {
      const b2 = row(element.dataset.id);
      return new Sortable2({ id: b2.id, index, group: "page", element, handle: element.querySelector(".ro-handle"), disabled: b2.locked, accept: (source) => row(source.id)?.segment === b2.segment, transition: { duration: 0 } }, manager);
    });
    manager.monitor.addEventListener("dragstart", (event) => {
      dragging = true;
      const source = event.operation.source;
      if (source) {
        select(source.id);
        source.element.classList.add("ro-picked");
        say(`Picked up block ${numberFor(source.id)}. Use arrows to move, Space or Enter to drop, Escape to cancel.`);
      }
    });
    manager.monitor.addEventListener("dragover", (event) => {
      dialog.querySelectorAll(".ro-insertion").forEach((e2) => e2.classList.remove("ro-insertion"));
      event.operation.source?.element?.classList.add("ro-insertion");
    });
    manager.monitor.addEventListener("dragend", (event) => {
      dragging = false;
      const source = event.operation.source, canceled = event.canceled, id = source?.id, index = source?.index, changed = isSortable(source) && source.index !== source.initialIndex;
      requestAnimationFrame(() => {
        if (!dialog.open) return;
        if (canceled) {
          render(id);
          say("Move cancelled. Draft unchanged.");
        } else if (changed) move2(id, index);
        else render(id);
      });
    });
  }
  function move2(id, index) {
    if (busy || uncertain) return;
    const from = order.indexOf(id);
    if (from === index) return;
    const candidate = [...order];
    candidate.splice(from, 1);
    candidate.splice(index, 0, id);
    if (!Number.isInteger(index) || index < 0 || index >= order.length || candidate.some((identity, i2) => snapshot2.rows[i2].locked ? identity !== order[i2] : row(identity).locked || row(identity).segment !== snapshot2.rows[i2].segment)) {
      $("ro-status").textContent = "Shared blocks are fixed boundaries. Move within the same section.";
      render(id);
      return;
    }
    history.push(capture());
    order = candidate;
    operations.push({ action: "order", block_ids: order.filter((id2) => !row(id2).locked) });
    selected = id;
    render(id);
    say(`Moved to block ${snapshot2.rows[index].number}. Draft only.`);
  }
  async function stage(operation) {
    if (busy || uncertain) return;
    const candidate = [...operations, operation];
    try {
      bridge.guard();
      busy = true;
      bridge.busy(true);
      render();
      $("ro-cancel").disabled = true;
      $("ro-close").disabled = true;
      $("ro-status").textContent = "Checking staged changes\u2026";
      const view = await bridge.api(`/api/source-pages/${snapshot2.page}/reading-order/preview`, { method: "POST", headers: bridge.headers(), signal: AbortSignal.timeout(3e4), body: JSON.stringify({ project_id: snapshot2.project_id, expected_review_token: snapshot2.review_token, operations: candidate }) });
      pending = { view, operations: candidate, before: capture(), operation };
      $("ro-confirm-content").replaceChildren();
      const merging = operation.action === "merge";
      $("ro-confirm-heading").textContent = merging ? "Preview merged content" : "Restore retained originals";
      $("ro-confirm-stage").textContent = merging ? "Stage merge" : "Stage unmerge";
      $("ro-confirm-note").textContent = merging ? "Nothing is saved yet. Paragraph boundaries use one joining space. Existing hyphens and internal line breaks stay unchanged. List item boundaries, nesting and recorded numbering stay intact. The result will need review." : "Nothing is saved yet. Restore original content, IDs and review decisions at this row\u2019s current position. Current page assignment is retained. Edited merged content cannot be silently discarded.";
      const ids2 = merging ? operation.block_ids : [operation.block_id];
      for (const id of ids2) {
        const title = document.createElement("h3");
        title.textContent = `${merging ? "Original" : "Merged"} \xB7 Block ${numberFor(id)} (current draft)`;
        $("ro-confirm-content").append(title, previewNode(row(id).preview));
      }
      const results = merging ? [view.rows.find((b2) => b2.id === ids2[0])] : view.rows.filter((b2) => row(operation.block_id).originals.some((o2) => o2.id === b2.id));
      results.forEach((b2, index) => {
        const heading = document.createElement("h3");
        heading.textContent = `${merging ? "Result" : `Restored original ${index + 1}`} \xB7 Block ${b2.number} (after Apply)`;
        $("ro-confirm-content").append(heading, previewNode(b2.preview));
      });
      confirm.showModal();
      $("ro-confirm-cancel").focus();
      $("ro-status").textContent = "Review the exact result, then stage it or keep editing.";
    } catch (error) {
      pending = null;
      $("ro-status").textContent = error.message;
      say(error.message);
    } finally {
      busy = false;
      bridge.busy(false);
      $("ro-cancel").disabled = false;
      $("ro-close").disabled = false;
      render(selected);
    }
  }
  $("ro-merge").onclick = () => {
    const reason = selectionReason();
    if (reason) {
      say(reason);
      return;
    }
    stage({ action: "merge", block_ids: order.filter((id) => checked.has(id)) });
  };
  function cancelConfirmation() {
    const operation = pending?.operation;
    confirm.close();
    pending = null;
    $("ro-status").textContent = "Confirmation cancelled. Draft unchanged.";
    const target = operation?.action === "unmerge" ? [...$("ro-cards").querySelectorAll("[data-unmerge]")].find((e2) => e2.dataset.unmerge === operation.block_id) : $("ro-merge");
    (target && !target.disabled ? target : $("ro-cancel")).focus();
  }
  $("ro-confirm-cancel").onclick = cancelConfirmation;
  confirm.addEventListener("cancel", (event) => {
    event.preventDefault();
    cancelConfirmation();
  });
  $("ro-confirm-stage").onclick = () => {
    if (!pending) return;
    history.push(pending.before);
    snapshot2 = pending.view;
    operations = pending.operations;
    order = snapshot2.rows.map((b2) => b2.id);
    selected = pending.operation.block_ids?.[0] || pending.operation.block_id;
    checked.clear();
    pending = null;
    confirm.close();
    render(selected);
    $("ro-status").textContent = "Change staged. Apply saves it; Cancel leaves saved content untouched.";
    say("Change staged. Apply saves it; Cancel leaves saved content untouched.");
  };
  function finish() {
    clearTimeout(imageTimer);
    destroy();
    dialog.close();
    launch.focus({ preventScroll: true });
  }
  function close() {
    if (busy) return;
    if (dirty()) {
      $("ro-discard-heading").textContent = uncertain ? "Close this draft view?" : "Discard this reading-order draft?";
      discard.querySelector("p").textContent = uncertain ? "The saved result is uncertain. Reload Structure before another change. Closing discards only this local view." : "Nothing has been saved.";
      discard.showModal();
      $("ro-keep").focus();
    } else finish();
  }
  launch.addEventListener("click", async () => {
    if (opening || dialog.open) return;
    opening = true;
    launch.disabled = true;
    const status = $("reading-order-launch-status");
    status.textContent = "";
    try {
      bridge.guard();
      const page = Number($("source-page-number").value);
      snapshot2 = await bridge.api(`/api/source-pages/${page}/reading-order`);
      bridge.guard();
      if (snapshot2.transaction_version !== 1) throw new Error("Relaunch PTW and reload Structure to use the staged merge editor.");
      if (snapshot2.project_id !== launch.dataset.projectId || snapshot2.review_token !== $("manual-reconstruction-control").dataset.reviewToken) throw new Error("The project or saved review changed. Reload Structure before repairing reading order.");
      order = snapshot2.rows.map((b2) => b2.id);
      operations = [];
      history = [];
      checked.clear();
      selected = null;
      uncertain = false;
      baselineKey = key();
      initialView = structuredClone(snapshot2);
      $("ro-heading").textContent = `Repair reading order \xB7 source page ${page}`;
      $("ro-scope").textContent = `${snapshot2.rows.length} included blocks \xB7 ${snapshot2.excluded.length} excluded. Shared blocks are fixed. Order, merge and unmerge stay drafts until one Apply. Other pages and unlocated blocks stay in place.`;
      $("ro-source-title").textContent = `Source page ${page}`;
      imageReady = false;
      imageFailed = false;
      $("ro-image").hidden = false;
      clearTimeout(imageTimer);
      imageTimer = setTimeout(() => {
        imageReady = false;
        imageFailed = true;
        $("ro-image").removeAttribute("src");
        $("ro-image").hidden = true;
        drawRegions();
      }, 3e4);
      $("ro-image").src = `/source-page/${page}.png${$("source-image").dataset.loadedSourceUrl?.split("?")[1] ? "?" + $("source-image").dataset.loadedSourceUrl.split("?")[1] : ""}`;
      $("ro-image").alt = `Rendered source PDF page ${page}`;
      const sourceLink = new URL($("open-source-page").href);
      sourceLink.hash = `page=${page}`;
      $("ro-source-link").href = sourceLink.href;
      $("ro-source-link").textContent = `Open source PDF page ${page}`;
      $("ro-status").textContent = snapshot2.held ? "This page is held for manual reconstruction. Restore it before editing." : "";
      $("ro-excluded-count").textContent = `\xB7 ${snapshot2.excluded.length}`;
      $("ro-excluded").hidden = !snapshot2.excluded.length;
      $("ro-excluded-list").replaceChildren();
      for (const b2 of snapshot2.excluded) {
        const li = document.createElement("li");
        li.textContent = `Block ${b2.number} \xB7 ${excerpt(b2)}`;
        $("ro-excluded-list").append(li);
      }
      dialog.showModal();
      render();
      $("ro-cards").scrollTop = 0;
      $("ro-close").focus({ preventScroll: true });
      if (matchMedia("(max-width:760px) and (max-height:760px)").matches) dialog.querySelector(".ro-columns").scrollTop = dialog.querySelector(".ro-source").offsetHeight;
    } catch (error) {
      status.textContent = error.message;
      bridge.announce(error.message);
    } finally {
      opening = false;
      launch.disabled = false;
    }
  });
  $("ro-image").addEventListener("load", () => {
    clearTimeout(imageTimer);
    imageReady = true;
    imageFailed = false;
    drawRegions();
  });
  $("ro-image").addEventListener("error", () => {
    clearTimeout(imageTimer);
    imageReady = false;
    imageFailed = true;
    $("ro-image").hidden = true;
    drawRegions();
  });
  $("ro-labels").onchange = drawRegions;
  $("ro-close").onclick = close;
  $("ro-cancel").onclick = close;
  dialog.addEventListener("cancel", (event) => {
    event.preventDefault();
    if (!dragging) close();
  });
  $("ro-keep").onclick = () => {
    discard.close();
    $("ro-cancel").focus();
  };
  $("ro-discard-confirm").onclick = () => {
    discard.close();
    finish();
  };
  $("ro-undo").onclick = () => {
    if (history.length && !busy && !uncertain) {
      restore(history.pop());
      render(selected);
      say("Last draft change undone.");
    }
  };
  $("ro-reset").onclick = () => {
    if (!dirty() || busy || uncertain) return;
    history.push(capture());
    while (operations.length) operations.pop();
    snapshot2 = structuredClone(initialView);
    order = snapshot2.rows.map((b2) => b2.id);
    checked.clear();
    selected = null;
    render();
    say("Draft reset.");
  };
  dialog.addEventListener("close", () => {
    pending = null;
  });
  $("ro-apply").onclick = async () => {
    let sent = false;
    try {
      bridge.guard();
      if (busy || uncertain || !dirty()) return;
      busy = true;
      bridge.busy(true);
      destroy();
      dialog.querySelectorAll("button,select,input").forEach((e2) => e2.disabled = true);
      $("ro-status").textContent = "Saving staged changes\u2026";
      sent = true;
      const saved = await bridge.api(`/api/source-pages/${snapshot2.page}/reading-order`, { method: "POST", headers: bridge.headers(), signal: AbortSignal.timeout(3e4), body: JSON.stringify({ project_id: snapshot2.project_id, expected_review_token: snapshot2.review_token, operations }) });
      baselineKey = key();
      $("ro-status").textContent = "Changes saved. Reloading Structure\u2026";
      bridge.saved(snapshot2.page, selected && order.includes(selected) ? selected : order[0], saved.source_page_reviews);
    } catch (error) {
      if (sent && !error.confirmedRejection) {
        uncertain = true;
        bridge.uncertain();
        $("ro-status").textContent = "The save result could not be confirmed. Do not retry. Reload Structure to inspect saved changes; your draft remains here.";
      } else $("ro-status").textContent = error.message;
    } finally {
      busy = false;
      bridge.busy(false);
      if (dialog.open) {
        dialog.querySelectorAll("button,input").forEach((e2) => e2.disabled = false);
        render(selected);
      }
    }
  };
  const compactView = matchMedia("(max-width:760px) and (max-height:760px)");
  compactView.addEventListener("change", () => {
    if (dialog.open && compactView.matches && !dragging) requestAnimationFrame(() => {
      if (dialog.open) {
        const li = [...$("ro-cards").children].find((c2) => c2.dataset.id === (selected || order[0]));
        reveal(li, $("ro-cards"));
        reveal(li, dialog.querySelector(".ro-columns"));
      }
    });
  });
  window.addEventListener("beforeunload", (event) => {
    if (dialog.open && dirty()) {
      event.preventDefault();
      event.returnValue = "";
    }
  });
  window.addEventListener("pagehide", destroy);
};
window.dispatchEvent(new Event("reading-order-ready"));
