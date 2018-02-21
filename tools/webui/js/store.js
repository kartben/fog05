// Generated by CoffeeScript 2.1.1
(function() {
  // This file contain the implementation of a proxy Store for interacting
  // with fog05. Through this API any JS-based runtime can interact with the
  // distributed store used by fog05. As such it can access the full power of
  // fog05
  var Create, Get, GetAll, GetKeys, Keys, NOK, Notify, OK, Observe, Parser, Put, Resolve, ResolveAll, Runtime, Store, Value, Values, exports, fog05, root, z_;

  root = this;

  z_ = root.coffez;

  fog05 = {};

  if (typeof exports !== 'undefined') {
    if (typeof module !== 'undefined' && module.exports) {
      exports = module.exports = fog05;
    }
    exports.fog05 = fog05;
  } else {
    root.fog05 = fog05;
  }

  fog05.VERSION = "0.1.0";

  // Commands
  OK = class OK {
    constructor(oid, sid1, rest) {
      this.oid = oid;
      this.sid = sid1;
      this.rest = rest;
      this.cid = 'OK';
    }

    show() {
      var args;
      args = this.rest.reduce(function(a, x) {
        return a + " " + x;
      });
      return `${this.cid} ${this.oid} ${this.sid} ${this.args}`;
    }

  };

  NOK = class NOK {
    constructor(oid, sid1) {
      this.oid = oid;
      this.sid = sid1;
      this.cid = 'NOK';
    }

    show() {
      return `${this.cid} ${this.oid} ${this.sid}`;
    }

  };

  Create = class Create {
    constructor(sid1, root1, home, cache_size) {
      this.sid = sid1;
      this.root = root1;
      this.home = home;
      this.cache_size = cache_size;
      this.cid = 'create';
    }

    show() {
      return `${this.cid} ${this.sid} ${this.root} ${this.home} ${this.cache_size}`;
    }

  };

  Put = class Put {
    constructor(sid1, uri, value1) {
      this.sid = sid1;
      this.uri = uri;
      this.value = value1;
      this.cid = 'put';
    }

    show() {
      return `${this.cid} ${this.sid} ${this.uri} ${this.value}`;
    }

  };

  Get = class Get {
    constructor(sid1, uri) {
      this.sid = sid1;
      this.uri = uri;
      this.cid = 'get';
    }

    show() {
      return `${this.cid} ${this.sid} ${this.uri}`;
    }

  };

  GetAll = class GetAll {
    constructor(sid1, uri) {
      this.sid = sid1;
      this.uri = uri;
      this.cid = 'aget';
    }

    show() {
      return `${this.cid} ${this.sid} ${this.uri}`;
    }

  };

  Resolve = class Resolve {
    constructor(sid1, uri) {
      this.sid = sid1;
      this.uri = uri;
      this.cid = 'resolve';
    }

    show() {
      return `${this.cid} ${this.sid} ${this.uri}`;
    }

  };

  ResolveAll = class ResolveAll {
    constructor(sid1, uri) {
      this.sid = sid1;
      this.uri = uri;
      this.cid = 'aresolve';
    }

    show() {
      return `${this.cid} ${this.sid} ${this.uri}`;
    }

  };

  Observe = class Observe {
    constructor(sid1, cookie1, uri) {
      this.sid = sid1;
      this.cookie = cookie1;
      this.uri = uri;
      this.cid = 'observe';
    }

    show() {
      return `${this.cid} ${this.sid} ${this.uri} ${this.cookie}`;
    }

  };

  Notify = class Notify {
    constructor(sid1, cookie1, uri, value1) {
      this.sid = sid1;
      this.cookie = cookie1;
      this.uri = uri;
      this.value = value1;
      this.cid = 'notify';
    }

    show() {
      return `${this.cid} ${this.sid} ${this.uri} ${this.value} ${this.cookie}`;
    }

  };

  Value = class Value {
    constructor(sid1, key1, value1) {
      this.sid = sid1;
      this.key = key1;
      this.value = value1;
      this.cid = 'value';
    }

    show() {
      return `${this.cid} ${this.sid} ${this.key} ${this.value}`;
    }

  };

  Values = class Values {
    constructor(sid1, key1, values) {
      this.sid = sid1;
      this.key = key1;
      this.values = values;
      this.cid = 'values';
    }

    show() {
      var str;
      str = this.values.reduce(function(a, v) {
        return a + '|' + v;
      });
      return `${this.cid} ${this.sid} ${this.key} [${str}]`;
    }

  };

  GetKeys = class GetKeys {
    constructor(sid1) {
      this.sid = sid1;
      this.cid = 'gkeys';
    }

    show() {
      return `${this.cid} ${this.sid}`;
    }

  };

  Keys = class Keys {
    constructor(sid1, keys) {
      this.sid = sid1;
      this.keys = keys;
      this.cid = 'keys';
    }

    show() {
      var str;
      str = this.keys.reduce(function(a, v) {
        return a + '|' + v;
      });
      return `${this.cid} ${this.sid} [${str}]`;
    }

  };

  Parser = {};

  Parser.parseOK = function(ts) {
    if (ts.length > 2) {
      return z_.Some(new OK(ts[1], ts[2], ts.slice(3)));
    } else {
      return z_.None;
    }
  };

  Parser.parseNOK = function(ts) {
    if (ts.length > 2) {
      return z_.Some(new NOK(ts[1], ts[2]));
    } else {
      return z_.None;
    }
  };

  Parser.parseNotify = function(ts) {
    if (ts.length > 4) {
      return z_.Some(new Notify(ts[1], ts[2], ts[3], ts[4]));
    } else {
      return z_.None;
    }
  };

  Parser.parseValue = function(ts) {
    if (ts.length === 3) {
      return z_.Some(new Value(ts[1], ts[2], z_.None));
    } else if (ts.length > 3) {
      return z_.Some(new Value(ts[1], ts[2], z_.Some(ts.slice(3).join(' '))));
    } else {
      return z_.None;
    }
  };

  Parser.parseValues = function(ts) {
    var xs;
    if (ts.length === 3) {
      return z_.Some(new Values(ts[1], ts[2], []));
    } else if (ts.length > 3) {
      xs = ts[3].split('|').map(function(x) {
        return x.split('@');
      });
      return z_.Some(new Values(ts[1], ts[2], xs));
    } else {
      return z_.None;
    }
  };

  Parser.parseKeys = function(ts) {
    var xs;
    if (ts.length > 2) {
      xs = ts[2].split('|');
      return z_.Some(new Keys(ts[1], xs));
    } else {
      return z_.None;
    }
  };

  Parser.parseCmd = function(cmd) {
    var t, tokens, x;
    tokens = (function() {
      var i, len, ref, results;
      ref = cmd.split(' ');
      results = [];
      for (i = 0, len = ref.length; i < len; i++) {
        x = ref[i];
        if (x !== '') {
          results.push(x);
        }
      }
      return results;
    })();
    if (tokens.length === 0) {
      return z_.None;
    } else {
      t = tokens[0];
      switch (t) {
        case 'OK':
          return Parser.parseOK(tokens);
        case 'NOK':
          return Parser.parseNOK(tokens);
        case 'notify':
          return Parser.parseNotify(tokens);
        case 'value':
          return Parser.parseValue(tokens);
        case 'values':
          return Parser.parseValues(tokens);
        case 'keys':
          return Parser.parseKeys(tokens);
        default:
          return z_.None;
      }
    }
  };

  // The `Runtime` maintains the connection with the server, re-establish the connection if dropped and mediates
  // the `DataReader` and `DataWriter` communication.
  Runtime = class Runtime {
    // Creates a new fog05 runtime
    constructor(url) {
      // Establish a connection with the dscript.play server
      this.connect = this.connect.bind(this);
      // Disconnects, withouth closing, a `Runtime`. Notice that there is a big difference between disconnecting and
      // closing a `Runtime`. The a disconnected `Runtime` can be reconnected and retains state across
      // connection/disconnections. On the other hand, once closed a `Runtime` clears up all current state.
      this.disconnect = this.disconnect.bind(this);
      // Close the fog05 runtime and as a consequence all the `DataReaders` and `DataWriters` that belong to this runtime.
      this.close = this.close.bind(this);
      this.isConnected = this.isConnected.bind(this);
      this.isClosed = this.isClosed.bind(this);
      this.handleMessage = this.handleMessage.bind(this);
      this.url = url;
      this.onclose = function(evt) {};
      this.onconnect = function() {};
      this.ondisconnect = function(evt) {};
      this.connected = false;
      this.closed = true;
      this.cookieId = 0;
      this.pendingWebSock = z_.None;
      this.webSock = z_.None;
      this.storeMap = {};
    }

    generateCookie() {
      var id;
      id = this.cookieId;
      this.cookieId += 1;
      return id;
    }

    connect() {
      if (this.connected === false) {
        console.log(`Connecting to: ${this.url}`);
        this.pendingWebSock = z_.Some(new WebSocket(this.url));
        this.pendingWebSock.map(((s) => {
          return s.onopen = () => {
            console.log('Connected to: ' + this.url);
            this.webSock = this.pendingWebSock;
            this.connected = true;
            // We may need to re-establish dropped data connection, if this connection is following
            // a disconnection.
            return this.onconnect();
          };
        }));
        this.pendingWebSock.map(((s) => {
          return s.onclose = (evt) => {
            console.log(`The server at ${this.url} seems to have dropped the connection.`);
            this.connected = false;
            this.webSock.close();
            this.closed = true;
            this.webSock = z_.None;
            return this.ondisconnect(evt);
          };
        }));
        return this.pendingWebSock.map(((s) => {
          return s.onmessage = (msg) => {
            return this.handleMessage(msg);
          };
        }));
      } else {
        return console.log("Warning: Trying to connect an already connected Runtime");
      }
    }

    disconnect() {
      this.connected = false;
      this.webSock.map(function(s) {
        return s.close();
      });
      return this.ondisconnect();
    }

    close() {
      return this.webSock.map(((s) => {
        s.close();
        return this.onclose();
      }));
    }

    isConnected() {
      return this.connected;
    }

    isClosed() {
      return this.closed;
    }

    handleMessage(s) {
      var cmd, msg, smap;
      msg = s.data;
      cmd = Parser.parseCmd(msg);
      smap = this.storeMap;
      return cmd.foreach((function(c) {
        return z_.get(smap, c.sid).foreach(function(s) {
          var cid;
          cid = c.cid;
          return s.handleCommand(c);
        });
      }));
    }

    send(msg) {
      return this.webSock.map(function(s) {
        return s.send(msg);
      });
    }

    register(sid, store) {
      return this.storeMap[sid] = store;
    }

  };

  root.fog05.Runtime = Runtime;

  Store = class Store {
    constructor(runtime, sid1, home, root1, cache_size) {
      var cmd;
      this.runtime = runtime;
      this.sid = sid1;
      this.home = home;
      this.root = root1;
      this.cache_size = cache_size;
      this.getTable = {};
      this.obsTable = {};
      this.keyFun = z_.None;
      this.runtime.register(this.sid, this);
      cmd = new Create(this.sid, this.home, this.root, this.cache_size);
      this.runtime.send(cmd.show());
    }

    put(key, value) {
      var cmd;
      cmd = new Put(this.sid, key, value);
      return this.runtime.send(cmd.show());
    }

    keys(fun) {
      var cmd;
      this.keyFun = z_.Some(fun);
      cmd = new GetKeys(this.sid);
      return this.runtime.send(cmd.show());
    }

    get(key, fun) {
      var cmd;
      this.getTable[key] = fun;
      cmd = new Get(this.sid, key);
      return this.runtime.send(cmd.show());
    }

    getAll(key, fun) {
      var cmd;
      this.getTable[key] = fun;
      cmd = new GetAll(this.sid, key);
      return this.runtime.send(cmd.show());
    }

    resolve(key, fun) {
      var cmd;
      this.getTable[key] = fun;
      cmd = new Resolve(this.sid, key);
      return this.runtime.send(cmd.show());
    }

    resolveAll(key, fun) {
      var cmd;
      this.getTable[key] = fun;
      cmd = new Resolve(this.sid, key);
      return this.runtime.send(cmd.show());
    }

    observe(key, fun) {
      var cmd, cookie;
      cookie = this.runtime.generateCookie();
      this.obsTable[cookie] = fun;
      cmd = new Observe(this.sid, cookie, key);
      return this.runtime.send(cmd.show());
    }

    handleOK(cmd) {
      return console.log('>>> Store Handling OK');
    }

    handleNOK(cmd) {
      return console.log('>>> Store Handling NOK');
    }

    handleValue(cmd) {
      console.log('>>> Store Handling Value');
      return z_.get(this.getTable, cmd.key).foreach(function(fun) {
        return fun(cmd.key, cmd.value);
      });
    }

    handleValues(cmd) {
      console.log('>>> Store Handling Values');
      return z_.get(this.getTable, cmd.key).foreach(function(fun) {
        return fun(cmd.key, cmd.values);
      });
    }

    handleNotify(cmd) {
      console.log('>>> Store Handling Notify');
      return z_.get(this.obsTable, cmd.cookie).foreach(function(fun) {
        return fun(cmd.uri, cmd.value);
      });
    }

    handleKeys(cmd) {
      return this.keyFun.foreach(function(f) {
        return f(cmd.keys);
      });
    }

    // No so elegant, but there were issues with the map of lambdas.
    handleCommand(cmd) {
      switch (cmd.cid) {
        case 'NOK':
          return this.handleNOK(cmd);
        case 'OK':
          return this.handleOK(cmd);
        case 'value':
          return this.handleValue(cmd);
        case 'values':
          return this.handleValues(cmd);
        case 'keys':
          return this.handleKeys(cmd);
        case 'notify':
          return this.handleNotify(cmd);
      }
    }

  };

  root.fog05.Store = Store;

}).call(this);